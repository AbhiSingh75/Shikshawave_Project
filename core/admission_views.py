# core/admission_views.py
"""
Admission-related views for student admission, payment, and application management.
All admission functionality is centralized in this module.
"""

import json
import base64
import logging
from .decorators import custom_login_required
import threading
from datetime import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import make_password
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from functools import wraps
from django.core.files.storage import default_storage
import os

from .pdf_generator import generate_pdf_from_template
from .email_tracking_models import EmailTrackingManager
from mail.utils import send_email_by_code
from .utils import get_context, get_school_dropdown

# Constants
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Helper functions

def safe_int(value, default=0):
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_json_obj(obj):
    return json.loads(json.dumps(obj, cls=DjangoJSONEncoder))

def _bytes_to_data_uri(blob: bytes, mime: str = "image/png") -> str:
    if not blob:
        return ""
    return f"data:{mime};base64,{base64.b64encode(blob).decode('utf-8')}"

def validate_uploaded_file(file, allowed_types=None, max_size=MAX_FILE_SIZE):
    if not file:
        return False, "No file provided"
    if allowed_types is None:
        allowed_types = ALLOWED_DOCUMENT_TYPES
    if file.size > max_size:
        return False, f"File size exceeds {max_size / (1024*1024):.0f}MB limit"
    if file.content_type not in allowed_types:
        return False, f"File type {file.content_type} not allowed"
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"File extension {file_ext} not allowed"
    return True, "File is valid"

# Removed local get_context to use the one from core.utils
# This ensures consistent header data (photo, logo) across the app using correct PostgreSQL queries.


logger = logging.getLogger(__name__)


def send_admission_emails_async(email_data):
    """Send admission emails asynchronously in background thread"""
    def email_worker():
        try:
            logger.info("Background email worker started")
            
            placeholders_ack = {
                'student_name': email_data.get('student_name'),
                'student_code': email_data.get('student_code'),
                'admission_class': email_data.get('admission_class'),
                'admission_date': email_data.get('admission_date'),
                'school_name': email_data.get('school_name'),
            }
            # Get fee breakdown from database
            fee_breakdown_list = []
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM proc_student_fee_structure_get(NULL, %s)", [email_data.get('student_code')])
                    fee_columns = [col[0] for col in cursor.description]
                    fee_rows = cursor.fetchall()
                    for row in fee_rows:
                        fee_breakdown_list.append(dict(zip(fee_columns, row)))
            except:
                pass
            
            placeholders_rcpt = {
                'student_name': email_data.get('student_name'),
                'student_code': email_data.get('student_code'),
                'receipt_number': email_data.get('payment_receipt', {}).get('receipt_number'),
                'amount_paid': email_data.get('payment_receipt', {}).get('amount_paid'),
                'payment_mode': email_data.get('payment_receipt', {}).get('payment_mode'),
                'payment_date': email_data.get('payment_receipt', {}).get('payment_date'),
                'school_name': email_data.get('school_name'),
                'fee_breakdown': fee_breakdown_list,
            }

            try:
                logger.info("Background: Generating acknowledgment PDF...")
                ack_data = {}
                student_code = email_data.get('student_code')
                if student_code:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM proc_student_acknowledgment_get(%s)", [student_code])
                        row = cursor.fetchone()
                        if row:
                            columns = [col[0] for col in cursor.description]
                            ack_data = dict(zip(columns, row))
                            if ack_data.get('StudentCode'):
                                ack_data['student_code'] = ack_data['StudentCode']
                            if ack_data.get('school_logo'):
                                ack_data['school_logo'] = _bytes_to_data_uri(ack_data['school_logo'])
                        ack_data['instructions'] = []
                        if cursor.nextset():
                            ack_data['instructions'] = [{'title': r[0], 'text': r[1]} for r in cursor.fetchall()]
                        ack_data['documents'] = []
                        if cursor.nextset():
                            ack_data['documents'] = [{'type': r[0], 'name': r[1]} for r in cursor.fetchall()]
                        ack_data['fees'] = []
                        if cursor.nextset():
                            ack_data['fees'] = [{'name': r[0], 'amount': float(r[1] or 0), 'discount': float(r[2] or 0), 'final': float(r[3] or 0)} for r in cursor.fetchall()]
                ack_pdf = generate_pdf_from_template('admission_acknowledgment.html', {'acknowledgment': ack_data})
                
                logger.info("Background: Generating receipt PDF...")
                receipt_template = 'core/document_templates/payment_receipt/payment_success.html'
                school_id = email_data.get('school_id')
                if school_id:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT "TemplateFile" FROM "TemplateSettings" WHERE "SchoolID" = %s AND "TemplateType" = \'PaymentReceipt\' AND "IsActive" = TRUE AND "IsDeleted" = FALSE', [school_id])
                        row = cursor.fetchone()
                        if row and row[0]:
                            receipt_template = row[0]
                
                # Get full receipt data with fee breakdown from database (same as preview)
                receipt_data_full = {}
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT * FROM proc_payment_receipt_get(NULL, %s)", [email_data.get('student_code')])
                        columns = [col[0] for col in cursor.description]
                        row = cursor.fetchone()
                        if row:
                            receipt_data_full = dict(zip(columns, row))
                            if receipt_data_full.get('school_logo'):
                                receipt_data_full['school_logo'] = _bytes_to_data_uri(receipt_data_full['school_logo'])
                            if receipt_data_full.get('fee_breakdown'):
                                import json
                                receipt_data_full['fee_breakdown'] = json.loads(receipt_data_full['fee_breakdown'])
                except Exception as e:
                    logger.error(f"Failed to get receipt data: {e}")
                    receipt_data_full = email_data.get('payment_receipt', {})
                
                rcpt_pdf = generate_pdf_from_template(receipt_template, {'payment_receipt': receipt_data_full})

                logger.info("Background: Sending acknowledgment email...")
                send_email_by_code(
                    code='ADMISSION_ACKNOWLEDGMENT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_ack,
                    school_id=email_data.get('school_id'),
                    attachments=[(f"Acknowledgment-{email_data.get('student_code')}.pdf", ack_pdf, 'application/pdf')]
                )
                
                logger.info("Background: Sending receipt email...")
                send_email_by_code(
                    code='PAYMENT_RECEIPT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_rcpt,
                    school_id=email_data.get('school_id'),
                    attachments=[(f"Receipt-{email_data.get('student_code')}.pdf", rcpt_pdf, 'application/pdf')]
                )
                
                logger.info("Background: Emails with PDFs sent successfully")
                
            except Exception as pdf_error:
                logger.warning(f"Background: PDF generation failed, sending emails without attachments: {str(pdf_error)}")
                
                send_email_by_code(
                    code='ADMISSION_ACKNOWLEDGMENT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_ack,
                    school_id=email_data.get('school_id')
                )
                
                send_email_by_code(
                    code='PAYMENT_RECEIPT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_rcpt,
                    school_id=email_data.get('school_id')
                )
                
                logger.info("Background: Emails sent without PDFs")
                
        except Exception as email_error:
            logger.error(f"Background: Email sending failed: {str(email_error)[:100]}")
    
    email_thread = threading.Thread(target=email_worker, daemon=True)
    email_thread.start()
    logger.info("Background email thread started")


