from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
import logging
from .decorators import custom_login_required
from .utils import (
    safe_int, _get_custom_session_info,
    get_school_dropdown, get_class_dropdown
)

logger = logging.getLogger(__name__)

# FeeType Master Management Views

@custom_login_required
def fee_type_list(request):
    """List all fee types for the current school using stored procedure"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        school_id = session_info.get('school_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # Get search parameters
        search_text = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class_id', '')
        school_filter = request.GET.get('school_id', '')
        page_no = safe_int(request.GET.get('page', 1))
        page_size = safe_int(request.GET.get('page_size', 10))  # Changed default from 50 to 10
        
        # Convert parameters for stored procedure
        class_id_param = int(class_filter) if class_filter else None
        
        # For Super Admin (profile_id = 1), DO NOT show data unless a school is selected
        if profile_id == 1:  # Super Admin
            if school_filter:
                school_id_param = int(school_filter)
            else:
                # Requirement: Super Admin sees nothing by default
                school_id_param = -1 # Non-existent ID to ensure empty result if procedure doesn't handle NULL strictly
        else:
            school_id_param = int(school_filter) if school_filter else school_id  # Use filtered school or current school
        
        search_param = search_text if search_text else None
        
        # Get fee types using stored procedure
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_FeeTypeMaster_List"(%s, %s, %s, %s, %s)
            """, [school_id_param, class_id_param, search_param, page_no, page_size])
            
            # Get the first result set (fee types)
            fee_types = []
            for row in cursor.fetchall():
                fee_types.append({
                    'FeeTypeId': row[0],
                    'SchoolId': row[1],
                    'SchoolName': row[2],
                    'ClassId': row[3],
                    'ClassName': row[4] if row[4] else 'All Classes',
                    'FeeTypeName': row[5],
                    'DefaultAmount': float(row[6]) if row[6] else 0,
                    'IsActive': not row[7],  # 0 = Active, 1 = Inactive in database
                    # Add additional fields that might be needed
                    'CreatedAt': None,  # Not returned by procedure
                    'UpdatedAt': None,  # Not returned by procedure
                    'CreatedByName': 'System',  # Not returned by procedure
                    'UpdatedByName': 'N/A'  # Not returned by procedure
                })
            
            # Get the second result set (total count) if pagination is used
            total_records = 0
            if page_no and page_size:
                try:
                    cursor.nextset()  # Move to next result set
                    count_result = cursor.fetchone()
                    if count_result:
                        total_records = count_result[0]
                except:
                    total_records = len(fee_types)
            else:
                total_records = len(fee_types)
        
        # Get schools for dropdown (universal function)
        schools = get_school_dropdown()
        
        # Get classes for dropdown (universal function)
        # Sequential Requirement: If school is not selected for Super Admin, return empty classes list
        if profile_id == 1 and not school_filter:
            classes = []
        else:
            classes = get_class_dropdown(school_id_param if school_id_param != -1 else None)
        
        # Calculate pagination info
        total_pages = (total_records + page_size - 1) // page_size if page_size > 0 else 1
        has_previous = page_no > 1
        has_next = page_no < total_pages
        
        context = {
            'fee_types': fee_types,
            'classes': classes,
            'schools': schools,
            'user': session_info,
            'search_text': search_text,
            'class_filter': class_filter,
            'school_filter': school_filter,
            'current_page': page_no,
            'page_size': page_size,
            'total_records': total_records,
            'total_pages': total_pages,
            'has_previous': has_previous,
            'has_next': has_next,
            'previous_page': page_no - 1 if has_previous else None,
            'next_page': page_no + 1 if has_next else None,
            'is_super_admin': profile_id == 1  # Add flag to identify Super Admin
        }
        
        return render(request, 'core/fee_type_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in fee_type_list: {e}")
        messages.error(request, 'An error occurred while loading fee types.')
        return redirect('dashboard')


@custom_login_required
def fee_type_list_ajax(request):
    """AJAX endpoint for fee type list with pagination"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        school_id = session_info.get('school_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get search parameters
        search_text = request.GET.get('search', '').strip()
        class_filter = request.GET.get('class_id', '')
        school_filter = request.GET.get('school_id', '')
        page_no = safe_int(request.GET.get('page', 1))
        page_size = safe_int(request.GET.get('page_size', 10))
        
        # Convert parameters for stored procedure
        class_id_param = int(class_filter) if class_filter else None
        
        # For Super Admin (profile_id = 1), DO NOT show data unless a school is selected
        if profile_id == 1:  # Super Admin
            if school_filter:
                school_id_param = int(school_filter)
            else:
                school_id_param = -1
        else:
            school_id_param = int(school_filter) if school_filter else school_id  # Use filtered school or current school
        
        search_param = search_text if search_text else None
        
        # Get fee types using stored procedure
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_FeeTypeMaster_List"(%s, %s, %s, %s, %s)
            """, [school_id_param, class_id_param, search_param, page_no, page_size])
            
            # Get the first result set (fee types)
            fee_types = []
            for row in cursor.fetchall():
                fee_types.append({
                    'FeeTypeId': row[0],
                    'SchoolId': row[1],
                    'SchoolName': row[2],
                    'ClassId': row[3],
                    'ClassName': row[4] if row[4] else 'All Classes',
                    'FeeTypeName': row[5],
                    'DefaultAmount': float(row[6]) if row[6] else 0,
                    'IsActive': not row[7],  # 0 = Active, 1 = Inactive in database
                })
            
            # Get the second result set (total count) if pagination is used
            total_records = 0
            if page_no and page_size:
                try:
                    cursor.nextset()  # Move to next result set
                    count_result = cursor.fetchone()
                    if count_result:
                        total_records = count_result[0]
                except:
                    total_records = len(fee_types)
            else:
                total_records = len(fee_types)
        
        # Calculate pagination info
        total_pages = (total_records + page_size - 1) // page_size if page_size > 0 else 1
        has_previous = page_no > 1
        has_next = page_no < total_pages
        
        # Return JSON response
        return JsonResponse({
            'fee_types': fee_types,
            'pagination': {
                'current_page': page_no,
                'page_size': page_size,
                'total_records': total_records,
                'total_pages': total_pages,
                'has_previous': has_previous,
                'has_next': has_next,
                'previous_page': page_no - 1 if has_previous else None,
                'next_page': page_no + 1 if has_next else None
            },
            'is_super_admin': profile_id == 1
        })
        
    except Exception as e:
        logger.error(f"Error in fee_type_list_ajax: {e}")
        return JsonResponse({'error': 'An error occurred while loading fee types.'}, status=500)


