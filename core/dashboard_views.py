# core/dashboard_views.py
import json
import logging
from datetime import datetime, timedelta

from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods
import logging
from decimal import Decimal
from .decorators import custom_login_required
from .url_encryption import decrypt_id_int

logger = logging.getLogger(__name__)


def _fetch_user_menus(profile_id):
    """Fetch user menus using inline SQL for PostgreSQL compatibility"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT 
                m."MenuID",
                m."MenuName",
                m."MenuURL",
                m."Icon",
                m."ParentMenuID",
                m."DisplayOrder",
                pmm."CanAdd",
                pmm."CanEdit",
                pmm."CanDelete"
            FROM "MenuMaster" m
            INNER JOIN "ProfileMenuMapping" pmm ON m."MenuID" = pmm."MenuID"
            WHERE pmm."ProfileID" = %s 
                AND m."IsActive" = TRUE 
                AND m."IsDeleted" IS FALSE
            ORDER BY m."DisplayOrder", m."MenuName"
        """, [profile_id])
        rows = cursor.fetchall()
    
    flat = []
    by_parent = {}
    for r in rows:
        item = {
            'id': r[0], 'name': r[1], 'url': r[2] or '#', 'icon': r[3] or 'fas fa-circle',
            'parent_id': r[4], 'order': r[5], 'can_add': bool(r[6]),
            'can_edit': bool(r[7]), 'can_delete': bool(r[8])
        }
        flat.append(item)
        by_parent.setdefault(item['parent_id'], []).append(item)
    
    def build_tree(parent_id=None):
        children = by_parent.get(parent_id, [])
        children.sort(key=lambda x: (x['order'], x['name']))
        for c in children:
            c['children'] = build_tree(c['id'])
        return children
    
    return {'flat': flat, 'tree': build_tree(None)}