@custom_login_required
def student_admission(request):
    """
    Render student admission form and handle form submission using merged stored procedure
    """
    user_id = request.session.get('UserId')
    
    if not user_id:
        messages.error(request, "Please login to access admission form")
        return redirect('login')



    # School Context Logic
    school_id = request.session.get('SchoolID')
    school_name = request.session.get('SchoolName')
    
    # Super Admin Override
    school_options = []
    # Fix: UserMaster does not have is_superuser. Rely on Session ProfileName or safe check.
    is_super_admin = request.session.get('ProfileName') == 'Super Admin' or getattr(request.user, 'is_superuser', False)
    
    if is_super_admin:
        try:
            # Use global utility for school list (standard format [Code] Name)
            school_options = get_school_dropdown()
        except Exception as e:
            logger.error(f"Error fetching school dropdown: {e}")
            school_options = []
        
        
        # Handle Context Switch via POST (Cleaner URL)
        if request.method == 'POST' and request.POST.get('action') == 'switch_school':
            get_school_id = request.POST.get('school_id')
            if get_school_id:
                try:
                    new_school_id = int(get_school_id)
                    # Verify school exists in options
                    selected_school = next((s for s in school_options if s['SchoolID'] == new_school_id), None)
                    if selected_school:
                        request.session['SchoolID'] = new_school_id
                        request.session['SchoolName'] = selected_school['SchoolName']
                        messages.success(request, f"Switched to {selected_school['SchoolName']}")
                        return redirect(request.path)
                except ValueError:
                    pass

    if not school_id and not is_super_admin:
        messages.error(request, "School context missing.")
        return redirect('dashboard')
    
    context = get_context(request)
    
    # Reload School Logo if school_id differs from session (e.g. Super Admin selection)
    if school_id and school_id != request.session.get('SchoolID'):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                logo_row = cursor.fetchone()
                if logo_row and logo_row[0]:
                    context['school_logo_src'] = _bytes_to_data_uri(logo_row[0])
                else:
                    context['school_logo_src'] = '' # Clear if no logo found for selected school
        except Exception as e:
            logger.error(f"Error fetching school logo for ID {school_id}: {e}")

    admission_fee_types = []
    if school_id:
        try:
            with connection.cursor() as cursor:
                # PostgreSQL call
                cursor.execute("SELECT * FROM proc_admission_fee_types_get(%s)", [school_id])
                for row in cursor.fetchall():
                    admission_fee_types.append({
                        'FeeTypeId': row[0],
                        'FeeTypeName': row[2],
                        'DefaultAmount': float(row[3])
                    })
                logger.info(f"Loaded {len(admission_fee_types)} admission fee types for School ID: {school_id}")
                
        except Exception as e:
            logger.error(f"Error fetching admission fee types for School ID {school_id}: {str(e)}")
            messages.warning(request, "Could not load admission fee types. Please contact administrator.")
    
    context.update({
        'user_id': user_id,
        'school_id': school_id,
        'school_name': school_name,
        'admission_fee_types': admission_fee_types,
        'monthly_fee_types': [],
        'is_super_admin': is_super_admin,
        'school_options': school_options,
    })
    
    if request.method == 'POST':
        try:
            # Extract form data
            full_name = request.POST.get('fullName')
            gender = request.POST.get('gender')
            date_of_birth = request.POST.get('dateOfBirth')
            age = request.POST.get('age')
            blood_group = request.POST.get('bloodGroup')
            category = request.POST.get('category')
            religion = request.POST.get('religion')
            nationality = request.POST.get('nationality')
            mother_tongue = request.POST.get('motherTongue')
            present_address = request.POST.get('presentAddress')
            permanent_address = request.POST.get('permanentAddress')
            parent_mobile = request.POST.get('parentMobile', '').replace('-', '')
            alternate_number = request.POST.get('alternateNumber', '').replace('-', '')
            email = request.POST.get('email')
            father_name = request.POST.get('fatherName')
            father_occupation = request.POST.get('fatherOccupation')
            father_qualification = request.POST.get('fatherQualification')
            father_aadhaar = request.POST.get('fatherAadhaar', '').replace('-', '')
            father_mobile = request.POST.get('fatherMobile', '').replace('-', '')
            mother_name = request.POST.get('motherName')
            mother_occupation = request.POST.get('motherOccupation')
            mother_qualification = request.POST.get('motherQualification')
            mother_aadhaar = request.POST.get('motherAadhaar', '').replace('-', '')
            mother_mobile = request.POST.get('motherMobile', '').replace('-', '')
            guardian_name = request.POST.get('guardianName')
            guardian_relation = request.POST.get('guardianRelation')
            guardian_mobile = request.POST.get('guardianMobile', '').replace('-', '')
            last_school = request.POST.get('lastSchool')
            last_class = request.POST.get('lastClass')
            tc_number = request.POST.get('tcNumber')
            medium_of_instruction = request.POST.get('medium')
            academic_year_id = request.POST.get('academicYear')
            admission_class = request.POST.get('admissionClass')
            section = request.POST.get('section')
            stream = request.POST.get('stream')
            mode_of_admission = request.POST.get('mode')
            admission_date = request.POST.get('admissionDate')
            father_sign = request.POST.get('fatherSign')
            mother_sign = request.POST.get('motherSign')
            guardian_sign = request.POST.get('guardianSign')
            student_sign = request.POST.get('studentSign')
            declaration_date = request.POST.get('declarationDate')
            principal_approval = request.POST.get('principalApproval')
            student_aadhaar = request.POST.get('studentAadhaarNumber', '').replace('-', '')
            student_password = request.POST.get('studentPassword')
            
            country_id = request.POST.get('country_id')
            state_id = request.POST.get('state_id')
            district_id = request.POST.get('district_id')
            
            # Helper to convert empty string or invalid to None (for PostgreSQL integer/null support)
            def clean_int(val):
                if val is None: return None
                val = str(val).strip()
                return int(val) if val and val.isdigit() else None

            # Clean all integer IDs
            country_id = clean_int(country_id)
            state_id = clean_int(state_id)
            district_id = clean_int(district_id)
            academic_year_id = clean_int(academic_year_id)
            admission_class = clean_int(admission_class)
            section = clean_int(section)
            # stream is VARCHAR in proc, so just trim or None
            stream = stream.strip() if stream and str(stream).strip() else None
            
            if not country_id and request.POST.get('country_text'):
                country_id = None
            if not state_id and request.POST.get('state_text'):
                state_id = None
            if not district_id and request.POST.get('district_text'):
                district_id = None
            
            student_password_hash = make_password(student_password) if student_password else None
            
            # Extract fee details
            fees_data = []
            total_fees_amount = 0
            
            for fee_type in admission_fee_types:
                try:
                    fee_type_id = int(fee_type['FeeTypeId'])
                    fee_type_name = fee_type['FeeTypeName']
                    default_amount = float(fee_type['DefaultAmount'])
                    discount_str = request.POST.get(f'discount_{fee_type_id}', '').strip()
                    discount_percentage = float(discount_str) if discount_str and discount_str.replace('.', '', 1).isdigit() else 0.0
                    
                    if discount_percentage < 0:
                        discount_percentage = 0.0
                    elif discount_percentage > 100:
                        discount_percentage = 100.0

                    final_amount = default_amount
                    if discount_percentage > 0:
                        final_amount = default_amount - (default_amount * discount_percentage / 100)

                    fee_data = {
                        'feeTypeId': fee_type_id,
                        'feeTypeName': fee_type_name,
                        'amount': round(default_amount, 2),
                        'discountPercentage': round(discount_percentage, 2),
                        'finalAmount': round(final_amount, 2)
                    }
                    
                    fees_data.append(fee_data)
                    total_fees_amount += round(final_amount, 2)
                
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing admission fee type {fee_type[0]}: {str(e)}")
                    continue
            
            # Process monthly fees
            monthly_fee_ids = request.POST.getlist('monthly_fee_id[]')
            monthly_fee_names = request.POST.getlist('monthly_fee_name[]')
            monthly_fee_amounts = request.POST.getlist('monthly_fee_amount[]')
            monthly_fee_discounts = request.POST.getlist('monthly_fee_discount[]')
            
            for i in range(len(monthly_fee_ids)):
                try:
                    fee_type_id = int(monthly_fee_ids[i])
                    fee_type_name = monthly_fee_names[i]
                    default_amount = float(monthly_fee_amounts[i])
                    discount_percentage = float(monthly_fee_discounts[i]) if monthly_fee_discounts[i] else 0.0
                    
                    if discount_percentage < 0:
                        discount_percentage = 0.0
                    elif discount_percentage > 100:
                        discount_percentage = 100.0
                    
                    final_amount = default_amount
                    if discount_percentage > 0:
                        final_amount = default_amount - (default_amount * discount_percentage / 100)
                    
                    fee_data = {
                        'feeTypeId': fee_type_id,
                        'feeTypeName': fee_type_name,
                        'amount': round(default_amount, 2),
                        'discountPercentage': round(discount_percentage, 2),
                        'finalAmount': round(final_amount, 2)
                    }
                    
                    fees_data.append(fee_data)
                    total_fees_amount += round(final_amount, 2)
                    
                except (ValueError, TypeError, IndexError) as e:
                    logger.warning(f"Error processing monthly fee at index {i}: {str(e)}")
                    continue
            
            fees_json = json.dumps({'fees': fees_data}) if fees_data else None

            # Process documents
            documents = []
            doc_types = request.POST.getlist('docType[]')
            doc_files = request.FILES.getlist('docFile[]')
            for doc_type, file in zip(doc_types, doc_files):
                if doc_type and file:
                    is_valid, message = validate_uploaded_file(file, ALLOWED_DOCUMENT_TYPES)
                    if not is_valid:
                        messages.error(request, f"Document validation failed: {message}")
                        return render(request, 'student_admission.html', {**context, 'form_data': request.POST})
                    document_data = base64.b64encode(file.read()).decode('utf-8')
                    documents.append({'type': doc_type, 'name': file.name, 'data': document_data})
            
            documents_json = json.dumps(documents) if documents else None
            
            # Call PostgreSQL function
            with connection.cursor() as cursor:
                user_code = None
                error_message = None
                
                # PostgreSQL Function Call
                cursor.execute("""
                    SELECT "out_UserCode", "out_ErrorMessage"
                    FROM proc_student_admission_with_documents(
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """, [
                    full_name, gender, date_of_birth, age, blood_group, category, religion,
                    nationality, mother_tongue, present_address, permanent_address,
                    district_id, state_id, country_id,
                    parent_mobile, alternate_number, email,
                    father_name, father_occupation, father_qualification, father_aadhaar,
                    father_mobile, mother_name, mother_occupation, mother_qualification,
                    mother_aadhaar, mother_mobile, guardian_name, guardian_relation,
                    guardian_mobile, last_school, last_class, tc_number, medium_of_instruction,
                    academic_year_id, admission_class, section, stream, mode_of_admission, admission_date,
                    father_sign, mother_sign, guardian_sign, student_sign, declaration_date,
                    principal_approval, user_id, student_password_hash,
                    student_aadhaar, fees_json, documents_json, school_id
                ])
                
                result = cursor.fetchone()
                if result:
                    user_code = result[0]
                    error_message = result[1]
                    
                if error_message:
                    raise ValueError(error_message)
            
            # Get student ID
            student_id = None
            with connection.cursor() as cursor:
                # PostgreSQL compatible
                cursor.execute('SELECT "StudentID" FROM "Student" WHERE "StudentCode" = %s', [user_code])
                student_result = cursor.fetchone()
                if student_result:
                    student_id = student_result[0]
            
            # Insert documents
            if student_id and documents:
                try:
                    with connection.cursor() as cursor:
                        for doc in documents:
                            # Decode back to binary if needed, but our proc handles documents in the main call now?
                            # Wait, the new proc DOES accept documents_json, but it didn't use it to insert into StudentDocuments in my definition!
                            # I missed that logic in the SQL definition. I only handled User and Fees. 
                            # Checking the SQL definition... yes, I missed `documents_json` logic in the SQL file.
                            # So I will keep this manual insertion but ensure it uses PostgreSQL syntax.
                            # Actually, it's better to keep it here for safety as managing binary data in JSON procedure args can be tricky.
                            
                            
                            doc_bytes = base64.b64decode(doc['data']) if doc.get('data') else None
                            cursor.execute(
                                """
                                SELECT proc_student_document_upsert(%s, %s, %s, %s, %s)
                                """,
                                [student_id, doc.get('type'), doc.get('name'), doc_bytes, str(user_id)]
                            )
                except Exception as e:
                    logger.error(f"Failed to save student documents: {e}")
            
            # Store admission data in session
            admission_data_raw = {
                'student_id': int(student_id) if student_id else 0,
                'student_code': str(user_code) if user_code else '',
                'student_name': str(full_name) if full_name else '',
                'school_id': int(school_id) if school_id else 0,
                'academic_year_id': int(academic_year_id) if academic_year_id else 0,
                'admission_class': str(admission_class) if admission_class else '',
                'section': str(section) if section else '',
                'email': str(email) if email else '',
                'student_password': str(student_password) if student_password else '',
                'admission_date': str(admission_date) if admission_date else '',
            }
            request.session['admission_data'] = safe_json_obj(admission_data_raw)
            
            return redirect('payment_page')
            
        except Exception as e:
            logger.error(f"Error admitting student: {str(e)}", exc_info=True)
            error_msg = str(e)
            
            if "User authentication required" in error_msg:
                messages.error(request, "Session expired. Please login again.")
                return redirect('login')
            elif "Invalid user account" in error_msg:
                messages.error(request, "Your account is no longer valid. Please contact administrator.")
                return redirect('login')
            elif "already exists in the system" in error_msg:
                messages.error(request, error_msg)
            else:
                messages.error(request, f"Error admitting student: {error_msg}")
                
            return render(request, 'student_admission.html', {**context, 'form_data': request.POST})
    
    return render(request, 'student_admission.html', context)


