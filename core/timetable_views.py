from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.http import require_http_methods
from core.decorators import login_required
from core.views import get_context
import json
from core.url_encryption import decrypt_id_int, encrypt_id

def _get_timetable_school_id(request, data=None):
    """Helper to get school_id with Super Admin fallback."""
    sid = request.GET.get('school_id')
    if not sid and data:
        sid = data.get('school_id')
    
    # Priority for Super Admin: manually selected school
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    if profile_id == 1:
        selected_sid = request.session.get('timetable_selected_school_id')
        if selected_sid:
            return selected_sid
        else:
            return None # Force Super Admin to select a school

    if not sid:
        sid = request.session.get('SchoolID')
    
    return sid


@login_required
def timetable_management(request):
    """Main timetable management page"""
    from .utils import get_school_dropdown
    context = get_context(request)
    tab = request.GET.get('tab', 'periods')

    # Add schools for Super Admin
    if context.get('profile_id') == 1:
        context['schools'] = get_school_dropdown()
        # Read selected school from session (not URL) so school_id stays out of URL
        context['selected_school_id'] = request.session.get('timetable_selected_school_id', '')

    if tab == 'view':
        return render(request, 'core/timetable_list.html', context)
    elif tab == 'templates':
        return render(request, 'core/timetable_templates.html', context)
    else:
        return render(request, 'core/timetable_management.html', context)


@login_required
@require_http_methods(["POST"])
def set_school_session(request):
    """Save the super-admin school selection to session so it never appears in the URL."""
    try:
        data = json.loads(request.body)
        school_id = data.get('school_id', '')
        if school_id:
            request.session['timetable_selected_school_id'] = int(school_id)
        else:
            request.session.pop('timetable_selected_school_id', None)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["GET"])
