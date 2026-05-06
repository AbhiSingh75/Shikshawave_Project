import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from datetime import date, datetime
from core.decorators import login_required

@login_required
def mark_staff_attendance(request):
    school_id = request.session.get('SchoolID')
    user_id = request.session.get('UserId')
    profile_name = request.session.get('ProfileName')
    
    if profile_name == 'Super Admin':
        # Check if school_id is passed in request (GET or POST)
        req_school_id = request.POST.get('school_id') or request.GET.get('school_id')
        if req_school_id:
            from core.url_encryption import decrypt_id
            decrypted = decrypt_id(req_school_id)
            if decrypted:
                school_id = decrypted
            else:
                try:
                    school_id = int(req_school_id)
                except:
                    pass
            
    # For Super Admin and Support Executive, school_id is not required initially, 
    # but they might need to select one.
    if not school_id and profile_name not in ['Super Admin', 'Support Executive']:
        from django.http import HttpResponse
        return HttpResponse('<h1>ERROR: Cannot get school_id</h1><p>User has no school assigned</p>')
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.method == 'POST':
            import json
            date_param = request.POST.get('date')
            attendance_data = request.POST.get('attendance_data')
            
            # Load staff if date is provided without attendance_data
            if date_param and not attendance_data:
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"Loading staff - SchoolID: {school_id}, Date: {date_param}, User: {user_id}, Profile: {profile_name}")
                    
                    with connection.cursor() as cursor:
                        # Explicitly pass NULL for Support Executive and Super Admin without school
                        if not school_id:
                            cursor.execute(
                                "SELECT * FROM Proc_StaffList_Get(%s, %s, %s, %s)", 
                                [None, date_param, user_id, profile_name]
                            )
                        else:
                            cursor.execute(
                                "SELECT * FROM Proc_StaffList_Get(%s, %s, %s, %s)", 
                                [school_id, date_param, user_id, profile_name]
                            )
                        columns = [col[0] for col in cursor.description]
                        staff_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    
                    # Non-admin users can only mark their own attendance
                    ADMIN_PROFILES = ['Super Admin', 'School Admin', 'Support Executive']
                    if profile_name not in ADMIN_PROFILES:
                        staff_list = [s for s in staff_list if str(s.get('EmployeeID', '')) == str(user_id)]
                    
                    logger.info(f"Staff list count: {len(staff_list)}")
                    return JsonResponse({'status': 'SUCCESS', 'staff': staff_list})
                except Exception as e:
                    logger.error(f"Error loading staff: {str(e)}")
                    return JsonResponse({'status': 'ERROR', 'message': str(e)})
            
            # Save attendance if attendance_data is provided
            if attendance_data:
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    attendance_dict = json.loads(attendance_data)
                    attendance_list = [{'EmployeeID': emp_id, 'Status': status, 'Remarks': ''} for emp_id, status in attendance_dict.items()]
                    attendance_json = json.dumps(attendance_list)
                    
                    logger.info(f"Marking attendance - SchoolID: {school_id}, Date: {date_param}, User: {user_id}, Profile: {profile_name}")
                    logger.info(f"Attendance data: {attendance_json}")
                    
                    with connection.cursor() as cursor:
                        # Explicitly pass NULL for Support Executive and Super Admin without school
                        if not school_id:
                            cursor.execute(
                                "SELECT * FROM Proc_StaffAttendance_Mark_Bulk(%s, %s, %s, %s, %s)", 
                                [None, date_param, attendance_json, user_id, profile_name]
                            )
                        else:
                            cursor.execute(
                                "SELECT * FROM Proc_StaffAttendance_Mark_Bulk(%s, %s, %s, %s, %s)", 
                                [school_id, date_param, attendance_json, user_id, profile_name]
                            )
                        result = cursor.fetchone()
                        logger.info(f"Procedure result: {result}")
                        
                        if result and result[0] == 'ERROR':
                            return JsonResponse({'status': 'ERROR', 'message': result[1]})
                    
                    if profile_name in ['School Admin', 'Super Admin']:
                        msg = 'Attendance saved and approved'
                    elif profile_name == 'Support Executive':
                        msg = 'Attendance saved, pending approval from Super Admin'
                    else:
                        msg = 'Attendance saved, pending approval'
                    return JsonResponse({'status': 'SUCCESS', 'message': msg})
                except Exception as e:
                    logger.error(f"Error saving attendance: {str(e)}")
                    return JsonResponse({'status': 'ERROR', 'message': str(e)})
        
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    # Regular page load
    attendance_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    
    # Get context for header
    from core.views import get_context
    context = get_context(request)
    context.update({
        'attendance_date': attendance_date,
        'today': date.today().strftime('%Y-%m-%d'),
        'profile_name': profile_name,
        'school_id': school_id,
        'selected_school_id': school_id
    })
    
    return render(request, 'core/mark_staff_attendance.html', context)