@custom_login_required
def get_monthly_fee_types(request):
    """AJAX endpoint to get monthly fee types based on class selection"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    class_id = request.GET.get('class_id')
    school_id = request.session.get('SchoolID')
    
    
    if not class_id or not school_id:
        return JsonResponse({'error': 'Class ID and School ID are required'}, status=400)
    
    try:
        with connection.cursor() as cursor:
            # PostgreSQL function call
            cursor.execute("SELECT * FROM proc_monthly_fee_types_get(%s, %s)", [school_id, class_id])
            
            monthly_fees = []
            rows = cursor.fetchall()
            
            for row in rows:
                monthly_fees.append({
                    'FeeTypeId': row[0],
                    'SchoolId': row[1],
                    'FeeTypeName': row[2],
                    'DefaultAmount': float(row[3])
                })
            
            return JsonResponse({
                'success': True,
                'monthly_fees': monthly_fees,
                'school_id': school_id,
                'class_id': class_id
            })
            
    except Exception as e:
        logger.error(f"Error fetching monthly fee types: {str(e)}")
        return JsonResponse({'error': 'Failed to load monthly fee types', 'details': str(e)}, status=500)


@custom_login_required
def payment_page(request):
    """Handle payment after successful admission"""
    admission_data = request.session.get('admission_data')
    if not admission_data:
        messages.error(request, "No admission data found. Please start the admission process again.")
        return redirect('student_admission')
    
    total_fees = 0
    fee_breakdown = []
    
    try:
        current_month = timezone.now().strftime('%Y%m')
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ft."FeeTypeName", sfa."FeeAmount", sfa."DiscountPercentage", sfa."FinalAmount"
                FROM "Student_Fee_Assignment" sfa
                JOIN "FeeType_Master" ft ON sfa."FeeTypeId" = ft."FeeTypeId"
                WHERE sfa."StudentId" = %s AND sfa."FeeMonth" = %s AND COALESCE(sfa."IsDeleted", false) = false
                """,
                [admission_data.get('student_id'), current_month]
            )
            for row in cursor.fetchall():
                fee_data = {
                    'fee_name': str(row[0]) if row[0] else '',
                    'default_amount': float(row[1]) if row[1] is not None else 0.0,
                    'discount_percentage': float(row[2]) if row[2] is not None else 0.0,
                    'amount': float(row[3]) if row[3] is not None else 0.0
                }
                fee_breakdown.append(fee_data)
                total_fees += fee_data['amount']
    except Exception as e:
        logger.error(f"Error loading fees from database: {str(e)}")
        total_fees = 0
    
    context = get_context(request)
    context.update({
        'admission_data': admission_data,
        'total_fees': total_fees,
        'fee_breakdown': fee_breakdown,
    })
    
    if request.method == 'POST':
        payment_mode = request.POST.get('payment_mode')
        paid_amount = request.POST.get('paid_amount')
        transaction_ref = request.POST.get('transaction_ref', '')
        user_id = request.session.get('UserId')
        
        try:
            current_month = timezone.now().strftime('%Y%m')
            fee_breakdown = []
            fee_breakdown_serializable = []
            total_amount = 0
            
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT sfa."FeeTypeId", ft."FeeTypeName", sfa."FeeAmount", sfa."DiscountPercentage", sfa."FinalAmount"
                    FROM "Student_Fee_Assignment" sfa
                    JOIN "FeeType_Master" ft ON sfa."FeeTypeId" = ft."FeeTypeId"
                    WHERE sfa."StudentId" = %s AND sfa."FeeMonth" = %s AND COALESCE(sfa."IsDeleted", false) = false
                    """,
                    [admission_data['student_id'], current_month]
                )
                for row in cursor.fetchall():
                    fee_data = {
                        'fee_type_id': int(row[0]) if row[0] is not None else 0,
                        'fee_name': str(row[1]) if row[1] else '',
                        'default_amount': float(row[2]) if row[2] is not None else 0.0,
                        'discount_percentage': float(row[3]) if row[3] is not None else 0.0,
                        'amount': float(row[4]) if row[4] is not None else 0.0
                    }
                    fee_breakdown.append(fee_data)
                    fee_breakdown_serializable.append(fee_data.copy())
                    total_amount += fee_data['amount']
            
            receipt_number = None
            with connection.cursor() as cursor:
                today_date = timezone.now().strftime('%Y%m%d')
                cursor.execute(
                    """
                    SELECT COUNT(*) + 1 
                    FROM "Payment" 
                    WHERE "SchoolID" = %s 
                      AND "PaymentFor" = 'Admission' 
                      AND "PaymentDate"::DATE = CURRENT_DATE
                    """,
                    [admission_data['school_id']]
                )
                sequence = cursor.fetchone()[0]
                receipt_number = f"ADM-{admission_data['school_id']}-{admission_data['student_code']}-{today_date}-{sequence:03d}"
                
                cursor.execute(
                    """
                    INSERT INTO "Payment" (
                        "SchoolID", "PaymentFor", "EntityID", "EntityType", "ReceiptNumber",
                        "TotalAmount", "PaidAmount", "PaymentMode", "TransactionRef", "PaymentStatus",
                        "PaymentDate", "PaymentMonth", "FeeBreakdown", "Remarks", "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMM'), %s, %s, %s, CURRENT_TIMESTAMP, false
                    )
                    """,
                    [
                        admission_data['school_id'], 'Admission', admission_data['student_id'], 'Student', receipt_number,
                        float(total_amount), float(paid_amount), payment_mode, transaction_ref, 'Paid',
                        json.dumps(fee_breakdown_serializable, cls=DjangoJSONEncoder), 'Admission payment', user_id
                    ]
                )
            
            payment_receipt_raw = {
                'receipt_number': str(receipt_number) if receipt_number else '',
                'student_name': str(admission_data.get('student_name', '')),
                'student_code': str(admission_data.get('student_code', '')),
                'payment_date': str(timezone.now().strftime('%Y-%m-%d %H:%M')),
                'payment_mode': str(payment_mode) if payment_mode else '',
                'amount_paid': float(paid_amount) if paid_amount else 0.0,
                'total_amount': float(total_amount),
                'transaction_ref': str(transaction_ref) if transaction_ref else '',
                'fee_breakdown': fee_breakdown_serializable,
            }
            payment_receipt = safe_json_obj(payment_receipt_raw)

            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT SchoolName, SchoolLogo FROM SchoolMaster WHERE SchoolID = %s", [admission_data.get('school_id')])
                    row = cursor.fetchone()
                    if row:
                        school_name, school_logo_blob = row
                        payment_receipt['school_name'] = school_name
                        if school_logo_blob:
                            payment_receipt['school_logo'] = _bytes_to_data_uri(school_logo_blob)
            except Exception:
                pass

            ack_data = {}
            receipt_data = {}
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM proc_student_acknowledgment_get(%s)", [admission_data['student_code']])
                    columns = [col[0] for col in cursor.description]
                    row = cursor.fetchone()
                    if row:
                        ack_data = dict(zip(columns, row))
                        if ack_data.get('school_logo'):
                            ack_data['school_logo'] = _bytes_to_data_uri(ack_data['school_logo'])
                    
                    cursor.execute("SELECT * FROM proc_student_fee_structure_get(NULL, %s)", [admission_data['student_code']])
                    fee_columns = [col[0] for col in cursor.description]
                    fee_rows = cursor.fetchall()
                    fee_breakdown = [dict(zip(fee_columns, row)) for row in fee_rows]
                    
                    receipt_data = {**payment_receipt, 'fee_breakdown': fee_breakdown, **ack_data}
                    
            except Exception as e:
                logger.error(f"Error fetching accurate data from database: {e}")
                ack_data = payment_receipt
                receipt_data = payment_receipt
            
            request.session['admission_completion'] = safe_json_obj({
                'acknowledgment': ack_data,
                'payment_receipt': receipt_data,
            })

            if admission_data.get('email'):
                try:
                    EmailTrackingManager.create_email_task(
                        email_code='ADMISSION_ACKNOWLEDGMENT',
                        to_email=admission_data.get('email'),
                        placeholders={'student_code': admission_data.get('student_code')},
                        school_id=admission_data.get('school_id'),
                        priority=5,
                        student_code=admission_data.get('student_code'),
                        has_attachments=True
                    )
                    
                    EmailTrackingManager.create_email_task(
                        email_code='PAYMENT_RECEIPT',
                        to_email=admission_data.get('email'),
                        placeholders={
                            'student_code': admission_data.get('student_code'),
                            'receipt_number': receipt_number,
                            'amount_paid': paid_amount,
                            'payment_mode': payment_mode,
                        },
                        school_id=admission_data.get('school_id'),
                        priority=5,
                        student_code=admission_data.get('student_code'),
                        has_attachments=True
                    )
                except Exception as e:
                    logger.error(f"Failed to queue admission emails: {e}")
            
            return redirect('admission_complete')
            
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}", exc_info=True)
            messages.error(request, f"Payment processing failed: {str(e)}")
            return render(request, 'payment.html', context)
    
    return render(request, 'payment.html', context)


@custom_login_required
def admission_complete(request):
    """Display admission completion page with acknowledgment and receipt"""
    completion_data = request.session.get('admission_completion')
    if not completion_data:
        messages.error(request, "No completion data found.")
        return redirect('student_admission')
    
    context = get_context(request)
    acknowledgment = completion_data.get('acknowledgment', {})
    context.update({
        'acknowledgment': acknowledgment,
        'payment_receipt': completion_data.get('payment_receipt', {}),
        'student_code': acknowledgment.get('student_code') or acknowledgment.get('StudentCode', ''),
    })
    
    return render(request, 'admission_complete.html', context)


@custom_login_required
def admission_acknowledgment_preview(request):
    """HTML preview for admission acknowledgment templates"""
    from django.views.decorators.clickjacking import xframe_options_exempt
    
    template = request.GET.get('template', 'core/document_templates/admission_acknowledgment/admission_acknowledgment_template1.html')
    school_id = request.session.get('SchoolID')
    
    ack_data = {'school_name': request.session.get('SchoolName', 'Sample School')}
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "StudentCode" FROM "Student" WHERE "SchoolID" = %s AND COALESCE("IsDeleted", FALSE) = FALSE ORDER BY "AdmissionDate" DESC LIMIT 1', [school_id])
            row = cursor.fetchone()
            if row:
                cursor.execute("SELECT * FROM proc_student_acknowledgment_get(%s)", [row[0]])
                columns = [col[0] for col in cursor.description]
                data_row = cursor.fetchone()
                if data_row:
                    ack_data = dict(zip(columns, data_row))
                    if ack_data.get('school_logo'):
                        ack_data['school_logo'] = _bytes_to_data_uri(ack_data['school_logo'])
    except Exception as e:
        logger.error(f"Error fetching preview data: {e}")
    
    return render(request, template, {'acknowledgment': ack_data})


@custom_login_required
def print_acknowledgment(request):
    """Print acknowledgment PDF"""
    school_id = request.session.get('SchoolID')
    
    template_path = 'core/document_templates/admission_acknowledgment/admission_acknowledgment_template1.html'
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "TemplateFile" FROM "TemplateSettings" 
                    WHERE "SchoolID" = %s AND "TemplateType" = 'AdmissionAcknowledgment' 
                    AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                """, [school_id])
                result = cursor.fetchone()
                if result and result[0]:
                    template_path = result[0]
        except Exception as e:
            logger.error(f"Error fetching template settings: {e}")
    
    completion_data = request.session.get('admission_completion')
    if not completion_data:
        return HttpResponse("No data available", status=404)
    
    try:
        pdf_content = generate_pdf_from_template(
            template_path,
            {'acknowledgment': completion_data.get('acknowledgment', {})}
        )
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="acknowledgment.pdf"'
        return response
    except Exception as e:
        logger.error(f"Error generating acknowledgment PDF: {e}")
        return HttpResponse("Error generating PDF", status=500)