def get_periods(request):
    """Get all periods for a school"""
    school_id = _get_timetable_school_id(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT "PeriodID", "PeriodName", "PeriodType", "StartTime", "EndTime", "DisplayOrder", "IsActive" 
            FROM "PeriodMaster" 
            WHERE "SchoolID"=%s AND COALESCE("IsDeleted", false)=false 
            ORDER BY "DisplayOrder", "StartTime"
        """, [school_id])
        
        columns = [col[0] for col in cursor.description]
        periods = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return JsonResponse({'success': True, 'periods': periods})

@login_required
@require_http_methods(["POST"])
def save_period(request):
    """Save or update a period"""
    data = json.loads(request.body)
    school_id = _get_timetable_school_id(request, data)
    user_id = request.session.get('UserId')
    
    action = 'UPDATE' if data.get('period_id') else 'INSERT'
    
    with connection.cursor() as cursor:
        if action == 'INSERT':
            cursor.execute("""
                INSERT INTO "PeriodMaster" ("SchoolID", "PeriodName", "PeriodType", "StartTime", "EndTime", "DisplayOrder", "IsActive", "CreatedBy", "CreatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING "PeriodID", 'Period created'
            """, [school_id, data.get('period_name'), data.get('period_type', 'Class'), data.get('start_time'), data.get('end_time'), data.get('display_order'), data.get('is_active', True), user_id])
        else:
            cursor.execute("""
                UPDATE "PeriodMaster" SET "PeriodName"=%s, "PeriodType"=%s, "StartTime"=%s, 
                    "EndTime"=%s, "DisplayOrder"=%s, "IsActive"=%s, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP
                WHERE "PeriodID"=%s AND "SchoolID"=%s AND COALESCE("IsDeleted", false)=false
                RETURNING "PeriodID", 'Period updated'
            """, [data.get('period_name'), data.get('period_type', 'Class'), data.get('start_time'), data.get('end_time'), data.get('display_order'), data.get('is_active', True), user_id, data.get('period_id'), school_id])
        
        result = cursor.fetchone()
    
    return JsonResponse({'success': True, 'message': result[1] if result else 'Period saved'})

@login_required
@require_http_methods(["POST"])
def delete_period(request):
    """Delete a period"""
    data = json.loads(request.body)
    school_id = _get_timetable_school_id(request, data)
    user_id = request.session.get('UserId')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE "PeriodMaster" SET "IsDeleted"=true, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP
            WHERE "PeriodID"=%s AND "SchoolID"=%s
        """, [user_id, data.get('period_id'), data.get('school_id') or school_id])
    
    return JsonResponse({'success': True, 'message': 'Period deleted'})

@login_required
@require_http_methods(["GET"])
def get_timetables(request):
    """Get all timetables for a school"""
    school_id = _get_timetable_school_id(request)
    user_id = request.session.get('UserId')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.*, cm."ClassName", sm."SectionName" FROM "TimetableMaster" t
            INNER JOIN "ClassMaster" cm ON t."ClassID" = cm."ClassID"
            LEFT JOIN "SectionMaster" sm ON t."SectionID" = sm."SectionID"
            WHERE t."SchoolID"=%s AND COALESCE(t."IsDeleted", false)=false 
            ORDER BY t."ClassID" ASC, t."TimetableID" DESC
        """, [school_id])
        
        columns = [col[0] for col in cursor.description]
        timetables = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['EncryptedID'] = encrypt_id(d['TimetableID'])
            timetables.append(d)
    
    return JsonResponse({'success': True, 'timetables': timetables})

@login_required
@require_http_methods(["POST"])
def create_timetable(request):
    """Create a new timetable"""
    data = json.loads(request.body)
    school_id = data.get('school_id') or request.session.get('SchoolID')
    user_id = request.session.get('UserId')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM "TimetableMaster" WHERE "SchoolID"=%s AND "ClassID"=%s 
            AND ("SectionID" = %s OR ("SectionID" IS NULL AND %s IS NULL)) AND "IsActive"=true AND COALESCE("IsDeleted", false)=false
        """, [school_id, data.get('class_id'), data.get('section_id'), data.get('section_id')])
        
        if cursor.fetchone():
            return JsonResponse({'success': False, 'message': 'Active timetable exists'})

        cursor.execute("""
            INSERT INTO "TimetableMaster" ("SchoolID", "ClassID", "SectionID", "AcademicYear", "EffectiveFrom", "EffectiveTo", "IsActive", "CreatedBy", "CreatedAt")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING "TimetableID", 'Timetable created'
        """, [school_id, data.get('class_id'), data.get('section_id'), data.get('academic_year'), data.get('effective_from'), data.get('effective_to'), data.get('is_active', True), user_id])
        
        result = cursor.fetchone()
    
    return JsonResponse({
        'success': result[0] > 0,
        'timetable_id': result[0],
        'encrypted_timetable_id': encrypt_id(result[0]),
        'message': result[1]
    })

