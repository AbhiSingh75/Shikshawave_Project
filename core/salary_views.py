from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.template.loader import render_to_string
from mail.utils import send_email_by_code
import json
import threading
import logging
from .decorators import custom_login_required
import base64
import tempfile
import os
import subprocess

logger = logging.getLogger(__name__)

def custom_login_required(view_func):
    from functools import wraps
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('UserId'):
            messages.error(request, "Please login to continue.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wraps(view_func)(_wrapped)

@custom_login_required
def salary_management(request):
    """Render salary management page"""
    from core.views import get_context
    context = get_context(request)
    
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
    
    context['is_super_admin'] = (profile_id == 1)
    
    # For Super Admin, get school list for dropdown
    if context['is_super_admin']:
        from .subject_views import get_school_dropdown
        from .url_encryption import encrypt_id
        
        raw_schools = get_school_dropdown()
        schools = []
        for s in raw_schools:
            schools.append({
                'SchoolID': s['SchoolID'],
                'SchoolName': s['SchoolName'],
                'DisplayName': s['DisplayName']
            })
        context['schools'] = schools
        
        # Check if a school is selected via GET param (encrypted)
        from .url_encryption import decrypt_id
        enc_school_id = request.GET.get('sid')
        if enc_school_id:
            context['selected_school_id'] = enc_school_id
            try:
                context['selected_school_id_raw'] = decrypt_id(enc_school_id)
            except:
                pass
    
    return render(request, 'core/salary_management.html', context)

@custom_login_required
def get_employees(request):
    """Get all employees for dropdown"""
    try:
        school_id = request.GET.get('school_id') or request.session.get('SchoolID')
        
        if not school_id:
            return JsonResponse({'status': 'FAILED', 'message': 'School not selected'})
        
        school_id = int(school_id)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT e."EmployeeID", e."EmployeeName", p."ProfileName", e."EmployeeCode"
                FROM "EmployeeMaster" e
                INNER JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
                WHERE e."SchoolID" = %s AND COALESCE(e."IsDeleted", FALSE) = FALSE
                ORDER BY e."EmployeeName"
            """, [school_id])
            
            employees = []
            for row in cursor.fetchall():
                employees.append({
                    'id': row[0],
                    'name': row[1],
                    'designation': row[2],
                    'code': row[3]
                })
        
        return JsonResponse({'status': 'SUCCESS', 'employees': employees})
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

from .url_encryption import encrypt_id, decrypt_id_int

@custom_login_required
def get_salary_list(request):
    """Get salary list"""
    try:
        school_id = request.GET.get('school_id') or request.session.get('SchoolID')
        month = request.GET.get('month')
        search = request.GET.get('search', '').strip()
        employee_code = request.GET.get('employee_code', '').strip()
        employee_id = request.GET.get('employee_id')
        
        if not school_id and not employee_code:
            return JsonResponse({'status': 'FAILED', 'message': 'School not selected'})
        
        if school_id:
            try:
                school_id = int(school_id)
            except (ValueError, TypeError):
                school_id = None
        
        if employee_code:
            with connection.cursor() as cursor:
                # If school_id is not provided or 0 (Super Admin fallback), find it from EmployeeCode
                if not school_id:
                    cursor.execute('SELECT "SchoolID" FROM "EmployeeMaster" WHERE "EmployeeCode" = %s', [employee_code])
                    row = cursor.fetchone()
                    if row:
                        school_id = row[0]
                
                if not school_id:
                    return JsonResponse({'status': 'FAILED', 'message': 'School identification failed'})

                cursor.execute("""
                    SELECT "EmployeeID" FROM "EmployeeMaster"
                    WHERE "EmployeeCode" = %s AND "SchoolID" = %s AND COALESCE("IsDeleted", FALSE) = FALSE
                """, [employee_code, school_id])
                emp_row = cursor.fetchone()
                employee_id = emp_row[0] if emp_row else None
            
            if not employee_id:
                return JsonResponse({'status': 'FAILED', 'message': 'Employee not found'})
            
            year = request.GET.get('year', '').strip()
            
            # Format year to match what Proc_Salary_Get expects for p_Month ('YYYY-MM' or 'YYYY-')
            # If we only have year, send 'YYYY-' so the procedure extracts v_Year and leaves v_Month as NULL
            month_param = f"{year}-" if year else None
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Salary_Get"(
                        %s, %s, %s, %s
                    )
                """, [school_id, month_param, employee_id, None])
                
                salaries = []
                for row in cursor.fetchall():
                    salaries.append({
                        'payment_id': row[0],
                        'encrypted_payment_id': encrypt_id(row[0]),
                        'employee_id': row[1],
                        'employee_code': row[2],
                        'employee_name': row[3],
                        'employee_email': row[4],
                        'designation': row[5],
                        'salary_month': row[6],
                        'gross_salary': float(row[7] or 0),
                        'deductions': float(row[8] or 0),
                        'net_salary': float(row[9] or 0),
                        'payment_status': row[10] or 'Pending',
                        'payment_date': row[11].strftime('%Y-%m-%d') if row[11] else None,
                        'payment_mode': row[12],
                        'transaction_ref': row[13],
                        'salary_reference_id': row[14]
                    })
            
            return JsonResponse({'status': 'SUCCESS', 'salaries': salaries})
        
        if not employee_id:
            try:
                emp_id_param = int(request.GET.get('employee_id')) if request.GET.get('employee_id') else None
            except:
                emp_id_param = None
        else:
            emp_id_param = int(employee_id) if employee_id else None

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_Salary_Get"(
                    %s, %s, %s, %s
                )
            """, [school_id, month, emp_id_param, search if search else None])
            
            salaries = []
            for row in cursor.fetchall():
                salaries.append({
                    'payment_id': row[0],
                    'encrypted_payment_id': encrypt_id(row[0]),
                    'employee_id': row[1],
                    'employee_code': row[2],
                    'employee_name': row[3],
                    'employee_email': row[4],
                    'designation': row[5],
                    'salary_month': row[6],
                    'gross_salary': float(row[7] or 0),
                    'deductions': float(row[8] or 0),
                    'net_salary': float(row[9] or 0),
                    'payment_status': row[10] or 'Pending',
                    'payment_date': row[11].strftime('%Y-%m-%d') if row[11] else None,
                    'payment_mode': row[12],
                    'transaction_ref': row[13],
                    'salary_reference_id': row[14]
                })
        
        return JsonResponse({'status': 'SUCCESS', 'salaries': salaries})
    except Exception as e:
        logger.error(f"Error fetching salaries: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def pay_salary(request):
    """Pay salary to employee"""
    try:
        data = json.loads(request.body)
        user_id = request.session.get('UserId')
        school_id = request.session.get('SchoolID')
        payment_id = data.get('payment_id')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_Salary_Pay"(
                    %s, %s, %s, %s, %s, %s
                )
            """, [
                payment_id,
                data.get('payment_date'),
                data.get('payment_mode'),
                data.get('transaction_ref'),
                data.get('remarks'),
                user_id
            ])
        
        # Offload PDF generation and Email dispatch to a background thread to prevent blocking the user
        try:
            email_thread = threading.Thread(
                target=send_salary_slip_email,
                args=(payment_id, school_id),
                daemon=True
            )
            email_thread.start()
        except Exception as thread_error:
            logger.error(f"Error starting salary email thread: {thread_error}")
        
        return JsonResponse({'status': 'SUCCESS', 'message': 'Salary paid successfully'})
    except Exception as e:
        logger.error(f"Error paying salary: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def generate_salary_records(request):
    """Generate salary records for selected month"""
    try:
        data = json.loads(request.body)
        school_id = data.get('school_id') or request.session.get('SchoolID')
        
        if not school_id:
            return JsonResponse({'status': 'FAILED', 'message': 'School not selected'})
        
        school_id = int(school_id)
        user_id = request.session.get('UserId')
        salary_month = data.get('salary_month')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_SalaryRelease_Generate"(
                    %s, %s, %s
                )
            """, [school_id, salary_month, user_id])
            result = cursor.fetchone()
        
        return JsonResponse({'status': result[0], 'message': result[1]})
    except Exception as e:
        logger.error(f"Error generating salary records: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

from django.db import transaction

def get_salary_slip_data(payment_id):
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Proc_SalarySlip_Get"(%s)', [payment_id])
            
            # Postgres returns rows where each row contains a cursor name
            cursors = cursor.fetchall()
            if not cursors:
                return None
                
            # 1. Header Cursor
            header_cursor_name = cursors[0][0]
            cursor.execute(f'FETCH ALL FROM "{header_cursor_name}"')
            row = cursor.fetchone()
            
            if not row:
                return None
            
            school_logo = ''
            if row[21]:
                try:
                    logo_base64 = base64.b64encode(row[21]).decode('utf-8')
                    school_logo = f'data:image/png;base64,{logo_base64}'
                except:
                    school_logo = ''
            
            data = {
                'employee_code': row[2], 'employee_name': row[3], 'employee_email': row[4],
                'designation': row[5], 'salary_month': row[6],
                'gross_salary': f"{float(row[7] or 0):,.2f}",
                'total_deductions': f"{float(row[8] or 0):,.2f}",
                'net_salary': f"{float(row[9] or 0):,.2f}",
                'payment_date': row[11].strftime('%d-%b-%Y') if row[11] else '',
                'payment_mode': row[12] or '', 'transaction_ref': row[13] or 'N/A',
                'salary_reference_id': row[14] or '', 'remarks': row[15] or '',
                'school_id': row[1],
                'school_name': row[16],
                'school_address': row[18] or '', 'school_phone': row[19] or '',
                'school_email': row[20] or '', 'school_logo': school_logo,
                'bank_account': row[22] or 'N/A', 'upi_id': row[23] or 'N/A',
                'uan_number': row[24] or 'N/A'
            }
            
            earnings = []
            deductions = []
            
            # 2. Earnings Cursor
            if len(cursors) > 1:
                earnings_cursor_name = cursors[1][0]
                cursor.execute(f'FETCH ALL FROM "{earnings_cursor_name}"')
                earnings_rows = cursor.fetchall()
                earnings = [{'name': r[0], 'amount': f"{float(r[2] or 0):,.2f}"} for r in earnings_rows]
                
            # 3. Deductions Cursor
            if len(cursors) > 2:
                deductions_cursor_name = cursors[2][0]
                cursor.execute(f'FETCH ALL FROM "{deductions_cursor_name}"')
                deductions_rows = cursor.fetchall()
                deductions = [{'name': r[0], 'amount': f"{float(r[2] or 0):,.2f}"} for r in deductions_rows]
            
            data['earnings'] = earnings
            data['deductions'] = deductions
            
            return data

def generate_salary_slip_pdf(payment_id, school_id=None):
    try:
        data = get_salary_slip_data(payment_id)
        if not data:
            return None
        
        template = 'core/document_templates/salary_slip/salary_slip_template1.html'
        
        # Prioritize school_id from data, then argument
        school_id = data.get('school_id') or school_id
        
        if school_id:
            try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [school_id, 'SalarySlip'])
                    row = cursor.fetchone()
                    if row and row[0]:
                        template = row[0]
            except Exception as e:
                logger.error(f"Error fetching salary slip template: {e}")
        
        html = render_to_string(template, data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            html_path = f.name
        
        pdf_path = html_path.replace('.html', '.pdf')
        
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
        ]
        
        chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)
        
        if chrome_exe:
            subprocess.run([
                chrome_exe,
                '--headless',
                '--disable-gpu',
                '--print-to-pdf=' + pdf_path,
                '--print-to-pdf-no-header',
                '--no-pdf-header-footer',
                html_path
            ], check=True, capture_output=True, timeout=10)
            
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            os.unlink(html_path)
            os.unlink(pdf_path)
            return pdf_content
        
        os.unlink(html_path)
        return None
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        return None

def send_salary_slip_email(payment_id, school_id):
    data = get_salary_slip_data(payment_id)
    if not data:
        return
    
    pdf_content = generate_salary_slip_pdf(payment_id, school_id)
    attachments = []
    if pdf_content:
        attachments.append((f"SalarySlip-{data['salary_reference_id']}.pdf", pdf_content, 'application/pdf'))
    else:
        logger.warning(f"PDF generation failed for payment {payment_id}, sending email without attachment")
    
    send_email_by_code(
        code='SALARY_SLIP',
        to_emails=data['employee_email'],
        placeholders={
            'employee_name': data['employee_name'],
            'school_name': data['school_name'],
            'salary_month': data['salary_month'],
            'net_salary': data['net_salary'],
            'payment_date': data['payment_date'],
            'salary_reference_id': data['salary_reference_id'],
            'payment_mode': data['payment_mode']
        },
        attachments=attachments if attachments else None
    )

@custom_login_required
def preview_salary_slip(request, encrypted_payment_id):
    payment_id = decrypt_id_int(encrypted_payment_id)
    if not payment_id:
         return HttpResponse('Invalid Salary Slip ID', status=400)

    data = get_salary_slip_data(payment_id)
    if not data:
        return HttpResponse('Salary slip not found', status=404)
    
    school_id = request.GET.get('school_id') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID'))
    
    # Priority: Data > GET > Session
    if data.get('school_id'):
        school_id = data['school_id']

    template = 'core/document_templates/salary_slip/salary_slip_template1.html'
    
    if school_id:
        try:
            school_id_int = int(school_id)
            with connection.cursor() as cursor:
                cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [school_id_int, 'SalarySlip'])
                row = cursor.fetchone()
                if row and row[0]:
                    template = row[0]
        except Exception:
            pass
    
    return render(request, template, data)

@custom_login_required
def download_salary_slip(request, encrypted_payment_id):
    payment_id = decrypt_id_int(encrypted_payment_id)
    if not payment_id:
         return HttpResponse('Invalid Salary Slip ID', status=400)

    data = get_salary_slip_data(payment_id)
    if not data:
        return HttpResponse('Salary slip not found', status=404)
    
    school_id = request.GET.get('school_id') or request.session.get('SchoolID')
    pdf_content = generate_salary_slip_pdf(payment_id, school_id)
    if not pdf_content:
        return HttpResponse('Error generating PDF', status=500)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    # Set the filename to the Salary Reference ID for a professional convention
    filename = data.get('salary_reference_id', f'SalarySlip-{payment_id}')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

@custom_login_required
@require_POST
def resend_salary_slip(request, encrypted_payment_id):
    try:
        payment_id = decrypt_id_int(encrypted_payment_id)
        if not payment_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Invalid Salary Slip ID'})

        school_id = request.session.get('SchoolID')
        send_salary_slip_email(payment_id, school_id)
        return JsonResponse({'status': 'SUCCESS', 'message': 'Salary slip sent successfully'})
    except Exception as e:
        logger.error(f"Error resending salary slip: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})