@login_required
def view_staff_attendance(request):
    # Get school_id from session
    school_id = request.session.get('SchoolID')
    profile_name = request.session.get('ProfileName')
    
    if profile_name == 'Super Admin':
        # Check if school_id is passed in request (GET)
        req_school_id = request.GET.get('school_id')
        if req_school_id:
            from core.url_encryption import decrypt_id
            decrypted = decrypt_id(req_school_id)
            if decrypted:
                school_id = decrypted
            else:
                try:
                    school_id = int(req_school_id)
                except:
                    pass
            
    # Super Admin and Support Executive don't need school_id initially
    if not school_id and profile_name not in ['Super Admin', 'Support Executive']:
        messages.error(request, 'School not found for user')
        return redirect('dashboard')
    
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    employee_id = request.GET.get('employee_id', '')
    status = request.GET.get('status', '')
    page = int(request.GET.get('page') or 1)
    page_size = int(request.GET.get('size') or 10)

    # Non-admin users can only view their own attendance records
    ADMIN_PROFILES = ['Super Admin', 'School Admin', 'Support Executive']
    user_id_session = request.session.get('UserId')
    if profile_name not in ADMIN_PROFILES:
        employee_id = str(user_id_session)   # force filter to self
    
    is_filter_applied = bool(start_date or end_date or employee_id or status)
    
    attendance_records = []
    stats = {}
    graph_data = []
    total_records = 0
    total_pages = 0
    
    if is_filter_applied:
        with connection.cursor() as cursor:
            import logging
            logger = logging.getLogger(__name__)
            
            # Call the new unified procedure
            cursor.execute("SELECT Proc_Staff_AttendanceReport_Get(%s, %s, %s, %s, %s, %s, %s)", [
                school_id,
                start_date if start_date else None,
                end_date if end_date else None,
                employee_id if employee_id else None,
                status if status else None,
                page,
                page_size
            ])
            
            # Result is a single JSONB object
            result_data = cursor.fetchone()[0]
            if isinstance(result_data, str):
                import json
                result_data = json.loads(result_data)
            
            attendance_records = result_data.get('records', [])
            stats = result_data.get('stats', {})
            graph_data = result_data.get('graph_data', [])
            pagination = result_data.get('pagination', {})
            
            total_records = pagination.get('total_items', 0)
            total_pages = pagination.get('total_pages', 0)
            
            # Convert date strings to date objects for template formatting
            from datetime import datetime
            for record in attendance_records:
                if 'date' in record and record['date']:
                    try:
                        record['date'] = datetime.strptime(record['date'], '%Y-%m-%d').date()
                    except:
                        pass

    # Fetch employees for the filter dropdown
    employees_list = []
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "UserID", "UserName", "UserCode"
                    FROM "UserMaster"
                    WHERE "SchoolID" = %s AND "IsActive" = TRUE AND COALESCE("IsDeleted", FALSE) = FALSE AND "ProfileID" != 1
                    ORDER BY "UserName" ASC
                """, [school_id])
                employees_list = [{"id": r[0], "name": r[1], "code": r[2]} for r in cursor.fetchall()]
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching employees: {str(e)}")

    # Get context for header
    from core.views import get_context
    import json
    
    context = get_context(request)
    context.update({
        'attendance_records': attendance_records,
        'stats': stats,
        'graph_data': json.dumps(graph_data),
        'employees': employees_list,
        'is_filter_applied': is_filter_applied,
        'is_self_only': profile_name not in ADMIN_PROFILES,  # restricts employee dropdown in template
        'filters': {
            'start_date': start_date,
            'end_date': end_date,
            'employee_id': employee_id,
            'employee_code': next((e['code'] for e in employees_list if str(e['id']) == str(employee_id)), employee_id) if employee_id else '',
            'status': status
        },
        'page': page,
        'page_str': str(page),
        'total_pages': total_pages,
        'total_records': total_records,
        'page_start': (page - 1) * page_size + 1,
        'page_end': min(page * page_size, total_records),
        'selected_school_id': school_id
    })
    
    return render(request, 'core/view_staff_attendance.html', context)

@login_required
def approve_staff_attendance(request):
    # Get session data
    school_id = request.session.get('SchoolID')
    user_id = request.session.get('UserId')
    profile_id = request.session.get('ProfileID')
    profile_name = request.session.get('ProfileName')
    
    school_list = []
    if profile_name == 'Super Admin':
        req_school_id = request.GET.get('school_id')
        if req_school_id:
            from core.url_encryption import decrypt_id
            decrypted = decrypt_id(req_school_id)
            if decrypted:
                school_id = decrypted
            else:
                try:
                    school_id = int(req_school_id)
                except:
                    pass
        
        from core.utils import get_school_dropdown
        from core.url_encryption import encrypt_id
        raw_schools = get_school_dropdown()
        for s in raw_schools:
            s['EncryptedSchoolID'] = encrypt_id(s['SchoolID'])
            school_list.append(s)
            
    # Super Admin and Support Executive don't need school_id initially
    if not school_id and profile_name not in ['Super Admin', 'Support Executive']:
        messages.error(request, 'School not found for user')
        return redirect('dashboard')
    
    # Only School Admin and Super Admin can approve
    if profile_name not in ['School Admin', 'Super Admin']:
        messages.error(request, 'You do not have permission to approve attendance!')
        return redirect('view_staff_attendance')
    
    if request.method == 'POST':
        attendance_id = request.POST.get('attendance_id')
        action = request.POST.get('action')  # 'approve' or 'reject'
        remarks = request.POST.get('remarks', '')
        
        state = 'Approved' if action == 'approve' else 'Rejected'
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Proc_StaffAttendance_Approve(%s, %s, %s, %s)
            """, [attendance_id, user_id, state, remarks])
        
        messages.success(request, f'Attendance {state.lower()} successfully!')
        return redirect('pending_staff_attendance')
    
    with connection.cursor() as cursor:
        if profile_name == 'Super Admin':
            cursor.execute(
                "SELECT * FROM Proc_StaffAttendance_Pending(%s, %s, %s)", 
                [None, user_id, profile_name]
            )
        else:
            cursor.execute(
                "SELECT * FROM Proc_StaffAttendance_Pending(%s, %s, %s)", 
                [school_id, user_id, profile_name]
            )
        columns = [col[0] for col in cursor.description]
        pending_records = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Get context for header
    from core.views import get_context
    context = get_context(request)
    context.update({
        'pending_records': pending_records,
        'schools_list': school_list,
        'selected_school_id': school_id
    })
    
    return render(request, 'core/approve_staff_attendance.html', context)

