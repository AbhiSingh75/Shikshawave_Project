from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging
from .decorators import custom_login_required
from .url_encryption import encrypt_id, decrypt_id_int
from functools import wraps

logger = logging.getLogger(__name__)


def get_context(request):
    import base64
    user_name = request.session.get('UserName', '')
    profile_name = request.session.get('ProfileName', '')
    school_name = request.session.get('SchoolName', '')
    user_id = request.session.get('UserId')
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    
    user_photo_src = ''
    school_logo_src = ''
    
    if user_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "UserPhoto" FROM "UserMaster" WHERE "UserID" = %s AND "IsDeleted" = FALSE', [user_id])
                photo_data = cursor.fetchone()
                if photo_data and photo_data[0]:
                    user_photo_src = f"data:image/jpeg;base64,{base64.b64encode(photo_data[0]).decode('utf-8')}"
        except Exception as e:
            logger.error(f"Error fetching user photo: {e}")
    
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID" = %s AND "IsDeleted" = FALSE', [school_id])
                logo_data = cursor.fetchone()
                if logo_data and logo_data[0]:
                    school_logo_src = f"data:image/jpeg;base64,{base64.b64encode(logo_data[0]).decode('utf-8')}"
        except Exception as e:
            logger.error(f"Error fetching school logo: {e}")
    
    return {
        'user_name': user_name,
        'profile_name': profile_name,
        'school_name': school_name,
        'user_photo_src': user_photo_src,
        'school_logo_src': school_logo_src,
        'profile_id': profile_id,
    }

@custom_login_required
def exam_management(request):
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    
    schools = []
    # If Super Admin (1) or Support Executive (6), fetch all schools
    if str(profile_id) in ['1', '6']:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "SchoolID", "SchoolName" FROM "SchoolMaster" WHERE "IsDeleted" = FALSE ORDER BY "SchoolName"')
            schools = cursor.fetchall()

    active_school = school_id
    exams = []
    academic_years = []
    total_records = 0

    if active_school:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_ExamMaster_View(%s, 1, 10, %s, %s, NULL, NULL, NULL, NULL)', 
                           [active_school, 'StartDate', 'DESC'])
            cols = [c.name for c in cursor.description]
            exams = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
            total_records = exams[0]['TotalRecords'] if exams else 0
            
            cursor.execute('SELECT "AcademicYearID", "AcademicYear" FROM "AcademicYear" WHERE "SchoolID" = %s AND "IsActive" = TRUE ORDER BY "AcademicYear" DESC', [active_school])
            academic_years = cursor.fetchall()
        
    context = get_context(request)
    # Robust Role Check for Template
    profile_name = context.get('profile_name', '').strip()
    is_admin_view = (str(profile_id) in ['1', '6'] or 
                     profile_id in [1, 6] or 
                     profile_name in ['Super Admin', 'Support Executive'])
    
    context.update({
        'exams': exams, 
        'academic_years': academic_years, 
        'total_records': total_records,
        'page_size': 10,
        'schools': schools,
        'active_school_id': active_school,
        'is_admin_view': is_admin_view
    })
    return render(request, 'core/exam_management.html', context)

