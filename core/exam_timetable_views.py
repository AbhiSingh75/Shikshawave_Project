from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging
from .decorators import custom_login_required
import base64
from functools import wraps
from .utils import get_context, safe_int
from .url_encryption import encrypt_id, decrypt_id, decrypt_id_int

logger = logging.getLogger(__name__)

from .database_email_queue import database_email_queue


@custom_login_required
def exam_timetable(request, encrypted_exam_id):
    exam_id = decrypt_id(encrypted_exam_id)
    if not exam_id:
        messages.error(request, "Invalid exam identifier")
        return redirect('exam_management')
    
    context = get_context(request)
    profile_id = request.session.get('ProfileID')
    
    # Super Admin / Support Executive can override school_id via GET param
    req_school_id = request.GET.get('school_id')
    if req_school_id and str(profile_id) in ['1', '6']:
        # Decrypt if necessary before storing in session
        if not str(req_school_id).isdigit():
            req_school_id = decrypt_id_int(req_school_id)
        if req_school_id:
            request.session['SchoolID'] = str(req_school_id)
    
    school_id = request.session.get('SchoolID')
    # Standardize school_id (ensure it's an integer for raw SQL)
    if school_id and not str(school_id).isdigit():
        school_id = decrypt_id_int(school_id)
    
    if not school_id:
        messages.error(request, "Unauthorized access or no school selected")
        return redirect('exam_management')
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT "ExamID", "ExamName", "ExamType", "StartDate", "EndDate" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s AND "IsActive" = FALSE', [exam_id, school_id])
        exam_row = cursor.fetchone()
        if not exam_row:
            messages.error(request, "Exam not found or access denied")
            return redirect('exam_management')
        exam = {'ExamID': exam_row[0], 'ExamName': exam_row[1], 'ExamType': exam_row[2], 'StartDate': exam_row[3], 'EndDate': exam_row[4]}
        cursor.execute("""
            SELECT c."ClassID", c."ClassName",
                   (SELECT COUNT(*) FROM "ExamTimeTable" WHERE "ExamID" = %s AND "ClassID" = c."ClassID" AND "IsActive" = FALSE) as ScheduledCount,
                   (SELECT COUNT(*) FROM "SubjectMaster" WHERE "ClassId" = c."ClassID" AND "SchoolID" = %s AND "IsDeleted" = FALSE) as TotalSubjects
            FROM "ClassMaster" c WHERE c."SchoolID" = %s ORDER BY c."ClassID"
        """, [exam_id, school_id, school_id])
        classes = [{'ClassID': r[0], 'ClassName': r[1], 'ScheduledCount': r[2], 'TotalSubjects': r[3], 'IsComplete': r[2] >= r[3] and r[3] > 0} for r in cursor.fetchall()]
        cursor.execute("""
            SELECT et."ExamTimeTableID", c."ClassName", s."SubjectName", et."ExamDate", et."StartTime", et."EndTime"
            FROM "ExamTimeTable" et
            JOIN "ClassMaster" c ON et."ClassID" = c."ClassID"
            JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
            WHERE et."ExamID" = %s AND et."SchoolID" = %s AND et."IsActive" = FALSE
            ORDER BY et."ExamDate", et."StartTime"
        """, [exam_id, school_id])
        scheduled_exams = [{'ExamTimeTableID': r[0], 'ClassName': r[1], 'SubjectName': r[2], 'ExamDate': r[3], 'StartTime': r[4], 'EndTime': r[5]} for r in cursor.fetchall()]
    context.update({
        'exam': exam,
        'classes': classes,
        'scheduled_exams': scheduled_exams,
        'page_title': 'Exam Time Table',
        'active_menu': 'exam_management'
    })
    return render(request, 'core/exam_timetable.html', context)