@login_required
@require_http_methods(["GET"])
def view_timetable(request, encrypted_timetable_id):
    """View a specific timetable"""
    timetable_id = decrypt_id_int(encrypted_timetable_id)
    if not timetable_id:
        return render(request, 'error.html', {'message': 'Invalid Timetable ID'})
        
    school_id = _get_timetable_school_id(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t."TimetableID", t."AcademicYear", t."EffectiveFrom", t."EffectiveTo", cm."ClassName", sm."SectionName", t."ClassID"
            FROM "TimetableMaster" t 
            INNER JOIN "ClassMaster" cm ON t."ClassID" = cm."ClassID"
            LEFT JOIN "SectionMaster" sm ON t."SectionID" = sm."SectionID" 
            WHERE t."TimetableID"=%s AND t."SchoolID"=%s AND COALESCE(t."IsDeleted", false)=false
        """, [timetable_id, school_id])
        
        columns = [col[0] for col in cursor.description]
        timetable_row = cursor.fetchone()
        if not timetable_row:
            return render(request, 'error.html', {'message': 'Timetable not found'})
        
        timetable = dict(zip(columns, timetable_row))
        timetable['EncryptedID'] = encrypted_timetable_id
        class_id = timetable.get('ClassID')
        
        # Get periods
        cursor.execute("""
            SELECT * FROM "PeriodMaster" 
            WHERE "SchoolID"=%s AND COALESCE("IsDeleted", false)=false 
            ORDER BY "DisplayOrder", "StartTime"
        """, [school_id])
        columns = [col[0] for col in cursor.description]
        periods = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get slots
        cursor.execute("""
            SELECT ts."SlotID", ts."DayOfWeek", ts."PeriodID", ts."RoomNumber", ts."Notes",
                p."PeriodName", p."StartTime", p."EndTime", p."PeriodType",
                sm."SubjectID", sm."SubjectName", sm."SubjectCode", EM."EmployeeID" AS "TeacherID", EM."EmployeeName" AS "TeacherName"
            FROM "TimetableSlot" ts 
            INNER JOIN "PeriodMaster" p ON ts."PeriodID" = p."PeriodID"
            LEFT JOIN "SubjectMaster" sm ON ts."SubjectID" = sm."SubjectID" 
            LEFT JOIN "EmployeeMaster" EM ON ts."TeacherID" = EM."EmployeeID"
            WHERE ts."TimetableID"=%s AND COALESCE(ts."IsDeleted", false)=false 
            ORDER BY ts."DayOfWeek", p."DisplayOrder"
        """, [timetable_id])
        columns = [col[0] for col in cursor.description]
        slots = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get all employees as "Teachers" for the school
        cursor.execute("""
            SELECT EM."EmployeeID" AS "TeacherID", EM."EmployeeName" AS "TeacherName"
            FROM "EmployeeMaster" AS EM
            WHERE EM."SchoolID" = %s AND COALESCE(EM."IsDeleted", false) = false
            ORDER BY EM."EmployeeName"
        """, [school_id])
        teachers = [{'TeacherID': row[0], 'TeacherName': row[1]} for row in cursor.fetchall()]
        
        # Get subjects for this class
        subjects = []
        if class_id:
            cursor.execute("""
                SELECT "SubjectID", "SubjectName" FROM "SubjectMaster" 
                WHERE "SchoolID"=%s AND "ClassId"=%s AND COALESCE("IsDeleted", false)=false ORDER BY "SubjectName"
            """, [school_id, class_id])
            subjects = [{'SubjectID': row[0], 'SubjectName': row[1]} for row in cursor.fetchall()]
        
        # Get school details
        school_logo = ''
        school_name = ''
        school_address = ''
        cursor.execute('SELECT "SchoolLogo", "SchoolName", "Address", "District", "State", "Pincode" FROM "SchoolMaster" WHERE "SchoolID"=%s', [school_id])
        school_row = cursor.fetchone()
        if school_row:
            if school_row[0]:
                import base64
                school_logo = f"data:image/jpeg;base64,{base64.b64encode(school_row[0]).decode('utf-8')}"
            school_name = school_row[1]
            
            # Combine address parts
            parts = [str(p) for p in school_row[2:6] if p]
            school_address = ", ".join(parts)
    
    context = get_context(request)
    context.update({
        'timetable': timetable,
        'periods': periods,
        'slots': slots,
        'teachers': json.dumps(teachers),
        'subjects': json.dumps(subjects),
        'SchoolName': school_name,
        'SchoolAddress': school_address,
        'SchoolLogo': school_logo,
        'encrypted_timetable_id': encrypted_timetable_id,
    })
    
    return render(request, 'core/timetable_view.html', context)

@login_required
@require_http_methods(["POST"])
def save_timetable_slot(request):
    """Save a timetable slot"""
    data = json.loads(request.body)
    user_id = request.session.get('UserId')
    school_id = _get_timetable_school_id(request, data)
    
    timetable_id_raw = data.get('timetable_id')
    timetable_id = decrypt_id_int(timetable_id_raw) or (int(timetable_id_raw) if str(timetable_id_raw).isdigit() else None)
    
    # Validate timetable belongs to school
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM "TimetableMaster" 
            WHERE "TimetableID"=%s AND "SchoolID"=%s AND COALESCE("IsDeleted", false)=false
        """, [timetable_id, school_id])
        if not cursor.fetchone():
            return JsonResponse({'success': False, 'message': 'Invalid timetable'})
        
        cursor.execute('SELECT 1 FROM "TimetableSlot" WHERE "SlotID"=%s AND COALESCE("IsDeleted", false)=false', [data.get('slot_id')])
        if cursor.fetchone():
            cursor.execute("""
                UPDATE "TimetableSlot" SET "SubjectID"=%s, "TeacherID"=%s, "RoomNumber"=%s,
                    "Notes"=%s, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP 
                WHERE "SlotID"=%s
                RETURNING "SlotID", 'Slot updated'
            """, [data.get('subject_id'), data.get('teacher_id'), data.get('room_number'), data.get('notes'), user_id, data.get('slot_id')])
        else:
            cursor.execute("""
                INSERT INTO "TimetableSlot" ("TimetableID", "DayOfWeek", "PeriodID", "SubjectID", "TeacherID", "RoomNumber", "Notes", "CreatedBy", "CreatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING "SlotID", 'Slot created'
            """, [timetable_id, data.get('day_of_week'), data.get('period_id'), data.get('subject_id'), data.get('teacher_id'), data.get('room_number'), data.get('notes'), user_id])
        
        result = cursor.fetchone()
        slot_id = result[0]
        message = result[1]
    
    return JsonResponse({
        'success': slot_id > 0,
        'message': message
    })

