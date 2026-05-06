from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from core.decorators import login_required
from core.views import get_context
from .services import TicketService
from .models import TicketCategory, TicketPriority
from core.utils import get_school_dropdown
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

# Security configuration for chat attachments
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


@login_required
def ticket_list(request):
    """Display ticket list with filters"""
    context = get_context(request)
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    # Get filter parameters
    filters = {
        'school_id': request.GET.get('school_id'),
        'assigned_to': request.GET.get('assigned_to'),
        'status': request.GET.get('status'),
        'category': request.GET.get('category'),
        'priority': request.GET.get('priority'),
        'search': request.GET.get('search'),
        'from_date': request.GET.get('from_date'),
        'to_date': request.GET.get('to_date')
    }
    
    # Normalize filters: convert empty strings to None (Prevents PostgreSQL integer cast error)
    filters = {k: (v if v != '' else None) for k, v in filters.items()}
    
    # Auto-filter for School Admin if school_id is not specified
    if role_name == 'School Admin' and not filters.get('school_id'):
        filters['school_id'] = context.get('school_id')
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    sort_column = request.GET.get('sort') or 'CreatedAt'
    sort_direction = request.GET.get('direction') or 'DESC'
    
    # Get tickets
    result = TicketService.get_tickets(
        user_id, role_name, filters, page, page_size, sort_column, sort_direction
    )
    
    if not result['success']:
        messages.error(request, result.get('error', 'Error loading tickets'))
        result['tickets'] = []
        result['total_count'] = 0
    
    # Get categories and priorities for filters
    categories = TicketCategory.objects.filter(is_deleted=False)
    priorities = TicketPriority.objects.filter(is_deleted=False).order_by('priority_level')
    
    # Get schools for Super Admin
    schools = []
    if role_name == 'Super Admin' or role_name == 'Support Executive':
        schools = get_school_dropdown()
    
    # Get support executives for assignment
    executives_result = TicketService.get_support_executives()
    executives = executives_result.get('executives', []) if executives_result['success'] else []
    
    # Get KPIs from all tickets (not paginated)
    kpis_result = TicketService.get_ticket_kpis(user_id, role_name, filters)
    kpis = kpis_result.get('kpis', {
        'open': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0,
        'reopened': 0,
    })
    
    import math
    total_pages = math.ceil(result['total_count'] / page_size) if page_size > 0 else 1
    
    record_offset = (page - 1) * page_size
    
    context.update({
        'tickets': result['tickets'],
        'total_count': result['total_count'],
        'total_pages': total_pages,
        'page': page,
        'page_size': page_size,
        'record_offset': record_offset,
        'categories': categories,
        'priorities': priorities,
        'schools': schools,
        'executives': executives,
        'filters': filters,
        'kpis': kpis,
        'role_name': role_name,
        'can_create': role_name in ['Super Admin', 'School Admin'],
        'can_assign': role_name == 'Super Admin',
    })
    
    return render(request, 'tickets/ticket_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def ticket_create(request):
    """Create a new ticket"""
    context = get_context(request)
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    # Check permission
    if role_name not in ['Super Admin', 'School Admin']:
        messages.error(request, 'You do not have permission to create tickets')
        return redirect('tickets:ticket_list')
    
    if request.method == 'POST':
        school_id = request.POST.get('school_id')
        if not school_id:
            school_id = context.get('school_id')
            
        category_id = request.POST.get('category_id')
        priority = request.POST.get('priority')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        source = request.POST.get('source', 'Website')
        
        # Validate required fields
        if not all([school_id, category_id, priority, subject, description, source]):
            messages.error(request, 'All fields are required (including School selection)')
            return render(request, 'tickets/ticket_create.html', context)
        
        # Handle file upload
        file_data = None
        file_name = None
        file_size = None
        content_type = None
        if 'attachment' in request.FILES:
            file = request.FILES['attachment']
            file_data = file.read()
            file_name = file.name
            file_size = file.size
            content_type = file.content_type
        
        # Create ticket
        result = TicketService.create_ticket(
            user_id, role_name, school_id, category_id, priority, subject, description,
            file_data, file_name, file_size, content_type, source
        )
        
        if result['success']:
            from core.url_encryption import encrypt_id
            messages.success(request, f'Ticket #{result["ticket_number"]} created successfully!', extra_tags='modal')
            token = encrypt_id(result['ticket_id'])
            return redirect('tickets:ticket_detail', token=token)
        else:
            messages.error(request, result.get('error', 'Error creating ticket'))
    
    # Get categories and priorities
    categories = TicketCategory.objects.filter(is_deleted=False)
    priorities = TicketPriority.objects.filter(is_deleted=False).order_by('priority_level')
    
    # Get schools for Super Admin
    schools = []
    if role_name == 'Super Admin':
        schools = get_school_dropdown()
    
    context.update({
        'categories': categories,
        'priorities': priorities,
        'schools': schools,
        'role_name': role_name,
    })
    
    return render(request, 'tickets/ticket_create.html', context)


@login_required
def ticket_detail(request, token):
    """Display ticket details"""
    from core.url_encryption import decrypt_id
    
    context = get_context(request)
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    # Decrypt ticket ID
    ticket_id = decrypt_id(token)
    if not ticket_id:
        messages.error(request, 'Invalid ticket link')
        return redirect('tickets:ticket_list')
    
    # Get ticket details
    result = TicketService.get_ticket_details(user_id, role_name, ticket_id)
    
    if not result['success']:
        messages.error(request, result.get('error', 'Error loading ticket'))
        return redirect('tickets:ticket_list')
    
    ticket = result['ticket']
    activities = result['activities']
    comments = result['comments']
    attachments = result['attachments']
    
    # Parse JSON date strings into datetime objects for template formatting
    from datetime import datetime
    if ticket.get('CreatedAt'):
        try:
            ticket['CreatedAt'] = datetime.fromisoformat(ticket['CreatedAt'].replace('Z', '+00:00'))
        except (ValueError, TypeError): pass
    if ticket.get('UpdatedAt'):
        try:
            if isinstance(ticket['UpdatedAt'], str):
                ticket['UpdatedAt'] = datetime.fromisoformat(ticket['UpdatedAt'].replace('Z', '+00:00'))
            # If after parsing it is still aware, make it naive in Local Time IF USE_TZ is False
            if ticket['UpdatedAt'].tzinfo:
                 ticket['UpdatedAt'] = ticket['UpdatedAt'].astimezone(None).replace(tzinfo=None)
        except Exception: pass
    
    # Get support executives for assignment
    executives_result = TicketService.get_support_executives()
    executives = executives_result.get('executives', []) if executives_result['success'] else []
    
    # Determine available actions based on role and status
    current_status = ticket.get('CurrentStatus')
    available_actions = []
    
    # Support Executive & Super Admin: Status movement (In Progress, Resolved)
    if role_name in ['Support Executive', 'Super Admin']:
        if current_status in ['Open', 'Reopened']:
            available_actions.append({'status': 'In Progress', 'label': 'Start Working', 'class': 'warning'})
        elif current_status == 'In Progress':
            available_actions.append({'status': 'Resolved', 'label': 'Mark Resolved', 'class': 'success'})
            
    # Super Admin & School Admin: Closure Management & Re-opening (RESTRICTED)
    # Note: Support Executives are explicitly excluded from Re-opening permissions
    if role_name in ['Super Admin', 'School Admin']:
        if current_status in ['Resolved', 'Closed']:
            # USER REQUIREMENT: Reopen only allowed within 3 days (72 hours) of last update
            can_reopen = True
            updated_at = ticket.get('UpdatedAt')
            if updated_at:
                # updated_at is already normalized to local naive datetime above
                diff = datetime.now() - updated_at
                if diff.days >= 3:
                    can_reopen = False
            
            if can_reopen:
                available_actions.append({'status': 'Reopened', 'label': 'Reopen Ticket', 'class': 'danger'})
        
        # Only Super Admin can permanently Close a Resolved ticket
        if role_name == 'Super Admin' and current_status == 'Resolved':
            available_actions.append({'status': 'Closed', 'label': 'Close Ticket', 'class': 'success'})
    
    # Create unified timeline (Comments + Activities)
    timeline = []
    
    # 1. Add Activities (Audit Trail)
    for a in activities:
        # Parse activity timestamp
        if a.get('Timestamp'):
            try:
                if isinstance(a['Timestamp'], str):
                    a['Timestamp'] = datetime.fromisoformat(a['Timestamp'].replace('Z', '+00:00'))
                if a['Timestamp'].tzinfo:
                    a['Timestamp'] = a['Timestamp'].astimezone(None).replace(tzinfo=None)
            except Exception: pass
            
        timeline.append({
            'type': 'activity',
            'data': a,
            'time': a.get('Timestamp')
        })

    # 2. Add Comments
    for c in comments:
        # Parse comment creation date
        if c.get('CreatedAt'):
            try:
                if isinstance(c['CreatedAt'], str):
                    c['CreatedAt'] = datetime.fromisoformat(c['CreatedAt'].replace('Z', '+00:00'))
                if c['CreatedAt'].tzinfo:
                    c['CreatedAt'] = c['CreatedAt'].astimezone(None).replace(tzinfo=None)
            except Exception: pass
            
        # Add secure attachment URL if present
        if c.get('AttachmentID'):
             from core.url_encryption import encrypt_id
             import os
             c['AttachmentURL'] = reverse('tickets:ticket_attachment', kwargs={'token': encrypt_id(c['AttachmentID'])})
             # Identify if it's an image
             ext = os.path.splitext(c.get('AttachmentName', '') or '')[1].lower()
             c['IsImage'] = ext in {'.png', '.jpg', '.jpeg', '.gif'}
 
        timeline.append({
            'type': 'comment', 
            'data': c, 
            'time': c.get('CreatedAt')
        })
    
    # Sort timeline by date
    timeline.sort(key=lambda x: x['time'] if x['time'] else datetime.min)

    today = date.today()
    yesterday = today - timedelta(days=1)

    context.update({
        'ticket': ticket,
        'timeline': timeline,
        'attachments': attachments,
        'executives': executives,
        'available_actions': available_actions,
        'role_name': role_name,
        'user_id': user_id,
        'today': today,
        'yesterday': yesterday,
        'can_assign': role_name == 'Super Admin' and current_status in ['Open', 'Reopened'],
        'can_comment': True,
    })
    
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
@require_POST
def ticket_assign(request):
    """Assign ticket to support executive"""
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    ticket_id = request.POST.get('ticket_id')
    assign_to_user_id = request.POST.get('assign_to_user_id')
    comment = request.POST.get('comment', '')
    
    logger.info(f"Assign attempt - UserID: {user_id}, RoleName: {role_name}, TicketID: {ticket_id}, AssignTo: {assign_to_user_id}, Comment: {comment}")
    
    result = TicketService.assign_ticket(user_id, role_name, ticket_id, assign_to_user_id, comment)
    
    logger.info(f"Assign result: {result}")
    
    if result['success']:
        messages.success(request, 'Ticket assigned successfully')
    else:
        messages.error(request, result.get('error', 'Error assigning ticket'))
    
    from core.url_encryption import encrypt_id
    token = encrypt_id(ticket_id)
    return redirect('tickets:ticket_detail', token=token)


@login_required
@require_POST
def ticket_update_status(request):
    """Update ticket status"""
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    ticket_id = request.POST.get('ticket_id')
    new_status = request.POST.get('new_status')
    comment = request.POST.get('comment', '')
    
    result = TicketService.update_status(user_id, role_name, ticket_id, new_status, comment)
    
    if result['success']:
        messages.success(request, f'Ticket status updated to {new_status}')
    else:
        messages.error(request, result.get('error', 'Error updating ticket status'))
    
    from core.url_encryption import encrypt_id
    token = encrypt_id(ticket_id)
    return redirect('tickets:ticket_detail', token=token)


@login_required
@require_POST
def ticket_add_comment(request):
    """Add comment to ticket"""
    from datetime import datetime
    from core.url_encryption import encrypt_id
    
    user_id = request.session.get('UserId')
    user_name = request.session.get('UserName', 'User')
    ticket_id = request.POST.get('ticket_id')
    comment_text = request.POST.get('comment_text', '').strip()
    is_internal = request.POST.get('is_internal') == 'true'
    reply_to_comment_id = request.POST.get('reply_to_comment_id') or None
    
    # Handle file upload
    file_data = None
    file_name = None
    file_size = None
    content_type = None
    attachment_id = None
    if 'attachment' in request.FILES:
        file = request.FILES['attachment']
        file_name = file.name
        file_size = file.size
        content_type = file.content_type
        
        # Security: Extension check
        import os
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'})
            messages.error(request, f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}')
            token = encrypt_id(ticket_id)
            return redirect('tickets:ticket_detail', token=token)
            
        # Security: Size check
        if file_size > MAX_FILE_SIZE:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'File too large. Max size: 1MB'})
            messages.error(request, 'File too large. Max size: 1MB')
            token = encrypt_id(ticket_id)
            return redirect('tickets:ticket_detail', token=token)

        file_data = file.read()
    
    # Require either text or attachment
    if not comment_text and not file_data:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Please enter a message or attach a file'})
        messages.error(request, 'Please enter a message or attach a file')
        token = encrypt_id(ticket_id)
        return redirect('tickets:ticket_detail', token=token)
    
    # Use placeholder text if only attachment
    if not comment_text and file_data:
        comment_text = f'Sent {file_name}'
    
    result = TicketService.add_comment(ticket_id, user_id, comment_text, is_internal, file_data, file_name, file_size, content_type, reply_to_comment_id)
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if result['success']:
            comment_data = {
                'id': result.get('comment_id'),
                'text': comment_text,
                'user_name': user_name,
                'user_id': user_id,
                'time': datetime.now().strftime('%H:%M'),
                'is_internal': is_internal,
                'attachment_name': file_name,
                'attachment_url': f"/tickets/attachment/{encrypt_id(result.get('attachment_id'))}/" if result.get('attachment_id') else None,
                'is_image': file_name and any(file_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']) if file_name else False,
                'reply_to': None
            }
            
            # Get reply info if replying
            if reply_to_comment_id:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT c."CommentID", u."UserName", c."CommentText"
                        FROM "TicketComments" c
                        JOIN "UserMaster" u ON c."CommentByUserID" = u."UserID"
                        WHERE c."CommentID" = %s
                    """, [reply_to_comment_id])
                    reply_row = cursor.fetchone()
                    if reply_row:
                        comment_data['reply_to'] = {
                            'id': reply_row[0],
                            'name': reply_row[1],
                            'text': reply_row[2][:100]
                        }
            
            return JsonResponse({'success': True, 'comment': comment_data})
        else:
            return JsonResponse({'success': False, 'error': result.get('error', 'Error sending message')})
    
    # Handle normal form submission
    if result['success']:
        messages.success(request, 'Message sent successfully')
    else:
        messages.error(request, result.get('error', 'Error sending message'))
    
    token = encrypt_id(ticket_id)
    from django.http import HttpResponseRedirect
    from django.urls import reverse
    url = reverse('tickets:ticket_detail', kwargs={'token': token})
    return HttpResponseRedirect(url + '#chat-section')


# API Endpoints for AJAX
@login_required
def api_tickets_list(request):
    """API endpoint for ticket list (AJAX)"""
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    filters = {
        'school_id': request.GET.get('school_id'),
        'assigned_to': request.GET.get('assigned_to'),
        'status': request.GET.get('status'),
        'category': request.GET.get('category'),
        'priority': request.GET.get('priority'),
        'search': request.GET.get('search'),
        'from_date': request.GET.get('from_date'),
        'to_date': request.GET.get('to_date')
    }
    
    # Normalize filters: convert empty strings to None
    filters = {k: (v if v != '' else None) for k, v in filters.items()}
    
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    
    result = TicketService.get_tickets(user_id, role_name, filters, page, page_size)
    
    if result['success']:
        # Convert datetime objects to strings
        for ticket in result['tickets']:
            for key, value in ticket.items():
                if hasattr(value, 'isoformat'):
                    ticket[key] = value.isoformat()
        
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=result.get('code', 500))


@login_required
def api_support_executives(request):
    """API endpoint to get support executives"""
    result = TicketService.get_support_executives()
    
    if result['success']:
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=result.get('code', 500))


@login_required
def api_ticket_insights(request):
    """API endpoint to get ticket insights dashboard"""
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    school_id = request.GET.get('school_id')
    if school_id == '': school_id = None
    
    # Default to current month start and end if not provided
    if not start_date or not end_date:
        from datetime import datetime
        import calendar
        now = datetime.now()
        if not start_date:
            start_date = now.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            _, last_day = calendar.monthrange(now.year, now.month)
            end_date = now.replace(day=last_day).strftime('%Y-%m-%d')
    
    result = TicketService.get_ticket_insights(user_id, role_name, start_date, end_date, school_id)
    
    if result['success']:
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        # Ensure all trends have ISO format dates (already handled but safe to keep or rely on encoder)
        return JsonResponse(result, encoder=DjangoJSONEncoder)
    else:
        return JsonResponse(result, status=result.get('code', 500))


# Secure Attachment Handler
def ticket_attachment(request, token):
    """Securely serve ticket attachments from database"""
    from core.url_encryption import decrypt_id
    from django.db import connection
    from django.http import HttpResponse, Http404
    
    attachment_id = decrypt_id(token)
    if not attachment_id:
        raise Http404("Attachment not found")
        
    user_id = request.session.get('UserId')
    role_name = request.session.get('ProfileName')
    
    try:
        with connection.cursor() as cursor:
            # Get attachment and its ticket_id for permission check
            cursor.execute("""
                SELECT "FileData", "FileName", "ContentType", "FileSize", "TicketID"
                FROM "TicketAttachments"
                WHERE "AttachmentID" = %s AND "IsDeleted" = FALSE
            """, [attachment_id])
            
            row = cursor.fetchone()
            if not row:
                raise Http404("Attachment not found")
                
            file_data, file_name, content_type, file_size, ticket_id = row
            
            # Security: Verify ticket access
            # We reuse the logic from ticket_detail conceptually
            # Simpler: check if user's school matches or if super admin/executive
            # Better: call a lightweight check
            cursor.execute("""
                SELECT 1 FROM "TicketMaster" t
                WHERE t."TicketID" = %s AND (
                   %s = 'Super Admin' OR %s = 'Support Executive' OR
                   t."CreatedByUserID" = %s OR 
                   t."SchoolID" = (SELECT "SchoolID" FROM "UserMaster" WHERE "UserID" = %s)
                )
            """, [ticket_id, role_name, role_name, user_id, user_id])
            
            if not cursor.fetchone():
                return HttpResponse("Access Denied", status=403)
            
            response = HttpResponse(file_data, content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{file_name}"'
            response['Content-Length'] = file_size
            return response
            
    except Exception as e:
        logger.error(f"Error serving attachment {attachment_id}: {str(e)}")
        raise Http404("Internal Server Error")
