from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db import connection
from django.views.decorators.clickjacking import xframe_options_exempt
from .views import custom_login_required, get_context
from .models import BrandProfile
from .url_encryption import encrypt_id
from .utils import get_school_dropdown
import logging
import json
import base64
from datetime import datetime

logger = logging.getLogger(__name__)

def _get_template_with_context(request, template_type, default_template, student_code_param='student_code'):
    """Helper to resolve school_id and fetch saved template preference."""
    school_id = request.GET.get('school_id') or (request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID'))
    student_code = request.GET.get(student_code_param)
    template = request.GET.get('template')
    
    # Resolve school_id from student_code if missing
    if not school_id and student_code:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolID" FROM "Student" WHERE "StudentCode" = %s AND COALESCE("IsDeleted", false) = false', [student_code])
                row = cursor.fetchone()
                if row:
                    school_id = row[0]
        except Exception as e:
            logger.error(f"Error resolving school from student {student_code}: {e}")
            
    # Fetch saved preference if no explicit template in URL
    if not template and school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [school_id, template_type])
                row = cursor.fetchone()
                if row and row[0]:
                    template = row[0]
        except Exception as e:
            logger.error(f"Error fetching template preference for {template_type}: {e}")
            
    return template or default_template, school_id, student_code

@custom_login_required
def template_management(request):
    context = get_context(request)
    school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    filter_school_id = request.GET.get('school_id')
    
    # 🛡️ SECURITY: Restrict to Super Admin (1) and School Admin (2)
    if profile_id not in [1, 2]:
        logger.warning(f"SECURITY: Unauthorized access attempt to Template Management by UserID: {user_id}, ProfileID: {profile_id}")
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You do not have permission to access this page.")
    
    templates = {}
    
    # 🛡️ SECURITY: IDOR Protection - School Admins can only view their own school
    if profile_id == 2:
        context['selected_school_id'] = school_id # Force from session
        context['is_super_admin'] = False
    elif profile_id == 1:
        context['is_super_admin'] = True
        context['schools'] = get_school_dropdown()
        
        if filter_school_id:
            try:
                school_id = int(filter_school_id)
                context['selected_school_id'] = school_id
            except (ValueError, TypeError):
                pass
    
    # Global Preference Logic for Subscription Invoice
    if template_management: # Just to keep scope
        pass
    
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "TemplateType", "TemplateFile" FROM "Proc_Template_Preference_Get"(%s)', [school_id])
                rows = cursor.fetchall()
                for row in rows:
                    templates[row[0]] = row[1]
                
                # Force Security Templates to Global preference (SchoolID=0)
                security_types = ['ACCOUNT_BLOCKED', 'PASSWORD_CHANGED_NOTIFICATION', 'PASSWORD_RESET_OTP', 'LOGIN_OTP', 'NEW_LOGIN_ALERT']
                for s_type in security_types:
                    if school_id != 0:
                        cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(0) WHERE "TemplateType" = %s', [s_type])
                        sec_row = cursor.fetchone()
                        if sec_row and sec_row[0]:
                            templates[s_type] = sec_row[0]
                
                # Force SubscriptionInvoice to Global preference (SchoolID=0)
                if school_id != 0:
                    cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(0) WHERE "TemplateType" = \'SubscriptionInvoice\'')
                    global_row = cursor.fetchone()
                    if global_row and global_row[0]:
                        templates['SubscriptionInvoice'] = global_row[0]
            logger.info(f"Loaded {len(templates)} templates for school {school_id}")
        except Exception as e:
            logger.error(f"Error fetching templates: {e}")
    else:
        # For Super Admin with no school selected, fetch Global (0)
        if profile_id == 1:
             try:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT "TemplateType", "TemplateFile" FROM "Proc_Template_Preference_Get"(0)')
                    rows = cursor.fetchall()
                    for row in rows:
                        templates[row[0]] = row[1]
                context['templates'] = templates
             except Exception as e:
                logger.error(f"Error fetching global templates: {e}")

    context['templates'] = templates
    return render(request, 'template_management.html', context)

