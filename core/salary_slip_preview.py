from django.shortcuts import render
from django.db import connection
from django.views.decorators.clickjacking import xframe_options_exempt
from .views import custom_login_required
from datetime import datetime
import base64

@custom_login_required
@xframe_options_exempt
def salary_slip_preview(request):
    school_id = request.GET.get('school_id') or request.session.get('SchoolID')
    template = request.GET.get('template')

    # Fetch saved preference if no explicit template in URL
    if not template and school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [school_id, 'SalarySlip'])
                row = cursor.fetchone()
                if row and row[0]:
                    template = row[0]
        except Exception:
            pass
            
    if not template:
        template = 'core/document_templates/salary_slip/salary_slip_template1.html'
    
    data = {
        'employee_code': 'EMP001',
        'employee_name': 'John Doe',
        'employee_email': 'john@example.com',
        'designation': 'Senior Teacher',
        'salary_month': 'January 2024',
        'gross_salary': '50,000.00',
        'total_deductions': '5,000.00',
        'net_salary': '45,000.00',
        'payment_date': datetime.now().strftime('%d-%b-%Y'),
        'payment_mode': 'Bank Transfer',
        'transaction_ref': 'TXN123456',
        'salary_reference_id': 'SAL-2024-001',
        'bank_account': '1234567890',
        'upi_id': 'john@upi',
        'uan_number': 'UAN123456',
        'earnings': [
            {'name': 'Basic Salary', 'amount': '30,000.00'},
            {'name': 'HRA', 'amount': '12,000.00'},
            {'name': 'Transport Allowance', 'amount': '5,000.00'},
            {'name': 'Special Allowance', 'amount': '3,000.00'}
        ],
        'deductions': [
            {'name': 'PF', 'amount': '3,600.00'},
            {'name': 'Professional Tax', 'amount': '200.00'},
            {'name': 'TDS', 'amount': '1,200.00'}
        ]
    }
    
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SchoolName, SchoolAddress, SchoolPhone, SchoolEmail, SchoolLogo FROM SchoolMaster WHERE SchoolID = %s", [school_id])
                row = cursor.fetchone()
                if row:
                    data['school_name'] = row[0]
                    data['school_address'] = row[1] or ''
                    data['school_phone'] = row[2] or ''
                    data['school_email'] = row[3] or ''
                    if row[4]:
                        data['school_logo'] = f"data:image/png;base64,{base64.b64encode(row[4]).decode('utf-8')}"
                    else:
                        data['school_logo'] = ''
        except:
            data['school_name'] = 'Sample School'
            data['school_address'] = 'Sample Address'
            data['school_phone'] = '1234567890'
            data['school_email'] = 'school@example.com'
            data['school_logo'] = ''
    else:
        # Default data if no school selected
        data['school_name'] = 'Sample School'
        data['school_address'] = 'Sample Address'
        data['school_phone'] = '1234567890'
        data['school_email'] = 'school@example.com'
        data['school_logo'] = ''
    
    return render(request, template, data)