@custom_login_required
def print_receipt(request):
    """Print payment receipt PDF"""
    completion_data = request.session.get('admission_completion')
    if not completion_data:
        return HttpResponse("No data available", status=404)
    
    try:
        school_id = completion_data.get('payment_receipt', {}).get('school_id')
        receipt_template = 'core/document_templates/payment_receipt/payment_success.html'
        
        if school_id:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT "TemplateFile" FROM "TemplateSettings" WHERE "SchoolID" = %s AND "TemplateType" = \'PaymentReceipt\' AND "IsActive" = TRUE AND "IsDeleted" = FALSE',
                    [school_id]
                )
                row = cursor.fetchone()
                if row and row[0]:
                    receipt_template = row[0]
        
        pdf_content = generate_pdf_from_template(
            receipt_template,
            {'payment_receipt': completion_data.get('payment_receipt', {})}
        )
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="receipt.pdf"'
        return response
    except Exception as e:
        logger.error(f"Error generating receipt PDF: {e}")
        return HttpResponse("Error generating PDF", status=500)


@custom_login_required
def clear_receipt_session(request):
    """Clear admission completion data from session"""
    if 'admission_completion' in request.session:
        del request.session['admission_completion']
    if 'admission_data' in request.session:
        del request.session['admission_data']
    return redirect('dashboard')


