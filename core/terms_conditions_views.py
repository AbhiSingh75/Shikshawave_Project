from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from .views import custom_login_required, get_context
from .utils import get_school_dropdown
import logging

logger = logging.getLogger(__name__)

@custom_login_required
def terms_conditions(request):
    context = get_context(request)
    
    # Get session info
    school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else None
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Fallback
    if not school_id:
        school_id = request.session.get('SchoolID')

    # Super Admin Logic
    if profile_id == 1:
        context['is_super_admin'] = True
        
        # Get schools for dropdown
        schools = get_school_dropdown()
        context['schools'] = schools
        
        # Check for school_id filter
        filter_school_id = request.GET.get('school_id')
        if filter_school_id:
            try:
                school_id = int(filter_school_id)
            except ValueError:
                pass
        
        # If no school selected, show empty
        if not school_id:
            context['terms'] = []
            context['selected_school_id'] = ''
            return render(request, 'terms_conditions.html', context)
    else:
        context['is_super_admin'] = False

    context['selected_school_id'] = school_id
    
    # Fetch Terms & Conditions
    terms = []
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_TermsConditions_List"(%s)
                """, [school_id])
                
                # Columns: Id, SchoolId, Title, Description, Category, IsActive, DisplayOrder, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
                rows = cursor.fetchall()
                for row in rows:
                    terms.append({
                        'Id': row[0],
                        'SchoolId': row[1],
                        'Title': row[2],
                        'Description': row[3],
                        'Category': row[4],
                        'IsActive': bool(row[5]),
                        'DisplayOrder': row[6],
                        'CreatedBy': row[7],
                        'CreatedAt': row[8],
                        'UpdatedBy': row[9],
                        'UpdatedAt': row[10]
                    })
        except Exception as e:
            logger.error(f"Error fetching terms: {e}")
    
    context['terms'] = terms
    return render(request, 'terms_conditions.html', context)

@custom_login_required
def terms_conditions_save(request):
    if request.method != 'POST':
        return redirect('terms_conditions')
    
    # Get user info
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    # Get school_id - from POST for Super Admin, from session for others
    school_id = request.POST.get('school_id')
    if not school_id:
        school_id = request.session.get('SchoolID')
    
    term_id = request.POST.get('term_id') or None
    title = request.POST.get('title')
    description = request.POST.get('description')
    category = request.POST.get('category') or None
    display_order = request.POST.get('display_order', 0)
    is_active = True if request.POST.get('is_active') else False
    
    # Convert term_id to int or None
    try:
        term_id = int(term_id) if term_id else None
    except (ValueError, TypeError):
        term_id = None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_TermsConditions_Save"(%s, %s, %s, %s, %s, %s, %s, %s)
            """, [term_id, school_id, title, description, category, is_active, display_order, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                messages.success(request, result[1])
            else:
                msg = result[1] if result else 'Failed to save terms & conditions'
                messages.error(request, msg)
    except Exception as e:
        logger.error(f"Error saving terms: {e}")
        messages.error(request, f'Failed to save terms & conditions: {str(e)}')
    
    # Redirect back, preserving school selection for super admin
    if school_id and request.POST.get('school_id'):
        return redirect(f"/master-data/terms-conditions/?school_id={school_id}")
    
    return redirect('terms_conditions')

@custom_login_required
def terms_conditions_delete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    # Get school_id - from POST for Super Admin, from session for others
    school_id = request.POST.get('school_id')
    if not school_id:
        school_id = request.session.get('SchoolID')
    
    term_id = request.POST.get('term_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_TermsConditions_Delete"(%s, %s)
            """, [term_id, school_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                return JsonResponse({'status': 'SUCCESS', 'message': result[1]})
            else:
                msg = result[1] if result else 'Failed to delete'
                return JsonResponse({'status': 'ERROR', 'message': msg})
    except Exception as e:
        logger.error(f"Error deleting terms: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})

@custom_login_required
def terms_conditions_load(request):
    """AJAX endpoint to load terms for a specific school (Super Admin use)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    school_id = request.POST.get('school_id')
    
    try:
        terms = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_TermsConditions_List"(%s)
            """, [school_id])
            
            rows = cursor.fetchall()
            for row in rows:
                terms.append({
                    'Id': row[0],
                    'SchoolId': row[1],
                    'Title': row[2],
                    'Description': row[3],
                    'Category': row[4],
                    'IsActive': 1 if row[5] else 0,
                    'DisplayOrder': row[6],
                    'CreatedAt': str(row[8]) if row[8] else None
                })
        
        return JsonResponse({'status': 'SUCCESS', 'data': terms})
    except Exception as e:
        logger.error(f"Error loading terms: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