@login_required
@require_http_methods(["POST"])
def delete_timetable_slot(request):
    """Delete a timetable slot"""
    data = json.loads(request.body)
    user_id = request.session.get('UserId')
    school_id = _get_timetable_school_id(request, data)
    
    timetable_id_raw = data.get('timetable_id')
    timetable_id = decrypt_id_int(timetable_id_raw) or (int(timetable_id_raw) if str(timetable_id_raw).isdigit() else None)
    
    with connection.cursor() as cursor:
        # Validate slot belongs to school
        cursor.execute("""
            SELECT 1 FROM "TimetableSlot" ts
            INNER JOIN "TimetableMaster" tm ON ts."TimetableID" = tm."TimetableID"
            WHERE ts."SlotID" = %s AND tm."SchoolID" = %s
        """, [data.get('slot_id'), school_id])
        if not cursor.fetchone():
            return JsonResponse({'success': False, 'message': 'Invalid slot'})
        
        cursor.execute("""
            UPDATE "TimetableSlot" SET "IsDeleted"=true, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP 
            WHERE "SlotID"=%s
        """, [user_id, data.get('slot_id')])
        
        result = cursor.fetchone()
    
    return JsonResponse({'success': True, 'message': result[0] if result else 'Slot deleted'})

@login_required
@require_http_methods(["POST"])
def delete_timetable(request):
    """Delete a timetable"""
    data = json.loads(request.body)
    school_id = _get_timetable_school_id(request, data)
    user_id = request.session.get('UserId')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE "TimetableMaster" SET "IsDeleted"=true, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP
            WHERE "TimetableID"=%s AND "SchoolID"=%s
        """, [user_id, data.get('timetable_id'), data.get('school_id') or school_id])
        
        cursor.execute("""
            UPDATE "TimetableSlot" SET "IsDeleted"=true, "UpdatedBy"=%s, "UpdatedAt"=CURRENT_TIMESTAMP 
            WHERE "TimetableID"=%s
        """, [user_id, data.get('timetable_id')])
    
    return JsonResponse({'success': True, 'message': 'Timetable deleted'})

@login_required
@require_http_methods(["GET"])
def get_teachers(request):
    """Get all teachers for a school"""
    school_id = _get_timetable_school_id(request)
    
    with connection.cursor() as cursor:
        # Get all employees as "Teachers" for the school
        cursor.execute("""
            SELECT EM."EmployeeID" AS "TeacherID", EM."EmployeeCode" AS "TeacherCode", EM."EmployeeName" AS "TeacherName"
            FROM "EmployeeMaster" AS EM
            WHERE EM."SchoolID" = %s AND COALESCE(EM."IsDeleted", false) = false
            ORDER BY EM."EmployeeName"
        """, [school_id])
        
        columns = [col[0] for col in cursor.description]
        teachers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return JsonResponse({'success': True, 'teachers': teachers})

@login_required
@require_http_methods(["GET"])
def print_timetable(request, encrypted_timetable_id):
    """Print timetable using saved template"""
    timetable_id = decrypt_id_int(encrypted_timetable_id)
    if not timetable_id:
        return HttpResponse("Invalid Timetable ID", status=400)
        
    from django.template.loader import render_to_string
    import base64
    
    # Robust SchoolID resolution
    school_id = _get_timetable_school_id(request)
    
    # Get saved template preference
    template_path = 'core/document_templates/class_timetable/timetable_template1.html'
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT "TemplateFile" FROM "TemplateSettings" 
            WHERE "SchoolID"=%s AND "TemplateType"='ClassTimetable' AND "IsActive" = TRUE AND "IsDeleted" = FALSE
        """, [school_id])
        row = cursor.fetchone()
        if row and row[0]:
            template_path = row[0]
    
        # Get timetable data
        cursor.execute("""
            SELECT t."TimetableID", t."AcademicYear", t."EffectiveFrom", t."EffectiveTo", cm."ClassName", sm."SectionName", t."ClassID"
            FROM "TimetableMaster" t 
            INNER JOIN "ClassMaster" cm ON t."ClassID" = cm."ClassID"
            LEFT JOIN "SectionMaster" sm ON t."SectionID" = sm."SectionID" 
            WHERE t."TimetableID"=%s AND t."SchoolID"=%s AND COALESCE(t."IsDeleted", false)=false
        """, [timetable_id, school_id])
        columns1 = [col[0] for col in cursor.description]
        timetable_row = cursor.fetchone()
        if not timetable_row:
            return HttpResponse("Timetable not found", status=404)
        timetable = dict(zip(columns1, timetable_row))
        
        # Get periods
        cursor.execute("""
            SELECT * FROM "PeriodMaster" 
            WHERE "SchoolID"=%s AND COALESCE("IsDeleted", false)=false 
            ORDER BY "DisplayOrder", "StartTime"
        """, [school_id])
        columns2 = [col[0] for col in cursor.description]
        periods = [dict(zip(columns2, row)) for row in cursor.fetchall()]
        
        # Get slots - JOIN with EmployeeMaster for Teachers
        cursor.execute("""
            SELECT ts."SlotID", ts."DayOfWeek", ts."PeriodID", ts."RoomNumber", ts."Notes",
                p."PeriodName", p."StartTime", p."EndTime", p."PeriodType",
                sm."SubjectID", sm."SubjectName", sm."SubjectCode", EM."EmployeeID" AS "TeacherID", EM."EmployeeName" AS "TeacherName"
            FROM "TimetableSlot" ts 
            INNER JOIN "PeriodMaster" p ON ts."PeriodID" = p."PeriodID"
            LEFT JOIN "SubjectMaster" sm ON ts."SubjectID" = sm."SubjectID" 
            LEFT JOIN "EmployeeMaster" EM ON ts."TeacherID" = EM."EmployeeID"
            WHERE ts."TimetableID"=%s AND COALESCE(ts."IsDeleted", false)=false 
            ORDER BY ts."DayOfWeek", p."DisplayOrder"
        """, [timetable_id])
        columns3 = [col[0] for col in cursor.description]
        slots = [dict(zip(columns3, row)) for row in cursor.fetchall()]
        
        # Get school details with geographical names
        cursor.execute("""
            SELECT sm."SchoolName",
                CONCAT_WS(', ',
                    sm."Address",
                    d."Geog_Name",
                    s."Geog_Name",
                    c."Geog_Name",
                    sm."Pincode"
                ) AS "Address",
                sm."SchoolLogo"
            FROM "SchoolMaster" sm
            LEFT JOIN "Geographical_Master" d ON sm."District" = d."Geog_Id" and d."Geog_Type"='District'
            LEFT JOIN "Geographical_Master" s ON sm."State" = s."Geog_Id" and s."Geog_Type"='State'
            LEFT JOIN "Geographical_Master" c ON sm."Country" = c."Geog_Id" and c."Geog_Type"='Country'
            WHERE sm."SchoolID" = %s
        """, [school_id])
        school_row = cursor.fetchone()
        school_name = ''
        school_address = ''
        school_logo = ''
        if school_row:
            school_name = school_row[0]
            school_address = school_row[1]
            if school_row[2]:
                school_logo = f"data:image/jpeg;base64,{base64.b64encode(school_row[2]).decode('utf-8')}"
    
    context = {
        'SchoolName': school_name,
        'SchoolAddress': school_address,
        'SchoolLogo': school_logo,
        'timetable': timetable,
        'periods': periods,
        'slots': slots
    }
    
    html = render_to_string(template_path, context)
    return HttpResponse(html)