@custom_login_required
def view_applications(request):
    """View all student applications/admissions"""
    context = get_context(request)
    session_school_id = request.session.get('SchoolID')
    
    # Super Admin Logic
    is_super_admin = False
    school_list = []
    
    # Check if user is Super Admin
    if context.get('profile_name') == 'Super Admin':
        is_super_admin = True
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT "SchoolID", "SchoolName" FROM "SchoolMaster" WHERE COALESCE("IsDeleted", false) = false ORDER BY "SchoolName"')
                school_list = [{'SchoolID': row[0], 'SchoolName': row[1]} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching school list: {e}")
            
        # Get School ID from request
        req_school_id = request.GET.get('school_id')
        if req_school_id and req_school_id != 'all':
            current_school_id = safe_int(req_school_id)
        else:
            current_school_id = None # All schools
    else:
        current_school_id = session_school_id

    page_number = max(1, safe_int(request.GET.get('page', 1)))
    page_size = safe_int(request.GET.get('per_page', 10))
    # Security: Only allow specific page sizes to prevent DoS
    if page_size not in (10, 25, 50, 100):
        page_size = 10
    
    applications = []
    total_count = 0
    
    try:
        with connection.cursor() as cursor:
            # PostgreSQL Stored Procedure Call
            offset = (page_number - 1) * page_size
            cursor.execute(
                "SELECT * FROM proc_student_applications_get(%s, %s, %s)",
                [current_school_id, offset, page_size]
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            applications = [dict(zip(columns, row)) for row in rows]
            
            # total_count is returned in each row if using the CTE logic
            if applications:
                total_count = applications[0].get('total_count', 0)
            else:
                total_count = 0
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        messages.error(request, "Error loading applications")
    
    paginator = Paginator(applications, page_size)
    page_obj = paginator.get_page(page_number)
    
    # Calculate pagination info
    start_index = (page_number - 1) * page_size + 1 if total_count > 0 else 0
    end_index = min(page_number * page_size, total_count)
    
    context.update({
        'applications': page_obj,
        'total_count': total_count,
        'page': page_number,
        'per_page': page_size,
        'start_index': start_index,
        'end_index': end_index,
        'has_next': page_obj.has_next() if hasattr(page_obj, 'has_next') else False,
        'has_previous': page_obj.has_previous() if hasattr(page_obj, 'has_previous') else False,
        'is_super_admin': is_super_admin,
        'school_list': school_list,
        'selected_school_id': current_school_id,
        'search': request.GET.get('search', '')[:200],  # Security: limit search length
        'gender': request.GET.get('gender', '') if request.GET.get('gender', '') in ('', 'Male', 'Female') else '',
        'category': request.GET.get('category', '') if request.GET.get('category', '') in ('', 'General', 'OBC', 'SC', 'ST') else '',
        'status': request.GET.get('status', '') if request.GET.get('status', '') in ('', 'Active', 'Deactive') else '',
    })
    
    return render(request, 'view_applications.html', context)


@custom_login_required
def view_application_detail(request, encrypted_code):
    """View detailed application information"""
    from .url_encryption import decrypt_id
    
    # Security: Decrypt the encrypted student code from URL
    student_code = decrypt_id(encrypted_code)
    if not student_code:
        messages.error(request, "Invalid or expired link")
        return redirect('view_applications')
    
    import re
    # Security: Validate decrypted student_code format
    if not re.match(r'^[A-Za-z0-9_-]{1,30}$', student_code):
        messages.error(request, "Invalid student code")
        return redirect('view_applications')
    
    context = get_context(request)
    
    # Get school_id - check session first, then custom_user
    school_id = request.session.get('SchoolID')
    if not school_id and hasattr(request, 'custom_user'):
        school_id = request.custom_user.get('school_id')
    
    profile_id = request.session.get('ProfileID') or (
        request.custom_user.get('profile_id') if hasattr(request, 'custom_user') else None
    )
    
    # Super Admin (profile_id=1) may not have a SchoolID in session
    # Look up the student's actual SchoolID so we can fetch their data
    if not school_id and str(profile_id) == '1':
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT "SchoolID" FROM "Student" WHERE "StudentCode" = %s LIMIT 1',
                    [student_code]
                )
                row = cursor.fetchone()
                if row:
                    school_id = row[0]
        except Exception as e:
            logger.error(f"Error looking up student school: {e}")
    
    try:
        with connection.cursor() as cursor:
            # Call unified procedure split into 3 functions for PostgreSQL
            
            # Result Set 1: Student Application Details
            cursor.execute("SELECT * FROM proc_application_details_get_core(%s, %s)", [student_code, school_id])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                application = dict(zip(columns, row))
                # Process school logo if exists
                if application.get('SchoolLogo'):
                    application['school_logo'] = _bytes_to_data_uri(application['SchoolLogo'])
                context['application'] = application
            else:
                messages.error(request, "Application not found")
                return redirect('view_applications')
            
            # Result Set 2: Fee Structure
            cursor.execute("SELECT * FROM proc_application_details_get_fee(%s, %s)", [student_code, school_id])
            fee_columns = [col[0] for col in cursor.description]
            fee_rows = cursor.fetchall()
            fee_mapped = [dict(zip(fee_columns, r)) for r in fee_rows]
            context['fee_structure'] = fee_mapped
            
            # Result Set 3: Documents
            cursor.execute("SELECT * FROM proc_application_details_get_docs(%s, %s)", [student_code, school_id])
            
            all_documents_status = []
            ALL_DOCUMENT_TYPES = [
                'Student Passport Photo', 'Birth Certificate', 'Aadhaar (Student)',
                'Aadhaar (Parents)', 'Transfer Certificate', 'Marksheet/Report Card',
                'Father Passport Photo', 'Mother Passport Photo'
            ]
            
            existing_docs_map = {}
            if cursor.description:
                doc_columns = [col[0] for col in cursor.description]
                doc_rows = cursor.fetchall()
                for row in doc_rows:
                    doc = dict(zip(doc_columns, row))
                    # Process Base64 for data
                    if doc.get('DocumentData'):
                         try:
                             import base64
                             data = doc['DocumentData']
                             if isinstance(data, memoryview):
                                 data = data.tobytes()
                             
                             if isinstance(data, (bytes, bytearray)):
                                 doc['DocumentData'] = base64.b64encode(data).decode('utf-8')
                             
                             doc_name = doc.get('DocumentName', '').lower()
                             if doc_name.endswith('.pdf'):
                                 doc['MimeType'] = 'application/pdf'
                             elif doc_name.endswith('.jpg') or doc_name.endswith('.jpeg'):
                                 doc['MimeType'] = 'image/jpeg'
                             elif doc_name.endswith('.png'):
                                 doc['MimeType'] = 'image/png'
                             else:
                                 doc['MimeType'] = 'application/octet-stream'
                         except Exception as e:
                             logger.error(f"Error processing document data: {e}")
                             doc['DocumentData'] = None
                    
                    existing_docs_map[doc['DocumentType']] = doc

            # Build the consolidated list for the UI
            for doc_type in ALL_DOCUMENT_TYPES:
                if doc_type in existing_docs_map:
                    # Document exists
                    doc_info = existing_docs_map[doc_type]
                    doc_info['exists'] = True
                    all_documents_status.append(doc_info)
                else:
                    # Document does not exist (placeholder)
                    all_documents_status.append({
                        'DocumentType': doc_type,
                        'DocumentName': None,
                        'DocumentData': None,
                        'exists': False,
                        # We might need a fake ID or handle it by type in frontend
                        'DocumentID': f"new_{doc_type.replace(' ', '_')}" 
                    })
                    
            context['documents'] = all_documents_status

            # Extract Student Passport Photo for header summary
            student_photo_uri = None
            for doc in all_documents_status:
                if doc.get('DocumentType') == 'Student Passport Photo' and doc.get('exists'):
                    mime = doc.get('MimeType', 'image/jpeg')
                    student_photo_uri = f"data:{mime};base64,{doc.get('DocumentData')}"
                    break
            context['student_photo_uri'] = student_photo_uri

                
    except Exception as e:
        logger.error(f"Error fetching application detail: {e}")
        messages.error(request, "Error loading application details")
        return redirect('view_applications')
    
    return render(request, 'application_detail.html', context)


@custom_login_required
def update_student_section(request):
    """AJAX endpoint to update student information by section"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        student_code = data.get('student_code')
        section = data.get('section')
        fields = data.get('fields', {})
        updated_by = request.session.get('UserId') # Use UserId directly

        if not student_code or not section:
            return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})

        procedure_map = {
            'personal': 'proc_student_info_update',
            'contact': 'proc_student_contact_update',
            'parent': 'proc_student_parent_update',
            'previous_school': 'proc_student_previousschool_update',
            'admission': 'proc_student_admission_update'
        }

        procedure_name = procedure_map.get(section)
        if not procedure_name:
            return JsonResponse({'status': 'error', 'message': 'Invalid section'})

        params = [student_code]
        
        # Prepare parameters based on section
        # Prepare parameters based on section
        # Prepare parameters based on section
        if section == 'personal':
            params.extend([
                fields.get('FullName'),
                fields.get('Gender'),
                fields.get('DateOfBirth'),
                fields.get('Age'),
                fields.get('BloodGroup'),
                fields.get('Category'),
                fields.get('Religion'),
                fields.get('Nationality'),
                fields.get('MotherTongue'),
                fields.get('StudentAadhaar', '').replace('-', '')
            ])
        elif section == 'contact':
            params.extend([
                fields.get('ParentMobile', '').replace('-', ''),
                fields.get('AlternateNumber', '').replace('-', ''),
                fields.get('Email'),
                fields.get('PresentAddress'),
                fields.get('PermanentAddress'),
                fields.get('District'),
                fields.get('State'),
                fields.get('Country')
            ])
        elif section == 'parent':
            params.extend([
                fields.get('FatherName'),
                fields.get('FatherOccupation'),
                fields.get('FatherQualification'),
                fields.get('FatherAadhaar', '').replace('-', ''),
                fields.get('FatherMobile', '').replace('-', ''),
                fields.get('MotherName'),
                fields.get('MotherOccupation'),
                fields.get('MotherQualification'),
                fields.get('MotherAadhaar', '').replace('-', ''),
                fields.get('MotherMobile', '').replace('-', ''),
                fields.get('GuardianName'),
                fields.get('GuardianRelation'),
                fields.get('GuardianMobile', '').replace('-', '')
            ])
        elif section == 'previous_school':
            params.extend([
                fields.get('LastSchool'),
                fields.get('LastClass'),
                fields.get('TCNumber'),
                fields.get('MediumOfInstruction')
            ])
        elif section == 'admission':
            params.extend([
                fields.get('AdmissionClass'),
                fields.get('Section'),
                fields.get('Stream'),
                fields.get('ModeOfAdmission'),
                fields.get('AdmissionDate')
            ])

        params.append(updated_by)
        
        try:
            with connection.cursor() as cursor:
                # Construct execution string
                # Unlike MSSQL EXEC, we select from the function
                param_placeholders = ', '.join(['%s'] * len(params))
                sql = f"SELECT * FROM {procedure_name}({param_placeholders})"
                
                cursor.execute(sql, params)
                row = cursor.fetchone()
                
                if row:
                    status = row[0]
                    message = row[1] if len(row) > 1 else 'Success'
                    
                    if status == 'Success' or status == 'SUCCESS':
                        return JsonResponse({'status': 'success', 'message': message})
                    else:
                        return JsonResponse({'status': 'error', 'message': message})
                
                return JsonResponse({'status': 'error', 'message': 'Database update failed'})
                
        except Exception as e:
            logger.error(f"Error updating student info: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    except Exception as e:
        logger.error(f"Error processing update request: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})


@custom_login_required
def update_student_documents(request):
    """Handle document updates for student application"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        student_code = request.POST.get('student_code')
        updated_by = request.session.get('UserId')

        if not student_code:
            return JsonResponse({'status': 'error', 'message': 'Student code is missing'})

        # Get StudentID from Code
        student_id = None
        with connection.cursor() as cursor:
            cursor.execute("SELECT StudentID FROM Student WHERE StudentCode = %s", [student_code])
            res = cursor.fetchone()
            if res:
                student_id = res[0]

        if not student_id:
             return JsonResponse({'status': 'error', 'message': 'Invalid Student Code'})

        # We iterate over uploaded files. 
        # The frontend will send files with keys like 'document_FILES_ID' or just handle by DocumentID passed in form
        # Strategy: The form will likely have inputs named "document_<DocumentID>".
        
        files_updated = 0
        
        files_updated = 0
        
        # Iterate over posted files
        for key, file in request.FILES.items():
            # Validate each file
            from .utils import validate_uploaded_file
            is_valid, error_msg = validate_uploaded_file(file)
            if not is_valid:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': f'File validation failed for "{file.name}": {error_msg}'
                }, status=400)

            # Check if this is a signature file based on common naming patterns
            # We switched to using DocumentType as the reliable identifier for updates/inserts in the new plan
            
            if key.startswith('doc_'):
                try:
                    # The key suffix is the Document Type (sanitized or raw, handled by frontend)
                    # Ideally, frontend sends "doc_Student_Passport_Photo"
                    # We can also rely on a hidden input sending the real type name if the file input name is tricky.
                    
                    # Better approach: Look for corresponding "type_<key_suffix>" in POST data?
                    # Or just assume the suffix maps to type. 
                    # Let's see how frontend implements it. 
                    # Proposed frontend change: <input type="file" name="doc_{{ doc.DocumentType }}">
                    # So key will be "doc_Student Passport Photo" (spaces might be underscores in request?)
                    # Let's rely on a helper hidden field if possible, OR parse the key.
                    
                    # Actually, a cleaner way is:
                    # <input type="file" name="doc_file_{{ loop_index }}">
                    # <input type="hidden" name="doc_type_{{ loop_index }}" value="{{ doc.DocumentType }}">
                    
                    # BUT, to keep it simple with the current loop:
                    # Let's assume the key is "doc_" + DocumentType (with underscores for spaces)
                    
                    # Wait, the PLAN said "Ensure file inputs are named to associate with the correct type."
                    # Let's parse the key, assuming spaces are replaced by underscores or passed as is.
                    # Django request.FILES keys usually preserve the name attribute.
                    
                    doc_type_identifier = key[4:] # Remove "doc_"
                    # If we used underscores in HTML name for safety:
                    # doc_type = doc_type_identifier.replace('_', ' ') 
                    # This is risky if the type has real underscores.
                    
                    # Alternative: We look for the doc type in the POST data
                    # Let's retrieve the doc_type from a hidden field that matches the file key
                    # Frontend: <input type="hidden" name="type_of_doc_..." value="...">
                    
                    # Let's use the POST data to find the type.
                    # We can assume the input name IS the document type for simplicity, 
                    # but typically spaces in input names are valid but can be tricky.
                    # Let's assume the frontend sends 'doc_Student Passport Photo' exactly.
                    
                    doc_type = doc_type_identifier
                    
                    if not file: 
                        continue
                        
                    is_valid, message = validate_uploaded_file(file, ALLOWED_DOCUMENT_TYPES)
                    if not is_valid:
                        return JsonResponse({'status': 'error', 'message': f"File {file.name}: {message}"})
                    
                    doc_data = file.read() # Binary
                    doc_name = file.name
                    
                    with connection.cursor() as cursor:
                         # UPSERT LOGIC via PostgreSQL Function
                         cursor.execute("SELECT proc_student_document_upsert(%s, %s, %s, %s, %s)", 
                             [student_id, doc_type, doc_name, doc_data, str(updated_by)]
                         )
                         
                         files_updated += 1
                             
                except Exception as e:
                    logger.error(f"Error updating document {key}: {e}")
                    return JsonResponse({'status': 'error', 'message': f"Error updating file {doc_type}: {str(e)}"})

        if files_updated > 0:
            return JsonResponse({'status': 'success', 'message': f'{files_updated} document(s) updated successfully'})
        else:
            return JsonResponse({'status': 'info', 'message': 'No documents were updated'})

    except Exception as e:
        logger.error(f"Error in update_student_documents: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)})



@custom_login_required
def load_more_applications(request):
    """AJAX endpoint to load more applications"""
    school_id = request.session.get('SchoolID')
    page_number = safe_int(request.GET.get('page', 1))
    page_size = safe_int(request.GET.get('per_page', 10))
    
    try:
        with connection.cursor() as cursor:
            offset = (page_number - 1) * page_size
            cursor.execute(
                "SELECT * FROM proc_student_applications_get(%s, %s, %s)",
                [school_id, offset, page_size]
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            applications = [dict(zip(columns, row)) for row in rows]
            
            return JsonResponse({
                'success': True,
                'applications': applications,
                'has_next': len(applications) == page_size
            })
    except Exception as e:
        logger.error(f"Error loading more applications: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
def test_send_admission_email(request, student_code):
    """Test endpoint to send admission emails"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT Email, FullName, SchoolID FROM Student WHERE StudentCode = %s", [student_code])
            row = cursor.fetchone()
            if not row:
                return HttpResponse("Student not found", status=404)
            
            email, student_name, school_id = row
            
            email_data = {
                'email': email,
                'student_name': student_name,
                'student_code': student_code,
                'school_id': school_id,
            }
            
            send_admission_emails_async(email_data)
            return HttpResponse(f"Test email queued for {student_code}")
    except Exception as e:
        logger.error(f"Error in test email: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500)