@custom_login_required
def get_classes_by_school_ajax(request):
    """AJAX endpoint to get classes by school"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        school_id = request.GET.get('school_id', '')
        
        if not school_id:
            return JsonResponse({'classes': []})
        
        # Get classes for the selected school
        classes = get_class_dropdown(int(school_id))
        
        return JsonResponse({'classes': classes})
        
    except Exception as e:
        logger.error(f"Error in get_classes_by_school_ajax: {e}")
        return JsonResponse({'error': 'An error occurred while loading classes.'}, status=500)


@custom_login_required
def fee_type_add(request):
    """Add new fee type"""
    try:
        # Get session info
        session_info = _get_custom_session_info(request)
        user_id = session_info.get('user_id')
        school_id = session_info.get('school_id')
        profile_id = session_info.get('profile_id')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            fee_type_name = request.POST.get('fee_type_name', '').strip()
            default_amount = request.POST.get('default_amount', '0')
            class_id = request.POST.get('class_id', '')
            is_active = request.POST.get('is_active') == 'on'  # If checked, True (Active); if unchecked, False (Inactive)
            
            # For super admin, get school_id from form selection
            if profile_id == 1:  # Super Admin
                selected_school_id = request.POST.get('school_id', '')
                if not selected_school_id:
                    messages.error(request, 'Please select a school.')
                    return redirect('fee_type_list')
                school_id = selected_school_id
                logger.info("Super admin selected school")
            else:
                # For non-super admin, use session school_id
                logger.info("Non-super admin using session school")
            
            # Validation
            if not fee_type_name:
                messages.error(request, 'Fee type name is required.')
                return redirect('fee_type_list')
            
            try:
                default_amount = float(default_amount)
                if default_amount < 0:
                    messages.error(request, 'Default amount cannot be negative.')
                    return redirect('fee_type_list')
            except ValueError:
                messages.error(request, 'Invalid default amount.')
                return redirect('fee_type_list')
            
            # Use unified procedure for INSERT
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "Proc_FeeTypeMaster_Manage"('INSERT', NULL, %s, %s, %s, %s, %s, %s)
                """, [school_id, class_id if class_id else None, fee_type_name, default_amount, 
                      is_active, user_id])
                
                result = cursor.fetchone()
                if result:
                    import json
                    result_data = json.loads(result[0])
                    if result_data['status'] == 'success':
                        messages.success(request, result_data['message'])
                        return redirect('fee_type_list')
                    else:
                        messages.error(request, result_data['message'])
                    return redirect('fee_type_add')
                
        # Get schools for super admin
        schools = []
        classes = []
        
        # Check if school is selected for super admin
        selected_school_id = request.GET.get('school_id', '')
        
        if profile_id == 1:  # Super Admin
            schools = get_school_dropdown()
            
            # If school is selected, get classes for that school
            if selected_school_id:
                classes = get_class_dropdown(int(selected_school_id))
            else:
                # Super admin starts with empty classes
                classes = []
        else:
            # Non-super admin gets classes for their school
            classes = get_class_dropdown(school_id)
        
        context = {
            'classes': classes,
            'schools': schools,
            'is_super_admin': profile_id == 1,
            'selected_school_id': selected_school_id,
            'user': session_info
        }
        
        return render(request, 'core/fee_type_add.html', context)
        
    except Exception as e:
        logger.error(f"Error in fee_type_add: {e}")
        messages.error(request, 'An error occurred while adding fee type.')
        return redirect('fee_type_list')


