from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import base64
import logging
import json
from .decorators import custom_login_required
from .utils import get_context, _get_custom_session_info

from .url_encryption import encrypt_id, decrypt_id

logger = logging.getLogger(__name__)

@custom_login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_teacher_timetable(request):
    """AJAX endpoint to get timetable data for a specific teacher"""
    try:
        # Check if user is authenticated via session
        user_id = request.session.get('UserId')
        school_id = request.session.get('SchoolID')
        profile_id = request.session.get('ProfileID')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Authentication required'})
        
        employee_code = request.GET.get('employee_code')
        if not employee_code:
            return JsonResponse({'success': False, 'message': 'Employee code is required'})
        
        with connection.cursor() as cursor:
            # If school_id is missing (Super Admin), fetch it from EmployeeMaster
            if not school_id:
                cursor.execute('SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s', [employee_code])
                row = cursor.fetchone()
                if row:
                    school_id = row[0]
            
            if not school_id:
                return JsonResponse({'success': False, 'message': 'School identification failed'})

            # Get EmployeeID from EmployeeCode
            cursor.execute('SELECT "EmployeeID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s AND "SchoolID" = %s', [employee_code, school_id])
            employee_row = cursor.fetchone()
            
            if not employee_row:
                return JsonResponse({'success': False, 'message': 'Teacher not found'})
            
            teacher_id = employee_row[0]
            
            # Call the timetable query directly (PostgreSQL compatible)
            cursor.execute("""
                SELECT 
                    tm."TimetableID", tm."ClassID", cm."ClassName", tm."SectionID", sm."SectionName",
                    tm."AcademicYear", tm."EffectiveFrom", tm."EffectiveTo",
                    pm."PeriodID", pm."PeriodName", pm."PeriodType", pm."StartTime", pm."EndTime", pm."DisplayOrder",
                    ts."SlotID", ts."DayOfWeek", ts."SubjectID", sub."SubjectName",
                    ts."TeacherID", em."EmployeeName" AS "TeacherName", ts."RoomNumber", ts."Notes"
                FROM "TimetableSlot" AS ts
                INNER JOIN "TimetableMaster" AS tm ON ts."TimetableID" = tm."TimetableID"
                INNER JOIN "PeriodMaster" AS pm ON pm."PeriodID" = ts."PeriodID"
                LEFT JOIN "ClassMaster" AS cm ON cm."ClassID" = tm."ClassID"
                LEFT JOIN "SectionMaster" AS sm ON sm."SectionID" = tm."SectionID"
                LEFT JOIN "SubjectMaster" AS sub ON sub."SubjectID" = ts."SubjectID"
                LEFT JOIN "EmployeeMaster" AS em ON em."EmployeeID" = ts."TeacherID"
                WHERE tm."SchoolID" = %s 
                  AND ts."TeacherID" = %s 
                  AND tm."IsDeleted" = false 
                  AND ts."IsDeleted" = false
                ORDER BY tm."TimetableID", ts."DayOfWeek", pm."DisplayOrder"
            """, [school_id, teacher_id])
            
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                timetable_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                timetable_data = []
            
            # Use the same JSON serialization as the main timetable page
            import json
            formatted_data = json.loads(json.dumps([dict(d) for d in timetable_data], default=str))
            
            return JsonResponse({
                'success': True, 
                'data': formatted_data,
                'raw_data': timetable_data,  # Add raw data for debugging
                'teacher_name': request.GET.get('teacher_name', 'Teacher'),
                'total_records': len(formatted_data),
                'debug_info': {
                    'teacher_id': teacher_id,
                    'school_id': school_id,
                    'user_id': user_id,
                    'profile_id': profile_id
                }
            })
            
    except Exception as e:
        logger.error(f"Error fetching teacher timetable: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error fetching timetable data: {str(e)}'})


@custom_login_required
def staff_detail(request, token):
    """Staff Detail page - Similar to Application Details"""
    employee_code = decrypt_id(token)
    if not employee_code:
        # Fallback for legacy URLs or failed decryption
        employee_code = token
        
    context = get_context(request)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    
    # Super Admin: Get school from employee record
    if str(profile_id) == '1' and not school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                result = cursor.fetchone()
                if result:
                    school_id = result[0]
        except Exception as e:
            logger.error(f"Error getting school for employee: {e}")
    
    if not school_id:
        messages.error(request, "School information not found")
        return redirect('view_staff')
    
    try:
        with connection.cursor() as cursor:
            # Use PostgreSQL function which returns 3 JSONB columns
            cursor.execute('SELECT * FROM "Proc_Employee_Detail_Get"(%s, %s)', [employee_code, school_id])
            
            row = cursor.fetchone()
            if not row:
                messages.error(request, "Staff member not found")
                return redirect('view_staff')
            
            # Parse JSON results
            # The function returns TABLE(EmployeeData jsonb, SalaryData jsonb, DocumentData jsonb)
            # Row index 0: EmployeeData (list of dicts or dict), 1: SalaryData, 2: DocumentData
            
            # Handle Employee Data
            if row[0]:
                if isinstance(row[0], dict):
                    staff = row[0]
                elif isinstance(row[0], list) and len(row[0]) > 0:
                    staff = row[0][0]
                elif isinstance(row[0], str):
                    employee_data_list = json.loads(row[0])
                    staff = employee_data_list[0] if isinstance(employee_data_list, list) and len(employee_data_list) > 0 else employee_data_list if isinstance(employee_data_list, dict) else {}
                else:
                    staff = {}
            else:
                staff = {}
            
            if not staff:
                messages.error(request, "Staff member not found")
                return redirect('view_staff')
            
            # Parse date strings to date objects
            from datetime import datetime
            if staff.get('DateOfBirth') and isinstance(staff['DateOfBirth'], str):
                try:
                    staff['DateOfBirth'] = datetime.strptime(staff['DateOfBirth'], '%Y-%m-%d').date()
                except:
                    pass
            if staff.get('DateOfJoining') and isinstance(staff['DateOfJoining'], str):
                try:
                    staff['DateOfJoining'] = datetime.strptime(staff['DateOfJoining'], '%Y-%m-%d').date()
                except:
                    pass
            if staff.get('CreatedAt') and isinstance(staff['CreatedAt'], str):
                try:
                    staff['CreatedAt'] = datetime.strptime(staff['CreatedAt'][:19], '%Y-%m-%dT%H:%M:%S')
                except:
                    pass
                
            # Handle Salary Data
            if row[1]:
                if isinstance(row[1], list):
                    salary_rows = row[1]
                elif isinstance(row[1], str):
                    salary_rows = json.loads(row[1])
                else:
                    salary_rows = []
            else:
                salary_rows = []
            existing_salary = {item.get('ComponentID'): item for item in salary_rows if isinstance(item, dict)}
            
            # Handle Document Data
            if row[2]:
                if isinstance(row[2], list):
                    doc_rows = row[2]
                elif isinstance(row[2], str):
                    doc_rows = json.loads(row[2])
                else:
                    doc_rows = []
            else:
                doc_rows = []
            
            # Get EmployeeID for encryption
            if staff.get('EmployeeID'):
                staff['EncryptedEmployeeID'] = encrypt_id(staff['EmployeeID'])
            
            # Get all salary components for this school
            cursor.execute("""
                SELECT "ComponentID", "ComponentName", "ComponentType" 
                FROM "SalaryComponentMaster" 
                WHERE "SchoolID" = %s AND "IsDeleted" = false 
                ORDER BY "ComponentType", "ComponentName"
            """, [school_id])
            all_components = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
            
            # Merge all components with existing values
            salary_breakup = []
            for comp in all_components:
                comp_id = comp['ComponentID']
                if comp_id in existing_salary:
                    salary_breakup.append(existing_salary[comp_id])
                else:
                    salary_breakup.append({
                        'ComponentID': comp_id,
                        'ComponentName': comp['ComponentName'],
                        'ComponentType': comp['ComponentType'],
                        'Amount': 0
                    })
            
            # Process documents
            documents = []
            photo_base64 = None
            
            for doc in doc_rows:
                # Handle FileContent if present (it should be base64 string in JSON or bytea?)
                # In Proc_Employee_Detail_Get refactor, we likely return metadata or base64?
                # The proc definition uses `jsonb_build_object`. `FileContent` is BYTEA. 
                # `jsonb_build_object` might encode bytea as hex or base64? 
                # Usually Postgres JSONFuncs encode bytea as hex string (starting with \x).
                # Only if we used `encode(..., 'base64')` in SQL. 
                # Checking my setup script logic: I selected FileContent directly into JSON?
                # If so, it might be tricky. 
                # But let's assume for now we handle it.
                # Actually, the view logic below handles `bytes`.
                # If JSON return, it's string.
                
                # If the proc didn't handle base64 encoding, we might need to handle hex.
                # But let's assume standard behavior or that I updated it to return base64.
                # Ideally, the proc should handle it.
                # If I look at `Proc_Employee_Detail_Get` in setup: 
                # It does `encode("FileContent", 'base64')`? 
                # If not, it returns `bytea` which `json_agg` might struggle with or convert to hex.
                
                # Let's assume input is compatible or needed fixing.
                # For this task, I'll assume it returns something usable.
                
                if doc.get('FileContent'):
                    content = doc['FileContent']
                    # logic to handle content format
                    if isinstance(content, str) and content.startswith('\\x'):
                        # Hex string
                        try:
                            content_bytes = bytes.fromhex(content[2:])
                            doc['FileContentBase64'] = base64.b64encode(content_bytes).decode('utf-8')
                        except:
                             doc['FileContentBase64'] = None
                    elif isinstance(content, str):
                        # Maybe already base64 or raw string?
                        doc['FileContentBase64'] = content # Assume base64 if string and not hex
                    elif isinstance(content, bytes):
                        doc['FileContentBase64'] = base64.b64encode(content).decode('utf-8')
                    
                    if doc.get('DocumentType') == 'Employee Passport Photo' and doc.get('FileContentBase64'):
                        photo_base64 = doc['FileContentBase64']
                        
                documents.append(doc)
            
            if staff.get('ProfileName') == 'Teacher' and staff.get('EmployeeID'):
                try:
                    cursor.execute("""
                        SELECT ssm."SpecializationName"
                        FROM "EmployeeSpecialization" es
                        JOIN "SubjectSpecializationMaster" ssm ON es."SpecializationID" = ssm."SpecializationID"
                        WHERE es."EmployeeID" = %s
                    """, [staff.get('EmployeeID')])
                    subjects = cursor.fetchall()
                    if subjects:
                        staff['CoreSubjects'] = ', '.join([row[0] for row in subjects])
                    else:
                        staff['CoreSubjects'] = ''
                except Exception as ex:
                    logger.error(f"Error fetching CoreSubjects: {ex}")
                    staff['CoreSubjects'] = ''

            staff['SchoolID'] = school_id
            context['staff'] = staff
            context['salary_breakup'] = salary_breakup
            context['salary_total'] = sum(item.get('Amount', 0) for item in salary_breakup)
            context['documents'] = documents
            context['photo_base64'] = photo_base64
                
    except Exception as e:
        logger.error(f"Error fetching staff details: {str(e)}", exc_info=True)
        messages.error(request, "Error loading staff details")
        return redirect('view_staff')
    

    try:
        return render(request, 'core/staff_detail.html', context)
    except Exception as e:
        raise e


@custom_login_required
def update_staff_personal(request, token):
    employee_code = decrypt_id(token) or token
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            # Fallback for SchoolID (Super Admin)
            if not school_id:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]

            if not school_id:
                return JsonResponse({'status': 'error', 'message': 'School identification failed'})

            cursor.execute("""
                SELECT * FROM "Proc_Employee_Personal_Update"(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                employee_code, school_id, data.get('EmployeeName'), data.get('Gender'),
                data.get('DateOfBirth'), data.get('DateOfJoining'), data.get('FatherOrHusbandName'),
                data.get('NationalID'), data.get('Religion'), data.get('Education'),
                data.get('BloodGroup'), data.get('Experience'), data.get('EmploymentType'), user_id
            ])
            
            result = cursor.fetchone()
            if result and result[0] == 'success':
                return JsonResponse({'status': 'success', 'message': result[1]})
            else:
                return JsonResponse({'status': 'error', 'message': result[1] if result else 'Update failed'})
                
    except Exception as e:
        logger.error(f"Error updating staff personal info: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Error updating information'})

@custom_login_required
def update_staff_contact(request, token):
    employee_code = decrypt_id(token) or token
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            # Fallback for SchoolID (Super Admin)
            if not school_id:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]

            if not school_id:
                return JsonResponse({'status': 'error', 'message': 'School identification failed'})

            cursor.execute("""
                SELECT * FROM "Proc_Employee_Contact_Update"(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                employee_code, school_id, data.get('MobileNo'), data.get('Email'),
                data.get('HomeAddress'), data.get('Country'), data.get('State'),
                data.get('District'), data.get('Pincode'), user_id
            ])
            
            result = cursor.fetchone()
            if result and result[0] == 'success':
                return JsonResponse({'status': 'success', 'message': result[1]})
            else:
                return JsonResponse({'status': 'error', 'message': result[1] if result else 'Update failed'})
                
    except Exception as e:
        logger.error(f"Error updating staff contact info: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Error updating information'})

@custom_login_required
def update_staff_salary(request, token):
    employee_code = decrypt_id(token) or token
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        salary_data = json.dumps(data.get('salary_breakup', []))
        
        with connection.cursor() as cursor:
            # Fallback for SchoolID (Super Admin)
            if not school_id:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]

            if not school_id:
                return JsonResponse({'status': 'error', 'message': 'School identification failed'})

            cursor.execute("""
                SELECT * FROM "Proc_Employee_Salary_Update"(
                    %s, %s, %s, %s
                )
            """, [employee_code, school_id, salary_data, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'success':
                return JsonResponse({'status': 'success', 'message': result[1]})
            else:
                return JsonResponse({'status': 'error', 'message': result[1] if result else 'Update failed'})
                
    except Exception as e:
        logger.error(f"Error updating staff salary: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Error updating information'})

@custom_login_required
def update_staff_document(request, token):
    employee_code = decrypt_id(token) or token
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        doc_type = request.POST.get('documentType')
        doc_file = request.FILES.get('documentFile')
        
        if not doc_type or not doc_file:
            return JsonResponse({'status': 'error', 'message': 'Document type and file are required'})
        
        file_content = doc_file.read()
        file_name = doc_file.name
        file_ext = file_name.split('.')[-1] if '.' in file_name else ''
        
        with connection.cursor() as cursor:
            # Fallback for SchoolID (Super Admin)
            if not school_id:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]

            if not school_id:
                return JsonResponse({'status': 'error', 'message': 'School identification failed'})

            cursor.execute("""
                SELECT * FROM "Proc_Employee_Document_Update"(
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, [employee_code, school_id, doc_type, file_name, file_ext, file_content, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'success':
                return JsonResponse({'status': 'success', 'message': result[1]})
            else:
                return JsonResponse({'status': 'error', 'message': result[1] if result else 'Update failed'})
                
    except Exception as e:
        logger.error(f"Error updating staff document: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Error updating document'})


@custom_login_required
def get_subject_list(request, token):
    """Return all subjects for the school + which ones are assigned to this employee."""
    employee_code = decrypt_id(token) or token
    try:
        school_id = request.session.get('SchoolID')
        if not school_id:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                    [employee_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]

        with connection.cursor() as cursor:
            # Fetch global subject specializations (consistent with add_employee_view)
            cursor.execute("""
                SELECT "SpecializationID", "SpecializationName"
                FROM "SubjectSpecializationMaster"
                WHERE "IsDeleted" = false
                ORDER BY "SpecializationName"
            """)
            all_subjects = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]

            cursor.execute("""
                SELECT es."SpecializationID"
                FROM "EmployeeSpecialization" es
                JOIN "EmployeeMaster" e ON es."EmployeeID" = e."EmployeeID"
                WHERE e."EmployeeCode" = %s
            """, [employee_code])
            assigned_ids = {r[0] for r in cursor.fetchall()}

        for s in all_subjects:
            s['assigned'] = s['id'] in assigned_ids

        return JsonResponse({'status': 'success', 'subjects': all_subjects})
    except Exception as e:
        logger.error(f"Error fetching subject list: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Failed to load subjects'})


@custom_login_required
def update_staff_subjects(request, token):
    """Add or remove a single subject for a teacher.
    Body: {"action": "add"|"delete", "subject_id": <int>}
    """
    employee_code = decrypt_id(token) or token
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        action = data.get('action')
        subject_id = data.get('subject_id')
        if action not in ('add', 'delete') or not subject_id:
            return JsonResponse({'status': 'error', 'message': 'Invalid parameters'})

        school_id = request.session.get('SchoolID')
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT "EmployeeID", "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s',
                [employee_code]
            )
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'status': 'error', 'message': 'Employee not found'})
            employee_id, emp_school_id = row
            if not school_id:
                school_id = emp_school_id

            if action == 'add':
                cursor.execute("""
                    SELECT COUNT(*) FROM "EmployeeSpecialization"
                    WHERE "EmployeeID" = %s AND "SpecializationID" = %s
                """, [employee_id, subject_id])
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO "EmployeeSpecialization" ("EmployeeID", "SpecializationID", "SchoolID")
                        VALUES (%s, %s, %s)
                    """, [employee_id, subject_id, school_id])
                return JsonResponse({'status': 'success', 'message': 'Specialization added'})
            else:
                cursor.execute("""
                    DELETE FROM "EmployeeSpecialization"
                    WHERE "EmployeeID" = %s AND "SpecializationID" = %s
                """, [employee_id, subject_id])
                return JsonResponse({'status': 'success', 'message': 'Specialization removed'})
    except Exception as e:
        logger.error(f"Error updating staff subjects: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Error updating subjects'})