@custom_login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def dashboard_view(request):
    """Main dashboard view with student statistics"""
    sess = request.custom_user
    profile_id = sess.get('profile_id')
    school_id = sess.get('school_id')
    
    # Fetch active academic year
    # For Super Admin (1) and Support Executive (11), use global session (SchoolID=0)
    target_school_id = 0 if profile_id in [1, 11] else school_id
    current_session = "2023-24"
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "AcademicYear" FROM "Proc_AcademicYear_Active_Get"(%s)', [target_school_id])
            row = cursor.fetchone()
            if row:
                current_session = row[0]
    except Exception as e:
        logger.error(f"Error fetching current session: {str(e)}")
    
    menus = _fetch_user_menus(profile_id)
    
    dashboard_stats = {
        'total_students': 0,
        'male_students': 0,
        'female_students': 0,
        'active_students': 0,
        'class_breakdown': []
    }
    
    try:
        with connection.cursor() as cursor:
            # 1. Overall Student Stats
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s."StudentID") AS TotalStudents,
                    COUNT(DISTINCT CASE WHEN s."Gender" = 'Male' THEN s."StudentID" END) AS MaleStudents,
                    COUNT(DISTINCT CASE WHEN s."Gender" = 'Female' THEN s."StudentID" END) AS FemaleStudents,
                    COUNT(DISTINCT CASE WHEN s."Category" = 'General' THEN s."StudentID" END) AS GeneralCategory,
                    COUNT(DISTINCT CASE WHEN s."Category" = 'OBC' THEN s."StudentID" END) AS OBCCategory,
                    COUNT(DISTINCT CASE WHEN s."Category" = 'SC' THEN s."StudentID" END) AS SCCategory,
                    COUNT(DISTINCT CASE WHEN s."Category" = 'ST' THEN s."StudentID" END) AS STCategory,
                    COUNT(DISTINCT CASE WHEN s."IsDeleted" IS NOT TRUE THEN s."StudentID" END) AS ActiveStudents,
                    COUNT(DISTINCT CASE WHEN s."IsDeleted" IS TRUE THEN s."StudentID" END) AS InactiveStudents
                FROM "Student" s
                WHERE s."SchoolID" = %s
            """, [school_id])
            row = cursor.fetchone()
            if row:
                dashboard_stats['total_students'] = row[0] or 0
                dashboard_stats['male_students'] = row[1] or 0
                dashboard_stats['female_students'] = row[2] or 0
                dashboard_stats['general_category'] = row[3] or 0
                dashboard_stats['obc_category'] = row[4] or 0
                dashboard_stats['sc_category'] = row[5] or 0
                dashboard_stats['st_category'] = row[6] or 0
                dashboard_stats['active_students'] = row[7] or 0
                dashboard_stats['inactive_students'] = row[8] or 0
            
            # 2. Class-wise Breakdown
            cursor.execute("""
                SELECT 
                    c."ClassID",
                    c."ClassName",
                    COUNT(DISTINCT s."StudentID") AS StudentCount,
                    COUNT(DISTINCT CASE WHEN s."Gender" = 'Male' THEN s."StudentID" END) AS MaleCount,
                    COUNT(DISTINCT CASE WHEN s."Gender" = 'Female' THEN s."StudentID" END) AS FemaleCount
                FROM "Student" s
                INNER JOIN "ClassMaster" c ON s."AdmissionClass"::integer = c."ClassID"
                WHERE s."SchoolID" = %s AND s."IsDeleted" IS NOT TRUE
                GROUP BY c."ClassID", c."ClassName"
                ORDER BY c."ClassID"
            """, [school_id])
            
            class_breakdown = []
            for class_row in cursor.fetchall():
                class_breakdown.append({
                    'class_id': class_row[0],
                    'class_name': class_row[1],
                    'student_count': class_row[2],
                    'male_count': class_row[3],
                    'female_count': class_row[4]
                })
            dashboard_stats['class_breakdown'] = class_breakdown
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
    
    # Get employee stats
    employee_stats = {'total_employees': 0}
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT e."EmployeeID") AS TotalEmployees
                FROM "EmployeeMaster" e
                WHERE e."SchoolID" = %s AND e."IsDeleted" IS NOT TRUE
            """, [school_id])
            emp_row = cursor.fetchone()
            if emp_row:
                employee_stats['total_employees'] = emp_row[0] or 0
    except Exception as e:
        logger.error(f"Error fetching employee stats: {str(e)}")
    
    timeout_minutes = 60  # default
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT \"SessionTimeoutMinutes\" FROM \"UserMaster\" WHERE \"UserID\" = %s", [sess.get('user_id')])
            row = cursor.fetchone()
            if row and row[0]:
                timeout_minutes = row[0]
    except Exception as e:
        logger.error(f"Error fetching timeout: {str(e)}")

    # Session expiry is now handled globally in core/context_processors.py
    session_expires_timestamp = request.session.get('session_expires_at')
    
    context = {
        'menus': menus['tree'],
        'flat_menus': menus['flat'],
        'school_id': school_id,
        'current_session': current_session,
        'dashboard_stats': dashboard_stats,
        'employee_stats': employee_stats,
        'dark_mode': request.session.get('dark_mode', False),
        'timeout_minutes': timeout_minutes,
        'session_expires_timestamp': session_expires_timestamp,
    }
    return render(request, 'core/dashboard.html', context)