@login_required
@require_http_methods(["GET"])
def view_timetable_page(request):
    """View timetable page with role-based filtering"""
    from core.url_encryption import decrypt_id_int, encrypt_id
    
    # Robust ID/Profile resolution
    school_id = _get_timetable_school_id(request)
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Add schools for Super Admin
    schools = []
    selected_school_id = None
    if profile_id == 1:
        from .utils import get_school_dropdown
        schools = get_school_dropdown()
        selected_school_id = request.session.get('timetable_selected_school_id')
    
    # Decrypt IDs from URL
    class_id = None
    section_id = None
    teacher_id = None
    if request.GET.get('class_id'):
        class_id = decrypt_id_int(request.GET.get('class_id'))
    if request.GET.get('section_id'):
        section_id = decrypt_id_int(request.GET.get('section_id'))
    if request.GET.get('teacher_id'):
        teacher_id = decrypt_id_int(request.GET.get('teacher_id'))
    
    # Enforce single filter: Prioritize class over teacher if both are provided
    if class_id and teacher_id:
        teacher_id = None
        
    # Debug: Print values
    print(f"DEBUG: school_id={school_id} ({type(school_id)}), class_id={class_id} ({type(class_id)}), section_id={section_id} ({type(section_id)}), teacher_id={teacher_id} ({type(teacher_id)}), profile_id={profile_id}")
    
    # Logic ported from Proc_Timetable_View_ByRole
    role_timetables = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u."UserCode", p."ProfileName" 
            FROM "UserMaster" AS u
            INNER JOIN "ProfileMaster" AS p ON u."ProfileID" = p."ProfileID"
            WHERE u."UserID" = %s
        """, [user_id])
        row = cursor.fetchone()
        user_code = row[0] if row else None
        profile_name = row[1] if row else None

        student_id = None
        student_class_id = None
        employee_id = None

        if profile_name == 'Student' and user_code:
            cursor.execute('SELECT "StudentID" FROM "Student" WHERE "StudentCode" = %s', [user_code])
            s_row = cursor.fetchone()
            student_id = s_row[0] if s_row else None
            if student_id:
                cursor.execute('SELECT "ClassID" FROM "StudentAcademicTrack" WHERE "StudentID" = %s AND "IsCurrent" = true', [student_id])
                c_row = cursor.fetchone()
                student_class_id = c_row[0] if c_row else None
        
        if (profile_name == 'Teacher' or profile_name == 'School Admin') and user_code:
            cursor.execute('SELECT "EmployeeID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s', [user_code])
            e_row = cursor.fetchone()
            employee_id = e_row[0] if e_row else None

        # Base query for timetable slots
        base_sql = """
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
            LEFT JOIN "SectionMaster" sm ON sm."SectionID" = tm."SectionID"
            LEFT JOIN "SubjectMaster" sub ON sub."SubjectID" = ts."SubjectID"
            LEFT JOIN "EmployeeMaster" em ON em."EmployeeID" = ts."TeacherID"
            WHERE tm."SchoolID" = %s AND tm."IsDeleted" = false AND ts."IsDeleted" = false
        """
        params = [school_id]

        if profile_id == 2 or profile_id == 1:  # School Admin or Super Admin
            if class_id:
                base_sql += ' AND tm."ClassID" = %s'
                params.append(class_id)
                if section_id:
                    base_sql += ' AND tm."SectionID" = %s'
                    params.append(section_id)
            elif teacher_id:
                base_sql += ' AND ts."TeacherID" = %s'
                params.append(teacher_id)
            else:
                # No data if no filter for admin (as per original proc logic line 97)
                base_sql += " AND 1=0"
        elif profile_id == 3:  # Teacher
            base_sql += ' AND ts."TeacherID" = %s'
            params.append(employee_id if employee_id else -1)
        elif profile_id == 4:  # Student
            base_sql += ' AND tm."ClassID" = %s'
            params.append(student_class_id if student_class_id else -1)
        else:
            base_sql += " AND 1=0"

        base_sql += ' ORDER BY tm."TimetableID", ts."DayOfWeek", pm."DisplayOrder"'
        
        cursor.execute(base_sql, params)
        columns = [col[0] for col in cursor.description]
        all_data = []
        for row in cursor.fetchall():
            d = dict(zip(columns, row))
            d['EncryptedTimetableID'] = encrypt_id(d['TimetableID'])
            all_data.append(d)
    
    # Get classes for filter dropdown (School Admin or Super Admin with selected school)
    classes = []
    sections = []
    teachers = []
    if profile_id == 2 or (profile_id == 1 and school_id):  # School Admin or Super Admin
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "ClassID", "ClassName" FROM "ClassMaster" 
                WHERE "SchoolID"=%s AND COALESCE("IsDeleted", false)=false ORDER BY "ClassName"
            """, [school_id])
            classes = [{'ClassID': row[0], 'ClassName': row[1], 'EncryptedID': encrypt_id(row[0])} for row in cursor.fetchall()]
            
            if class_id:
                cursor.execute("""
                    SELECT "SectionID", "SectionName" FROM "SectionMaster" 
                    WHERE "ClassID"=%s AND COALESCE("IsDeleted", false)=false ORDER BY "SectionName"
                """, [class_id])
                sections = [{'SectionID': row[0], 'SectionName': row[1], 'EncryptedID': encrypt_id(row[0])} for row in cursor.fetchall()]

            # Get all employees as teachers
            cursor.execute("""
                SELECT EM."EmployeeID" AS "TeacherID", EM."EmployeeName" AS "TeacherName"
                FROM "EmployeeMaster" AS EM
                WHERE EM."SchoolID" = %s AND COALESCE(EM."IsDeleted", false) = false
                ORDER BY EM."EmployeeName"
            """, [school_id])
            teachers = [{'EmployeeID': row[0], 'UserName': row[1], 'EncryptedID': encrypt_id(row[0])} for row in cursor.fetchall()]
    
    context = get_context(request)
    context.update({
        'all_data': all_data,
        'all_data_json': json.dumps([dict(d) for d in all_data], default=str),
        'classes': classes,
        'sections': sections,
        'teachers': teachers,
        'selected_class': class_id,
        'selected_section': section_id,
        'selected_teacher': teacher_id,
        'selected_school_list': [selected_school_id] if selected_school_id else [],
        'selected_class_list': [class_id] if class_id else [],
        'selected_section_list': [section_id] if section_id else [],
        'selected_teacher_list': [teacher_id] if teacher_id else [],
        'profile_id': profile_id,
        'schools': schools,
        'selected_school_id': selected_school_id
    })
    
    return render(request, 'core/view_timetable.html', context)

