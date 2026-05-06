from django.shortcuts import render, redirect # type: ignore
from django.http import JsonResponse # type: ignore
from django.contrib import messages # type: ignore
from django.db import connection # type: ignore
from django.urls import reverse # type: ignore
import logging
import json
from .decorators import custom_login_required # type: ignore
from .utils import get_context, safe_int # type: ignore
from .url_encryption import decrypt_id_int # type: ignore
from mail.services import send_email_from_template # type: ignore
import threading
from typing import List, Dict, Any, Optional

# Global logger
logger = logging.getLogger(__name__)

def background_promotion_emails(school_id, academic_year, academic_year_id, student_ids_str, school_name=None):
    """Background task to send promotion emails without blocking the main request."""
    try:
        if not school_name:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolName" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                school_row = cursor.fetchone()
                school_name = school_row[0] if school_row else 'School Admin'

        ids_list = [int(sid) for sid in student_ids_str.split(',') if sid.strip().isdigit()]
        if not ids_list:
            return

        placeholders_sql = ','.join(['%s'] * len(ids_list))
        query = f"""
            SELECT 
                S."FullName", 
                S."Email", 
                CM."ClassName" as NewClass, 
                SM."SectionName" as NewSection,
                SAT."RollNumber",
                (SELECT CM2."ClassName" FROM "StudentAcademicTrack" SAT2 
                 JOIN "ClassMaster" CM2 ON SAT2."ClassID" = CM2."ClassID" 
                 WHERE SAT2."StudentID" = S."StudentID" AND SAT2."IsCurrent" = FALSE 
                 ORDER BY SAT2."TrackID" DESC LIMIT 1) as PrevClass,
                (SELECT SM2."SectionName" FROM "StudentAcademicTrack" SAT2 
                 JOIN "SectionMaster" SM2 ON SAT2."SectionID" = SM2."SectionID" 
                 WHERE SAT2."StudentID" = S."StudentID" AND SAT2."IsCurrent" = FALSE 
                 ORDER BY SAT2."TrackID" DESC LIMIT 1) as PrevSection
            FROM "Student" S
            JOIN "StudentAcademicTrack" SAT ON S."StudentID" = SAT."StudentID"
            JOIN "ClassMaster" CM ON SAT."ClassID" = CM."ClassID"
            JOIN "SectionMaster" SM ON SAT."SectionID" = SM."SectionID"
            WHERE S."StudentID" IN ({placeholders_sql})
              AND SAT."IsCurrent" = TRUE
              AND SAT."AcademicYearID" = %s
              AND S."SchoolID" = %s
        """
        params = ids_list + [academic_year_id, school_id]
        
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            promoted_students = cursor.fetchall()
            
            for p_student in promoted_students:
                student_name, student_email, new_class, new_section, roll_no, prev_class, prev_section = p_student
                if student_email:
                    placeholders = {
                        "student_name": student_name,
                        "new_class": new_class,
                        "new_section": new_section,
                        "prev_class": prev_class or "N/A",
                        "prev_section": prev_section or "N/A",
                        "roll_no": roll_no or "N/A",
                        "academic_year": academic_year, 
                        "school_name": school_name,
                        "to": student_email
                    }
                    try:
                        send_email_from_template('STUDENT_PROMOTION', school_id, 'en', placeholders)
                    except Exception as email_err:
                        logger.error(f"Failed to send email to {student_email}: {email_err}")
    except Exception as e:
        logger.error(f"Error in background_promotion_emails: {e}")