@custom_login_required
@require_POST
def exam_timetable_save(request):
    try:
        data = json.loads(request.body)
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        # Standardize school_id (handle encrypted IDs if necessary)
        if school_id and not str(school_id).isdigit():
            school_id = decrypt_id_int(school_id)
        
        if not school_id or not user_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'}, status=403)
        
        # Validate exam date is within master exam date range
        with connection.cursor() as cursor:
            cursor.execute('SELECT "StartDate", "EndDate" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s', [data['exam_id'], school_id])
            exam_dates = cursor.fetchone()
            if not exam_dates:
                return JsonResponse({'status': 'FAILED', 'message': 'Invalid exam'}, status=400)
            
            from datetime import datetime
            exam_date = datetime.strptime(data['exam_date'], '%Y-%m-%d').date()
            if exam_date < exam_dates[0] or exam_date > exam_dates[1]:
                return JsonResponse({'status': 'FAILED', 'message': f'Selected exam date is outside the exam period. Please select a date between {exam_dates[0].strftime("%d %b %Y")} and {exam_dates[1].strftime("%d %b %Y")}'}, status=400)
        
        timetable_id = data.get('timetable_id')
        action = 'UPDATE' if timetable_id else 'INSERT'
        with connection.cursor() as cursor:
            if action == 'INSERT':
                cursor.execute("""
                    INSERT INTO "ExamTimeTable" (
                        "ExamID", "SchoolID", "ClassID", "SubjectID",
                        "ExamDate", "StartTime", "EndTime",
                        "ExamMode", "ExamLocation", "RoomNo", "Invigilator",
                        "MaxTheoryMarks", "MinTheoryMarks",
                        "MaxPracticalMarks", "MinPracticalMarks",
                        "MaxVivaMarks", "MinVivaMarks",
                        "EvaluationType", "PassingCriteria", "Remarks",
                        "IsActive", "CreatedBy", "CreatedDate"
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        FALSE, %s, NOW()
                    )
                """, [
                    data['exam_id'], school_id, data['class_id'], data['subject_id'],
                    data['exam_date'], data['start_time'], data['end_time'],
                    data.get('exam_mode', 'Offline'), data.get('exam_location'), data.get('room_no'), data.get('invigilator'),
                    data.get('max_theory_marks') or 0, data.get('min_theory_marks') or 0,
                    data.get('max_practical_marks') or None, data.get('min_practical_marks') or None,
                    data.get('max_viva_marks') or None, data.get('min_viva_marks') or None,
                    data.get('evaluation_type', 'Marks'), data.get('passing_criteria'), data.get('remarks'),
                    user_id
                ])
            else:
                cursor.execute("""
                    UPDATE "ExamTimeTable" SET
                        "ClassID" = %s, "SubjectID" = %s,
                        "ExamDate" = %s, "StartTime" = %s, "EndTime" = %s,
                        "ExamMode" = %s, "ExamLocation" = %s, "RoomNo" = %s, "Invigilator" = %s,
                        "MaxTheoryMarks" = %s, "MinTheoryMarks" = %s,
                        "MaxPracticalMarks" = %s, "MinPracticalMarks" = %s,
                        "MaxVivaMarks" = %s, "MinVivaMarks" = %s,
                        "EvaluationType" = %s, "PassingCriteria" = %s, "Remarks" = %s,
                        "UpdatedBy" = %s, "UpdatedDate" = NOW()
                    WHERE "ExamTimeTableID" = %s AND "SchoolID" = %s
                """, [
                    data['class_id'], data['subject_id'],
                    data['exam_date'], data['start_time'], data['end_time'],
                    data.get('exam_mode', 'Offline'), data.get('exam_location'), data.get('room_no'), data.get('invigilator'),
                    data.get('max_theory_marks') or 0, data.get('min_theory_marks') or 0,
                    data.get('max_practical_marks') or None, data.get('min_practical_marks') or None,
                    data.get('max_viva_marks') or None, data.get('min_viva_marks') or None,
                    data.get('evaluation_type', 'Marks'), data.get('passing_criteria'), data.get('remarks'),
                    user_id, timetable_id, school_id
                ])

        return JsonResponse({'status': 'SUCCESS', 'message': 'Timetable entry saved successfully'})
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def exam_timetable_delete(request):
    try:
        data = json.loads(request.body)
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        # Standardize school_id
        if school_id and not str(school_id).isdigit():
            school_id = decrypt_id_int(school_id)
        
        if not school_id or not user_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'}, status=403)
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE "ExamTimeTable"
                SET "IsActive" = TRUE, "UpdatedBy" = %s, "UpdatedDate" = NOW()
                WHERE "ExamTimeTableID" = %s AND "SchoolID" = %s
            """, [user_id, data.get('timetable_id'), school_id])
        return JsonResponse({'status': 'SUCCESS', 'message': 'Schedule deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def exam_timetable_get(request, encrypted_timetable_id):
    timetable_id = decrypt_id(encrypted_timetable_id)
    
    if not timetable_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Invalid identifier'}, status=400)
    school_id = request.session.get('SchoolID')
    
    # Standardize school_id
    if school_id and not str(school_id).isdigit():
        school_id = decrypt_id_int(school_id)
    
    if not school_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'}, status=403)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT et."ExamTimeTableID", et."ClassID", et."SubjectID", et."ExamDate", et."StartTime", et."EndTime", et."ExamMode", et."ExamLocation",
                   et."RoomNo", et."Invigilator", et."MaxTheoryMarks", et."MinTheoryMarks", et."MaxPracticalMarks", et."MinPracticalMarks",
                   et."MaxVivaMarks", et."MinVivaMarks", et."EvaluationType", et."PassingCriteria", et."Remarks", c."ClassName"
            FROM "ExamTimeTable" et JOIN "ClassMaster" c ON et."ClassID" = c."ClassID"
            WHERE et."ExamTimeTableID" = %s AND et."SchoolID" = %s AND et."IsActive" = FALSE
        """, [timetable_id, school_id])
        row = cursor.fetchone()
        if row:
            return JsonResponse({'status': 'SUCCESS', 'timetable': {
                'ExamTimeTableID': row[0], 'ClassID': row[1], 'SubjectID': row[2], 'ExamDate': row[3].isoformat() if row[3] else None,
                'StartTime': row[4].strftime('%H:%M') if row[4] else None, 'EndTime': row[5].strftime('%H:%M') if row[5] else None,
                'ExamMode': row[6], 'ExamLocation': row[7], 'RoomNo': row[8], 'Invigilator': row[9],
                'MaxTheoryMarks': row[10], 'MinTheoryMarks': row[11], 'MaxPracticalMarks': row[12], 'MinPracticalMarks': row[13],
                'MaxVivaMarks': row[14], 'MinVivaMarks': row[15], 'EvaluationType': row[16], 'PassingCriteria': row[17], 'Remarks': row[18], 'ClassName': row[19]
            }})
        return JsonResponse({'status': 'FAILED', 'message': 'Not found'})

