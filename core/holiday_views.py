import calendar
from datetime import datetime
from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .utils import get_context, get_school_dropdown, safe_int
from .url_encryption import encrypt_id, decrypt_id_int
import json
from django.core.serializers.json import DjangoJSONEncoder

def holiday_calendar(request):
    """Read-only view for the header icon (standalone or modal content)."""
    context = get_context(request)
    
    # Check if requested via AJAX for modal
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    
    now = datetime.now()
    year = safe_int(request.GET.get('year'), now.year)
    month = safe_int(request.GET.get('month'), now.month)
    
    raw_school_id = request.GET.get('school_id')
    decrypted_school_id = decrypt_id_int(raw_school_id) if raw_school_id else None
    school_id = context['school_id'] if not context['is_super_admin'] else (decrypted_school_id or safe_int(raw_school_id))

    if context['is_super_admin'] and not school_id:
        schools = get_school_dropdown()
        if schools: school_id = schools[0]['SchoolID']

    # Fetch holidays using the optimized procedure
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM "Proc_HolidayMaster_List"(%s, %s)', [school_id, year])
        columns = [col[0] for col in cursor.description]
        holidays_raw = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Process holidays into a useful map for the monthly view
    holiday_map = {}
    recurring_weekly = {} # day_of_week -> holiday_obj

    for h in holidays_raw:
        if h['DayOfWeek'] is not None and h['IsRecurring']:
            recurring_weekly[h['DayOfWeek']] = h
        elif h['HolidayDate']:
            d = h['HolidayDate']
            key = f"{d.month}-{d.day}" if h['IsRecurring'] else f"{d.year}-{d.month}-{d.day}"
            if key not in holiday_map: holiday_map[key] = []
            holiday_map[key].append(h)

    # Calendar generation
    cal = calendar.Calendar(firstweekday=6) # Sunday start
    month_days = cal.monthdays2calendar(year, month)
    
    # Hydrate month_days with holiday info
    processed_days = []
    for week in month_days:
        week_data = []
        for day, weekday in week:
            if day == 0:
                week_data.append({'day': 0})
            else:
                date_key = f"{year}-{month}-{day}"
                rec_key = f"{month}-{day}"
                day_holidays = []
                
                # 1. Check specific date
                if date_key in holiday_map: day_holidays.extend(holiday_map[date_key])
                # 2. Check recurring fixed date
                if rec_key in holiday_map: day_holidays.extend(holiday_map[rec_key])
                # 3. Check recurring weekly off
                # Python calendar: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
                # Our DB: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat
                # Convert Python weekday to our DB format
                db_weekday = (weekday + 1) % 7
                
                if db_weekday in recurring_weekly:
                    day_holidays.append(recurring_weekly[db_weekday])
                
                week_data.append({
                    'day': day,
                    'is_today': (day == now.day and month == now.month and year == now.year),
                    'holidays': day_holidays
                })
        processed_days.append(week_data)

    # Next/Prev navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context.update({
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'processed_days': processed_days,
        'selected_school_id': school_id,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'is_modal': is_ajax,
    })
    
    template = 'core/components/calendar_modal_content.html' if is_ajax else 'core/holiday_calendar.html'
    return render(request, template, context)

def holiday_list(request):
    """Interactive management dashboard for holidays."""
    context = get_context(request)
    if not (context['is_super_admin'] or context['is_admin']):
        messages.error(request, "Permission denied.")
        return redirect('dashboard')
        
    raw_school_id = request.GET.get('school_id')
    decrypted_school_id = decrypt_id_int(raw_school_id) if raw_school_id else None
    school_id = context['school_id'] if not context['is_super_admin'] else (decrypted_school_id or safe_int(raw_school_id))
    
    year = safe_int(request.GET.get('year'), datetime.now().year)

    if context['is_super_admin'] and not school_id:
        schools = get_school_dropdown()
        if schools: school_id = schools[0]['SchoolID']

    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM "Proc_HolidayMaster_List"(%s, %s)', [school_id, year])
        columns = [col[0] for col in cursor.description]
        holidays = [dict(zip(columns, row)) for row in cursor.fetchall()]

    context.update({
        'holidays': holidays,
        'holidays_json': json.dumps(holidays, cls=DjangoJSONEncoder),
        'schools': [{'SchoolID': s['SchoolID'], 'DisplayName': s['DisplayName'], 'EncID': encrypt_id(s['SchoolID'])} for s in get_school_dropdown()] if context['is_super_admin'] else [],
        'selected_school_id': encrypt_id(school_id) if school_id else '',
        'selected_year': year,
        'years': range(year - 1, year + 3),
        'active_view': request.GET.get('view', 'table'),
    })
    return render(request, 'core/holiday_list.html', context)

def holiday_manage(request):
    """CRUD handler for holidays."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
        
    context = get_context(request)
    if not (context['is_super_admin'] or context['is_admin']):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    action = request.POST.get('action', 'INSERT')
    holiday_id = safe_int(request.POST.get('holiday_id'), None)
    
    form_school_id = safe_int(request.POST.get('school_id'))
    school_id = form_school_id if context['is_super_admin'] else context['school_id']
    
    try:
        is_recurring = request.POST.get('is_recurring') == 'true'
        rec_type = request.POST.get('rec_type')
        day_of_week = safe_int(request.POST.get('day_of_week'), None)
        holiday_date = request.POST.get('holiday_date') or None

        # Data Integrity Enforcement:
        if is_recurring:
            if rec_type == 'date':
                day_of_week = None  # Force null for yearly date recurrence
            elif rec_type == 'day':
                holiday_date = None  # Force null for weekly day recurrence
        else:
            day_of_week = None  # Force null for one-time holidays

        with connection.cursor() as cursor:
            cursor.execute('SELECT "Proc_HolidayMaster_Manage"(%s, %s, %s, %s::DATE, %s, %s, %s, %s, %s, %s)', [
                action, holiday_id, school_id, holiday_date,
                request.POST.get('holiday_name'),
                request.POST.get('holiday_type', 'Public'),
                request.POST.get('description'),
                is_recurring, day_of_week, context['user_id']
            ])
            res_id = cursor.fetchone()[0]
        return JsonResponse({'status': 'success', 'holiday_id': res_id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def generate_weekly_offs(request):
    """Bulk generator for weekly offs (Optimized)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
        
    context = get_context(request)
    if not (context['is_super_admin'] or context['is_admin']):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    form_school_id = safe_int(request.POST.get('school_id'))
    school_id = form_school_id if context['is_super_admin'] else context['school_id']
    
    day_of_week = safe_int(request.POST.get('day_of_week', 0)) # 0 = Sunday
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "Proc_HolidayMaster_BulkGenerate"(%s, %s, %s)', [
                school_id, day_of_week, context['user_id']
            ])
            result = cursor.fetchone()[0]
        return JsonResponse({'status': 'success', 'created': result == 1})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