@custom_login_required
def promote_students(request):
    """
    Student Promotion page - Search and promote students to next class/section
    Uses GET method for search to allow bookmarking and avoid form resubmission warnings
    """
    # Get user context for header
    context = get_context(request)
    
    # Get user information - Robust extraction
    user_id = request.session.get('UserId') or (request.custom_user.get('user_id') if hasattr(request, 'custom_user') else None)
    school_id = request.session.get('SchoolID') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') else None)
    profile_id = request.session.get('ProfileID') or (request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None)
    
    is_super_admin = False
    if profile_id and int(profile_id) == 1:
        is_super_admin = True
        # For super admin, school_id comes from request GET params or context
        if request.GET.get('school_id'):
            school_id = request.GET.get('school_id')
    
    if not user_id:
        messages.error(request, "Please login to access student promotion")
        return redirect('login')
    
    # Validation for non-super admin
    if not is_super_admin and not school_id:
        messages.error(request, "School ID is required to access student promotion")
        return redirect('login')
    
    # Initialize variables with type hints for the linter
    students: List[Dict[str, Any]] = []
    total_count = 0
    start_index = 0
    end_index = 0
    has_next = False
    has_prev = False
    
    # Get search params from GET request
    page = safe_int(request.GET.get('page', 1))
    per_page = safe_int(request.GET.get('per_page', 25))
    search = request.GET.get('search', '').strip()
    class_id = request.GET.get('class_id', '')
    section_id = request.GET.get('section_id', '')
    
    # Search students if search parameters are provided or if school_id is selected (for SA)
    if search or class_id or section_id or (is_super_admin and school_id):
        try:
            if school_id:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT * FROM "func_promote_students_search"(%s, %s, %s, %s)', [
                        school_id,
                        int(class_id) if class_id else None,
                        int(section_id) if section_id else None,
                        search if search else None
                    ])
                    
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        raw_students = cursor.fetchall()
                        
                        for row in raw_students:
                            students.append(dict(zip(columns, row)))
                        
                        total_count = len(students)
            
        except Exception as e:
            logger.error(f"Error fetching students for promotion: {str(e)}", exc_info=True)
            messages.error(request, "Error loading student data. Please try again.")
    
    # Pagination
    if students:
        import math
        total_pages = math.ceil(total_count / per_page)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        # Use list comprehension instead of slicing to satisfy strict linter indexing checks
        students_page: List[Dict[str, Any]] = [
            students[i] for i in range(len(students)) 
            if start_index <= i < end_index
        ]
        
        has_next = page < total_pages
        has_prev = page > 1
    else:
        students_page = []
        start_index = 0
        end_index = 0
    
    context.update({
        'students': students_page,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'start_index': start_index + 1 if total_count > 0 else 0,
        'end_index': min(end_index, total_count),
        'has_next': has_next,
        'has_prev': has_prev,
        'search': search,
        'class_id': class_id,
        'section_id': section_id,
        'dark_mode': request.session.get('dark_mode', False),
        'is_super_admin': is_super_admin,
        'selected_school_id': school_id
    })
    
    return render(request, 'promote_students.html', context)