@custom_login_required
def api_dashboard_students(request):
    """API endpoint for filtered student statistics"""
    school_id = request.custom_user.get('school_id')
    
    # Helper to sanitize inputs (empty strings should be None for SQL casting)
    def clean(val):
        if val is None or str(val).lower() in ['', 'none', 'undefined', 'null']:
            return None
        return val

    class_id = clean(request.GET.get('class_id'))
    section_id = clean(request.GET.get('section_id'))
    academic_year = clean(request.GET.get('academic_year'))
    gender = clean(request.GET.get('gender'))
    category = clean(request.GET.get('category'))
    from_date = clean(request.GET.get('from_date'))
    to_date = clean(request.GET.get('to_date'))
    show_active_only = request.GET.get('show_active_only', '1') == '1'
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the centralized stored procedure
                # In PostgreSQL, SETOF REFCURSOR returns the names of the cursors
                cursor.execute('SELECT * FROM "Proc_DashboardStudentStats_Get"(%s, %s, %s, %s, %s, %s, %s, %s)', [
                    school_id, class_id, section_id, gender, category, from_date, to_date, show_active_only
                ])
                
                # Fetch the cursor names
                rows = cursor.fetchall()
                if not rows or len(rows) < 3:
                    raise Exception("Procedure did not return all required cursors (rs_overall, rs_breakdown, rs_trend)")
                
                cursor_names = [row[0] for row in rows]
                
                # 1. Overall Student Stats (from 'rs_overall')
                cursor.execute(f'FETCH ALL IN "{cursor_names[0]}"')
                stats = {}
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        stats = dict(zip(columns, row))
                
                # 2. Class-wise Breakdown (from 'rs_breakdown')
                cursor.execute(f'FETCH ALL IN "{cursor_names[1]}"')
                class_breakdown = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        class_item = dict(zip(columns, row))
                        # Convert Decimals to float for JSON serialization
                        if 'AdmissionRevenue' in class_item:
                            class_item['AdmissionRevenue'] = float(class_item['AdmissionRevenue'] or 0)
                        class_breakdown.append(class_item)
                
                # 3. Admission Trend (from 'rs_trend')
                cursor.execute(f'FETCH ALL IN "{cursor_names[2]}"')
                admission_trend = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        admission_trend.append(dict(zip(columns, row)))

                # Close cursors (Best practice)
                for name in cursor_names:
                    cursor.execute(f'CLOSE "{name}"')

        return JsonResponse({
            'success': True,
            'stats': stats,
            'class_breakdown': class_breakdown,
            'admission_trend': admission_trend
        })
    except Exception as e:
        logger.error(f"Error fetching dashboard students via proc: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_staff_profiles(request):
    """API endpoint to get staff profile types for dropdown"""
    try:
        with connection.cursor() as cursor:
            # India Standard: Get all active profiles in the school + core school roles
            cursor.execute("""
                SELECT DISTINCT pm."ProfileID", pm."ProfileName"
                FROM "ProfileMaster" pm
                WHERE pm."IsDeleted" IS NOT TRUE
                AND (pm."ProfileName" IN (
                    'School Admin', 'Teacher', 'Driver', 'Librarian', 
                    'Accountant', 'Support Executive', 'Principal', 'HOD'
                ) OR pm."ProfileID" IN (SELECT DISTINCT "ProfileID" FROM "UserMaster" WHERE "SchoolID" = %s))
                ORDER BY pm."ProfileName"
            """, [request.custom_user.get('school_id')])
            profiles = []
            for row in cursor.fetchall():
                profiles.append({
                    'ProfileID': row[0],
                    'ProfileName': row[1]
                })
            return JsonResponse(profiles, safe=False)
    except Exception as e:
        logger.error(f"Error fetching staff profiles: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_employees(request):
    """API endpoint for filtered employee/teacher statistics"""
    school_id = request.custom_user.get('school_id')
    department = request.GET.get('department')
    gender = request.GET.get('gender')
    employment_type = request.GET.get('employment_type')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    show_active_only = request.GET.get('show_active_only', '1') == '1'
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the centralized Employee Statistics procedure
                cursor.execute('SELECT * FROM "Proc_DashboardEmployeeStats_Get"(%s, %s, %s, %s, %s, %s, %s)', [
                    school_id, department, gender, employment_type, from_date, to_date, show_active_only
                ])
                
                rows = cursor.fetchall()
                if not rows or len(rows) < 3:
                    raise Exception("Procedure did not return all required cursors (rs_overall, rs_breakdown, rs_trend)")
                
                cursor_names = [row[0] for row in rows]
                
                # 1. Overall Employee Stats
                cursor.execute(f'FETCH ALL IN "{cursor_names[0]}"')
                stats = {}
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        stats = dict(zip(columns, row))
                
                # 2. Profile-wise Breakdown
                cursor.execute(f'FETCH ALL IN "{cursor_names[1]}"')
                profile_breakdown = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        profile_breakdown.append(dict(zip(columns, row)))
                
                # 3. Hiring Trend
                cursor.execute(f'FETCH ALL IN "{cursor_names[2]}"')
                hiring_trend = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        hiring_trend.append(dict(zip(columns, row)))

                # Close cursors
                for name in cursor_names:
                    cursor.execute(f'CLOSE "{name}"')

        return JsonResponse({
            'success': True,
            'stats': stats,
            'profile_breakdown': profile_breakdown,
            'hiring_trend': hiring_trend
        })
    except Exception as e:
        logger.error(f"Error fetching employee stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_attendance(request):
    """API endpoint for student attendance statistics"""
    school_id = request.custom_user.get('school_id')
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    attendance_date = request.GET.get('attendance_date')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the centralized Attendance Statistics procedure
                cursor.execute('SELECT * FROM "Proc_DashboardAttendanceStats_Get"(%s::INTEGER, %s::INTEGER, %s::INTEGER, %s::DATE, %s::DATE, %s::DATE)', [
                    school_id, class_id, section_id, attendance_date, from_date, to_date
                ])
                
                rows = cursor.fetchall()
                if not rows or len(rows) < 4:
                    raise Exception("Procedure did not return all required cursors (rs_overall, rs_gender, rs_class, rs_trend)")
                
                cursor_names = [row[0] for row in rows]
                
                # 1. Overall Student Attendance Stats
                cursor.execute(f'FETCH ALL IN "{cursor_names[0]}"')
                stats = {}
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        stats = dict(zip(columns, row))
                
                # 2. Gender-wise Stats
                cursor.execute(f'FETCH ALL IN "{cursor_names[1]}"')
                gender_stats = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        gender_stats.append(dict(zip(columns, row)))
                
                # 3. Class-wise Breakdown
                cursor.execute(f'FETCH ALL IN "{cursor_names[2]}"')
                class_breakdown = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        class_breakdown.append(dict(zip(columns, row)))
                
                # 4. Attendance Trend
                cursor.execute(f'FETCH ALL IN "{cursor_names[3]}"')
                trend = []
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        trend.append(dict(zip(columns, row)))

                # Close cursors
                for name in cursor_names:
                    cursor.execute(f'CLOSE "{name}"')

        # Map PascalCase SQL column names to expected JSON keys for frontend compatibility
        formatted_stats = {
            'total_marked': stats.get('TotalMarked', 0),
            'present_count': stats.get('PresentCount', 0),
            'absent_count': stats.get('AbsentCount', 0),
            'leave_count': stats.get('LeaveCount', 0),
            'late_count': stats.get('LateCount', 0),
            'holiday_count': stats.get('HolidayCount', 0),
            'attendance_percentage': float(stats.get('AttendancePercentage', 0)),
            'absent_percentage': float(stats.get('AbsentPercentage', 0)),
            'late_percentage': float(stats.get('LatePercentage', 0))
        }

        return JsonResponse({
            'success': True,
            'stats': formatted_stats,
            'gender_stats': gender_stats,
            'class_breakdown': class_breakdown,
            'trend': trend
        })
    except Exception as e:
        logger.error(f"Error fetching attendance stats via proc: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_attendance_trend(request):
    """API endpoint for student attendance trend"""
    school_id = request.custom_user.get('school_id')
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    try:
        with connection.cursor() as cursor:
            trend_query = """
                WITH RECURSIVE MonthRange AS (
                    SELECT 
                        CASE 
                            WHEN %s IS NULL THEN (DATE_TRUNC('month', CURRENT_TIMESTAMP) - INTERVAL '5 months')::DATE
                            ELSE DATE_TRUNC('month', %s::DATE)::DATE
                        END AS MonthDate
                    UNION ALL
                    SELECT (MonthDate + INTERVAL '1 month')::DATE
                    FROM MonthRange
                    WHERE MonthDate + INTERVAL '1 month' <= 
                        CASE 
                            WHEN %s IS NULL THEN (DATE_TRUNC('month', CURRENT_TIMESTAMP) + INTERVAL '1 month - 1 day')::DATE
                            ELSE (DATE_TRUNC('month', %s::DATE) + INTERVAL '1 month - 1 day')::DATE
                        END
                )
                SELECT 
                    TO_CHAR(m.MonthDate, 'Mon YYYY') AS MonthYear,
                    EXTRACT(MONTH FROM m.MonthDate)::INT AS Month,
                    EXTRACT(YEAR FROM m.MonthDate)::INT AS Year,
                    COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS PresentPercentage,
                    COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS AbsentPercentage,
                    COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('late', 'l') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS LatePercentage,
                    COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('holiday', 'h') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS HolidayPercentage
                FROM MonthRange m
                LEFT JOIN "StudentAttendance" a ON 
                    DATE_TRUNC('month', a."AttendanceDate") = m.MonthDate
                    AND COALESCE(a."IsDeleted", FALSE) = FALSE
                    AND (%s IS NULL OR a."SchoolID" = %s)
                    AND (%s IS NULL OR a."ClassID"::integer = %s)
                    AND (%s IS NULL OR a."SectionID" = %s)
                GROUP BY m.MonthDate
                ORDER BY m.MonthDate
            """
            params = [
                from_date, from_date,
                to_date, to_date,
                school_id, school_id,
                class_id, class_id,
                section_id, section_id
            ]
            cursor.execute(trend_query, params)
            trend = []
            for row in cursor.fetchall():
                trend.append({
                    'MonthYear': row[0],
                    'Month': row[1],
                    'Year': row[2],
                    'PresentPercentage': float(row[3]),
                    'AbsentPercentage': float(row[4]),
                    'LatePercentage': float(row[5]),
                    'HolidayPercentage': float(row[6])
                })
                
            return JsonResponse({
                'success': True,
                'trend': trend
            })
    except Exception as e:
        logger.error(f"Error fetching attendance trend: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_staff_attendance(request):
    """API endpoint for staff attendance statistics"""
    school_id = request.custom_user.get('school_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    employee_id = request.GET.get('employee_id')
    status = request.GET.get('status')
    employment_type = request.GET.get('employment_type')
    
    try:
        with connection.cursor() as cursor:
            staff_att_query = """
                SELECT 
                    COALESCE(COUNT(*), 0) AS TotalMarked,
                    COALESCE(SUM(CASE WHEN LOWER(sa."Status") IN ('present', 'p') THEN 1 ELSE 0 END), 0) AS PresentCount,
                    COALESCE(SUM(CASE WHEN LOWER(sa."Status") IN ('absent', 'a') THEN 1 ELSE 0 END), 0) AS AbsentCount,
                    COALESCE(SUM(CASE WHEN LOWER(sa."Status") IN ('leave', 'lv') THEN 1 ELSE 0 END), 0) AS LeaveCount,
                    COALESCE(SUM(CASE WHEN LOWER(sa."Status") IN ('late', 'l') THEN 1 ELSE 0 END), 0) AS LateCount
                FROM "StaffAttendance" sa
                INNER JOIN "UserMaster" um ON sa."EmployeeID" = um."UserID"
                WHERE sa."SchoolID" = %s
                AND sa."IsDeleted" IS NOT TRUE
            """
            params = [school_id]
            if from_date:
                staff_att_query += " AND sa.\"AttendanceDate\" >= %s"
                params.append(from_date)
            if to_date:
                staff_att_query += " AND sa.\"AttendanceDate\" <= %s"
                params.append(to_date)
            if employee_id:
                staff_att_query += " AND sa.\"EmployeeID\" = %s"
                params.append(employee_id)
            if status:
                staff_att_query += " AND sa.\"Status\" = %s"
                params.append(status)
            if employment_type:
                staff_att_query += " AND um.\"EmploymentType\" = %s"
                params.append(employment_type)
                
            cursor.execute(staff_att_query, params)
            row = cursor.fetchone()
            total = row[0] or 0
            stats = {
                'total_marked': total,
                'present_count': row[1] or 0,
                'absent_count': row[2] or 0,
                'leave_count': row[3] or 0,
                'late_count': row[4] or 0,
                'present_percentage': round((row[1] or 0) * 100.0 / total, 2) if total > 0 else 0,
                'absent_percentage': round((row[2] or 0) * 100.0 / total, 2) if total > 0 else 0,
                'late_percentage': round((row[4] or 0) * 100.0 / total, 2) if total > 0 else 0,
                'leave_percentage': round((row[3] or 0) * 100.0 / total, 2) if total > 0 else 0
            }
            
            return JsonResponse({
                'success': True,
                'stats': stats
            })
    except Exception as e:
        logger.error(f"Error fetching staff attendance: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_expense(request):
    """API endpoint for expense/salary statistics"""
    school_id = request.custom_user.get('school_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    employment_type = request.GET.get('employment_type')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the centralized Expense Statistics procedure
                cursor.execute('SELECT * FROM "Proc_DashboardExpenseStats_Get"(%s::INTEGER, %s::DATE, %s::DATE)', [
                    school_id, from_date, to_date
                ])
                
                rows = cursor.fetchall()
                if not rows or len(rows) < 3:
                    raise Exception("Procedure did not return all required cursors (rs_overall, rs_breakdown, rs_trend)")
                
                cursor_names = [row[0] for row in rows]
                
                # 1. Overall Expense Stats
                cursor.execute(f'FETCH ALL IN "{cursor_names[0]}"')
                stats = {}
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        val_row = [float(v) if isinstance(v, (Decimal, float)) else v for v in row]
                        raw_stats = dict(zip(columns, val_row))
                        stats = {
                            'total_expense': raw_stats.get('TotalExpense', 0),
                            'total_paid': raw_stats.get('TotalPaid', 0),
                            'total_pending': raw_stats.get('TotalPending', 0),
                            'total_employees_processed': raw_stats.get('TotalEmployeesProcessed', 0),
                            'paid_employees': raw_stats.get('PaidEmployees', 0),
                            'unpaid_employees': raw_stats.get('UnpaidEmployees', 0),
                            'permanent_expense': raw_stats.get('PermanentExpense', 0),
                            'contract_expense': raw_stats.get('ContractExpense', 0),
                            'guest_expense': raw_stats.get('GuestExpense', 0)
                        }
                
                # 2. Profile Breakdown
                cursor.execute(f'FETCH ALL IN "{cursor_names[1]}"')
                profile_breakdown = []
                if cursor.description:
                    columns = [col[0].lower() for col in cursor.description]
                    for row in cursor.fetchall():
                        val_row = [float(v) if isinstance(v, (Decimal, float)) else v for v in row]
                        profile_breakdown.append(dict(zip(columns, val_row)))
                
                # 3. Expense Trend
                cursor.execute(f'FETCH ALL IN "{cursor_names[2]}"')
                trend = []
                if cursor.description:
                    for row in cursor.fetchall():
                        trend.append({
                            'month_year': row[0],
                            'total_expense': float(row[1])
                        })

                # Close cursors
                for name in cursor_names:
                    cursor.execute(f'CLOSE "{name}"')

        return JsonResponse({
            'success': True,
            'stats': stats,
            'profile_breakdown': profile_breakdown,
            'trend': trend
        })
    except Exception as e:
        logger.error(f"Error fetching expense stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
def api_dashboard_revenue(request):
    """API endpoint for revenue/fee statistics using centralized procedures"""
    school_id = request.custom_user.get('school_id')
    class_id = request.GET.get('class_id')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the centralized Revenue Statistics procedure
                cursor.execute('SELECT * FROM "Proc_DashboardRevenueStats_Get"(%s::INTEGER, %s::INTEGER, %s::DATE, %s::DATE)', [
                    school_id, class_id, from_date, to_date
                ])
                
                rows = cursor.fetchall()
                if not rows or len(rows) < 3:
                    raise Exception("Procedure did not return all required cursors (rs_overall, rs_breakdown, rs_trend)")
                
                cursor_names = [row[0] for row in rows]
                
                # 1. Overall Revenue Stats
                cursor.execute(f'FETCH ALL IN "{cursor_names[0]}"')
                stats = {}
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        val_row = [float(v) if isinstance(v, (Decimal, float)) else v for v in row]
                        raw_stats = dict(zip(columns, val_row))
                        stats = {
                            'total_revenue': raw_stats.get('TotalRevenue', 0),
                            'total_pending': raw_stats.get('TotalPending', 0),
                            'total_transactions': raw_stats.get('TotalTransactions', 0),
                            'total_students_paid': raw_stats.get('TotalStudentsPaid', 0),
                            'cash_revenue': raw_stats.get('CashRevenue', 0),
                            'online_revenue': raw_stats.get('OnlineRevenue', 0),
                            'cheque_revenue': raw_stats.get('ChequeRevenue', 0),
                            'card_revenue': raw_stats.get('CardRevenue', 0),
                            'total_discount': raw_stats.get('TotalDiscount', 0),
                            'admission_revenue': raw_stats.get('AdmissionRevenue', 0),
                            'fee_revenue': raw_stats.get('FeeRevenue', 0)
                        }
                
                # 2. Class Breakdown
                cursor.execute(f'FETCH ALL IN "{cursor_names[1]}"')
                class_breakdown = []
                if cursor.description:
                    columns = [col[0].lower() for col in cursor.description]
                    for row in cursor.fetchall():
                        val_row = [float(v) if isinstance(v, (Decimal, float)) else v for v in row]
                        class_breakdown.append(dict(zip(columns, val_row)))
                
                # 3. Revenue Trend
                cursor.execute(f'FETCH ALL IN "{cursor_names[2]}"')
                trend = []
                if cursor.description:
                    for row in cursor.fetchall():
                        trend.append({
                            'month_year': row[0],
                            'revenue': float(row[1])
                        })

                # Close cursors
                for name in cursor_names:
                    cursor.execute(f'CLOSE "{name}"')

        return JsonResponse({
            'success': True,
            'stats': stats,
            'class_breakdown': class_breakdown,
            'trend': trend
        })
    except Exception as e:
        logger.error(f"Error fetching revenue stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@custom_login_required
@require_http_methods(["GET"])
def api_user_menus(request):
    """API endpoint to get user menus"""
    profile_id = request.custom_user.get('profile_id')
    
    if not profile_id:
        return JsonResponse({'menus': []})
    
    try:
        menus = _fetch_user_menus(profile_id)
        return JsonResponse({'menus': menus['tree']})
    except Exception as e:
        logger.error(f"Error fetching menus: {str(e)}")
        return JsonResponse({'menus': []})


@custom_login_required
def api_dashboard_subscription_revenue(request):
    """
    API endpoint for Super Admin subscription revenue statistics.
    Uses the unified subscription report procedure to get summary data.
    """
    profile_id = request.custom_user.get('profile_id')
    
    # Strictly for Super Admin
    if profile_id != 1:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    try:
        with connection.cursor() as cursor:
            # Call Unified JSONB Report Procedure with NULL dates for overall summary
            cursor.execute("SELECT fn_subscription_full_report_v2(NULL, NULL)")
            result = cursor.fetchone()[0]
            
            # Parse JSON if needed
            if isinstance(result, str):
                result = json.loads(result)
            
            summary = result.get('summary', {}) if result else {}
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'total_revenue': float(summary.get('total_revenue') or 0),
                    'total_paid': float(summary.get('total_revenue') or 0), # Map to total_revenue as seen in subscription_views
                    'pending_amount': float(summary.get('pending_amount') or 0),
                    'total_subscribers': summary.get('total_subscribers', 0),
                    'active_subscribers': summary.get('active_subscribers', 0)
                }
            })
    except Exception as e:
        logger.error(f"Error fetching subscription revenue stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
def api_dashboard_ticket_stats(request):
    """API endpoint for filtered ticket statistics"""
    profile_id = request.custom_user.get('profile_id')
    school_id = request.custom_user.get('school_id')
    role_name = request.session.get('ProfileName')
    
    # Super Admin (1) can filter by school, others are locked to their context
    school_id_param = request.GET.get('school_id')
    if profile_id == 1 and school_id_param:
        target_school_id = decrypt_id_int(school_id_param) or 0
    else:
        target_school_id = school_id

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    try:
        with connection.cursor() as cursor:
            # Call the centralized Dashboard Ticket Statistics procedure with explicit type casts
            cursor.execute('''
                SELECT * FROM "Proc_DashboardTicketStats_Get"(
                    %s::INTEGER, 
                    %s::VARCHAR, 
                    %s::INTEGER, 
                    %s::TIMESTAMP, 
                    %s::TIMESTAMP
                )
            ''', [
                request.custom_user.get('user_id'), role_name, target_school_id, from_date, to_date
            ])
            
            row = cursor.fetchone()
            if row:
                pulse_json, trend_json, distribution_json, leaderboard_json = row
                
                return JsonResponse({
                    'success': True,
                    'stats': json.loads(pulse_json) if pulse_json else {},
                    'trend': json.loads(trend_json) if trend_json else [],
                    'distribution': json.loads(distribution_json) if distribution_json else {},
                    'leaderboard': json.loads(leaderboard_json) if leaderboard_json else []
                })
            else:
                return JsonResponse({'success': False, 'error': 'No data returned'}, status=500)
    except Exception as e:
        logger.error(f"Error fetching dashboard ticket stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