@login_required
def approve_attendance_ajax(request):
    if request.method == 'POST':
        # Get session data
        user_id = request.session.get('UserId')
        profile_name = request.session.get('ProfileName')
        
        if profile_name not in ['School Admin', 'Super Admin']:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        attendance_id = request.POST.get('attendance_id')
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        
        state = 'Approved' if action == 'approve' else 'Rejected'
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Proc_StaffAttendance_Approve(%s, %s, %s, %s)
            """, [attendance_id, user_id, state, remarks])
        
        return JsonResponse({'success': True, 'message': f'Attendance {state.lower()}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def get_school_employees(request):
    """API endpoint to fetch active UserMaster employees for a school"""
    school_id = request.GET.get('school_id')
    
    if school_id:
        from core.url_encryption import decrypt_id
        decrypted = decrypt_id(school_id)
        if decrypted:
            school_id = decrypted
        else:
            try:
                school_id = int(school_id)
            except:
                school_id = None
                
    if not school_id:
        # Fallback to session
        school_id = request.session.get('SchoolID')
    
    if not school_id:
        return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
    
    employees = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "UserID", "UserName", "UserCode"
                FROM "UserMaster"
                WHERE "SchoolID" = %s AND "IsActive" = TRUE AND COALESCE("IsDeleted", FALSE) = FALSE AND "ProfileID" != 1
                ORDER BY "UserName" ASC
            """, [school_id])
            employees = [{"id": r[0], "name": r[1], "code": r[2]} for r in cursor.fetchall()]
        
        return JsonResponse({'status': 'SUCCESS', 'data': employees})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching employees: {str(e)}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