def fee_type_classes_ajax(request):
    """AJAX endpoint to get classes for a selected school"""
    try:
        school_id = request.GET.get('school_id')
        if not school_id:
            return JsonResponse({'classes': []})
        
        classes = get_class_dropdown(int(school_id))
        
        return JsonResponse({'classes': classes})
        
    except Exception as e:
        logger.error(f"Error in fee_type_classes_ajax: {e}")
        return JsonResponse({'classes': []})


@custom_login_required
def fee_type_edit(request, fee_type_id):
    """Edit fee type"""
    try:
        # Get session info (already validated by decorator)
        session_info = request.custom_user
        user_id = session_info.get('user_id')
        school_id = session_info.get('school_id')
        profile_id = session_info.get('profile_id')
        
        # Add debug message

        logger.info(f"Initial session info - user_id: {user_id}, school_id: {school_id}, profile_id: {profile_id}")
        
        # Determine school_id based on user profile
        if profile_id == 1:  # Super Admin
            # For super admin, get school_id from the fee type data (the school being viewed)
            logger.info("Super admin detected - getting school_id from fee type data")
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "SchoolId" FROM "FeeType_Master" WHERE "FeeTypeId" = %s
                """, [fee_type_id])
                result = cursor.fetchone()
                if result:
                    school_id = result[0]
                    logger.info(f"Super admin using school_id from fee type data: {school_id}")
                else:
                    logger.error(f"Fee type {fee_type_id} not found for super admin")
                    messages.error(request, f'Fee type not found for ID: {fee_type_id}')
                    return redirect('fee_type_list')
        else:  # Non-Super Admin
            # For non-super admin, use session school_id
            logger.info("Non-super admin detected - using session school_id")
            if not school_id:
                # Try Django session as fallback
                school_id = request.session.get('SchoolID')
                logger.info(f"Retrieved school_id from Django session: {school_id}")
            
            # If still no school_id, try to get it from the user's school
            if not school_id:
                with connection.cursor() as cursor:
                    logger.info(f"Attempting to get school_id from UserMaster for user_id: {user_id}")
                    cursor.execute("""
                        SELECT "SchoolID" FROM "UserMaster" WHERE "UserID" = %s
                    """, [user_id])
                    result = cursor.fetchone()
                    logger.info(f"UserMaster query result: {result}")
                    if result:
                        school_id = result[0]
                        logger.info(f"Retrieved school_id from UserMaster: {school_id}")
                    else:
                        logger.error(f"No user found in UserMaster with user_id: {user_id}")
            
            if not school_id:
                logger.error("No school_id found in session or user record")
                messages.error(request, 'Unable to determine school. Please login again.')
                return redirect('login')
        
        # Check permissions (Super Admin and School Admin only)
        if profile_id not in [1, 2]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            fee_type_name = request.POST.get('fee_type_name', '').strip()
            default_amount = request.POST.get('default_amount', '0')
            class_id = request.POST.get('class_id', '')
            is_active = request.POST.get('is_active') == 'on'  # If checked, True (Active); if unchecked, False (Inactive)
            
            # Validation
            if not fee_type_name:
                messages.error(request, 'Fee type name is required.')
                return redirect('fee_type_list')
            
            try:
                default_amount = float(default_amount)
                if default_amount < 0:
                    messages.error(request, 'Default amount cannot be negative.')
                    return redirect('fee_type_list')
            except ValueError:
                messages.error(request, 'Invalid default amount.')
                return redirect('fee_type_list')
            
            # Use unified procedure for UPDATE
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "Proc_FeeTypeMaster_Manage"('UPDATE', %s, %s, %s, %s, %s, %s, %s)
                """, [fee_type_id, school_id, class_id if class_id else None, fee_type_name, 
                      default_amount, is_active, user_id])
                
                result = cursor.fetchone()
                if result:
                    import json
                    result_data = json.loads(result[0])
                    if result_data['status'] == 'success':
                        messages.success(request, result_data['message'])
                else:
                        messages.error(request, result_data['message'])
                
                return redirect('fee_type_list')
        
        # Get fee type details
        with connection.cursor() as cursor:
            logger.info(f"Searching for fee type with ID: {fee_type_id}, School: {school_id}")
            
            # First, let's check if the fee type exists at all
            cursor.execute("""
                SELECT "FeeTypeId", "FeeTypeName", "DefaultAmount", "IsActive", "ClassId", "SchoolId"
                FROM "FeeType_Master" 
                WHERE "FeeTypeId" = %s
            """, [fee_type_id])
            debug_data = cursor.fetchone()
            logger.info(f"Debug - Fee type exists: {debug_data}")
            
            if not debug_data:
                logger.error(f"Fee type with ID {fee_type_id} does not exist in database")
                messages.error(request, f'Fee type with ID {fee_type_id} does not exist')
                return redirect('fee_type_list')
            
            # Now check with school filter
            cursor.execute("""
                SELECT "FeeTypeId", "FeeTypeName", "DefaultAmount", "IsActive", "ClassId"
                FROM "FeeType_Master" 
                WHERE "FeeTypeId" = %s AND "SchoolId" = %s
            """, [fee_type_id, school_id])
            
            fee_type_data = cursor.fetchone()
            logger.info(f"Fee type query result: {fee_type_data}")
            logger.info(f"Query params: fee_type_id={fee_type_id}, school_id={school_id}")
            
            if not fee_type_data:
                logger.error(f"Fee type not found for ID: {fee_type_id}, School: {school_id}")
                logger.error(f"Fee type exists but belongs to school: {debug_data[5]}")
                messages.error(request, f'Fee type not found for your school. Fee type belongs to school ID: {debug_data[5]}')
                return redirect('fee_type_list')
            
            fee_type = {
                'FeeTypeId': fee_type_data[0],
                'FeeTypeName': fee_type_data[1],
                'DefaultAmount': float(fee_type_data[2]) if fee_type_data[2] else 0,
                'IsActive': not fee_type_data[3],  # Convert database value: 0=Active, 1=Inactive
                'ClassId': fee_type_data[4]
            }
        
        # Get classes for dropdown
        classes = get_class_dropdown(school_id)
        
        context = {
            'fee_type': fee_type,
            'classes': classes,
            'user': session_info
        }
        
        return render(request, 'core/fee_type_edit.html', context)
        
    except Exception as e:
        logger.error(f"Error in fee_type_edit: {e}")
        messages.error(request, 'An error occurred while editing fee type.')
        return redirect('fee_type_list')


