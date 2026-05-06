import logging
import json
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import connection
from .decorators import custom_login_required
from .utils import get_context, _get_custom_session_info, get_school_dropdown

logger = logging.getLogger(__name__)

def ensure_email_templates_for_school(school_id):
    """
    Ensure email templates exist for the given school.
    If templates don't exist, create them by copying from a template school.
    """
    if not school_id:
        logger.warning("No school_id provided for email template check")
        return
    
    try:
        with connection.cursor() as cursor:
            # Check if templates already exist for this school
            cursor.execute("""
                SELECT COUNT(*) FROM "EmailTemplate" 
                WHERE "Code" = 'ADMISSION_ACKNOWLEDGMENT' AND "SchoolId" = %s
            """, [school_id])
            admission_exists = cursor.fetchone()[0] > 0
            
            cursor.execute("""
                SELECT COUNT(*) FROM "EmailTemplate" 
                WHERE "Code" = 'PAYMENT_RECEIPT' AND "SchoolId" = %s
            """, [school_id])
            payment_exists = cursor.fetchone()[0] > 0
            
            logger.info(f"Email templates for SchoolId {school_id}: ADMISSION_ACKNOWLEDGMENT={admission_exists}, PAYMENT_RECEIPT={payment_exists}")
            
            # If templates don't exist, create them
            if not admission_exists or not payment_exists:
                logger.info(f"Creating missing email templates for SchoolId {school_id}")
                
                # Find a school that has the templates (preferably SchoolId 3)
                cursor.execute("""
                    SELECT "SchoolId" FROM "EmailTemplate" 
                    WHERE "Code" = 'ADMISSION_ACKNOWLEDGMENT' 
                    ORDER BY "SchoolId"
                """)
                template_school_result = cursor.fetchone()
                
                if template_school_result:
                    template_school_id = template_school_result[0]
                    logger.info(f"Using templates from SchoolId {template_school_id}")
                    
                    # Copy ADMISSION_ACKNOWLEDGMENT template if missing
                    if not admission_exists:
                        cursor.execute("""
                            INSERT INTO "EmailTemplate" 
                            ("Code", "SchoolId", "Language", "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "IsActive", "CreatedAt", "UpdatedAt")
                            SELECT "Code", %s as "SchoolId", "Language", "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "IsActive", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            FROM "EmailTemplate" 
                            WHERE "Code" = 'ADMISSION_ACKNOWLEDGMENT' AND "SchoolId" = %s
                        """, [school_id, template_school_id])
                        logger.info(f"Created ADMISSION_ACKNOWLEDGMENT template for SchoolId {school_id}")
                    
                    # Copy PAYMENT_RECEIPT template if missing
                    if not payment_exists:
                        cursor.execute("""
                            INSERT INTO "EmailTemplate" 
                            ("Code", "SchoolId", "Language", "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "IsActive", "CreatedAt", "UpdatedAt")
                            SELECT "Code", %s as "SchoolId", "Language", "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "IsActive", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            FROM "EmailTemplate" 
                            WHERE "Code" = 'PAYMENT_RECEIPT' AND "SchoolId" = %s
                        """, [school_id, template_school_id])
                        logger.info(f"Created PAYMENT_RECEIPT template for SchoolId {school_id}")
                else:
                    logger.error("No template school found with ADMISSION_ACKNOWLEDGMENT template")
            else:
                logger.info(f"Email templates already exist for SchoolId {school_id}")
                
    except Exception as e:
        logger.error(f"Error ensuring email templates for SchoolId {school_id}: {e}")