@login_required
@require_http_methods(["GET"])
def view_timetable_detail(request, encrypted_timetable_id):
    """Get timetable detail for modal view"""
    timetable_id = decrypt_id_int(encrypted_timetable_id)
    if not timetable_id:
        return JsonResponse({'error': 'Invalid Timetable ID'}, status=400)
        
    school_id = _get_timetable_school_id(request)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t."TimetableID", t."AcademicYear", t."EffectiveFrom", t."EffectiveTo", cm."ClassName", sm."SectionName", t."ClassID"
            FROM "TimetableMaster" t 
            INNER JOIN "ClassMaster" cm ON t."ClassID" = cm."ClassID"
            LEFT JOIN "SectionMaster" sm ON t."SectionID" = sm."SectionID" 
            WHERE t."TimetableID"=%s AND t."SchoolID"=%s AND COALESCE(t."IsDeleted", false)=false
        """, [timetable_id, school_id])
        
        columns = [col[0] for col in cursor.description]
        timetable_row = cursor.fetchone()
        if not timetable_row:
            return JsonResponse({'error': 'Timetable not found'}, status=404)
        
        timetable = dict(zip(columns, timetable_row))
        
        # Get periods
        cursor.execute("""
            SELECT * FROM "PeriodMaster" 
            WHERE "SchoolID"=%s AND COALESCE("IsDeleted", false)=false 
            ORDER BY "DisplayOrder", "StartTime"
        """, [school_id])
        columns = [col[0] for col in cursor.description]
        periods = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get slots
        cursor.execute("""
            SELECT ts."SlotID", ts."DayOfWeek", ts."PeriodID", ts."RoomNumber", ts."Notes",
                p."PeriodName", p."StartTime", p."EndTime", p."PeriodType",
                sm."SubjectID", sm."SubjectName", sm."SubjectCode", EM."EmployeeID" AS "TeacherID", EM."EmployeeName" AS "TeacherName"
            FROM "TimetableSlot" ts 
            INNER JOIN "PeriodMaster" p ON ts."PeriodID" = p."PeriodID"
            LEFT JOIN "SubjectMaster" sm ON ts."SubjectID" = sm."SubjectID" 
            LEFT JOIN "EmployeeMaster" EM ON ts."TeacherID" = EM."EmployeeID"
            WHERE ts."TimetableID"=%s AND COALESCE(ts."IsDeleted", false)=false 
            ORDER BY ts."DayOfWeek", p."DisplayOrder"
        """, [timetable_id])
        columns = [col[0] for col in cursor.description]
        slots = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return JsonResponse({
        'timetable': timetable,
        'encrypted_timetable_id': encrypted_timetable_id,
        'periods': periods,
        'slots': slots
    })

@login_required
@require_http_methods(["GET"])
def timetable_preview(request):
    """Preview timetable template"""
    from django.template.loader import render_to_string
    import datetime
    import base64
    
    template = request.GET.get('template', 'core/document_templates/class_timetable/timetable_template1.html')
    
    # Robust SchoolID resolution
    school_id = _get_timetable_school_id(request)
    school_name = request.session.get('SchoolName', 'Sample School')
    
    # Get school logo as base64 data URI
    school_logo = ''
    if school_id:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID"=%s', [school_id])
            logo_row = cursor.fetchone()
            if logo_row and logo_row[0]:
                school_logo = f"data:image/jpeg;base64,{base64.b64encode(logo_row[0]).decode('utf-8')}"
    
    # Sample data for preview
    context = {
        'SchoolName': school_name,
        'SchoolLogo': school_logo,
        'timetable': {
            'ClassName': 'Class X',
            'SectionName': 'A',
            'AcademicYear': '2024-25',
            'EffectiveFrom': datetime.date.today(),
            'EffectiveTo': datetime.date.today() + datetime.timedelta(days=365)
        },
        'periods': [
            {'PeriodID': 1, 'PeriodName': 'Period 1', 'PeriodType': 'Class', 'StartTime': '08:00:00', 'EndTime': '08:45:00'},
            {'PeriodID': 2, 'PeriodName': 'Period 2', 'PeriodType': 'Class', 'StartTime': '08:45:00', 'EndTime': '09:30:00'},
            {'PeriodID': 3, 'PeriodName': 'Break', 'PeriodType': 'Break', 'StartTime': '09:30:00', 'EndTime': '09:45:00'},
            {'PeriodID': 4, 'PeriodName': 'Period 3', 'PeriodType': 'Class', 'StartTime': '09:45:00', 'EndTime': '10:30:00'},
            {'PeriodID': 5, 'PeriodName': 'Period 4', 'PeriodType': 'Class', 'StartTime': '10:30:00', 'EndTime': '11:15:00'},
        ],
        'slots': [
            {'DayOfWeek': 1, 'PeriodID': 1, 'SubjectName': 'Mathematics', 'TeacherName': 'Mr. Smith'},
            {'DayOfWeek': 1, 'PeriodID': 2, 'SubjectName': 'English', 'TeacherName': 'Ms. Johnson'},
            {'DayOfWeek': 1, 'PeriodID': 4, 'SubjectName': 'Science', 'TeacherName': 'Dr. Brown'},
            {'DayOfWeek': 2, 'PeriodID': 1, 'SubjectName': 'Hindi', 'TeacherName': 'Mrs. Sharma'},
            {'DayOfWeek': 2, 'PeriodID': 2, 'SubjectName': 'Social Studies', 'TeacherName': 'Mr. Patel'},
            {'DayOfWeek': 3, 'PeriodID': 1, 'SubjectName': 'Mathematics', 'TeacherName': 'Mr. Smith'},
        ]
    }
    
    html = render_to_string(template, context)
    return HttpResponse(html)
 
# triggering server reload to flush template cache
 
# triggering server reload to flush template cache for final format fix
 
# triggering server reload for final parenthesis fix