@custom_login_required
def template_management_save(request):
    if request.method != 'POST':
        return redirect('template_management')
    
    school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    # 🛡️ SECURITY: Level 1 - Access Control
    if profile_id not in [1, 2]:
        logger.warning(f"SECURITY ALERT: Unauthorized save attempt by UserID: {user_id}, ProfileID: {profile_id}")
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Access Denied")

    template_type = request.POST.get('template_type')
    template_file = request.POST.get('template_file')

    # 🛡️ SECURITY: Level 2 - IDOR Protection
    if profile_id == 1:
        post_school_id = request.POST.get('school_id')
        if post_school_id is not None and post_school_id != '':
            try:
                school_id = int(post_school_id)
            except (ValueError, TypeError):
                pass
        
        # Strictly use Global branding (SchoolID=0) for Subscription Invoices
        if template_type == 'SubscriptionInvoice':
            school_id = 0
    else:
        # School Admins CANNOT specify school_id, always use their session-bound ID
        pass

    # Validate inputs
    if any(x is None for x in [school_id, user_id, template_type, template_file]):
        missing = [k for k, v in {'school_id': school_id, 'user_id': user_id, 'template_type': template_type, 'template_file': template_file}.items() if v is None]
        logger.warning(f"Missing required information for template save: {missing}")
        
        if school_id is None and profile_id == 1:
            messages.error(request, 'Please select a school first to update template preferences.')
        else:
            messages.error(request, 'Missing required information')
            
        return redirect('template_management')
    
    # Validate template file
    valid_templates = [
        # Admission Acknowledgment
        'core/document_templates/admission_acknowledgment/admission_acknowledgment_template1.html',
        'core/document_templates/admission_acknowledgment/admission_acknowledgment_template2.html',
        'core/document_templates/admission_acknowledgment/admission_acknowledgment_template3.html',
        'core/document_templates/admission_acknowledgment/admission_acknowledgment_template4.html',
        'core/document_templates/admission_acknowledgment/admission_acknowledgment_template5.html',
        
        # Payment Receipt
        'core/document_templates/payment_receipt/payment_success.html',
        'core/document_templates/payment_receipt/payment_receipt_template2.html',
        'core/document_templates/payment_receipt/payment_receipt_template3.html',
        'core/document_templates/payment_receipt/payment_receipt_template4.html',
        'core/document_templates/payment_receipt/payment_receipt_template5.html',
        
        # Student ID Card
        'core/document_templates/student_id_card/student_card_horizontal_1.html',
        'core/document_templates/student_id_card/student_card_horizontal_2.html',
        'core/document_templates/student_id_card/student_card_horizontal_3.html',
        'core/document_templates/student_id_card/student_card_horizontal_4.html',
        'core/document_templates/student_id_card/student_card_horizontal_5.html',
        'core/document_templates/student_id_card/student_card_horizontal_6.html',
        'core/document_templates/student_id_card/student_card_horizontal_7.html',
        'core/document_templates/student_id_card/student_card_horizontal_8.html',
        'core/document_templates/student_id_card/student_card_horizontal_9.html',
        'core/document_templates/student_id_card/student_card_horizontal_10.html',
        'core/document_templates/student_id_card/student_card_vertical_1.html',
        'core/document_templates/student_id_card/student_card_vertical_2.html',
        'core/document_templates/student_id_card/student_card_vertical_3.html',
        'core/document_templates/student_id_card/student_card_vertical_4.html',
        'core/document_templates/student_id_card/student_card_vertical_5.html',
        'core/document_templates/student_id_card/student_card_vertical_6.html',
        'core/document_templates/student_id_card/student_card_vertical_7.html',
        'core/document_templates/student_id_card/student_card_vertical_8.html',
        'core/document_templates/student_id_card/student_card_vertical_9.html',
        'core/document_templates/student_id_card/student_card_vertical_10.html',
        'core/document_templates/student_id_card/student_card_vertical_11.html',
        'core/document_templates/student_id_card/student_card_vertical_12.html',
        'core/document_templates/student_id_card/student_card_vertical_13.html',
        'core/document_templates/student_id_card/student_card_vertical_14.html',

        # Fee Receipt
        'core/document_templates/fee_receipt/fee_receipt_template1.html',
        'core/document_templates/fee_receipt/fee_receipt_template2.html',
        'core/document_templates/fee_receipt/fee_receipt_template3.html',
        'core/document_templates/fee_receipt/fee_receipt_template4.html',
        'core/document_templates/fee_receipt/fee_receipt_template5.html',
        'core/document_templates/fee_receipt/fee_receipt_template6.html',
        'core/document_templates/fee_receipt/fee_receipt_template7.html',
        'core/document_templates/fee_receipt/fee_receipt_template8.html',
        'core/document_templates/fee_receipt/fee_receipt_template9.html',
        'core/document_templates/fee_receipt/fee_receipt_template10.html',
        'core/document_templates/fee_receipt/fee_receipt_template11.html',

        # Salary Slip
        'core/document_templates/salary_slip/salary_slip_template0.html',
        'core/document_templates/salary_slip/salary_slip_template1.html',
        'core/document_templates/salary_slip/salary_slip_template2.html',
        'core/document_templates/salary_slip/salary_slip_template3.html',
        'core/document_templates/salary_slip/salary_slip_template4.html',
        'core/document_templates/salary_slip/salary_slip_template5.html',
        'core/document_templates/salary_slip/salary_slip_template6.html',
        'core/document_templates/salary_slip/salary_slip_template7.html',
        'core/document_templates/salary_slip/salary_slip_template8.html',
        'core/document_templates/salary_slip/salary_slip_template9.html',
        'core/document_templates/salary_slip/salary_slip_template10.html',
        'core/document_templates/salary_slip/salary_slip_template11.html',
        'core/document_templates/salary_slip/salary_slip_template12.html',
        'core/document_templates/salary_slip/salary_slip_template13.html',
        'core/document_templates/salary_slip/salary_slip_template14.html',
        'core/document_templates/salary_slip/salary_slip_template15.html',

        # Employee Job Letter
        'core/document_templates/job_letter/job_letter_template1.html',
        'core/document_templates/job_letter/job_letter_template2.html',
        'core/document_templates/job_letter/job_letter_template3.html',
        'core/document_templates/job_letter/job_letter_template4.html',
        'core/document_templates/job_letter/job_letter_template5.html',
        'core/document_templates/job_letter/job_letter_template6.html',
        'core/document_templates/job_letter/job_letter_template7.html',
        'core/document_templates/job_letter/job_letter_template8.html',
        'core/document_templates/job_letter/job_letter_template9.html',
        'core/document_templates/job_letter/job_letter_template10.html',
        'core/document_templates/job_letter/job_letter_template11.html',
        'core/document_templates/job_letter/job_letter_template12.html',
        'core/document_templates/job_letter/job_letter_template13.html',
        'core/document_templates/job_letter/job_letter_template14.html',
        'core/document_templates/job_letter/job_letter_template15.html',
        'core/document_templates/job_letter/job_letter_template16.html',
        'core/document_templates/job_letter/job_letter_template17.html',
        'core/document_templates/job_letter/job_letter_template18.html',
        'core/document_templates/job_letter/job_letter_template19.html',
        'core/document_templates/job_letter/job_letter_template20.html',
        'core/document_templates/job_letter/job_letter_template21.html',
        'core/document_templates/job_letter/job_letter_template22.html',

        # Exam Result
        'core/document_templates/exam_result/exam_result_template1.html',
        'core/document_templates/exam_result/exam_result_template2.html',
        'core/document_templates/exam_result/exam_result_template3.html',
        'core/document_templates/exam_result/exam_result_template4.html',
        'core/document_templates/exam_result/exam_result_template5.html',
        'core/document_templates/exam_result/exam_result_template6.html',
        'core/document_templates/exam_result/exam_result_template7.html',
        'core/document_templates/exam_result/exam_result_template8.html',
        'core/document_templates/exam_result/exam_result_template9.html',
        'core/document_templates/exam_result/exam_result_template10.html',

        # Promotion Email
        'core/document_templates/promotion_email/promotion_template1.html',
        'core/document_templates/promotion_email/promotion_template2.html',
        'core/document_templates/promotion_email/promotion_template3.html',
        'core/document_templates/promotion_email/promotion_template4.html',
        'core/document_templates/promotion_email/promotion_template5.html',
        'core/document_templates/promotion_email/promotion_template6.html',
        'core/document_templates/promotion_email/promotion_template7.html',
        'core/document_templates/promotion_email/promotion_template8.html',
        'core/document_templates/promotion_email/promotion_template9.html',
        'core/document_templates/promotion_email/promotion_template10.html',
        'core/document_templates/promotion_email/promotion_template11.html',
        'core/document_templates/promotion_email/promotion_template12.html',

        # OTP Email
        'core/document_templates/Login_OTP/otp_template1.html',
        'core/document_templates/Login_OTP/otp_template2.html',
        'core/document_templates/Login_OTP/otp_template3.html',
        'core/document_templates/Login_OTP/otp_template4.html',
        'core/document_templates/Login_OTP/otp_template5.html',
        'core/document_templates/Login_OTP/otp_template6.html',
        'core/document_templates/Login_OTP/otp_template7.html',
        'core/document_templates/Login_OTP/otp_template8.html',
        'core/document_templates/Login_OTP/otp_template9.html',
        'core/document_templates/Login_OTP/otp_template10.html',
        'core/document_templates/Login_OTP/otp_template11.html',
        'core/document_templates/Login_OTP/otp_template12.html',
        'core/document_templates/Login_OTP/otp_template13.html',
        'core/document_templates/Login_OTP/otp_template14.html',
        'core/document_templates/Login_OTP/otp_template15.html',

        # Exam Timetable
        'core/document_templates/exam_timetable/exam_timetable_template1.html',
        'core/document_templates/exam_timetable/exam_timetable_template2.html',
        'core/document_templates/exam_timetable/exam_timetable_template3.html',
        'core/document_templates/exam_timetable/exam_timetable_template4.html',
        'core/document_templates/exam_timetable/exam_timetable_template5.html',
        'core/document_templates/exam_timetable/exam_timetable_template6.html',
        'core/document_templates/exam_timetable/exam_timetable_template7.html',
        'core/document_templates/exam_timetable/exam_timetable_template8.html',
        'core/document_templates/exam_timetable/exam_timetable_template9.html',
        'core/document_templates/exam_timetable/exam_timetable_template10.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_1.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_2.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_3.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_4.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_5.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_6.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_7.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_8.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_9.html',
        'core/document_templates/exam_timetable/exam_timetable_portrait_10.html',

        # Class Timetable
        'core/document_templates/class_timetable/timetable_template1.html',
        'core/document_templates/class_timetable/timetable_template2.html',
        'core/document_templates/class_timetable/timetable_template3.html',
        'core/document_templates/class_timetable/timetable_template4.html',
        'core/document_templates/class_timetable/timetable_template5.html',
        'core/document_templates/class_timetable/timetable_template6.html',
        'core/document_templates/class_timetable/timetable_template7.html',
        'core/document_templates/class_timetable/timetable_template8.html',
        'core/document_templates/class_timetable/timetable_template9.html',
        'core/document_templates/class_timetable/timetable_template10.html',
        'core/document_templates/class_timetable/timetable_template11.html',

        # Subscription Invoice
        'core/document_templates/subscription_invoice/template1.html',
        'core/document_templates/subscription_invoice/template2.html',
        'core/document_templates/subscription_invoice/template3.html',
        'core/document_templates/subscription_invoice/template4.html',
        'core/document_templates/subscription_invoice/template5.html',
        'core/document_templates/subscription_invoice/template6.html',
        'core/document_templates/subscription_invoice/template7.html',

        # Security Emails
        'core/document_templates/account_blocked/account_blocked_template1.html',
        'core/document_templates/account_blocked/account_blocked_template2.html',
        'core/document_templates/account_blocked/account_blocked_template3.html',
        'core/document_templates/account_blocked/account_blocked_template4.html',
        'core/document_templates/account_blocked/account_blocked_template5.html',
        'core/document_templates/password_changed_notification/password_changed_notification_template1.html',
        'core/document_templates/password_changed_notification/password_changed_notification_template2.html',
        'core/document_templates/password_changed_notification/password_changed_notification_template3.html',
        'core/document_templates/password_changed_notification/password_changed_notification_template4.html',
        'core/document_templates/password_changed_notification/password_changed_notification_template5.html',
        'core/document_templates/password_reset_otp/password_reset_otp_template1.html',
        'core/document_templates/password_reset_otp/password_reset_otp_template2.html',
        'core/document_templates/password_reset_otp/password_reset_otp_template3.html',
        'core/document_templates/password_reset_otp/password_reset_otp_template4.html',
        'core/document_templates/password_reset_otp/password_reset_otp_template5.html',
        'core/document_templates/login_otp/login_otp_template1.html',
        'core/document_templates/login_otp/login_otp_template2.html',
        'core/document_templates/login_otp/login_otp_template3.html',
        'core/document_templates/login_otp/login_otp_template4.html',
        'core/document_templates/login_otp/login_otp_template5.html',

        # Consolidated Security Emails (Shared across all security scenarios)
        'core/document_templates/security_emails/variant_1_indigo_elite.html',
        'core/document_templates/security_emails/variant_2_modern_minimal.html',
        'core/document_templates/security_emails/variant_3_glassmorphism.html',
        'core/document_templates/security_emails/variant_4_vibrant_orange.html',
        'core/document_templates/security_emails/variant_5_corporate_pro.html'
    ]
    
    if template_file not in valid_templates:
        logger.warning(f"Invalid template selected: {template_file}")
        return redirect('template_management')
    
    # Force Global (0) for Security and Subscription templates
    if template_type in ['ACCOUNT_BLOCKED', 'PASSWORD_CHANGED_NOTIFICATION', 'PASSWORD_RESET_OTP', 'LOGIN_OTP', 'NEW_LOGIN_ALERT', 'SubscriptionInvoice']:
        school_id = 0
        
    logger.info(f"Saving {template_type} template for school {school_id}")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Proc_Template_Preference_Save"(%s, %s, %s, %s)', 
                         [school_id, template_type, template_file, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                messages.success(request, result[1])
                
                # 📜 AUDIT TRAIL: Record the change in administrative logs
                try:
                    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Unknown'))
                    browser_info = request.META.get('HTTP_USER_AGENT', 'Unknown')
                    audit_action = f"Updated {template_type} Template Preference"
                    audit_details = f"New Template: {template_file} for School ID: {school_id}"
                    
                    cursor.execute('SELECT * FROM "Proc_AuditLog_Set"(%s, %s, %s, %s, %s, %s, %s, %s)',
                                 [user_id, audit_action, 'TemplateSettings', f"{school_id}_{template_type}", 
                                  'PREV_VALUE_FETCH_OMITTED', audit_details, ip_address, browser_info])
                except Exception as audit_e:
                    logger.warning(f"Audit logging failed: {audit_e}")
            else:
                logger.error(f"Failed to save template: {result}")
                messages.error(request, result[1] if result else 'Failed to save preference')
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        messages.error(request, 'Failed to update template')
    
    # Redirect back, preserving school selection for super admin
    if profile_id == 1 and school_id:
        return redirect(f"/template-management/?school_id={school_id}")
        
    return redirect('template_management')


@custom_login_required
@xframe_options_exempt
def subscription_invoice_preview(request):
    """Provides a preview for subscription invoice templates with realistic mock data."""
    from datetime import datetime
    template_path = request.GET.get('template', 'core/document_templates/subscription_invoice/template1.html')
    
    # Mock Data for rich preview
    # Fetch Brand Profile from Database
    brand_data = {
        'BrandName': 'ShikshaWave',
        'BrandLogo': None,
        'GSTIN': '29ABCDE1234F1Z5',
        'Address': 'Level 5, Indigo Tower, Sector 18, Noida, UP',
        'AuthorizedSignature': None
    }
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "Proc_BrandProfile_GET"()')
            db_brand = cursor.fetchone()[0]
            
            # Robust parsing of JSONB result
            if isinstance(db_brand, str):
                import json
                db_brand = json.loads(db_brand)
                
            if db_brand and isinstance(db_brand, dict) and db_brand.get('BrandName'):
                brand_data.update(db_brand)
    except Exception as e:
        logger.error(f"Error fetching brand profile: {e}")

    context = {
        'invoice': {
            'InvoiceNumber': 'INV-2026-001',
            'FormattedDate': '10 Apr, 2026',
            'TotalAmount': 15000.00,
            'FinalAmount': 15000.00
        },
        'school': {
            'SchoolName': 'ShikshaWave Elite School',
            'Address': '123 Academic Lane',
            'District': 'Bangalore',
            'State': 'Karnataka'
        },
        'plan': {
            'FormattedStart': '10 Apr, 2026',
            'FormattedEnd': '09 Apr, 2027'
        },
        'items': [
            {'ItemName': 'LMS Premium License (Annual)', 'TotalPrice': 15000.00}
        ],
        'brand': brand_data,
        'footer': {
            'Disclaimer': 'This is a sample tax invoice for preview purposes.',
            'CopyrightNotice': f'© {datetime.now().year} {brand_data.get("BrandName")}. All Rights Reserved.'
        },
        'subscription_id': 999,
        'current_year': datetime.now().year
    }
    
    return render(request, template_path, context)


@custom_login_required
@xframe_options_exempt
def payment_receipt_preview(request):
    import base64
    from datetime import datetime
    template, school_id, student_code = _get_template_with_context(
        request, 'PaymentReceipt', 'core/document_templates/payment_receipt/payment_success.html'
    )
    
    receipt_data = {}
    
    if student_code:
        try:
            with connection.cursor() as cursor:
                # 1. Get Payment Receipt Details
                cursor.execute('SELECT * FROM proc_payment_receipt_get(NULL, %s)', [student_code])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                if row:
                    receipt_data = dict(zip(columns, row))
                    
                    # Parse Fee Breakdown JSON
                    if receipt_data.get('fee_breakdown'):
                        import json
                        try:
                            if isinstance(receipt_data['fee_breakdown'], str):
                                receipt_data['fee_breakdown'] = json.loads(receipt_data['fee_breakdown'])
                        except Exception as e:
                            logger.error(f"Error parsing fee breakdown: {e}")
                            receipt_data['fee_breakdown'] = []
                    else:
                        receipt_data['fee_breakdown'] = []
                    
                    # Ensure numeric fields are float
                    receipt_data['total_amount'] = float(receipt_data.get('total_amount') or 0)
                    receipt_data['amount_paid'] = float(receipt_data.get('amount_paid') or 0)
                
                # 2. Get School Details (Logo, Name) - Fetch separately as proc doesn't return it
                if school_id:
                     cursor.execute('SELECT "SchoolName", "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                     school_row = cursor.fetchone()
                     if school_row:
                         receipt_data['school_name'] = school_row[0]
                         if school_row[1]:
                             receipt_data['school_logo'] = f"data:image/png;base64,{base64.b64encode(school_row[1]).decode('utf-8')}"

        except Exception as e:
            logger.error(f"Error fetching receipt data: {e}")
            receipt_data['fee_breakdown'] = []
    
    if not receipt_data:
        receipt_data = {
            'receipt_number': 'REC-2024-001',
            'student_name': 'John Doe',
            'student_code': 'STU001',
            'payment_date': datetime.now().strftime('%d-%b-%Y'),
            'payment_mode': 'Online',
            'amount_paid': '15000.00',
            'fee_breakdown': [],
        }
    
    return render(request, template, {'payment_receipt': receipt_data})


@custom_login_required
@xframe_options_exempt
def student_card_preview(request):
    import base64
    
    template, school_id, student_code = _get_template_with_context(
        request, 'StudentCard', 'core/document_templates/student_id_card/student_card_horizontal_1.html'
    )
    
    # Sample student data for preview
    student_data = {
        'FullName': 'John Doe',
        'StudentCode': 'STU001',
        'ClassName': 'Class 10',
        'SectionName': 'A',
        'RollNumber': '15',
        'DateOfBirth': '2010-05-15',
        'ParentMobile': '9876543210',
        'PhotoBase64': ''  # Empty for preview
    }
    
    # Get school info
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SchoolName, SchoolLogo FROM SchoolMaster WHERE SchoolID = %s", [school_id])
                row = cursor.fetchone()
                if row:
                    student_data['SchoolName'] = row[0]
                    if row[1]:
                        student_data['SchoolLogoBase64'] = base64.b64encode(row[1]).decode('utf-8')
        except:
            pass
    
    return render(request, template, {'student': student_data})


@custom_login_required
@xframe_options_exempt
def fee_receipt_preview(request):
    from .models import SchoolMaster
    from datetime import datetime
    
    template, school_id, student_code = _get_template_with_context(
        request, 'FeeReceipt', 'core/document_templates/fee_receipt/fee_receipt_template1.html'
    )
    
    context = get_context(request)
    context.update({
        'receipt_no': 'FEE-2024-001',
        'date_of_submission': datetime.now().strftime('%d-%b-%Y'),
        'full_name': 'John Doe',
        'student_code': 'STU001',
        'class_name': 'Class 10',
        'section_name': 'A',
        'fees_month': 'January 2024',
        'fee_breakdown': [
            {'name': 'Tuition Fee', 'user_enter_amount': 5000.00},
            {'name': 'Library Fee', 'user_enter_amount': 500.00},
            {'name': 'Sports Fee', 'user_enter_amount': 300.00},
            {'name': 'Lab Fee', 'user_enter_amount': 700.00}
        ],
        'total_amount': 6500.00,
        'paid_amount': 6500.00,
        'remaining_amount': 0.00
    })
    
    if school_id:
        try:
            school = SchoolMaster.objects.get(school_id=school_id, is_deleted=False)
            context['school_name'] = school.school_name
            context['school_address'] = school.address
            context['school_phone'] = school.phone
            context['school_email'] = school.email
            context['school_logo'] = school.get_school_logo()
        except:
            pass
    
    return render(request, template, context)


@custom_login_required
@xframe_options_exempt
def exam_result_preview(request):
    from datetime import datetime
    
    template, school_id, student_code = _get_template_with_context(
        request, 'ExamResult', 'core/document_templates/exam_result/exam_result_template1.html'
    )
    
    # Sample exam result data for preview
    context = get_context(request)
    context.update({
        'StudentCode': 'STU001',
        'StudentName': 'John Doe',
        'ExamName': 'Mid Term Examination',
        'ExamType': 'Theory + Practical',
        'ClassName': 'Class 10',
        'SectionName': 'A',
        'StartDate': '01 Jan, 2024',
        'EndDate': '15 Jan, 2024',
        'PublishedDate': '20 Jan, 2024',
        'Ranks': '5th',
        'subjects': [
            {
                'SubjectName': 'Mathematics',
                'MaxTheoryMarks': 80,
                'MaxPracticalMarks': 20,
                'MaxVivaMarks': None,
                'TotalMaxMarks': 100,
                'TheoryMarksObtained': 72,
                'PracticalMarksObtained': 18,
                'VivaMarksObtained': 0,
                'TotalMarksObtained': 90,
                'Grade': 'A+',
                'ResultStatus': 'Pass'
            },
            {
                'SubjectName': 'Science',
                'MaxTheoryMarks': 70,
                'MaxPracticalMarks': 30,
                'MaxVivaMarks': None,
                'TotalMaxMarks': 100,
                'TheoryMarksObtained': 65,
                'PracticalMarksObtained': 27,
                'VivaMarksObtained': 0,
                'TotalMarksObtained': 92,
                'Grade': 'A+',
                'ResultStatus': 'Pass'
            },
            {
                'SubjectName': 'English',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None,
                'TotalMaxMarks': 100,
                'TheoryMarksObtained': 85,
                'PracticalMarksObtained': 0,
                'VivaMarksObtained': 0,
                'TotalMarksObtained': 85,
                'Grade': 'A',
                'ResultStatus': 'Pass'
            },
            {
                'SubjectName': 'Social Studies',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None,
                'TotalMaxMarks': 100,
                'TheoryMarksObtained': 78,
                'PracticalMarksObtained': 0,
                'VivaMarksObtained': 0,
                'TotalMarksObtained': 78,
                'Grade': 'A',
                'ResultStatus': 'Pass'
            },
            {
                'SubjectName': 'Hindi',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None,
                'TotalMaxMarks': 100,
                'TheoryMarksObtained': 80,
                'PracticalMarksObtained': 0,
                'VivaMarksObtained': 0,
                'TotalMarksObtained': 80,
                'Grade': 'A',
                'ResultStatus': 'Pass'
            }
        ],
        'total_max': 500,
        'total_obtained': 425,
        'percentage': 85.0,
        'status': 'Pass',
        'color': '#10b981',
        'today': datetime.now().strftime('%d %b, %Y')
    })
    
    return render(request, template, context)


@xframe_options_exempt
def exam_timetable_preview(request):
    from datetime import datetime, timedelta
    import base64
    
    template, school_id, student_code = _get_template_with_context(
        request, 'ExamTimetable', 'core/document_templates/exam_timetable/exam_timetable_template1.html'
    )
    
    # Sample exam timetable data for preview
    context = {}
    base_date = datetime.now()
    
    # Get school logo if available
    school_logo_src = None
    school_name = 'Sample School'
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SchoolName, SchoolLogo FROM SchoolMaster WHERE SchoolID = %s", [school_id])
                row = cursor.fetchone()
                if row:
                    school_name = row[0]
                    if row[1]:
                        school_logo_src = f"data:image/png;base64,{base64.b64encode(row[1]).decode('utf-8')}"
        except:
            pass
    
    context.update({
        'school_name': school_name,
        'school_logo_src': school_logo_src,
        'exam': {
            'ExamName': 'Mid Term Examination',
            'ExamType': 'Theory + Practical',
            'StartDate': base_date,
            'EndDate': base_date + timedelta(days=10)
        },
        'class_name': 'Class 10 - A',
        'timetable': [
            {
                'SubjectName': 'Mathematics',
                'ExamDate': base_date,
                'StartTime': datetime.strptime('09:00', '%H:%M').time(),
                'EndTime': datetime.strptime('12:00', '%H:%M').time(),
                'RoomNo': 'Room 101',
                'MaxTheoryMarks': 80,
                'MaxPracticalMarks': 20,
                'MaxVivaMarks': None
            },
            {
                'SubjectName': 'Science',
                'ExamDate': base_date + timedelta(days=2),
                'StartTime': datetime.strptime('09:00', '%H:%M').time(),
                'EndTime': datetime.strptime('12:00', '%H:%M').time(),
                'RoomNo': 'Room 102',
                'MaxTheoryMarks': 70,
                'MaxPracticalMarks': 30,
                'MaxVivaMarks': None
            },
            {
                'SubjectName': 'English',
                'ExamDate': base_date + timedelta(days=4),
                'StartTime': datetime.strptime('09:00', '%H:%M').time(),
                'EndTime': datetime.strptime('12:00', '%H:%M').time(),
                'RoomNo': 'Room 103',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None
            },
            {
                'SubjectName': 'Social Studies',
                'ExamDate': base_date + timedelta(days=6),
                'StartTime': datetime.strptime('09:00', '%H:%M').time(),
                'EndTime': datetime.strptime('12:00', '%H:%M').time(),
                'RoomNo': 'Room 104',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None
            },
            {
                'SubjectName': 'Hindi',
                'ExamDate': base_date + timedelta(days=8),
                'StartTime': datetime.strptime('09:00', '%H:%M').time(),
                'EndTime': datetime.strptime('12:00', '%H:%M').time(),
                'RoomNo': 'Room 105',
                'MaxTheoryMarks': 100,
                'MaxPracticalMarks': None,
                'MaxVivaMarks': None
            }
        ]
    })
    
    return render(request, template, context)


@custom_login_required
@xframe_options_exempt
def otp_email_preview(request):
    template, school_id, student_code = _get_template_with_context(
        request, 'OTP_EMAIL', 'emails/otp_modern_gradient.html'
    )
    
    context = {
        'user_name': 'John Doe',
        'otp': '123456',
        'valid_minutes': 15,
        'ip_address': '192.168.1.1',
        'school_name': None
    }
    
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SchoolName FROM SchoolMaster WHERE SchoolID = %s", [school_id])
                row = cursor.fetchone()
                if row:
                    context['school_name'] = row[0]
        except:
            pass
    
    return render(request, template, context)


@custom_login_required
@xframe_options_exempt
def admission_acknowledgment_preview(request):
    import base64
    from datetime import datetime
    
    template, school_id, student_code = _get_template_with_context(
        request, 'AdmissionAcknowledgment', 'core/document_templates/admission_acknowledgment/admission_acknowledgment_template1.html'
    )
    
    ack_data = {'school_name': request.session.get('SchoolName', 'Sample School')}
    
    try:
        with connection.cursor() as cursor:
            if not student_code:
                cursor.execute('SELECT "StudentCode" FROM "Student" WHERE "SchoolID" = %s AND COALESCE("IsDeleted", false) = false ORDER BY "AdmissionDate" DESC LIMIT 1', [school_id])
                row = cursor.fetchone()
                student_code = row[0] if row else None
            
            if student_code:
                # Use the unified procedure to get all data in one go
                cursor.execute('SELECT proc_admission_acknowledgment_full_get(%s)', [student_code])
                result = cursor.fetchone()
                
                if result and result[0]:
                    data = result[0]
                    # Handle JSON string parsing if necessary
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    if 'error' not in data:
                        # Extract student info as the base acknowledgment data
                        ack_data = data.get('student', {})
                        # Merge other related data
                        ack_data['instructions'] = data.get('instructions') or []
                        ack_data['documents'] = data.get('documents') or []
                        ack_data['fees'] = data.get('fees') or []
                        ack_data['total_amount'] = data.get('total_amount') or 0
        
        # Format logo if it exists (though it's already a full Data URI from procedure)
        # We just ensure it's passed as is.

                
                if not ack_data.get('current_date'):
                    ack_data['current_date'] = datetime.now().strftime('%d-%b-%Y')
            else:
                ack_data['instructions'] = []
                ack_data['documents'] = []
                ack_data['fees'] = []
    except Exception as e:
        logger.error(f"Error fetching preview data: {e}")
    
    return render(request, template, {'acknowledgment': ack_data})


@custom_login_required
@xframe_options_exempt
def promotion_email_preview(request):
    from datetime import datetime
    
    template, school_id, student_code = _get_template_with_context(
        request, 'PromotionEmail', 'core/document_templates/promotion_email/promotion_template1.html'
    )
    
    # Normalize template path (handle cases where 'core/templates/' might be prepended)
    if template and template.startswith('core/templates/'):
        template = template.replace('core/templates/', '', 1)
        
    # Also handle the old emails/promotion path if it comes from the database
    if template and 'emails/promotion/' in template:
        template = template.replace('emails/promotion/', 'core/document_templates/promotion_email/', 1)
    
    context = {
        'student_name': 'John Doe',
        'new_class': 'Class 10',
        'new_section': 'A',
        'prev_class': 'Class 9',
        'prev_section': 'B',
        'roll_no': '202401',
        'academic_year': '2024-2025',
        'current_date': datetime.now().strftime('%d %B, %Y'),
        'school_name': 'Sample School'
    }
    
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT SchoolName FROM SchoolMaster WHERE SchoolID = %s", [school_id])
                row = cursor.fetchone()
                if row:
                    context['school_name'] = row[0]
        except:
            pass
            
    return render(request, template, context)


@custom_login_required
@xframe_options_exempt
def job_letter_preview(request):
    """Preview job letter with sample or first available employee data"""
    from datetime import datetime
    import json
    import base64
    from django.db import connection
    
    template, school_id, employee_code = _get_template_with_context(
        request, 'EmployeeJobLetter', 'core/document_templates/job_letter/job_letter_template1.html'
    )
    
    # If no employee_code provided via GET, try to find the first employee in the school
    if not employee_code and school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "EmployeeCode" FROM "EmployeeMaster" WHERE "SchoolID" = %s AND "IsActive" = TRUE AND "IsDeleted" = FALSE LIMIT 1', [school_id])
                row = cursor.fetchone()
                if row:
                    employee_code = row[0]
        except Exception as e:
            logger.error(f"Error fetching sample employee: {e}")

    # Default context if no employee found
    context_employee = {
        'school_name': 'ShikshaWave International School',
        'school_address': 'Sector 15, Global Tech Park, Bangalore',
        'school_logo': None,
        'current_date': datetime.now().strftime('%d-%b-%Y'),
        'employee_name': 'John Doe',
        'full_name': 'John Doe',
        'employee_code': 'EMP001',
        'position': 'Senior Faculty',
        'designation': 'Senior Faculty',
        'date_of_joining': '01-Apr-2024',
        'email': 'john.doe@example.com',
        'mobile_no': '+91 9876543210',
        'department': 'Academic',
        'father_name': 'Robert Doe',
        'password': 'Welcome@2024',
        'salary_components': [],
        'net_salary': 0,
        'total_salary': 0,
        'school_rules': []
    }

    if school_id and employee_code:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM "Proc_EmployeeJobLetter_Get"(%s, %s)', [employee_code, school_id])
                row = cursor.fetchone()
                if row:
                    staff_data = row[0]
                    salary_components = row[1]
                    school_data = row[2]
                    rules_data = row[3]
                    school_logo_binary = row[4]
                    photo_content = row[5]
                    photo_ext = row[6]
                    login_info = row[7] if len(row) > 7 else {}

                    if isinstance(staff_data, str): staff_data = json.loads(staff_data)
                    if isinstance(salary_components, str): salary_components = json.loads(salary_components)
                    if isinstance(school_data, str): school_data = json.loads(school_data)
                    if isinstance(rules_data, str): rules_data = json.loads(rules_data)
                    if isinstance(login_info, str): login_info = json.loads(login_info)
                    
                    # Ensure login_info is a dict
                    login_info = login_info or {}
                    
                    net_salary = 0
                    earnings = []
                    deductions = []
                    for comp in (salary_components or []):
                        amt = float(comp.get('Amount', 0))
                        if comp.get('ComponentType') == 'Earning':
                            net_salary += amt
                            earnings.append(comp)
                        else:
                            net_salary -= amt
                            deductions.append(comp)

                    school_logo_url = None
                    if school_logo_binary:
                        logo_base64 = base64.b64encode(bytes(school_logo_binary)).decode('utf-8')
                        school_logo_url = f"data:image/png;base64,{logo_base64}"

                    user_photo_url = None
                    if photo_content:
                        photo_base64 = base64.b64encode(bytes(photo_content)).decode('utf-8')
                        user_photo_url = f"data:image/{photo_ext or 'png'};base64,{photo_base64}"

                    context_employee = {
                        'school_name': school_data.get('SchoolName', 'ShikshaWave School'),
                        'school_address': school_data.get('SchoolAddress', 'N/A'),
                        'school_logo': school_logo_url,
                        'user_photo': user_photo_url,
                        'current_date': datetime.now().strftime('%d-%b-%Y'),
                        'employee_name': staff_data.get('EmployeeName', 'N/A'),
                        'full_name': staff_data.get('EmployeeName', 'N/A'),
                        'employee_code': employee_code,
                        'position': staff_data.get('Position', 'Staff'),
                        'designation': staff_data.get('Position', 'Staff'),
                        'date_of_joining': staff_data.get('DateOfJoining', 'N/A'),
                        'department': staff_data.get('Department', 'General'),
                        'father_name': staff_data.get('FatherOrHusbandName', 'N/A'),
                        'mobile_no': staff_data.get('MobileNo', 'N/A'),
                        'email': staff_data.get('Email', 'N/A'),
                        'date_of_birth': staff_data.get('DateOfBirth', 'N/A'),
                        'home_address': staff_data.get('HomeAddress', 'N/A'),
                        'gender': staff_data.get('Gender', 'N/A'),
                        'education': staff_data.get('Education', 'N/A'),
                        'password': staff_data.get('Password', 'Welcome@123'),
                        'greeting_message': staff_data.get('GreetingMessage', ''),
                        'salary_components': salary_components,
                        'earnings': earnings,
                        'deductions': deductions,
                        'net_salary': net_salary,
                        'total_salary': net_salary,
                        'school_rules': rules_data,
                        'school_terms_conditions': rules_data,
                        'login_info': login_info
                    }
        except Exception as e:
            logger.error(f"Error fetching preview data: {e}")
            
    return render(request, template, {
        'employee': context_employee,
        'login_info': context_employee.get('login_info', {})
    })


@custom_login_required
@xframe_options_exempt
def print_job_letter(request):
    """Print job letter with real employee data and preferred template"""
    from datetime import datetime
    from django.http import HttpResponse
    import json
    import base64
    from django.db import connection
    from core.url_encryption import decrypt_id
    
    encrypted_code = request.GET.get('employee_code')
    employee_code = decrypt_id(encrypted_code)
    
    # Check if decryption failed, fall back to plain code (for backward compatibility if needed, though safer to enforce encryption)
    if not employee_code:
        employee_code = encrypted_code

    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    
    if not employee_code:
        return HttpResponse('Employee code is required', status=400)
        
    # Security/Authorization: Ensure non-superadmins can only access their own school's employees
    if str(profile_id) != '1':
        # Verify employee belongs to this school
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT 1 FROM "EmployeeMaster" WHERE "EmployeeCode" = %s AND "SchoolID" = %s',
                    [employee_code, school_id]
                )
                if not cursor.fetchone():
                    logger.warning(f"Unauthorized access attempt by user (SchoolID: {school_id}) for employee {employee_code}")
                    return HttpResponse('Unauthorized access', status=403)
        except Exception as e:
            logger.error(f"Error verifying employee school: {e}")
            return HttpResponse('Error verifying access', status=500)
        
    # Super Admin: Get school from employee record if not in session
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
            logger.error(f"Error getting school for employee print: {e}")
            
    if not school_id:
        return HttpResponse('School information not found', status=404)
        
    # Get preferred template
    template_file = 'job_letter_template1.html' # Default
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT \"TemplateFile\" FROM \"TemplateSettings\" WHERE \"SchoolID\"=%s AND \"TemplateType\"='EmployeeJobLetter' AND \"IsActive\"=true AND \"IsDeleted\"=false", 
                [school_id]
            )
            row = cursor.fetchone()
            if row and row[0]:
                template_file = row[0].replace('core/document_templates/job_letter/', '')
    except Exception as e:
        logger.error(f"Error fetching template preference: {e}")
        
    template_path = f'core/document_templates/job_letter/{template_file}'
    
    # Fetch real employee data
    context_employee = {}
    try:
        with connection.cursor() as cursor:
            # Single call to get everything: Employee, Salary, School, Photo, Rules
            cursor.execute('SELECT * FROM "Proc_EmployeeJobLetter_Get"(%s, %s)', [employee_code, school_id])
            row = cursor.fetchone()
            
            if row:
                staff_data = row[0]
                salary_components = row[1]
                school_data = row[2]
                rules_data = row[3]
                school_logo_binary = row[4]
                photo_content = row[5]
                photo_ext = row[6]
                login_info = row[7] if len(row) > 7 else {}

                # Robust parsing for JSON fields in case driver returns strings
                if isinstance(staff_data, str):
                    staff_data = json.loads(staff_data)
                if isinstance(salary_components, str):
                    salary_components = json.loads(salary_components)
                if isinstance(school_data, str):
                    school_data = json.loads(school_data)
                if isinstance(rules_data, str):
                    rules_data = json.loads(rules_data)
                if isinstance(login_info, str):
                    login_info = json.loads(login_info)
                
                # Ensure login_info is a dict
                login_info = login_info or {}
                
                # Assign default empty if needed
                staff_data = staff_data or {}
                salary_components = salary_components or []
                school_data = school_data or {}
                rules_data = rules_data or []
                
                # Calculate Earnings and Deductions
                net_salary = 0
                earnings = []
                deductions = []
                for comp in (salary_components or []):
                    amt = float(comp.get('Amount', 0))
                    if comp.get('ComponentType') == 'Earning':
                        net_salary += amt
                        earnings.append(comp)
                    else:
                        net_salary -= amt
                        deductions.append(comp)
                
                # Process School Logo (Raw Binary from row[4])
                school_logo_url = None
                if school_logo_binary and len(school_logo_binary) > 0:
                    try:
                        binary_data = bytes(school_logo_binary)
                        if binary_data:
                            logo_base64 = base64.b64encode(binary_data).decode('utf-8')
                            school_logo_url = f"data:image/png;base64,{logo_base64}"
                    except Exception as e:
                        logger.warning(f"Failed to convert logo: {e}")

                # Process Employee Photo (Raw Binary from row[5])
                user_photo_url = None
                if photo_content and len(photo_content) > 0:
                    try:
                        binary_photo = bytes(photo_content)
                        if binary_photo:
                            photo_base64 = base64.b64encode(binary_photo).decode('utf-8')
                            ext = (photo_ext or 'png').replace('.', '')
                            user_photo_url = f"data:image/{ext};base64,{photo_base64}"
                    except Exception as e:
                        logger.warning(f"Failed to convert employee photo: {e}")

                context_employee = {
                    'school_name': school_data.get('SchoolName', 'ShikshaWave School'),
                    'school_address': school_data.get('SchoolAddress', 'N/A'),
                    'school_logo': school_logo_url,
                    'user_photo': user_photo_url,
                    'current_date': datetime.now().strftime('%d-%b-%Y'),
                    'employee_name': staff_data.get('EmployeeName', 'N/A'),
                    'full_name': staff_data.get('EmployeeName', 'N/A'),
                    'employee_code': employee_code,
                    'position': staff_data.get('Position', 'Staff'),
                    'designation': staff_data.get('Position', 'Staff'),
                    'date_of_joining': staff_data.get('DateOfJoining', 'N/A'),
                    'department': staff_data.get('Department', 'Education'),
                    'father_name': staff_data.get('FatherOrHusbandName', 'N/A'),
                    'mobile_no': staff_data.get('MobileNo', 'N/A'),
                    'email': staff_data.get('Email', 'N/A'),
                    'date_of_birth': staff_data.get('DateOfBirth', 'N/A'),
                    'home_address': staff_data.get('HomeAddress', 'N/A'),
                    'gender': staff_data.get('Gender', 'N/A'),
                    'education': staff_data.get('Education', 'N/A'),
                    'password': staff_data.get('Password', 'Welcome@123'),
                    'greeting_message': staff_data.get('GreetingMessage', ''),
                    'salary_components': salary_components,
                    'earnings': earnings,
                    'deductions': deductions,
                    'net_salary': net_salary,
                    'total_salary': net_salary,
                    'school_rules': rules_data,
                    'school_terms_conditions': rules_data,
                    'login_info': login_info
                }
                
                # Check if password is in session (for first-time print)
                ack_data = request.session.get('employee_ack_data')
                if ack_data and ack_data.get('employee_code') == employee_code:
                    context_employee['password'] = ack_data.get('password', '***')
            else:
                return HttpResponse('Employee details not found', status=404)
                
    except Exception as e:
        logger.error(f"Error generating job letter for print: {e}", exc_info=True)
        return HttpResponse(f'Error generating document: {e}', status=500)
        
    return render(request, template_path, {
        'employee': context_employee,
        'login_info': context_employee.get('login_info', {})
    })

