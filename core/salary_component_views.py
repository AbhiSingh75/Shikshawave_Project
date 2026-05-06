# Salary Component Master Management Views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
import logging
import json
from .url_encryption import encrypt_id, decrypt_id
from .views import strict_permission_required
from .utils import sanitize_input

logger = logging.getLogger(__name__)

@strict_permission_required('/master-data/salary-component/')
def salary_component_list(request):
    """List all salary components with modal for add/edit"""
    from .views import get_context
    from .subject_views import get_school_dropdown
    
    context = get_context(request)
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    is_super_admin = profile_id == 1
    
    # Get and decrypt selected school ID (for super admin filtering)
    from .url_encryption import decrypt_id_int
    enc_selected_school_id = request.GET.get('sid')
    selected_school_id = None
    if enc_selected_school_id:
        try:
            selected_school_id = decrypt_id_int(enc_selected_school_id)
        except Exception:
            logger.error(f"Security: Invalid School ID decryption attempt from {request.session.get('UserId')}")
            messages.error(request, "Invalid school reference.", extra_tags='salary_component')
            return redirect('salary_component_list')
    
    # For non-super admin, always use their school
    if not is_super_admin:
        selected_school_id = school_id
    
    components = []
    schools = []
    
    # Super Admin needs to apply a filter to see data.
    # Non-Super Admins always see their own school's data.
    should_fetch_data = not is_super_admin or selected_school_id

    try:
        with connection.cursor() as cursor:
            if should_fetch_data:
                # Call PostgreSQL function with explicit cast for NULL handling
                cursor.execute('SELECT * FROM "Proc_SalaryComponentMaster_List"(%s::INTEGER)', [selected_school_id])
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                for row in rows:
                    comp = dict(zip(columns, row))
                    # Encrypt ID for frontend
                    comp['EncComponentID'] = encrypt_id(comp['ComponentID'])
                    comp['EncSchoolID'] = encrypt_id(comp['SchoolID'])
                    components.append(comp)
            
            # Always get schools for dropdown if super admin (even if no data is fetched yet)
            if is_super_admin:
                raw_schools = get_school_dropdown()
                schools = []
                for s in raw_schools:
                    s['EncSchoolID'] = encrypt_id(s['SchoolID'])
                    schools.append(s)
    
    except Exception as e:
        logger.error(f"Error fetching salary components: {e}", exc_info=True)
        messages.error(request, "Error loading salary components", extra_tags='salary_component')
    
    context.update({
        'components': components,
        'schools': schools,
        'is_super_admin': is_super_admin,
        'selected_school_id': enc_selected_school_id, # For labels/links
        'selected_school_id_raw': selected_school_id, # For reliable dropdown pre-selection
    })
    
    return render(request, 'core/salary_component.html', context)


@strict_permission_required('Salary Components', action='add')
def salary_component_save(request):
    """Save (add/update) salary component"""
    if request.method != 'POST':
        return redirect('salary_component_list')
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    user_id = request.session.get('UserId')
    is_super_admin = profile_id == 1
    
    enc_component_id = request.POST.get('component_id')
    component_id = None
    if enc_component_id:
        try:
            component_id = decrypt_id(enc_component_id)
        except Exception:
            logger.warning(f"Security: Failed Component ID decryption in Save from User {user_id}")
            messages.error(request, "Invalid resource identifier.", extra_tags='salary_component')
            return redirect('salary_component_list')
    
    # ── IDOR & OWNERSHIP VERIFICATION ──
    if component_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolID" FROM "SalaryComponentMaster" WHERE "ComponentID" = %s', [component_id])
                row = cursor.fetchone()
                if not row or (not is_super_admin and row[0] != school_id):
                    logger.warning(f"IDOR Attempt: User {user_id} tried to edit Component {component_id} from School {row[0] if row else 'N/A'}")
                    messages.error(request, "Permission denied: Resource ownership mismatch.", extra_tags='salary_component')
                    return redirect('salary_component_list')
        except Exception as e:
            logger.error(f"Error during IDOR check: {e}")
            messages.error(request, "Error verifying resource ownership.", extra_tags='salary_component')
            return redirect('salary_component_list')

    component_name = sanitize_input(request.POST.get('component_name', '').strip())
    if not component_name:
        messages.error(request, "Component name cannot be empty.", extra_tags='salary_component')
        return redirect('salary_component_list')

    component_type = request.POST.get('component_type', '').strip()
    if component_type not in ['Earning', 'Deduction']:
        logger.warning(f"Security: Invalid Component Type '{component_type}' from User {user_id}")
        messages.error(request, "Invalid component type selected.", extra_tags='salary_component')
        return redirect('salary_component_list')
    
    enc_school_id = request.POST.get('school_id')
    selected_school_id = school_id # Default
    if is_super_admin and enc_school_id:
        try:
            selected_school_id = decrypt_id(enc_school_id)
        except Exception:
            logger.error(f"Security: School ID decryption fail in Save for User {user_id}")
            messages.error(request, "Invalid school reference.", extra_tags='salary_component')
            return redirect('salary_component_list')
    
    action = 'UPDATE' if component_id else 'INSERT'
    
    try:
        with connection.cursor() as cursor:
            # Signature: p_Action, p_ComponentID, p_SchoolID, p_ComponentName, p_ComponentType, p_UserId
            cursor.execute("""
                SELECT "Proc_SalaryComponentMaster_Manage"(%s, %s, %s, %s, %s, %s)
            """, [action, component_id, selected_school_id, component_name, component_type, user_id])
            
            result = cursor.fetchone()
            if result:
                response = json.loads(result[0])
                if response.get('status') == 'success':
                    messages.success(request, response.get('message'), extra_tags='salary_component')
                else:
                    messages.error(request, response.get('message'), extra_tags='salary_component')
    
    except Exception as e:
        logger.error(f"Error saving salary component: {e}", exc_info=True)
        messages.error(request, f"Error saving component: {str(e)}", extra_tags='salary_component')
    
    # Redirect back with school filter preserved
    redirect_url = '/master-data/salary-component/'
    if is_super_admin and enc_school_id:
        redirect_url += f'?sid={enc_school_id}'
        
    return redirect(redirect_url)