@custom_login_required
def fee_type_delete(request, fee_type_id):
    """Delete fee type (AJAX POST)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        session_info = request.custom_user
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        if profile_id not in [1, 2]:
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "Proc_FeeTypeMaster_Manage"('DELETE', %s, NULL, NULL, NULL, NULL, NULL, %s)
            """, [fee_type_id, user_id])
            
            result = cursor.fetchone()
            if result:
                import json
                result_data = json.loads(result[0])
                if result_data['status'] == 'success':
                    messages.success(request, result_data['message'])
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': result_data['message']})
        
        return JsonResponse({'status': 'error', 'message': 'Unknown error occurred.'}, status=500)
        
    except Exception as e:
        logger.error(f"Error in fee_type_delete: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@custom_login_required
def fee_type_restore(request, fee_type_id):
    """Restore fee type (AJAX POST)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        session_info = request.custom_user
        user_id = session_info.get('user_id')
        profile_id = session_info.get('profile_id')
        
        if profile_id not in [1, 2]:
            return JsonResponse({'status': 'error', 'message': 'Permission denied.'}, status=403)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "Proc_FeeTypeMaster_Manage"('RESTORE', %s, NULL, NULL, NULL, NULL, NULL, %s)
            """, [fee_type_id, user_id])
            
            result = cursor.fetchone()
            if result:
                import json
                result_data = json.loads(result[0])
                if result_data['status'] == 'success':
                    messages.success(request, result_data['message'])
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({'status': 'error', 'message': result_data['message']})
        
        return JsonResponse({'status': 'error', 'message': 'Unknown error occurred.'}, status=500)
        
    except Exception as e:
        logger.error(f"Error in fee_type_restore: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