@custom_login_required
@xframe_options_exempt
def security_email_preview(request):
    """Provides a preview for security email templates with relevant mock data."""
    # Standardize the path by removing core/templates prefix if present
    template_path = request.GET.get('template', 'core/document_templates/login_otp/login_otp_template1.html')
    if template_path.startswith('core/templates/'):
        template_path = template_path.replace('core/templates/', '', 1)
        
    code = request.GET.get('code', 'LOGIN_OTP')
    
    # Mock Data for rich preview
    context = {
        'user_name': 'Abhishek Singh',
        'full_name': 'Abhishek Singh',
        'login_id': 'abhishek.singh@shikshawave.com',
        'otp': '582041',
        'valid_minutes': 15,
        'ip_address': '192.168.1.45',
        'browser': 'Chrome on Windows 11 (Secure Session)',
        'profile': 'Super Admin',
        'school_logo': BrandProfile.objects.filter(is_active=True).first().get_brand_logo() if BrandProfile.objects.filter(is_active=True).exists() else '/static/images/ShikshaWave_Logo.png',
        'header_title': 'Identity Verification',
        'current_year': datetime.now().year,
        'timestamp': datetime.now().strftime('%d %b %Y, %H:%M:%S'),
        'blocked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'code': code
    }
    
    try:
        return render(request, template_path, context)
    except Exception as e:
        logger.error(f"Error rendering security email preview for {template_path}: {e}")
        return HttpResponse(f"Error loading template: {e}", status=404)