@strict_permission_required('Salary Components', action='delete')
def salary_component_delete_ajax(request):
    """Delete salary component via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    is_super_admin = profile_id == 1
    user_id = request.session.get('UserId')
    enc_component_id = request.POST.get('component_id')
    if not enc_component_id:
        return JsonResponse({'status': 'error', 'message': 'Missing identifier'})

    try:
        component_id = decrypt_id(enc_component_id)
    except Exception:
        logger.warning(f"Security: Failed Component ID decryption in Delete (AJAX) from User {user_id}")
        return JsonResponse({'status': 'error', 'message': 'Invalid resource identifier.'})
    
    # ── IDOR & OWNERSHIP VERIFICATION ──
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "SchoolID" FROM "SalaryComponentMaster" WHERE "ComponentID" = %s', [component_id])
            row = cursor.fetchone()
            if not row or (not is_super_admin and row[0] != school_id):
                return JsonResponse({'status': 'error', 'message': 'Resource ownership mismatch.'})
            
            # If authorized, proceed with deletion
            cursor.execute("""
                SELECT "Proc_SalaryComponentMaster_Manage"('DELETE', %s, NULL, NULL, NULL, %s)
            """, [component_id, user_id])
            
            result = cursor.fetchone()
            if result:
                return JsonResponse(json.loads(result[0]))
    
    except Exception as e:
        logger.error(f"Error deleting salary component: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Database error occurred.'})
    
    return JsonResponse({'status': 'error', 'message': 'Unknown error'})


@strict_permission_required('Salary Components', action='edit')
def salary_component_restore_ajax(request):
    """Restore salary component via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    is_super_admin = profile_id == 1
    user_id = request.session.get('UserId')
    enc_component_id = request.POST.get('component_id')
    if not enc_component_id:
        return JsonResponse({'status': 'error', 'message': 'Missing identifier'})

    try:
        component_id = decrypt_id(enc_component_id)
    except Exception:
        logger.warning(f"Security: Failed Component ID decryption in Restore (AJAX) from User {user_id}")
        return JsonResponse({'status': 'error', 'message': 'Invalid resource identifier.'})
    
    # ── IDOR & OWNERSHIP VERIFICATION ──
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "SchoolID" FROM "SalaryComponentMaster" WHERE "ComponentID" = %s', [component_id])
            row = cursor.fetchone()
            if not row or (not is_super_admin and row[0] != school_id):
                return JsonResponse({'status': 'error', 'message': 'Resource ownership mismatch.'})
            
            # If authorized, proceed with restoration
            cursor.execute("""
                SELECT "Proc_SalaryComponentMaster_Manage"('RESTORE', %s, NULL, NULL, NULL, %s)
            """, [component_id, user_id])
            
            result = cursor.fetchone()
            if result:
                return JsonResponse(json.loads(result[0]))
    
    except Exception as e:
        logger.error(f"Error restoring salary component: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Database error occurred.'})
    
    return JsonResponse({'status': 'error', 'message': 'Unknown error'})


# Keep old views for backward compatibility (redirect to new single-page view)
def salary_component_add(request):
    return redirect('salary_component_list')

def salary_component_edit(request, component_id):
    return redirect('salary_component_list')

def salary_component_delete(request, component_id):
    return redirect('salary_component_list')

def salary_component_restore(request, component_id):
    return redirect('salary_component_list')