@custom_login_required
def exam_timetable_print(request, encrypted_exam_id, encrypted_class_id):
    exam_id = decrypt_id(encrypted_exam_id)
    class_id = decrypt_id(encrypted_class_id)
    
    if not exam_id or not class_id:
        return HttpResponse("Invalid identifiers", status=400)
    import base64
    school_id = request.session.get('SchoolID')
    
    # Standardize school_id
    if school_id and not str(school_id).isdigit():
        school_id = decrypt_id_int(school_id)
    
    if not school_id:
        return HttpResponse("Unauthorized access", status=403)
    
    with connection.cursor() as cursor:
        # Verify exam belongs to school
        cursor.execute('SELECT "ExamID" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s AND "IsActive" = FALSE', [exam_id, school_id])
        if not cursor.fetchone():
            return HttpResponse("Exam not found or access denied", status=403)
        
        # Verify class belongs to school
        cursor.execute('SELECT "ClassID" FROM "ClassMaster" WHERE "ClassID" = %s AND "SchoolID" = %s', [class_id, school_id])
        if not cursor.fetchone():
            return HttpResponse("Class not found or access denied", status=403)
        # Get School Details
        cursor.execute('SELECT "SchoolName", "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
        school_row = cursor.fetchone()
        school_name = school_row[0] if school_row else "School Name"
        school_logo = None
        if school_row and school_row[1]:
            school_logo = f"data:image/png;base64,{base64.b64encode(school_row[1]).decode('utf-8')}"
        
        # Get Exam Details
        cursor.execute('SELECT "ExamName", "ExamType", "StartDate", "EndDate" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s', [exam_id, school_id])
        exam_row = cursor.fetchone()
        if not exam_row:
            return HttpResponse("Exam not found", status=404)
        exam = {'ExamName': exam_row[0], 'ExamType': exam_row[1], 'StartDate': exam_row[2], 'EndDate': exam_row[3]}
        
        # Get Class Name
        cursor.execute('SELECT "ClassName" FROM "ClassMaster" WHERE "ClassID" = %s AND "SchoolID" = %s', [class_id, school_id])
        class_row = cursor.fetchone()
        class_name = class_row[0] if class_row else "Unknown Class"
        
        # Get Timetable
        cursor.execute("""
            SELECT s."SubjectName", et."ExamDate", et."StartTime", et."EndTime", et."RoomNo", 
                   et."MaxTheoryMarks", et."MaxPracticalMarks", et."MaxVivaMarks"
            FROM "ExamTimeTable" et
            JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
            WHERE et."ExamID" = %s AND et."ClassID" = %s AND et."SchoolID" = %s AND et."IsActive" = FALSE
            ORDER BY et."ExamDate", et."StartTime"
        """, [exam_id, class_id, school_id])
        
        timetable = []
        for row in cursor.fetchall():
            timetable.append({
                'SubjectName': row[0],
                'ExamDate': row[1],
                'StartTime': row[2],
                'EndTime': row[3],
                'RoomNo': row[4],
                'MaxTheoryMarks': row[5],
                'MaxPracticalMarks': row[6],
                'MaxVivaMarks': row[7]
            })
        
        # Get template preference
        template_file = 'core/exam_timetable_print.html'
        template_param = request.GET.get('template')
        if template_param:
            template_file = template_param
        else:
            cursor.execute('SELECT "TemplateType", "TemplateFile" FROM "Proc_Template_Preference_Get"(%s)', [school_id])
            for row in cursor.fetchall():
                if row[0] == 'ExamTimetable':
                    template_file = row[1]
                    break
            
    context = {
        'school_name': school_name,
        'school_logo_src': school_logo,
        'exam': exam,
        'class_name': class_name,
        'timetable': timetable
    }
    
    return render(request, template_file, context)

@custom_login_required
def exam_timetable_filter(request, encrypted_exam_id, encrypted_class_id):
    exam_id = decrypt_id(encrypted_exam_id)
    class_id = decrypt_id(encrypted_class_id)
    
    if not exam_id or not class_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Invalid identifiers'}, status=400)
    school_id = request.session.get('SchoolID')
    
    # Standardize school_id
    if school_id and not str(school_id).isdigit():
        school_id = decrypt_id_int(school_id)
    
    if not school_id:
        return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'}, status=403)
    
    with connection.cursor() as cursor:
        # Verify exam and class belong to school
        cursor.execute('SELECT "ExamID" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s AND "IsActive" = FALSE', [exam_id, school_id])
        if not cursor.fetchone():
            return JsonResponse({'status': 'FAILED', 'message': 'Exam not found or access denied'}, status=403)
        
        cursor.execute('SELECT "ClassID" FROM "ClassMaster" WHERE "ClassID" = %s AND "SchoolID" = %s', [class_id, school_id])
        if not cursor.fetchone():
            return JsonResponse({'status': 'FAILED', 'message': 'Class not found or access denied'}, status=403)
        cursor.execute("""
            SELECT et."ExamTimeTableID", s."SubjectName", et."ExamDate", et."StartTime", et."EndTime", 
                   et."RoomNo", et."ExamLocation", et."ExamMode", 
                   et."MaxTheoryMarks", et."MinTheoryMarks", et."MaxPracticalMarks", et."MinPracticalMarks",
                   et."MaxVivaMarks", et."MinVivaMarks", et."EvaluationType", et."Invigilator", et."Remarks"
            FROM "ExamTimeTable" et
            JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
            WHERE et."ExamID" = %s AND et."ClassID" = %s AND et."SchoolID" = %s AND et."IsActive" = FALSE
            ORDER BY et."ExamDate", et."StartTime"
        """, [exam_id, class_id, school_id])
        
        timetable = []
        for row in cursor.fetchall():
            # Calculate Total Max Marks
            total_marks = 0
            if row[8]: total_marks += row[8] # MaxTheoryMarks
            if row[10]: total_marks += row[10] # MaxPracticalMarks
            if row[12]: total_marks += row[12] # MaxVivaMarks
            
            timetable.append({
                'ExamTimeTableID': row[0],
                'SubjectName': row[1],
                'ExamDate': row[2].isoformat() if row[2] else None,
                'StartTime': row[3].strftime('%H:%M') if row[3] else None,
                'EndTime': row[4].strftime('%H:%M') if row[4] else None,
                'RoomNo': row[5],
                'ExamLocation': row[6],
                'ExamMode': row[7],
                'MaxTheoryMarks': row[8],
                'MinTheoryMarks': row[9],
                'MaxPracticalMarks': row[10],
                'MinPracticalMarks': row[11],
                'MaxVivaMarks': row[12],
                'MinVivaMarks': row[13],
                'EvaluationType': row[14],
                'Invigilator': row[15],
                'Remarks': row[16],
                'TotalMaxMarks': total_marks
            })
            
    return JsonResponse({'status': 'SUCCESS', 'timetable': timetable})

@require_POST
@custom_login_required
def exam_timetable_send_email(request):
    """
    Sends the exam timetable to all students in a class via email queue.
    Expects JSON: { exam_id: int, class_id: int }
    """
    try:
        data = json.loads(request.body)
        exam_id = data.get('exam_id')
        class_id = data.get('class_id')
        
        if not exam_id or not class_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Missing Exam ID or Class ID'}, status=400)
            
        school_id = request.session.get('SchoolID')
        # Standardize school_id (handle encrypted strings)
        if school_id and not str(school_id).isdigit():
            school_id = decrypt_id_int(school_id)
            
        if not school_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'}, status=403)

        logger.info(f"Exam send email for school_id={school_id}, exam_id={exam_id}, class_id={class_id}")
        
        with connection.cursor() as cursor:
            # 1. Fetch Exam Name
            cursor.execute('SELECT "ExamName" FROM "ExamMaster" WHERE "ExamID" = %s AND "SchoolID" = %s', [exam_id, school_id])
            exam_row = cursor.fetchone()
            if not exam_row:
                logger.warning(f"Exam not found: exam_id={exam_id}, school_id={school_id}")
                return JsonResponse({'status': 'FAILED', 'message': f'Exam not found (ID: {exam_id}, School: {school_id})'}, status=200)
            exam_name = exam_row[0]
            
            # 2. Fetch Class Name
            cursor.execute('SELECT "ClassName" FROM "ClassMaster" WHERE "ClassID" = %s AND "SchoolID" = %s', [class_id, school_id])
            class_row = cursor.fetchone()
            if not class_row:
                logger.warning(f"Class not found: class_id={class_id}, school_id={school_id}")
                return JsonResponse({'status': 'FAILED', 'message': f'Class not found (ID: {class_id}, School: {school_id})'}, status=200)
            class_name = class_row[0]
            
            # 3. Fetch Timetable entries
            logger.info("Fetching timetable entries...")
            cursor.execute("""
                SELECT s."SubjectName", et."ExamDate", et."StartTime", et."EndTime"
                FROM "ExamTimeTable" et
                JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
                WHERE et."ExamID" = %s AND et."ClassID" = %s AND et."SchoolID" = %s AND et."IsActive" = FALSE
                ORDER BY et."ExamDate", et."StartTime"
            """, [exam_id, class_id, school_id])
            
            timetable_entries = cursor.fetchall()
            logger.info(f"Found {len(timetable_entries)} timetable entries")
            
            if not timetable_entries:
                return JsonResponse({'status': 'FAILED', 'message': 'No timetable entries found to send. Please create schedule first.'}, status=200)
                
            # 4. Construct Timetable HTML/Text for placeholders
            # Start with a clean HTML table for the email body
            timetable_html = '<table style="width:100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif;">'
            timetable_html += '<thead style="background:#f1f5f9; color: #475569;">'
            timetable_html += '<tr>'
            timetable_html += '<th style="padding:12px; border:1px solid #e2e8f0; text-align:left; font-weight: 600;">Subject</th>'
            timetable_html += '<th style="padding:12px; border:1px solid #e2e8f0; text-align:left; font-weight: 600;">Date</th>'
            timetable_html += '<th style="padding:12px; border:1px solid #e2e8f0; text-align:left; font-weight: 600;">Time</th>'
            timetable_html += '</tr></thead><tbody>'
            
            timetable_text = ""
            for subject, date, start, end in timetable_entries:
                date_str = date.strftime('%d-%b-%Y') if date else 'TBA'
                time_str = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}" if start and end else 'TBA'
                
                timetable_html += '<tr>'
                timetable_html += f'<td style="padding:10px; border:1px solid #e2e8f0; color: #1e293b;">{subject}</td> '
                timetable_html += f'<td style="padding:10px; border:1px solid #e2e8f0; color: #1e293b;">{date_str}</td> '
                timetable_html += f'<td style="padding:10px; border:1px solid #e2e8f0; color: #1e293b;">{time_str}</td>'
                timetable_html += '</tr>'
                
                timetable_text += f"• {subject}: {date_str} ({time_str})\n"
                
            timetable_html += '</tbody></table>'
            
            # 5. Fetch Students with valid emails using correct PostgreSQL schema
            cursor.execute("""
                SELECT "Email", "FullName", "StudentCode"
                FROM "Student"
                WHERE "AdmissionClass"::integer = %s 
                  AND "SchoolID" = %s 
                  AND "IsDeleted" IS NOT TRUE 
                  AND "Email" IS NOT NULL 
                  AND "Email" != ''
            """, [class_id, school_id])
            
            students = cursor.fetchall()
            if not students:
                logger.warning(f"No students with emails found for class_id={class_id}, school_id={school_id}")
                return JsonResponse({'status': 'FAILED', 'message': 'No students found with valid email addresses in this class.'}, status=200)
                
            # 6. Fetch Global School Name for footer
            cursor.execute('SELECT "SchoolName" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
            school_name_row = cursor.fetchone()
            db_school_name = school_name_row[0] if school_name_row else "ShikshaWave School"

            # 7. Queue emails for all students
            count = 0
            for email, student_name, student_code in students:
                placeholders = {
                    'student_name': student_name,
                    'exam_name': exam_name,
                    'class_name': class_name,
                    'timetable_html': timetable_html,
                    'timetable_text': timetable_text,
                    'school_name': db_school_name
                }
                
                database_email_queue.add_email_task(
                    email_code='EXAM_TIMETABLE_NOTIFICATION',
                    to_email=email.strip(),
                    placeholders=placeholders,
                    school_id=school_id,
                    student_code=student_code,
                    priority=3  # Higher priority for exam schedules
                )
                count += 1
                
            return JsonResponse({
                'status': 'SUCCESS', 
                'message': f'Exam timetable successfully queued for {count} students.'
            })
            
    except Exception as e:
        logger.error(f"Error in exam_timetable_send_email: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'FAILED', 'message': f'Internal server error: {str(e)}'}, status=500)