# EmailTemplate Management Views
@custom_login_required
def email_template_list(request):
    """
    EmailTemplate list view - Display all email templates
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user context for header
    context = get_context(request)
    
    # Get session info for user object (needed for header template)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    school_id = request.session.get('SchoolID')
    
    
    if not user_id:
        messages.error(request, "Please login to access email template management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        logger.warning(f"Access denied - ProfileID {profile_id} not in [1, 2]")
        messages.error(request, "You don't have permission to access email template management")
        return redirect('dashboard')
    
    # Initialize variables
    email_templates = []
    
    try:
        with connection.cursor() as cursor:
            # Get search and filter parameters from request
            search_query = request.GET.get('search', '').strip()
            school_filter = request.GET.get('school_id', '')
            search_param = search_query if search_query else None
            
            # Determine school_id parameter for stored procedure
            if profile_id == 1:  # Super Admin - can filter by school or see all
                school_id_param = int(school_filter) if school_filter else None
            else:  # School Admin - only their school's templates
                school_id_param = int(school_filter) if school_filter else school_id
            
            # Use stored procedure for better performance and consistency
            # Following the exact same pattern as Menu Data Management
            cursor.execute('SELECT * FROM "Proc_EmailTemplate_List"(%s, %s, %s)', 
                         [user_id, school_id_param, search_param])
            
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                template = dict(zip(columns, row))
                email_templates.append(template)
            
    
    except Exception as e:
        logger.error(f"Error fetching email templates: {str(e)}")
        messages.error(request, "Error loading email templates")
        email_templates = []
    
    # Get schools for dropdown (only for Super Admin)
    schools = []
    if profile_id == 1:  # Super Admin only
        schools = get_school_dropdown()
    
    # Add context info
    context.update({
        'email_templates': email_templates,
        'total_count': len(email_templates),
        'schools': schools,
        'school_filter': school_filter,
        'search_query': search_query,
        'is_super_admin': profile_id == 1,
        'page_title': 'Email Template Management',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Email Templates', 'url': None}
        ]
    })
    
    return render(request, 'core/email_template_list.html', context)


@custom_login_required
def email_template_add(request):
    """
    Add new email template
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user context for header
    context = get_context(request)
    
    # Get session info for user object (needed for header template)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    school_id = request.session.get('SchoolID')
    
    if not user_id:
        messages.error(request, "Please login to access email template management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access email template management")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Extract form data
            code = request.POST.get('code', '').strip()
            language = request.POST.get('language', 'en').strip()
            school_selection = request.POST.get('school_id', '').strip()
            subject_template = request.POST.get('subject_template', '').strip()
            body_text_template = request.POST.get('body_text_template', '').strip()
            body_html_template = request.POST.get('body_html_template', '').strip()
            default_from = request.POST.get('default_from', '').strip()
            cc = request.POST.get('cc', '').strip()
            bcc = request.POST.get('bcc', '').strip()
            placeholders = request.POST.get('placeholders', '').strip()
            is_active = request.POST.get('is_active', '1')
            
            # Validation
            errors = []
            if not code:
                errors.append("Code is required")
            if not subject_template:
                errors.append("Subject template is required")
            if not body_text_template and not body_html_template:
                errors.append("At least one body template (text or HTML) is required")
            
            if errors:
                context.update({
                    'errors': errors,
                    'form_data': request.POST
                })
            else:
                # Use stored procedure to insert new email template
                with connection.cursor() as cursor:
                    # Prepare parameters for stored procedure
                    # Determine school_id based on user role and selection
                    if profile_id == 1:  # Super Admin - can select any school or global
                        school_id_param = int(school_selection) if school_selection else None
                    else:  # School Admin - automatically use their school
                        school_id_param = school_id
                    
                    # Execute stored procedure
                    cursor.execute("""
                        SELECT "Message" FROM "Proc_EmailTemplate_Manage"(
                            'INSERT',
                            NULL,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    """, [
                        code,
                        school_id_param,
                        language,
                        subject_template,
                        body_text_template if body_text_template else None,
                        body_html_template if body_html_template else None,
                        default_from if default_from else None,
                        cc if cc else None,
                        bcc if bcc else None,
                        placeholders if placeholders else None,
                        True if is_active == '1' else False,
                        user_id
                    ])
                    
                    # Get the result message
                    result = cursor.fetchone()
                    logger.info(f"Stored procedure result: {result}")
                    
                    if result and len(result) > 0:
                        message = result[0] if result[0] else "Email template added successfully"
                        
                        # Check for success indicators
                        if message.startswith('✅') or 'successfully' in message.lower():
                            messages.success(request, message)
                            redirect_url = reverse('email_template_list')
                            if school_selection:
                                redirect_url += f'?school_id={school_selection}'
                            return redirect(redirect_url)
                        else:
                            messages.error(request, message)
                            context.update({'form_data': request.POST})
                    else:
                        # If no message returned, assume success
                        messages.success(request, "✅ Email template created successfully.")
                        redirect_url = reverse('email_template_list')
                        if school_selection:
                            redirect_url += f'?school_id={school_selection}'
                        return redirect(redirect_url)
        
        except Exception as e:
            logger.error(f"Error adding email template: {str(e)}")
            messages.error(request, "Error adding email template. Please try again.")
            context.update({'form_data': request.POST})
    
    # Get schools for dropdown (only for Super Admin)
    schools = []
    if profile_id == 1:  # Super Admin only
        schools = get_school_dropdown()
    
    context.update({
        'schools': schools,
        'is_super_admin': profile_id == 1,
        'page_title': 'Add Email Template',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Email Templates', 'url': 'email_template_list'},
            {'name': 'Add Email Template', 'url': None}
        ]
    })
    
    return render(request, 'core/email_template_add.html', context)


