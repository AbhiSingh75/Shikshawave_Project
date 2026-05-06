"""
Leave Management Views for ShikshaWave
Handles: leave types, balances, applications, approvals, reports
"""
import json
import logging
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection
from core.decorators import login_required
from core.utils import get_context, get_school_dropdown

logger = logging.getLogger(__name__)

ADMIN_PROFILES = ['Super Admin', 'School Admin']


# ─────────────────────────────────────────────────────────
# Helper: get session basics
# ─────────────────────────────────────────────────────────
def _session(request):
    return {
        'school_id':    request.session.get('SchoolID'),
        'user_id':      request.session.get('UserId'),
        'profile_id':   request.session.get('ProfileID'),
        'profile_name': request.session.get('ProfileName'),
    }


# ─────────────────────────────────────────────────────────
# Leave Dashboard (main hub)
# ─────────────────────────────────────────────────────────
@login_required
def leave_dashboard(request):
    s = _session(request)
    school_id    = s['school_id']
    user_id      = s['user_id']
    profile_name = s['profile_name']

    is_admin = profile_name in ADMIN_PROFILES

    # Current year
    current_year = date.today().year

    # Resolve school for super admin
    if profile_name == 'Super Admin':
        req_school_id = request.GET.get('school_id')
        if req_school_id:
            try:
                school_id = int(req_school_id)
            except (ValueError, TypeError):
                pass

    if not school_id and profile_name not in ['Super Admin', 'Support Executive']:
        return redirect('dashboard')

    # Leave types
    leave_types = []
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM Proc_LeaveType_List(%s)', [school_id])
                cols = [c[0] for c in cursor.description]
                leave_types = [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"leave_dashboard - leave types error: {e}")

    # Balance - Show for selected employee if admin, otherwise self
    selected_emp_id = request.GET.get('employee_id')
    if not selected_emp_id or not is_admin:
        selected_emp_id = user_id
    
    balance = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM Proc_LeaveBalance_Get(%s, %s, %s)',
                [school_id, selected_emp_id, current_year]
            )
            cols = [c[0] for c in cursor.description]
            balance = [dict(zip(cols, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"leave_dashboard - balance error: {e}")

    # Pending requests (last 20) – all for admin, own for staff
    requests_data = {}
    try:
        emp_filter = None if is_admin else user_id
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT Proc_LeaveRequest_List(%s,%s,%s,%s,%s,%s)',
                [school_id, emp_filter, None, current_year, 1, 50]
            )
            row = cursor.fetchone()
            if row and row[0]:
                raw = row[0]
                requests_data = raw if isinstance(raw, dict) else json.loads(raw)
    except Exception as e:
        logger.error(f"leave_dashboard - requests error: {e}")

    # Schools list    # Super Admin get schools
    schools_list = []
    if profile_name == 'Super Admin':
        # The original import for get_school_dropdown is already at the top: `from core.utils import get_school_dropdown`
        # Adding `from .utils import get_school_dropdown` here would be redundant or incorrect if `utils` is not in the same package.
        # Assuming `get_school_dropdown` is already imported from `core.utils` as per the file's header.
        try:
            schools_list = get_school_dropdown()
            # Add a placeholder for global staff if needed, or handle it via empty school_id
        except Exception as e:
            logger.error(f"leave_dashboard - schools error: {e}")

    # Use simple calendar years as per global standard
    current_year = date.today().year
    academic_years = [str(y) for y in range(current_year - 1, current_year + 3)]

    ctx = get_context(request)
    ctx.update({
        'leave_types':    leave_types,
        'balance':        balance,
        'requests':       requests_data.get('records', []),
        'total_requests': requests_data.get('total', 0),
        'is_admin':       is_admin,
        'is_super_admin': profile_name == 'Super Admin',
        'current_year':   current_year,
        'academic_years': academic_years,
        'school_id':      school_id,
        'schools_list':   schools_list,
        'selected_school_id': school_id,
        'selected_employee_id': selected_emp_id,
        'user_id':        user_id,
        'active_tab':     request.GET.get('tab', 'balance'),
    })
    return render(request, 'core/leave_dashboard.html', ctx)


@login_required
def api_staff_leave_balances(request):
    """AJAX: Returns leave balance table for all staff (Admin only)."""
    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    school_id = s['school_id']
    if s['profile_name'] == 'Super Admin':
        # Default to session school, but allow override or empty for global
        school_id_raw = request.GET.get('school_id')
        if school_id_raw is not None:
             try:
                 school_id = int(school_id_raw) if school_id_raw else None
             except (ValueError, TypeError):
                 school_id = None

    year_raw = request.GET.get('year') or str(date.today().year)
    try:
        if '-' in str(year_raw):
            year_raw = str(year_raw).split('-')[0]
        year = int(year_raw)
    except (ValueError, TypeError):
        year = date.today().year

    employee_id = request.GET.get('employee_id') or None
    search      = request.GET.get('search') or None

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveBalance_StaffList(%s, %s, %s, %s)', [school_id, year, employee_id, search])
            cols = [c[0] for c in cursor.description]
            records = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
        return JsonResponse({'status': 'SUCCESS', 'data': {'records': records}})
    except Exception as e:
        logger.error(f"api_staff_leave_balances error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Type: Save (AJAX POST)
# ─────────────────────────────────────────────────────────
@login_required
def leave_type_save(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    # For Super Admin, allow school_id override from POST
    school_id = s['school_id']
    if s['profile_name'] == 'Super Admin' and 'school_id' in request.POST:
        sid_raw = request.POST.get('school_id')
        school_id = int(sid_raw) if sid_raw else None

    leave_type_id   = request.POST.get('leave_type_id') or '0'
    name            = request.POST.get('name', '').strip()
    code            = request.POST.get('code', '').strip().upper()
    total_days      = float(request.POST.get('total_days') or 0)
    carry_forward   = request.POST.get('carry_forward') == '1'
    max_carry_days  = float(request.POST.get('max_carry_days') or 0)

    if not name or not code or total_days <= 0:
        return JsonResponse({'status': 'ERROR', 'message': 'Name, code, and total days are required'})

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM Proc_LeaveType_Save(%s,%s,%s,%s,%s,%s,%s,%s)',
                [school_id, int(leave_type_id), name, code, total_days,
                 carry_forward, max_carry_days, s['user_id']]
            )
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({'status': result['status'], 'message': result['message'],
                             'leave_type_id': result.get('leave_type_id', 0)})
    except Exception as e:
        logger.error(f"leave_type_save error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Type: Delete (AJAX POST)
# ─────────────────────────────────────────────────────────
@login_required
def leave_type_delete_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    leave_type_id = request.POST.get('leave_type_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveType_Delete(%s,%s)', [leave_type_id, s['user_id']])
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({'status': result['status'], 'message': result['message']})
    except Exception as e:
        logger.error(f"leave_type_delete error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Type: Restore (AJAX POST)
# ─────────────────────────────────────────────────────────
@login_required
def leave_type_restore_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    leave_type_id = request.POST.get('leave_type_id')
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveType_Restore(%s,%s)', [leave_type_id, s['user_id']])
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({'status': result['status'], 'message': result['message']})
    except Exception as e:
        logger.error(f"leave_type_restore error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Balance: Initialize (AJAX POST - Admin only)
# ─────────────────────────────────────────────────────────
@login_required
def leave_balance_init(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    # For Super Admin, check if school_id is passed in POST
    if s['profile_name'] == 'Super Admin' and request.POST.get('school_id'):
        try:
            school_id = int(request.POST.get('school_id'))
        except (ValueError, TypeError):
            school_id = s['school_id']
    else:
        school_id = s['school_id']

    if not school_id and s['profile_name'] != 'Super Admin':
        return JsonResponse({'status': 'ERROR', 'message': 'School ID not found'})

    year = request.POST.get('year') or str(date.today().year)

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveBalance_Init(%s,%s,%s)',
                           [school_id, year, s['user_id']])
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({
            'status': result['status'],
            'message': result['message'],
            'records_created': result.get('records_created', 0)
        })
    except Exception as e:
        logger.error(f"leave_balance_init error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Balance: API (GET) – returns employee's balance as JSON
# ─────────────────────────────────────────────────────────
@login_required
def leave_balance_api(request):
    s = _session(request)
    school_id = s['school_id']
    employee_id = request.GET.get('employee_id')

    # Non-admin can only see own
    if s['profile_name'] not in ADMIN_PROFILES:
        employee_id = s['user_id']
    elif not employee_id:
        employee_id = s['user_id']

    year = int(request.GET.get('year') or date.today().year)

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveBalance_Get(%s,%s,%s)',
                           [school_id, employee_id, year])
            cols = [c[0] for c in cursor.description]
            balance = [dict(zip(cols, row)) for row in cursor.fetchall()]
            # Convert Decimal to float for JSON
            for b in balance:
                for k, v in b.items():
                    if hasattr(v, '__float__'):
                        b[k] = float(v)
        return JsonResponse({'status': 'SUCCESS', 'data': balance})
    except Exception as e:
        logger.error(f"leave_balance_api error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Apply Leave (Staff + Admin)
# ─────────────────────────────────────────────────────────
@login_required
def leave_apply(request):
    s = _session(request)
    school_id    = s['school_id']
    user_id      = s['user_id']
    profile_name = s['profile_name']

    # Restrict super admin and school admin from applying leave
    if profile_name in ADMIN_PROFILES:
        return redirect('leave_dashboard')

    if not school_id and profile_name not in ['Super Admin']:
        return redirect('dashboard')

    # GET: render form
    leave_types = []
    balance = []
    current_year = date.today().year
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_LeaveType_List(%s)', [school_id])
            cols = [c[0] for c in cursor.description]
            leave_types = [dict(zip(cols, row)) for row in cursor.fetchall()
                           if not row[cols.index('IsDeleted')]]

            cursor.execute('SELECT * FROM Proc_LeaveBalance_Get(%s,%s,%s)',
                           [school_id, user_id, current_year])
            cols = [c[0] for c in cursor.description]
            balance = [dict(zip(cols, row)) for row in cursor.fetchall()]
            for b in balance:
                for k, v in b.items():
                    if hasattr(v, '__float__'):
                        b[k] = float(v)
    except Exception as e:
        logger.error(f"leave_apply GET error: {e}")

    if request.method == 'POST':
        # AJAX submission
        leave_type_id   = request.POST.get('leave_type_id')
        from_date       = request.POST.get('from_date')
        to_date         = request.POST.get('to_date')
        is_half_day     = request.POST.get('is_half_day') == '1'
        half_day_part   = request.POST.get('half_day_part') or None
        reason          = request.POST.get('reason', '').strip()

        if not all([leave_type_id, from_date, to_date]):
            return JsonResponse({'status': 'ERROR', 'message': 'Leave type, from date, and to date are required'})

        if is_half_day:
            to_date = from_date  # half day is single day

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM Proc_LeaveRequest_Apply(%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                    [school_id, user_id, leave_type_id, from_date, to_date,
                     is_half_day, half_day_part, reason, user_id]
                )
                cols = [c[0] for c in cursor.description]
                result = dict(zip(cols, cursor.fetchone()))
            return JsonResponse({
                'status':     result['status'],
                'message':    result['message'],
                'request_id': result.get('request_id', 0)
            })
        except Exception as e:
            logger.error(f"leave_apply POST error: {e}")
            return JsonResponse({'status': 'ERROR', 'message': str(e)})

    ctx = get_context(request)
    ctx.update({
        'leave_types':  leave_types,
        'balance':      balance,
        'balance_json': json.dumps(balance),
        'today':        date.today().strftime('%Y-%m-%d'),
        'current_year': current_year,
        'school_id':    school_id,
    })
    return render(request, 'core/leave_apply.html', ctx)


# ─────────────────────────────────────────────────────────
# Leave Request List (AJAX GET)
# ─────────────────────────────────────────────────────────
@login_required
def leave_request_list(request):
    s = _session(request)
    school_id    = s['school_id']
    user_id      = s['user_id']
    profile_name = s['profile_name']

    is_admin    = profile_name in ADMIN_PROFILES
    employee_id = request.GET.get('employee_id') if is_admin else user_id
    
    # Super Admin can view other schools or global (NULL)
    if profile_name == 'Super Admin':
        school_id_raw = request.GET.get('school_id')
        if school_id_raw is not None:
            try:
                school_id = int(school_id_raw) if school_id_raw else None
            except (ValueError, TypeError):
                school_id = None

    status      = request.GET.get('status') or None
    year_raw    = request.GET.get('year') or str(date.today().year)
    try:
        if '-' in str(year_raw):
            year_raw = str(year_raw).split('-')[0]
        year = int(year_raw)
    except (ValueError, TypeError):
        year = date.today().year
        
    page        = int(request.GET.get('page') or 1)
    page_size   = int(request.GET.get('page_size') or 20)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT Proc_LeaveRequest_List(%s,%s,%s,%s,%s,%s)',
                [school_id, employee_id or None, status, year, page, page_size]
            )
            row = cursor.fetchone()
            raw = row[0] if row else {}
            data = raw if isinstance(raw, dict) else json.loads(raw)

            # Serialize date objects
            for rec in data.get('records', []):
                for k in ('FromDate', 'ToDate', 'RequestedOn', 'ApprovedOn'):
                    if rec.get(k) and hasattr(rec[k], 'isoformat'):
                        rec[k] = rec[k].isoformat()
                if rec.get('DaysRequested') and hasattr(rec['DaysRequested'], '__float__'):
                    rec['DaysRequested'] = float(rec['DaysRequested'])

        return JsonResponse({'status': 'SUCCESS', 'data': data})
    except Exception as e:
        logger.error(f"leave_request_list error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Approve / Reject Leave (AJAX POST - Admin only)
# ─────────────────────────────────────────────────────────
@login_required
def leave_approve_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    if s['profile_name'] not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    request_id = request.POST.get('request_id')
    action     = request.POST.get('action')  # 'Approved' or 'Rejected'
    remarks    = request.POST.get('remarks', '').strip()

    if action not in ('Approved', 'Rejected'):
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid action'})

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM Proc_LeaveRequest_Approve(%s,%s,%s,%s)',
                [request_id, s['user_id'], action, remarks or None]
            )
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({'status': result['status'], 'message': result['message']})
    except Exception as e:
        logger.error(f"leave_approve_ajax error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Cancel Leave (AJAX POST - Staff)
# ─────────────────────────────────────────────────────────
@login_required
def leave_cancel_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid method'})

    s = _session(request)
    request_id = request.POST.get('request_id')

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM Proc_LeaveRequest_Cancel(%s,%s)',
                [request_id, s['user_id']]
            )
            cols = [c[0] for c in cursor.description]
            result = dict(zip(cols, cursor.fetchone()))
        return JsonResponse({'status': result['status'], 'message': result['message']})
    except Exception as e:
        logger.error(f"leave_cancel_ajax error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Leave Report Page
# ─────────────────────────────────────────────────────────
@login_required
def leave_report(request):
    from datetime import datetime
    s = _session(request)
    school_id    = s['school_id']
    profile_name = s['profile_name']
    is_admin     = profile_name in ADMIN_PROFILES
    current_year = datetime.now().year

    if not school_id and profile_name not in ['Super Admin']:
        return redirect('dashboard')

    # Employees for dropdown (admin only)
    employees = []
    if is_admin and school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "UserID", "UserName", "UserCode"
                    FROM "UserMaster"
                    WHERE "SchoolID" = %s AND "IsActive" = TRUE
                      AND COALESCE("IsDeleted", FALSE) = FALSE
                      AND "ProfileID" != 1
                    ORDER BY "UserName"
                """, [school_id])
                employees = [{'id': r[0], 'name': r[1], 'code': r[2]} for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"leave_report employees error: {e}")

    ctx = get_context(request)
    ctx.update({
        'employees':    employees,
        'is_admin':     is_admin,
        'is_super_admin': profile_name == 'Super Admin',
        'current_year':   current_year,
        'academic_years': [str(y) for y in range(current_year - 1, current_year + 3)],
        'school_id':      school_id,
        'months': [
            (1,'January'),(2,'February'),(3,'March'),(4,'April'),
            (5,'May'),(6,'June'),(7,'July'),(8,'August'),
            (9,'September'),(10,'October'),(11,'November'),(12,'December')
        ]
    })
    return render(request, 'core/leave_report.html', ctx)


# ─────────────────────────────────────────────────────────
# Leave Report Data (AJAX GET)
# ─────────────────────────────────────────────────────────
@login_required
def leave_report_data(request):
    s = _session(request)
    school_id    = s['school_id']
    profile_name = s['profile_name']
    is_admin     = profile_name in ADMIN_PROFILES

    employee_id = request.GET.get('employee_id') if is_admin else s['user_id']
    month       = request.GET.get('month') or None
    current_year = date.today().year
    year        = int(request.GET.get('year') or current_year)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT Proc_LeaveReport_Get(%s,%s,%s,%s)',
                [school_id, employee_id or None, month or None, year]
            )
            row = cursor.fetchone()
            raw = row[0] if row else {}
            data = raw if isinstance(raw, dict) else json.loads(raw)

            # Convert Decimal fields
            for rec in data.get('records', []):
                for k in ('TotalDaysTaken',):
                    if rec.get(k) and hasattr(rec[k], '__float__'):
                        rec[k] = float(rec[k])

        return JsonResponse({'status': 'SUCCESS', 'data': data})
    except Exception as e:
        logger.error(f"leave_report_data error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})


# ─────────────────────────────────────────────────────────
# Get School Employees (AJAX GET - Admin only, for filter dropdowns)
# ─────────────────────────────────────────────────────────
@login_required
def get_school_employees(request):
    s = _session(request)
    school_id    = s['school_id']
    profile_name = s['profile_name']

    if profile_name not in ADMIN_PROFILES:
        return JsonResponse({'status': 'ERROR', 'message': 'Permission denied'})

    if not school_id:
        return JsonResponse({'status': 'SUCCESS', 'data': []})

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "UserID", "UserName", "UserCode"
                FROM "UserMaster"
                WHERE "SchoolID" = %s AND "IsActive" = TRUE
                  AND COALESCE("IsDeleted", FALSE) = FALSE
                  AND "ProfileID" != 1
                ORDER BY "UserName"
            """, [school_id])
            employees = [{'id': r[0], 'name': r[1], 'code': r[2]} for r in cursor.fetchall()]
        return JsonResponse({'status': 'SUCCESS', 'data': employees})
    except Exception as e:
        logger.error(f"get_school_employees error: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