@custom_login_required
def exam_list_ajax(request):
    try:
        # Get school_id from GET (admin choice) or session
        school_id = request.GET.get('school_id') or request.session.get('SchoolID')
        
        # Standardize school_id (handle encrypted IDs from global API)
        if school_id and not str(school_id).isdigit():
            school_id = decrypt_id_int(school_id)
            
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        sort_col = request.GET.get('sort_col', 'StartDate')
        sort_dir = request.GET.get('sort_dir', 'DESC')
        search = request.GET.get('search', '')
        year_id = request.GET.get('year_id')
        status = request.GET.get('status', '')
        exam_type = request.GET.get('type', '')
        
        if year_id == '' or year_id == 'null': year_id = None
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_ExamMaster_View(%s, %s, %s, %s, %s, %s, %s, %s, %s)', 
                [school_id, page_num, page_size, sort_col, sort_dir, search, year_id, status, exam_type])
            cols = [c.name for c in cursor.description]
            exams = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
            total_records = exams[0]['TotalRecords'] if exams else 0
            
            for exam in exams:
                exam['encrypted_id'] = encrypt_id(exam['ExamID'])
                exam['StartDate'] = exam['StartDate'].strftime('%Y-%m-%d') if exam['StartDate'] else ''
                exam['EndDate'] = exam['EndDate'].strftime('%Y-%m-%d') if exam['EndDate'] else ''
                
        return JsonResponse({
            'status': 'SUCCESS',
            'exams': exams,
            'total_records': total_records,
            'page': page_num,
            'page_size': page_size
        })
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def exam_save(request):
    try:
        data = json.loads(request.body)
        # Use school_id from data (admin choice) or session
        school_id = data.get('school_id') or request.session.get('SchoolID')
        
        # Standardize school_id (handle encrypted IDs from global API)
        if school_id and not str(school_id).isdigit():
            school_id = decrypt_id_int(school_id)
            
        user_id = request.session.get('UserId')
        with connection.cursor() as cursor:
            exam_id = data.get('exam_id')
            if exam_id == '' or exam_id == 'null' or exam_id == 'undefined':
                exam_id = None
                
            academic_year_id = data.get('academic_year_id')
            if academic_year_id == '' or academic_year_id == 'null' or academic_year_id == 'undefined':
                academic_year_id = None

            action = 'UPDATE' if exam_id else 'ADD'
            
            cursor.execute("SELECT Proc_ExamMaster_Set(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                [action, exam_id, school_id, data['exam_name'], data.get('exam_type'),
                 data.get('start_date'), data.get('end_date'), academic_year_id,
                 data.get('is_publish', 'No'), user_id])
            result = cursor.fetchone()
            if result:
                response = result[0]
                # PostgreSQL with psycopg2 returns json as dict; SQL Server returns as str
                if isinstance(response, str):
                    response = json.loads(response)
                
                # Check for both 'Status' and 'status' for robustness
                status = response.get('Status') or response.get('status')
                message = response.get('Message') or response.get('message')
                return JsonResponse({'status': status, 'message': message})
            return JsonResponse({'status': 'FAILED', 'message': 'No response from database'})
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def exam_delete(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('UserId')
        school_id = request.session.get('SchoolID')
        with connection.cursor() as cursor:
            cursor.execute("SELECT Proc_ExamMaster_Set('DELETE', %s, %s, NULL, NULL, NULL, NULL, NULL, 'No', %s)", 
                [data['exam_id'], school_id, user_id])
            result = cursor.fetchone()
            if result:
                response = result[0]
                if isinstance(response, str):
                    response = json.loads(response)
                
                status = response.get('Status') or response.get('status')
                message = response.get('Message') or response.get('message')
                return JsonResponse({'status': status, 'message': message})
            return JsonResponse({'status': 'FAILED', 'message': 'No response from database'})
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def exam_get(request, exam_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "ExamID", "ExamName", "ExamType", "StartDate", "EndDate", "AcademicYearId", "IsPublish" FROM "ExamMaster" WHERE "ExamID" = %s', [exam_id])
            row = cursor.fetchone()
            if row:
                return JsonResponse({
                    'ExamID': row[0], 'ExamName': row[1], 'ExamType': row[2],
                    'StartDate': row[3].strftime('%Y-%m-%d'), 'EndDate': row[4].strftime('%Y-%m-%d'),
                    'AcademicYearId': row[5], 'IsPublish': row[6]
                })
            return JsonResponse({'error': 'Not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@custom_login_required
@require_POST
def exam_restore(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('UserId')
        school_id = request.session.get('SchoolID')
        with connection.cursor() as cursor:
            cursor.execute("SELECT Proc_ExamMaster_Set('RESTORE', %s, %s, NULL, NULL, NULL, NULL, NULL, 'No', %s)", 
                [data['exam_id'], school_id, user_id])
            result = cursor.fetchone()
            if result:
                response = result[0]
                if isinstance(response, str):
                    response = json.loads(response)
                
                status = response.get('Status') or response.get('status')
                message = response.get('Message') or response.get('message')
                return JsonResponse({'status': status, 'message': message})
            return JsonResponse({'status': 'FAILED', 'message': 'No response from database'})
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})