@custom_login_required
def email_template_edit(request, template_id):
    """
    Edit existing email template
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user context for header
    context = get_context(request)
    
    # Get session info for user object (needed for header template)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    school_id = request.session.get('SchoolID')
    
    if not user_id:
        messages.error(request, "Please login to access email template management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access email template management")
        return redirect('dashboard')
    
    # Get template data
    template = None
    try:
        with connection.cursor() as cursor:
            # Check if template exists and user has permission
            if profile_id == 1:  # Super Admin - can edit any template
                cursor.execute("""
                    SELECT 
                        "Id", "Code", "SchoolId", "Language", "SubjectTemplate", 
                        "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", 
                        "Cc", "Bcc", "Placeholders", "IsActive", "CreatedAt", "UpdatedAt"
                    FROM "EmailTemplate" 
                    WHERE "Id" = %s
                """, [template_id])
            else:  # School Admin - only their school's templates
                cursor.execute("""
                    SELECT 
                        "Id", "Code", "SchoolId", "Language", "SubjectTemplate", 
                        "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", 
                        "Cc", "Bcc", "Placeholders", "IsActive", "CreatedAt", "UpdatedAt"
                    FROM "EmailTemplate" 
                    WHERE "Id" = %s AND ("SchoolId" = %s OR "SchoolId" IS NULL)
                """, [template_id, school_id])
            
            row = cursor.fetchone()
            if row:
                template = {
                    'id': row[0],
                    'code': row[1],
                    'school_id': row[2],
                    'language': row[3],
                    'subject_template': row[4],
                    'body_text_template': row[5],
                    'body_html_template': row[6],
                    'default_from': row[7],
                    'cc': row[8],
                    'bcc': row[9],
                    'placeholders': row[10],
                    'is_active': row[11],
                    'created_at': row[12],
                    'updated_at': row[13]
                }
            else:
                messages.error(request, "Email template not found or you don't have permission to edit it")
                return redirect('email_template_list')
    
    except Exception as e:
        logger.error(f"Error fetching email template: {str(e)}")
        messages.error(request, "Error loading email template data")
        return redirect('email_template_list')
    
    if request.method == 'POST':
        try:
            # Extract form data
            code = request.POST.get('code', '').strip()
            language = request.POST.get('language', 'en').strip()
            school_selection = request.POST.get('school_id', '').strip()
            subject_template = request.POST.get('subject_template', '').strip()
            body_text_template = request.POST.get('body_text_template', '').strip()
            body_html_template = request.POST.get('body_html_template', '').strip()
            default_from = request.POST.get('default_from', '').strip()
            cc = request.POST.get('cc', '').strip()
            bcc = request.POST.get('bcc', '').strip()
            placeholders = request.POST.get('placeholders', '').strip()
            is_active = request.POST.get('is_active', '1')
            
            # Validation
            errors = []
            if not code:
                errors.append("Code is required")
            if not subject_template:
                errors.append("Subject template is required")
            if not body_text_template and not body_html_template:
                errors.append("At least one body template (text or HTML) is required")
            
            if errors:
                context.update({
                    'errors': errors,
                    'form_data': request.POST,
                    'template': template
                })
            else:
                # Use stored procedure to update email template
                with connection.cursor() as cursor:
                    # Prepare parameters for stored procedure
                    # Determine school_id based on user role and selection
                    if profile_id == 1:  # Super Admin - can select any school or global
                        school_id_param = int(school_selection) if school_selection else None
                    else:  # School Admin - automatically use their school
                        school_id_param = school_id
                    
                    # Execute stored procedure
                    cursor.execute("""
                        SELECT "Message" FROM "Proc_EmailTemplate_Manage"(
                            'UPDATE',
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    """, [
                        template_id,
                        code,
                        school_id_param,
                        language,
                        subject_template,
                        body_text_template if body_text_template else None,
                        body_html_template if body_html_template else None,
                        default_from if default_from else None,
                        cc if cc else None,
                        bcc if bcc else None,
                        placeholders if placeholders else None,
                        True if is_active == '1' else False,
                        user_id
                    ])
                    
                    # Get the result message
                    result = cursor.fetchone()
                    logger.info(f"Stored procedure result: {result}")
                    
                    if result and len(result) > 0:
                        message = result[0] if result[0] else "Email template updated successfully"
                        
                        # Check for success indicators
                        if message.startswith('✅') or 'successfully' in message.lower():
                            messages.success(request, message)
                            redirect_url = reverse('email_template_list')
                            if school_selection:
                                redirect_url += f'?school_id={school_selection}'
                            return redirect(redirect_url)
                        else:
                            messages.error(request, message)
                            context.update({'form_data': request.POST, 'template': template})
                    else:
                        # If no message returned, assume success
                        messages.success(request, "✅ Email template updated successfully.")
                        redirect_url = reverse('email_template_list')
                        if school_selection:
                            redirect_url += f'?school_id={school_selection}'
                        return redirect(redirect_url)
        
        except Exception as e:
            logger.error(f"Error updating email template: {str(e)}")
            messages.error(request, "Error updating email template. Please try again.")
            context.update({'form_data': request.POST, 'template': template})
    
    # Get schools for dropdown (only for Super Admin)
    schools = []
    if profile_id == 1:  # Super Admin only
        schools = get_school_dropdown()
    
    context.update({
        'template': template,
        'schools': schools,
        'is_super_admin': profile_id == 1,
        'page_title': 'Edit Email Template',
        'breadcrumb': [
            {'name': 'Dashboard', 'url': 'dashboard'},
            {'name': 'Master Data', 'url': None},
            {'name': 'Email Templates', 'url': 'email_template_list'},
            {'name': 'Edit Email Template', 'url': None}
        ]
    })
    
    return render(request, 'core/email_template_edit.html', context)


@custom_login_required
def email_template_delete(request, template_id):
    """
    Delete email template (soft delete by setting IsActive = 0)
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    school_id = request.session.get('SchoolID')
    
    if not user_id:
        messages.error(request, "Please login to access email template management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access email template management")
        return redirect('dashboard')
    
    try:
        with connection.cursor() as cursor:
            # Use stored procedure to delete email template
            cursor.execute("""
                SELECT "Message" FROM "Proc_EmailTemplate_Manage"(
                    'DELETE',
                    %s,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    %s
                )
            """, [
                template_id,
                user_id
            ])
            
            # Get the result message
            result = cursor.fetchone()
            if result and len(result) > 0:
                message = result[0] if result[0] else "Email template deleted successfully"
                
                # Check for success indicators
                if message.startswith('🗑️') or message.startswith('✅') or 'successfully' in message.lower():
                    messages.success(request, message)
                else:
                    messages.error(request, message)
            else:
                # If no message returned, assume success
                messages.success(request, "🗑️ Email template deleted successfully.")
    
    except Exception as e:
        logger.error(f"Error deleting email template: {str(e)}")
        messages.error(request, "Error deleting email template. Please try again.")
    
    school_filter = request.GET.get('school_id')
    redirect_url = reverse('email_template_list')
    if school_filter:
        redirect_url += f'?school_id={school_filter}'
    return redirect(redirect_url)


@custom_login_required
def email_template_restore(request, template_id):
    """
    Restore deleted email template (set IsActive = 0)
    Only Super Admin (ProfileID=1) and School Admin (ProfileID=2) can access
    """
    # Get user information
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    school_id = request.session.get('SchoolID')
    
    if not user_id:
        messages.error(request, "Please login to access email template management")
        return redirect('login')
    
    # Check permissions - only Super Admin and School Admin can access
    if profile_id not in [1, 2]:
        messages.error(request, "You don't have permission to access email template management")
        return redirect('dashboard')
    
    try:
        with connection.cursor() as cursor:
            
            # Use stored procedure to restore email template
            cursor.execute("""
                SELECT "Message" FROM "Proc_EmailTemplate_Manage"(
                    'RESTORE',
                    %s,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    %s
                )
            """, [
                template_id,
                user_id
            ])
            
            # Get the result message
            result = cursor.fetchone()
            if result and len(result) > 0:
                message = result[0] if result[0] else "Email template restored successfully"
                
                # Check for success indicators
                if message.startswith('♻️') or message.startswith('✅') or 'successfully' in message.lower():
                    messages.success(request, message)
                else:
                    messages.error(request, message)
            else:
                # If no message returned, assume success
                messages.success(request, "♻️ Email template restored successfully.")
    
    except Exception as e:
        logger.error(f"Error restoring email template: {str(e)}")
        messages.error(request, "Error restoring email template. Please try again.")
    
    school_filter = request.GET.get('school_id')
    redirect_url = reverse('email_template_list')
    if school_filter:
        redirect_url += f'?school_id={school_filter}'
    return redirect(redirect_url)
