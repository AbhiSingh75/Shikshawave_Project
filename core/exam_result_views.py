from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_POST
import json
import logging
from .decorators import custom_login_required

logger = logging.getLogger(__name__)

def custom_login_required(view_func):
    from functools import wraps
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('UserId'):
            from django.shortcuts import redirect
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wraps(view_func)(_wrapped)

@custom_login_required
def exam_result_entry(request):
    """Render exam result entry page"""
    from core.views import get_context
    context = get_context(request)
    
    # Ensure role flags are present (redundant now but safe for templates)
    profile_name = request.session.get('ProfileName', '')
    context['is_super_admin'] = context.get('is_super_admin') or ('Super Admin' in profile_name or profile_name == 'SuperAdmin')
    
    logger.info(f"Exam Result Entry: user={context.get('user_name')}, is_super={context.get('is_super_admin')}")
    
    return render(request, 'core/exam_result_entry.html', context)

@custom_login_required
def exam_result_students(request):
    """Get students list for selected exam and class"""
    try:
        from .url_encryption import decrypt_id_int
        exam_id = request.GET.get('exam_id')
        class_id = request.GET.get('class_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except:
                pass

        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
                
        if not all([exam_id, class_id, school_id]):
            return JsonResponse({'status': 'FAILED', 'message': 'Missing required parameters'})
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_GetStudentsForExamEntry(%s, %s, %s)', [int(school_id), int(exam_id), int(class_id)])
            
            students = []
            for row in cursor.fetchall():
                students.append({
                    'StudentID': row[0],
                    'StudentCode': row[1],
                    'StudentName': row[2]
                })
        
        return JsonResponse({
            'status': 'SUCCESS',
            'students': students
        })
        
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def exam_result_save(request):
    """Save exam results for students"""
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        results = data.get('results', [])
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        if not all([student_id, school_id, user_id]):
            return JsonResponse({'status': 'FAILED', 'message': 'Missing required parameters'})
        
        with connection.cursor() as cursor:
            for result in results:
                cursor.execute('SELECT Proc_ExamResult_set(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [
                    'SAVE',
                    result.get('exam_timetable_id'),
                    school_id,
                    student_id,
                    result.get('theory_marks'),
                    result.get('practical_marks'),
                    result.get('viva_marks'),
                    result.get('grade'),
                    result.get('status'),
                    result.get('remarks'),
                    user_id,
                    user_id
                ])
        
        return JsonResponse({'status': 'SUCCESS', 'message': 'Results saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def api_exams(request):
    """Get all exams for dropdown"""
    try:
        from .url_encryption import decrypt_id_int
        school_id = request.session.get('SchoolID')
        profile_name = request.session.get('ProfileName', '')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        is_super = 'Super Admin' in profile_name or profile_name == 'SuperAdmin'
        
        if is_super and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except Exception as de:
                logger.error(f"Decryption failed in api_exams: {de}")
                pass
        
        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
                
        logger.info(f"api_exams: profile={profile_name}, mapped_school_id={school_id}, req_school_id={req_school_id}")
        
        with connection.cursor() as cursor:
            # Match parameter passing style of working Exam Management exactly
            # But use empty strings instead of NULL for Postgres compatibility with string filters
            cursor.execute('SELECT * FROM Proc_ExamMaster_View(%s, 1, 100, %s, %s, %s, NULL, %s, %s)', 
                           [school_id, 'StartDate', 'DESC', '', '', ''])
            cols = [c.name for c in cursor.description]
            exams = [dict(zip(cols, row)) for row in cursor.fetchall()]
            
            logger.info(f"api_exams: found {len(exams)} exams for school {school_id}")
            
            # Reformat to match what API expects
            for e in exams:
                e['AcademicYear'] = e.get('AcademicYear', '')
                sd = e.get('StartDate')
                if sd:
                    e['StartDate'] = sd.strftime('%d %b, %Y') if hasattr(sd, 'strftime') else str(sd)
                else:
                    e['StartDate'] = ''
                    
                ed = e.get('EndDate')
                if ed:
                    e['EndDate'] = ed.strftime('%d %b, %Y') if hasattr(ed, 'strftime') else str(ed)
                else:
                    e['EndDate'] = ''
        
        return JsonResponse(exams, safe=False)
    except Exception as e:
        logger.error(f"Error fetching exams: {e}")
        return JsonResponse([], safe=False)

@custom_login_required
def api_subjects_by_class(request):
    """Get subjects for a class"""
    try:
        from .url_encryption import decrypt_id_int
        class_id = request.GET.get('class_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except:
                pass

        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "SubjectID", "SubjectName"
                FROM "SubjectMaster"
                WHERE "ClassId" = %s AND "SchoolID" = %s AND COALESCE("IsDeleted", FALSE) IS FALSE
                ORDER BY "SubjectName"
            """, [class_id, school_id])
            
            subjects = [{'SubjectID': row[0], 'SubjectName': row[1]} for row in cursor.fetchall()]
        
        return JsonResponse(subjects, safe=False)
    except Exception as e:
        logger.error(f"Error fetching subjects: {e}")
        return JsonResponse([], safe=False)

@custom_login_required
def api_classes_by_exam(request):
    """Get classes that have exam schedule for a specific exam"""
    try:
        from .url_encryption import decrypt_id_int
        exam_id = request.GET.get('exam_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        logger.info(f"api_classes_by_exam: incoming req_school_id={req_school_id}")
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
                logger.info(f"api_classes_by_exam: decrypted school_id={school_id}")
            except Exception as e:
                logger.error(f"Decryption failed for school_id: {e}")
        
        # Ensure school_id is an integer if possible
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
                
        logger.info(f"api_classes_by_exam EXEC: exam_id={exam_id}, school_id={school_id}")
        
        if not exam_id or not school_id:
            logger.warning(f"api_classes_by_exam: Missing params! exam_id={exam_id}, school_id={school_id}")
            return JsonResponse([], safe=False)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT C."ClassID", C."ClassName"
                FROM "ClassMaster" AS C
                INNER JOIN "ExamTimeTable" AS ET ON ET."ClassID" = C."ClassID"
                WHERE ET."IsActive" IS FALSE AND C."IsActive" IS TRUE 
                  AND ET."SchoolID" = %s AND ET."ExamID" = %s
                ORDER BY C."ClassName"
            """, [school_id, exam_id])
            
            classes = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        return JsonResponse(classes, safe=False)
    except Exception as e:
        logger.error(f"Error fetching classes by exam: {e}")
        return JsonResponse([], safe=False)

@custom_login_required
def get_student_exam_subjects(request):
    """Get exam subjects with marks configuration for a student"""
    try:
        from .url_encryption import decrypt_id_int
        exam_id = request.GET.get('exam_id')
        class_id = request.GET.get('class_id')
        student_id = request.GET.get('student_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except:
                pass

        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
                
        if not all([exam_id, class_id, student_id, school_id]):
            return JsonResponse({'status': 'FAILED', 'message': 'Missing required parameters'})
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_GetExamSubjectMarksForEntry(%s, %s, %s, %s)', 
                           [int(school_id), int(exam_id), int(class_id), int(student_id)])
            
            subjects = []
            for row in cursor.fetchall():
                subjects.append({
                    'ExamID': row[0],
                    'ExamTimeTableID': row[1],
                    'SubjectID': row[2],
                    'SubjectName': row[3],
                    'MaxTheoryMarks': row[4],
                    'MinTheoryMarks': row[5],
                    'MaxPracticalMarks': row[6],
                    'MinPracticalMarks': row[7],
                    'MaxVivaMarks': row[8],
                    'MinVivaMarks': row[9],
                    'TotalMaxMarks': row[10],
                    'ExamResultID': row[11],
                    'TheoryMarksObtained': row[12],
                    'PracticalMarksObtained': row[13],
                    'VivaMarksObtained': row[14],
                    'TotalMarksObtained': row[15],
                    'Grade': row[16],
                    'ResultStatus': row[17],
                    'Remarks': row[18],
                    'IsPublished': row[19]
                })
        
        return JsonResponse({
            'status': 'SUCCESS',
            'subjects': subjects
        })
        
    except Exception as e:
        logger.error(f"Error loading student exam subjects: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_student_result_list(request):
    """Get list of students with aggregate exam results"""
    try:
        from .url_encryption import decrypt_id_int
        exam_id = request.GET.get('exam_id')
        class_id = request.GET.get('class_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except:
                pass

        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass

        search_name = request.GET.get('search_name', '').strip() or None
        
        if not all([exam_id, class_id, school_id]):
            return JsonResponse({'status': 'FAILED', 'message': 'Missing required parameters'})
        
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM Proc_GetStudentExamResultList(%s, %s, %s, %s)', 
                           [int(school_id), int(exam_id), int(class_id), search_name])
            
            students = []
            rows = cursor.fetchall()
            for row in rows:
                students.append({
                    'StudentID': row[0],
                    'StudentCode': row[1],
                    'StudentName': row[2],
                    'TotalObtainedMarks': float(row[3]) if row[3] else 0,
                    'TotalMaxMarks': float(row[4]) if row[4] else 0,
                    'Percentage': float(row[5]) if row[5] else 0,
                    'ResultStatus': row[6],
                    'PublishStatus': row[7]
                })
            # Calculate summary stats
            total_students = len(students)
            passed = sum(1 for s in students if s.get('ResultStatus') == 'Pass')
            failed = total_students - passed
            
            return JsonResponse({
                'status': 'SUCCESS', 
                'students': students,
                'stats': {
                    'total': total_students,
                    'passed': passed,
                    'failed': failed
                }
            })
    except Exception as e:
        logger.error(f"Error fetching student result list: {e}", exc_info=True)
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_student_result(request):
    """Get detailed student exam result"""
    try:
        from .url_encryption import decrypt_id_int
        exam_id = request.GET.get('exam_id')
        class_id = request.GET.get('class_id')
        student_id = request.GET.get('student_id')
        profile_name = request.session.get('ProfileName', '')
        school_id = request.session.get('SchoolID')
        
        # Handle super admin school selection
        req_school_id = request.GET.get('school_id')
        if ('Super Admin' in profile_name or profile_name == 'SuperAdmin') and req_school_id:
            try:
                school_id = decrypt_id_int(req_school_id)
            except:
                pass

        # Ensure school_id is an integer
        if school_id and not isinstance(school_id, int):
            try:
                school_id = int(school_id)
            except:
                pass
                
        if not all([exam_id, class_id, student_id, school_id]):
            return JsonResponse({'status': 'FAILED', 'message': 'Missing required parameters'})
        
        with connection.cursor() as cursor:
            # Table 1: Basic Info
            cursor.execute('SELECT * FROM Proc_GetStudentExamResult_Info(%s, %s, %s, %s)', 
                           [int(school_id), int(exam_id), int(class_id), int(student_id)])
            basic_info = cursor.fetchall()
            if basic_info:
                b = basic_info[0]
                info = {
                    'StudentCode': b[0],
                    'StudentName': b[1],
                    'ExamName': b[2],
                    'ExamType': b[3],
                    'ClassName': b[4],
                    'SectionName': b[5],
                    'StartDate': b[6].strftime('%d %b, %Y') if b[6] else '',
                    'EndDate': b[7].strftime('%d %b, %Y') if b[7] else '',
                    'PublishedDate': b[8].strftime('%d %b, %Y') if b[8] else '',
                    'Ranks': b[9]
                }
            else:
                info = {}
            
            # Table 2: Subject Results
            cursor.execute('SELECT * FROM Proc_GetStudentExamResult_Subjects(%s, %s, %s, %s)', 
                           [int(school_id), int(exam_id), int(class_id), int(student_id)])
            subjects = []
            for row in cursor.fetchall():
                subjects.append({
                    'SubjectName': row[2],
                    'MaxTheoryMarks': float(row[10]) if row[10] else None,
                    'MaxPracticalMarks': float(row[11]) if row[11] else None,
                    'MaxVivaMarks': float(row[12]) if row[12] else None,
                    'TotalMaxMarks': float(row[13]) if row[13] else 0,
                    'TheoryMarksObtained': float(row[14]) if row[14] else 0,
                    'PracticalMarksObtained': float(row[15]) if row[15] else 0,
                    'VivaMarksObtained': float(row[16]) if row[16] else 0,
                    'TotalMarksObtained': float(row[17]) if row[17] else 0,
                    'Grade': row[18],
                    'ResultStatus': row[19],
                    'Remarks': row[20]
                })
        
        return JsonResponse({'status': 'SUCCESS', 'info': info, 'subjects': subjects})
    except Exception as e:
        logger.error(f"Error fetching student result: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def exam_result_view(request):
    """Render exam result view page"""
    from core.views import get_context
    context = get_context(request)
    profile_name = request.session.get('ProfileName', '')
    context['is_admin'] = profile_name == 'School Admin'
    context['is_teacher'] = profile_name == 'Teacher'
    context['is_student'] = profile_name == 'Student'
    context['is_super_admin'] = profile_name == 'Super Admin'
    return render(request, 'core/exam_result_view.html', context)

@custom_login_required
def exam_result_print(request):
    """Print student result card"""
    from core.views import get_context
    from datetime import datetime
    
    exam_id = request.GET.get('exam_id')
    class_id = request.GET.get('class_id')
    student_id = request.GET.get('student_id')
    school_id = request.session.get('SchoolID') or request.session.get('school_id')
    profile_name = request.session.get('ProfileName', '')
    
    # Super Admin can specify school_id
    from .url_encryption import decrypt_id_int
    req_school_id = request.GET.get('school_id')
    
    # Broaden check for Super Admin
    is_super = 'Super Admin' in profile_name or profile_name == 'SuperAdmin'
    
    if is_super and req_school_id:
        try:
            school_id = decrypt_id_int(req_school_id)
        except Exception as de:
            logger.error(f"Decryption failed in exam_result_print: {de}")
            pass

    # Ensure school_id is an integer
    if school_id and not isinstance(school_id, int):
        try:
            school_id = int(school_id)
        except:
            pass
    
    logger.info(f"api_exams: profile={profile_name}, mapped_school_id={school_id}, req_school_id={req_school_id}")
    
    # Get selected template from preferences
    template_file = 'core/exam_result_print.html'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "TemplateType", "TemplateFile" FROM "Proc_Template_Preference_Get"(%s)', [school_id])
            for row in cursor.fetchall():
                if row[0] == 'ExamResult' and row[1]:
                    template_file = row[1]
                    break
    except Exception as e:
        logger.error(f"Error fetching template preference: {e}")
    
    with connection.cursor() as cursor:
        # Table 1: Basic Info
        cursor.execute('SELECT * FROM "Proc_GetStudentExamResult_Info"(%s, %s, %s, %s)', 
                       [school_id, exam_id, class_id, student_id])
        basic_info = cursor.fetchall()
        if basic_info:
            info = basic_info[0]
            student_code = info[0]
            student_name = info[1]
            exam_name = info[2]
            exam_type = info[3]
            class_name = info[4]
            section_name = info[5]
            start_date = info[6].strftime('%d %b, %Y') if info[6] else ''
            end_date = info[7].strftime('%d %b, %Y') if info[7] else ''
            published_date = info[8].strftime('%d %b, %Y') if info[8] else ''
            rank = info[9]
        else:
            student_code = student_name = exam_name = exam_type = class_name = section_name = start_date = end_date = published_date = rank = ''
        
        # Table 2: Subject Results
        cursor.execute('SELECT * FROM "Proc_GetStudentExamResult_Subjects"(%s, %s, %s, %s)', 
                       [school_id, exam_id, class_id, student_id])
        subjects = []
        total_max = 0
        total_obtained = 0
        
        for row in cursor.fetchall():
            total_max += float(row[13]) if row[13] else 0
            total_obtained += float(row[17]) if row[17] else 0
            subjects.append({
                'SubjectName': row[2],
                'MaxTheoryMarks': float(row[10]) if row[10] else None,
                'MaxPracticalMarks': float(row[11]) if row[11] else None,
                'MaxVivaMarks': float(row[12]) if row[12] else None,
                'TotalMaxMarks': float(row[13]) if row[13] else 0,
                'TheoryMarksObtained': float(row[14]) if row[14] else 0,
                'PracticalMarksObtained': float(row[15]) if row[15] else 0,
                'VivaMarksObtained': float(row[16]) if row[16] else 0,
                'TotalMarksObtained': float(row[17]) if row[17] else 0,
                'Grade': row[18],
                'ResultStatus': row[19]
            })
    
    percentage = round((total_obtained / total_max) * 100, 2) if total_max > 0 else 0
    status = 'Pass' if percentage >= 33 else 'Fail'
    color = '#10b981' if percentage >= 75 else '#f59e0b' if percentage >= 60 else '#f97316' if percentage >= 40 else '#ef4444'
    
    context = get_context(request)
    context.update({
        'StudentCode': student_code,
        'StudentName': student_name,
        'ExamName': exam_name,
        'ExamType': exam_type,
        'ClassName': class_name,
        'SectionName': section_name,
        'StartDate': start_date,
        'EndDate': end_date,
        'PublishedDate': published_date,
        'Ranks': rank,
        'subjects': subjects,
        'total_max': total_max,
        'total_obtained': total_obtained,
        'percentage': percentage,
        'status': status,
        'color': color,
        'today': datetime.now().strftime('%d %b, %Y')
    })
    
    return render(request, template_file, context)