@custom_login_required
def promote_students_submit(request):
    """
    Handle student promotion submission
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    # Get user information - Robust extraction
    user_id = request.session.get('UserId') or (request.custom_user.get('user_id') if hasattr(request, 'custom_user') else None)
    school_id = request.session.get('SchoolID') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') else None)
    profile_id = request.session.get('ProfileID') or (request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None)
    
    if not user_id or not profile_id:
        return JsonResponse({'success': False, 'message': 'User session expired. Please login again.'})
        
    # Handle Super Admin school selection
    if int(profile_id) == 1:
        school_id = request.POST.get('school_id')
        if not school_id:
            return JsonResponse({'success': False, 'message': 'School selection is required for Super Admin'})
    elif not school_id:
        return JsonResponse({'success': False, 'message': 'School ID not found in session'})
    
    try:
        # Get form data
        student_ids = request.POST.get('student_ids', '')
        to_class_id = request.POST.get('to_class_id', '')
        to_section_id = request.POST.get('to_section_id', '')
        academic_year_id = request.POST.get('academic_year_id', '')
        remarks = request.POST.get('remarks', '')
        
        if not student_ids:
            return JsonResponse({'success': False, 'message': 'Please select at least one student'})
        if not to_class_id:
            return JsonResponse({'success': False, 'message': 'Please select target class'})
        if not to_section_id:
            return JsonResponse({'success': False, 'message': 'Please select target section'})
        if not academic_year_id:
            return JsonResponse({'success': False, 'message': 'Please select academic year'})
        
        # Get academic year from ID
        academic_year = None
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "AcademicYear" FROM "AcademicYear" 
                WHERE "AcademicYearID" = %s AND "SchoolID" = %s
            """, [academic_year_id, school_id])
            result = cursor.fetchone()
            if result:
                academic_year = result[0]
            else:
                return JsonResponse({'success': False, 'message': 'Invalid academic year selected'})
        
        # Call the stored procedure
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "func_student_academic_track_promote"(%s, %s, %s, %s, %s, %s, %s)', [
                school_id,
                student_ids,
                int(to_class_id),
                int(to_section_id),
                academic_year,
                remarks,
                profile_id
            ])
            
            row = cursor.fetchone()
            promoted_count = row[0] if row else 0
            failed_count = row[1] if row else 0
            error_message = row[2] if row else 'Unknown error'
            
            total_selected = promoted_count + failed_count
            
            if error_message and error_message != 'Success':
                return JsonResponse({
                    'success': False,
                    'message': error_message,
                    'promoted_count': promoted_count,
                    'failed_count': failed_count
                })
            elif promoted_count > 0:
                message = f'Successfully promoted {promoted_count} students.'
                if failed_count > 0:
                    message += f' {failed_count} students could not be promoted.'
                
                # Trigger email notification in background
                send_email_flag = request.POST.get('send_email') == 'true'
                if send_email_flag:
                    # Pre-fetch school name to avoid one extra DB hit in thread if possible
                    school_name = None
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT "SchoolName" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                            school_row = cursor.fetchone()
                            school_name = school_row[0] if school_row else None
                    except: pass
                    
                    email_thread = threading.Thread(
                        target=background_promotion_emails,
                        args=(school_id, academic_year, academic_year_id, student_ids, school_name)
                    )
                    email_thread.daemon = True
                    email_thread.start()
                
                return JsonResponse({'success': True, 'message': message})
            else:
                return JsonResponse({'success': False, 'message': 'No students were promoted.'})
            
    except Exception as e:
        logger.error(f"Error in student promotion: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error processing promotion: {str(e)}'})

@custom_login_required
def api_classes(request):
    """Return classes for the selected school."""
    # Robust extraction
    profile_id = request.session.get('ProfileID') or (request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None)
    school_id = request.session.get('SchoolID') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') else None)

    if str(profile_id) == '1':
        get_school = request.GET.get('school_id')
        if get_school:
            try:
                if str(get_school).isdigit():
                    school_id = int(get_school)
                else:
                    school_id = decrypt_id_int(get_school)
            except (ValueError, TypeError):
                pass
    
    classes = []
    try:
        with connection.cursor() as cursor:
            if school_id:
                cursor.execute("""
                    SELECT "ClassID", "ClassName" FROM "ClassMaster" 
                    WHERE "SchoolID" = %s AND COALESCE("IsDeleted", false) = false ORDER BY 1
                """, [school_id])
                rows = cursor.fetchall()
                classes = [{"ClassID": r[0], "ClassName": r[1]} for r in rows]
            else:
                cursor.execute('SELECT DISTINCT "ClassID", "ClassName" FROM "ClassMaster" WHERE COALESCE("IsDeleted", false) = false ORDER BY 1')
                rows = cursor.fetchall()
                classes = [{"ClassID": r[0], "ClassName": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"Error fetching classes: {e}")
    return JsonResponse({'classes': classes})

@custom_login_required
def api_sections(request):
    """Return sections for the selected class."""
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Class ID is required'})
    
    # Decrypt if encrypted ID
    if class_id and not str(class_id).isdigit():
        class_id = decrypt_id_int(class_id)
        if class_id is None:
            return JsonResponse({'status': 'FAILED', 'message': 'Invalid Class ID format'})
    
    sections = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "SectionID", "SectionName" FROM "SectionMaster" 
                WHERE "ClassID" = %s AND COALESCE("IsDeleted", false) = false ORDER BY 2
            """, [class_id])
            rows = cursor.fetchall()
            sections = [{"SectionID": r[0], "SectionName": r[1]} for r in rows]
        return JsonResponse({'status': 'SUCCESS', 'sections': sections})
    except Exception as e:
        logger.error(f"Error fetching sections: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def api_students(request):
    """Return students for the selected class and section."""
    # Robust extraction
    profile_id = request.session.get('ProfileID') or (request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None)
    school_id = request.session.get('SchoolID') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') else None)
    
    if str(profile_id) == '1':
        get_school = request.GET.get('school_id')
        if get_school:
            try: school_id = int(get_school)
            except: pass
            
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')
    
    # Decrypt IDs if they are not numeric
    if school_id and not str(school_id).isdigit():
        school_id = decrypt_id_int(school_id)
    if class_id and not str(class_id).isdigit():
        class_id = decrypt_id_int(class_id)
    if section_id and not str(section_id).isdigit():
        section_id = decrypt_id_int(section_id)
    
    if not school_id or not class_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Missing parameters'})
    
    students = []
    try:
        with connection.cursor() as cursor:
            # DEFINITIVE FIX: Use integer casting to match the newly created PostgreSQL function signature
            cursor.execute('SELECT * FROM "Proc_Student_list_for_fee_get"(%s::int, %s::int, %s::int)', 
                         [int(school_id), int(class_id), int(section_id) if section_id else None])
            rows = cursor.fetchall()
            students = [{"StudentCode": row[0], "FullName": row[1], "RollNumber": row[2] if len(row) > 2 else None} for row in rows]
        return JsonResponse({'students': students}, safe=False)
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def api_academic_years(request):
    """Return academic years for the selected school."""
    # Robust extraction
    profile_id = request.session.get('ProfileID') or (request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None)
    school_id = request.session.get('SchoolID') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') else None)
    
    if str(profile_id) == '1':
        get_school = request.GET.get('school_id')
        if get_school:
            try:
                if str(get_school).isdigit():
                    school_id = int(get_school)
                else:
                    school_id = decrypt_id_int(get_school)
            except: pass
            
    years = []
    try:
        with connection.cursor() as cursor:
            if school_id:
                cursor.execute("""
                    SELECT "AcademicYearID", "AcademicYear", "IsCurrent" 
                    FROM "AcademicYear" WHERE "SchoolID" = %s ORDER BY 1 DESC
                """, [school_id])
                rows = cursor.fetchall()
                years = [{"id": r[0], "name": r[1], "is_current": bool(r[2])} for r in rows]
    except Exception as e:
        logger.error(f"Error fetching academic years: {e}")
    return JsonResponse(years, safe=False)
