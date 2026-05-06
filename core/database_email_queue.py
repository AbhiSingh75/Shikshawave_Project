"""
Database-based Email Queue System for ShikshaWave
This module handles background email sending using the EmailTracking database table
"""

import threading
import logging
import time
import json
import base64
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
from .pdf_generator import generate_pdf_from_template
from mail.utils import send_email_by_code
from .utils import number_to_words
from .email_tracking_models import EmailTracking, EmailTrackingManager

logger = logging.getLogger(__name__)

class DatabaseEmailQueue:
    """Database-based email queue for background processing"""
    
    def __init__(self):
        self.processing = False
        self.worker_thread = None
        self._lock = threading.Lock()
        self.wake_event = threading.Event()
        self.max_concurrent_emails = 5
        self.processing_interval = 2
    
    def add_email_task(self, email_code, to_email, placeholders=None, school_id=None, 
                      priority=5, max_attempts=3, user_id=None, student_code=None, 
                      receipt_number=None, has_attachments=False, attachment_details=None,
                      session_id=None, request_id=None, school_code=None):
        """Add email task to database queue"""
        
        try:
            # Fetch email template from database
            from django.template import Template, Context
            from django.conf import settings
            
            template_data = None
            with connection.cursor() as cursor:
                if school_id:
                    cursor.execute("""
                        SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom"
                        FROM "EmailTemplate"
                        WHERE "Code" = %s AND "Language" = 'en' AND "IsActive" = TRUE
                              AND "SchoolId" = %s
                    """, [email_code, school_id])
                    template_data = cursor.fetchone()
                
                if not template_data:
                    cursor.execute("""
                        SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom"
                        FROM "EmailTemplate"
                        WHERE "Code" = %s AND "Language" = 'en' AND "IsActive" = TRUE
                              AND "SchoolId" IS NULL
                    """, [email_code])
                    template_data = cursor.fetchone()
            
            from_email = None
            subject = None
            email_body = None
            email_html_body = None
            
            if template_data:
                subject_template, body_text_template, body_html_template, default_from = template_data
                ctx = Context(placeholders or {})
                from_email = default_from or settings.DEFAULT_FROM_EMAIL
                subject = Template(subject_template).render(ctx) if subject_template else None
                email_body = Template(body_text_template or "").render(ctx)
                email_html_body = Template(body_html_template or "").render(ctx)
                logger.info(f"Email template found for {email_code}: from={from_email}, subject={subject[:50] if subject else 'None'}")
            else:
                logger.warning(f"Email template NOT found for {email_code} with school_id={school_id}")
            
            # Get SchoolCode if not provided
            if school_id and not school_code:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT "SchoolCode" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                    row = cursor.fetchone()
                    if row:
                        school_code = row[0]
            
            email_task = EmailTrackingManager.create_email_task(
                email_code=email_code,
                to_email=to_email,
                placeholders=placeholders,
                school_id=school_id,
                priority=priority,
                max_attempts=max_attempts,
                user_id=user_id,
                student_code=student_code,
                receipt_number=receipt_number,
                has_attachments=has_attachments,
                attachment_details=attachment_details,
                from_email=from_email,
                subject=subject,
                email_body=email_body,
                email_html_body=email_html_body,
                session_id=session_id,
                request_id=request_id,
                school_code=school_code
            )
            
            logger.info(f"Email task {email_task.email_tracking_id} added to database queue for {to_email}")
            
            # Start worker if not already running
            if not self.processing:
                self.start_worker()
            
            # Wake up worker immediately
            self.wake_event.set()
            
            return email_task.email_tracking_id
            
        except Exception as e:
            logger.error(f"Failed to add email task to database: {str(e)}")
            raise
    
    def start_worker(self):
        """Start background email worker"""
        if self.processing:
            return
            
        self.processing = True
        self.wake_event.set()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Database email queue worker started")
    
    def _worker(self):
        """Background worker that processes email queue from database"""
        while self.processing:
            try:
                # Wait for event or timeout
                self.wake_event.wait(timeout=self.processing_interval)
                self.wake_event.clear()
                
                # Get pending emails from database using atomic claim
                pending_emails = EmailTrackingManager.claim_pending_emails(
                    max_emails=self.max_concurrent_emails
                )
                
                if pending_emails:
                    logger.info(f"Processing {len(pending_emails)} pending emails")
                    
                    # Process emails in parallel using threads
                    threads = []
                    for email_task in pending_emails:
                        thread = threading.Thread(
                            target=self._process_email_task, 
                            args=(email_task,),
                            daemon=True
                        )
                        thread.start()
                        threads.append(thread)
                    
                    # Wait for all threads to complete
                    for thread in threads:
                        thread.join(timeout=10) # Reduced timeout for faster processing
                    
                    # If we processed emails, check again immediately
                    self.wake_event.set()
                
            except Exception as e:
                logger.error(f"Email worker error: {str(e)}")
                time.sleep(2)
    
    def _process_email_task(self, email_task):
        """Process a single email task from database"""
        try:
            logger.info(f"Processing email task {email_task.email_tracking_id} for {email_task.to_email}")
            
            # Status is already set to 'Processing' by claim_pending_emails
            
            # Get placeholders
            
            # Get placeholders
            placeholders = email_task.placeholders_dict
            
            # Fetch and populate email template fields if not already set
            if not email_task.from_email or not email_task.subject:
                from django.template import Template, Context
                from django.conf import settings
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom"
                        FROM "EmailTemplate"
                        WHERE "Code" = %s AND ("SchoolId" IS NULL OR "SchoolId" = %s) AND "Language" = 'en' AND "IsActive" = TRUE
                        ORDER BY "SchoolId" DESC
                    """, [email_task.email_code, email_task.school_id])
                    template_row = cursor.fetchone()
                    if template_row:
                        ctx = Context(placeholders)
                        email_task.from_email = template_row[3] or settings.DEFAULT_FROM_EMAIL
                        email_task.subject = Template(template_row[0]).render(ctx) if template_row[0] else f'Email - {email_task.email_code}'
                        email_task.email_body = Template(template_row[1]).render(ctx) if template_row[1] else ''
                        email_task.email_html_body = Template(template_row[2]).render(ctx) if template_row[2] else ''
                        email_task.save()
            
            # Try to generate PDFs and send emails with attachments
            try:
                if email_task.has_attachments and email_task.email_code in ['ADMISSION_ACKNOWLEDGMENT', 'PAYMENT_RECEIPT', 'EMPLOYEE_REGISTRATION_CONFIRMATION', 'SUBSCRIPTION_ACTIVATION']:
                    # Generate PDFs for admission emails
                    if email_task.email_code == 'ADMISSION_ACKNOWLEDGMENT':
                        logger.info(f"Task {email_task.email_tracking_id}: Generating acknowledgment PDF...")
                        
                        # Get complete data from stored procedure (JSON-based, no nextset)
                        ack_data = {}
                        student_code = placeholders.get('student_code') or email_task.student_code
                        if student_code:
                            with connection.cursor() as cursor:
                                # Use the unified JSON-returning procedure
                                cursor.execute('SELECT proc_admission_acknowledgment_full_get(%s)', [student_code])
                                result = cursor.fetchone()
                                
                                if result and result[0]:
                                    data = result[0]
                                    # Handle JSON string parsing if necessary
                                    if isinstance(data, str):
                                        import json
                                        data = json.loads(data)
                                    
                                    if 'error' not in data:
                                        # Extract student info as the base acknowledgment data
                                        ack_data = data.get('student', {})
                                        # Merge other related data
                                        ack_data['instructions'] = data.get('instructions') or []
                                        ack_data['documents'] = data.get('documents') or []
                                        ack_data['fees'] = data.get('fees') or []
                                        ack_data['total_amount'] = data.get('total_amount') or 0
                                        
                                        # Handle school logo
                                        if ack_data.get('school_logo') and isinstance(ack_data['school_logo'], (bytes, memoryview)):
                                            logo_data = ack_data['school_logo']
                                            if isinstance(logo_data, memoryview):
                                                logo_data = logo_data.tobytes()
                                            ack_data['school_logo'] = f"data:image/png;base64,{base64.b64encode(logo_data).decode('utf-8')}"
                                        
                                        if not ack_data.get('current_date'):
                                            from datetime import datetime
                                            ack_data['current_date'] = datetime.now().strftime('%d-%b-%Y')
                        
                        # Get school's selected template from TemplateSettings
                        ack_template = 'core/document_templates/admission_acknowledgment/admission_acknowledgment_template1.html'
                        if email_task.school_id:
                            with connection.cursor() as cursor:
                                cursor.execute("""SELECT "TemplateFile" FROM "TemplateSettings" WHERE "SchoolID" = %s AND "TemplateType" = 'AdmissionAcknowledgment' AND "IsActive" = TRUE""", [email_task.school_id])
                                row = cursor.fetchone()
                                if row and row[0]:
                                    ack_template = row[0]
                        
                        ack_pdf = generate_pdf_from_template(ack_template, {'acknowledgment': ack_data})
                        
                        # Send acknowledgment email with PDF
                        logger.info(f"Task {email_task.email_tracking_id}: Sending acknowledgment email...")
                        send_email_by_code(
                            code='ADMISSION_ACKNOWLEDGMENT',
                            to_emails=email_task.to_email,
                            placeholders=ack_data,
                            school_id=email_task.school_id,
                            attachments=[(f"Acknowledgment-{student_code}.pdf", ack_pdf, 'application/pdf')],
                            skip_tracking=True,
                            is_async=False # Run synchronously in worker thread
                        )
                        
                    elif email_task.email_code == 'PAYMENT_RECEIPT':
                        logger.info(f"Task {email_task.email_tracking_id}: Generating receipt PDF...")
                        
                        receipt_data = {}
                        student_code = placeholders.get('student_code') or email_task.student_code
                        if student_code:
                            with connection.cursor() as cursor:
                                cursor.execute("SELECT * FROM proc_payment_receipt_get(NULL, %s::VARCHAR)", [student_code])
                                columns = [col[0] for col in cursor.description]
                                row = cursor.fetchone()
                                if row:
                                    receipt_data = dict(zip(columns, row))
                                    if receipt_data.get('school_logo'):
                                        receipt_data['school_logo'] = f"data:image/png;base64,{base64.b64encode(receipt_data['school_logo']).decode('utf-8')}"
                                    if receipt_data.get('student_code'):
                                        receipt_data['student_code'] = receipt_data['student_code']
                                    if not receipt_data.get('amount_paid') and receipt_data.get('PaidAmount'):
                                        receipt_data['amount_paid'] = receipt_data['PaidAmount']
                                    
                                    # Parse fee_breakdown if it's a string
                                    if receipt_data.get('fee_breakdown') and isinstance(receipt_data['fee_breakdown'], str):
                                        try:
                                            receipt_data['fee_breakdown'] = json.loads(receipt_data['fee_breakdown'])
                                        except:
                                            pass
                                
                                # If fee_breakdown is still not available, get it from fee structure
                                if not receipt_data.get('fee_breakdown'):
                                    logger.info(f"Task {email_task.email_tracking_id}: Fetching fee structure for breakdown...")
                                    cursor.execute("SELECT * FROM proc_student_fee_structure_get(NULL, %s::VARCHAR)", [student_code])
                                    fee_columns = [col[0] for col in cursor.description]
                                    fee_rows = cursor.fetchall()
                                    if fee_rows:
                                        fee_breakdown = []
                                        for fee_row in fee_rows:
                                            fee_item = dict(zip(fee_columns, fee_row))
                                            fee_breakdown.append({
                                                'fee_name': fee_item.get('fee_name', ''),
                                                'FeeTypeName': fee_item.get('fee_name', ''),
                                                'default_amount': float(fee_item.get('default_amount', 0) or 0),
                                                'discount_percentage': float(fee_item.get('discount_percentage', 0) or 0),
                                                'FinalAmount': float(fee_item.get('amount', 0) or 0),
                                                'amount': float(fee_item.get('amount', 0) or 0),
                                                'FeeMonth': fee_item.get('FeeMonth', '')
                                            })
                                        receipt_data['fee_breakdown'] = fee_breakdown
                                        logger.info(f"Task {email_task.email_tracking_id}: Found {len(fee_breakdown)} fee items")
                                
                                # Calculate total from fee_breakdown if available
                                if receipt_data.get('fee_breakdown'):
                                    try:
                                        fees = receipt_data['fee_breakdown']
                                        if isinstance(fees, list):
                                            receipt_data['total_amount'] = sum(float(f.get('FinalAmount', 0) or f.get('amount', 0) or 0) for f in fees)
                                    except:
                                        receipt_data['total_amount'] = 0
                                else:
                                    receipt_data['total_amount'] = float(receipt_data.get('amount_paid', 0) or 0)
                        
                        # Override with latest payment info from placeholders if available
                        if placeholders.get('receipt_number'):
                            receipt_data['receipt_number'] = placeholders.get('receipt_number')
                        if placeholders.get('payment_date'):
                            receipt_data['payment_date'] = placeholders.get('payment_date')
                        if placeholders.get('payment_mode'):
                            receipt_data['payment_mode'] = placeholders.get('payment_mode')
                        if placeholders.get('amount_paid'):
                            receipt_data['amount_paid'] = placeholders.get('amount_paid')
                        if placeholders.get('transaction_ref'):
                            receipt_data['transaction_ref'] = placeholders.get('transaction_ref')
                        
                        # Get school's selected template
                        receipt_template = 'core/document_templates/payment_receipt/payment_success.html'
                        if email_task.school_id:
                            with connection.cursor() as cursor:
                                # Get school info for the receipt
                                cursor.execute('SELECT "SchoolName", "SchoolLogo" FROM "SchoolMaster" WHERE "SchoolID" = %s', [email_task.school_id])
                                school_row = cursor.fetchone()
                                if school_row:
                                    receipt_data['school_name'] = school_row[0]
                                    if school_row[1]:
                                        logo_data = school_row[1]
                                        if isinstance(logo_data, memoryview):
                                            logo_data = logo_data.tobytes()
                                        receipt_data['school_logo'] = f"data:image/png;base64,{base64.b64encode(logo_data).decode('utf-8')}"
                                
                                # Get template setting
                                cursor.execute("""SELECT "TemplateFile" FROM "TemplateSettings" WHERE "SchoolID" = %s AND "TemplateType" = 'PaymentReceipt' AND "IsActive" = TRUE""", [email_task.school_id])
                                row = cursor.fetchone()
                                if row and row[0]:
                                    receipt_template = row[0]
                        
                        logger.info(f"Task {email_task.email_tracking_id}: Receipt data prepared - fee_breakdown has {len(receipt_data.get('fee_breakdown', []))} items")
                        rcpt_pdf = generate_pdf_from_template(receipt_template, {'payment_receipt': receipt_data})
                        
                        # Send payment receipt email with PDF
                        logger.info(f"Task {email_task.email_tracking_id}: Sending receipt email...")
                        send_email_by_code(
                            code='PAYMENT_RECEIPT',
                            to_emails=email_task.to_email,
                            placeholders=receipt_data,
                            school_id=email_task.school_id,
                            attachments=[(f"Receipt-{student_code}.pdf", rcpt_pdf, 'application/pdf')],
                            skip_tracking=True,
                            is_async=False # Run synchronously in worker thread
                        )
                        
                    elif email_task.email_code == 'EMPLOYEE_REGISTRATION_CONFIRMATION':
                        logger.info(f"Task {email_task.email_tracking_id}: Generating employee job letter PDF...")
                        
                        # Get attachment details from the email task
                        attachment_details = email_task.attachment_details_dict
                        logger.info(f"Task {email_task.email_tracking_id}: Attachment details keys: {list(attachment_details.keys()) if attachment_details else 'None'}")
                        
                        job_letter_context = None
                        job_letter_template = None
                        
                        if attachment_details and 'job_letter' in attachment_details:
                            job_letter_info = attachment_details['job_letter']
                            job_letter_context = job_letter_info.get('context', {})
                            job_letter_template = job_letter_info.get('template')
                            logger.info(f"Task {email_task.email_tracking_id}: Job letter template found in metadata: {job_letter_template}")
                        else:
                            logger.warning(f"Task {email_task.email_tracking_id}: No 'job_letter' key in attachment_details")
                        
                        # Generate job letter PDF
                        from .pdf_generator import generate_employee_job_letter_pdf
                        logger.info(f"Task {email_task.email_tracking_id}: Calling PDF generator with template: {job_letter_template}")
                        job_letter_pdf = generate_employee_job_letter_pdf(job_letter_context, job_letter_template)
                        
                        # Send employee registration email with job letter PDF
                        logger.info(f"Task {email_task.email_tracking_id}: Sending employee registration email...")
                        send_email_by_code(
                            code='EMPLOYEE_REGISTRATION_CONFIRMATION',
                            to_emails=email_task.to_email,
                            placeholders=placeholders,
                            school_id=email_task.school_id,
                            attachments=[(f"Job_Letter_{placeholders.get('employee_code')}.pdf", job_letter_pdf, 'application/pdf')],
                            skip_tracking=True,
                            is_async=False # Run synchronously in worker thread
                        )
                        
                    elif email_task.email_code == 'SUBSCRIPTION_ACTIVATION':
                        logger.info(f"Task {email_task.email_tracking_id}: Generating subscription invoice PDF via procedure...")
                        
                        placeholder_data = email_task.placeholders_dict
                        subscriber_id = placeholder_data.get('subscriber_id')
                        
                        invoice_data = {}
                        if subscriber_id:
                            with connection.cursor() as cursor:
                                # CALL THE NEW UNIFIED PROCEDURE
                                cursor.execute('SELECT "proc_subscription_invoice_full_get"(%s)', [subscriber_id])
                                result = cursor.fetchone()
                                
                                if result and result[0]:
                                    data = result[0]
                                    invoice_master = data.get('invoice_master', {})
                                    school_details = data.get('school_details', {})
                                    plan_details = data.get('plan_details', {})
                                    items = data.get('invoice_items') or []
                                    
                                    # Fetch Active Brand Profile
                                    brand_data = {}
                                    try:
                                        with connection.cursor() as brand_cursor:
                                            brand_cursor.execute('SELECT "Proc_BrandProfile_GET"()')
                                            brand_data = brand_cursor.fetchone()[0] or {}
                                    except Exception as brand_err:
                                        logger.warning(f"Could not fetch Brand Profile: {brand_err}")

                                    # Convert Brand Logo to Data URI (from DB base64 string returned by Proc)
                                    logo_uri = '/static/images/ShikshaWave_Logo.png'
                                    if brand_data.get('BrandLogo'):
                                        logo_uri = f"data:image/png;base64,{brand_data['BrandLogo']}"
                                    else:
                                        # Fallback to static file if not in DB
                                        try:
                                            from django.conf import settings
                                            import os
                                            logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'ShikshaWave_Logo.png')
                                            if os.path.exists(logo_path):
                                                with open(logo_path, "rb") as image_file:
                                                    logo_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                                                    logo_uri = f"data:image/png;base64,{logo_base64}"
                                        except Exception as logo_err:
                                            logger.warning(f"Could not convert fallback logo to Data URI: {logo_err}")

                                    # Fetch Active Tax Metadata for Labeling
                                    with connection.cursor() as tax_cursor:
                                        tax_cursor.execute('SELECT "Proc_TaxMaster_GET"(NULL, TRUE)')
                                        tax_meta = tax_cursor.fetchone()[0]
                                    
                                    if isinstance(tax_meta, str):
                                        tax_meta = json.loads(tax_meta)
                                    
                                    tax_label = "Tax (GST)"
                                    if tax_meta and isinstance(tax_meta, list) and len(tax_meta) > 0:
                                        t_name = tax_meta[0].get('TaxName', 'GST')
                                        t_percent = tax_meta[0].get('TaxPercentage', 18)
                                        tax_label = f"{t_name} ({t_percent}%)"

                                    # 4. Resolve Template Preference (Always Global for Subscription Invoice)
                                    template_path = 'core/document_templates/subscription_invoice/template1.html' # Default Fallback
                                    try:
                                        with connection.cursor() as pref_cursor:
                                            # Strictly use Global branding (SchoolID=0) for Subscription Invoices
                                            pref_cursor.execute("""
                                                SELECT "TemplateFile" FROM "TemplateSettings" 
                                                WHERE "TemplateType" = 'SubscriptionInvoice' 
                                                  AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                                                  AND "SchoolID" = 0
                                                LIMIT 1
                                            """)
                                            pref_row = pref_cursor.fetchone()
                                            if pref_row and pref_row[0]:
                                                template_path = pref_row[0]
                                    except Exception as pref_err:
                                        logger.warning(f"Template resolve error for email task: {pref_err}")

                                    # Map to Rich Template Context (Standardized for Template 1-14)
                                    tax_rate = 18.0
                                    try:
                                        if tax_meta and isinstance(tax_meta, list) and len(tax_meta) > 0:
                                            tax_rate = float(tax_meta[0].get('TaxPercentage', 18))
                                    except: pass

                                    tax_total = float(invoice_master.get('TaxAmount', 0))
                                    final_total = float(invoice_master.get('FinalAmount', 0))

                                    rich_invoice_context = {
                                        'invoice': {
                                            'InvoiceNumber': invoice_master.get('InvoiceNumber'),
                                            'FormattedDate': datetime.strptime(invoice_master['InvoiceDate'], '%Y-%m-%dT%H:%M:%S').strftime('%d %b, %Y') if invoice_master.get('InvoiceDate') else '',
                                            'TotalAmount': float(invoice_master.get('TotalAmount', 0)),
                                            'FinalAmount': final_total,
                                            'TaxAmount': tax_total,
                                            'CGST_Rate': tax_rate / 2,
                                            'SGST_Rate': tax_rate / 2,
                                            'CGST_Amount': tax_total / 2,
                                            'SGST_Amount': tax_total / 2,
                                            'FinalAmountInWords': number_to_words(final_total),
                                            'DiscountAmount': float(invoice_master.get('DiscountAmount', 0)),
                                            'PaymentStatus': invoice_master.get('PaymentStatus', 'Paid')
                                        },
                                        'school': {
                                            'SchoolName': school_details.get('SchoolName'),
                                            'SchoolCode': school_details.get('SchoolCode'),
                                            'Address': school_details.get('Address'),
                                            'District': school_details.get('District'),
                                            'State': school_details.get('State'),
                                            'Country': school_details.get('Country'),
                                            'Phone': school_details.get('Phone')
                                        },
                                        'plan': {
                                            'PlanName': plan_details.get('PlanName'),
                                            'SubscriptionNo': plan_details.get('SubscriptionNo'),
                                            'FormattedStart': datetime.strptime(plan_details['StartDate'], '%Y-%m-%d').strftime('%d %b, %Y') if plan_details.get('StartDate') else '',
                                            'FormattedEnd': datetime.strptime(plan_details['EndDate'], '%Y-%m-%d').strftime('%d %b, %Y') if plan_details.get('EndDate') else '',
                                        },
                                        'items': items,
                                        'brand': brand_data,
                                        'footer': {
                                            'Disclaimer': invoice_data.get('footer_info', {}).get('Disclaimer', 'This is an electronically generated invoice.'),
                                            'CopyrightNotice': invoice_data.get('footer_info', {}).get('CopyrightNotice', f'© {timezone.now().year} {brand_data.get("BrandName", "ShikshaWave")}'),
                                            'TermsAndConditions': invoice_data.get('footer_info', {}).get('TermsAndConditions'),
                                            'LegalDeclaration': invoice_data.get('footer_info', {}).get('LegalDeclaration')
                                        },
                                        'tax_label': tax_label,
                                        'current_year': timezone.now().year,
                                        'subscription_id': subscriber_id
                                    }
                        
                        inv_pdf = generate_pdf_from_template(template_path, rich_invoice_context)

                        
                        # Send email
                        from mail.utils import send_email_by_code
                        send_email_by_code(
                            code='SUBSCRIPTION_ACTIVATION',
                            to_emails=email_task.to_email,
                            placeholders=placeholder_data,
                            school_id=email_task.school_id,
                            attachments=[(f"Invoice_{invoice_data.get('invoice_number', 'INV').replace('/', '_')}.pdf", inv_pdf, 'application/pdf')],
                            skip_tracking=True,
                            is_async=False
                        )
                else:
                    # Send email without PDF attachments
                    logger.info(f"Task {email_task.email_tracking_id}: Sending email without attachments...")
                    send_email_by_code(
                        code=email_task.email_code,
                        to_emails=email_task.to_email,
                        placeholders=placeholders,
                        school_id=email_task.school_id,
                        skip_tracking=True,
                        is_async=False # Run synchronously in worker thread
                    )
                
                # Mark as sent
                email_task.mark_as_sent()
                logger.info(f"Task {email_task.email_tracking_id}: Email sent successfully to {email_task.to_email}")
                
            except Exception as pdf_error:
                logger.warning(f"Task {email_task.email_tracking_id}: PDF generation failed, trying without attachments: {str(pdf_error)}")
                
                try:
                    # Send email without PDF attachments as fallback
                    send_email_by_code(
                        code=email_task.email_code,
                        to_emails=email_task.to_email,
                        placeholders=placeholders,
                        school_id=email_task.school_id,
                        skip_tracking=True,
                        is_async=False # Run synchronously in worker thread
                    )
                    
                    # Mark as sent
                    email_task.mark_as_sent()
                    logger.info(f"Task {email_task.email_tracking_id}: Email sent without PDFs to {email_task.to_email}")
                    
                except Exception as email_error:
                    # Mark as failed
                    email_task.mark_as_failed(
                        error_message=str(email_error),
                        error_details=f"PDF Error: {str(pdf_error)} | Email Error: {str(email_error)}"
                    )
                    logger.error(f"Task {email_task.email_tracking_id}: Email sending failed completely: {str(email_error)}")
                
        except Exception as email_error:
            logger.error(f"Task {email_task.email_tracking_id}: Email processing failed: {str(email_error)}")
            email_task.mark_as_failed(
                error_message=str(email_error),
                error_details=f"Processing error: {str(email_error)}"
            )
    
    def get_queue_status(self):
        """Get current queue status from database"""
        try:
            # Check if EmailTracking table exists
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'EmailTracking'
                """)
                table_exists = cursor.fetchone()[0] > 0
                
                if not table_exists:
                    logger.error("EmailTracking table does not exist")
                    return {
                        'total_tasks': 0,
                        'pending': 0,
                        'processing': 0,
                        'completed': 0,
                        'failed': 0,
                        'permanently_failed': 0,
                        'worker_running': self.processing,
                        'email_types': {},
                        'error': 'EmailTracking table not found. Please run the setup script.'
                    }
            
            stats = EmailTrackingManager.get_email_statistics()
            
            # Calculate totals
            total_tasks = sum(stat['total'] for stat in stats.values())
            pending = sum(stat['pending'] for stat in stats.values())
            processing = sum(stat['processing'] for stat in stats.values())
            completed = sum(stat['sent'] for stat in stats.values())
            failed = sum(stat['failed'] for stat in stats.values())
            permanently_failed = sum(stat['permanently_failed'] for stat in stats.values())
            
            return {
                'total_tasks': total_tasks,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed,
                'permanently_failed': permanently_failed,
                'worker_running': self.processing,
                'email_types': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {
                'total_tasks': 0,
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'permanently_failed': 0,
                'worker_running': self.processing,
                'email_types': {},
                'error': f'Database error: {str(e)}'
            }
    
    def get_recent_emails(self, limit=20):
        """Get recent email activity from database"""
        try:
            return EmailTrackingManager.get_recent_emails(limit=limit)
        except Exception as e:
            logger.error(f"Error getting recent emails: {str(e)}")
            return []
    
    def retry_failed_emails(self, max_retries=10):
        """Manually retry failed emails"""
        try:
            failed_emails = EmailTracking.objects.filter(
                is_active=True,
                status='Failed',
                attempt_count__lt=models.F('max_attempts')
            )[:max_retries]
            
            retry_count = 0
            for email_task in failed_emails:
                if email_task.can_retry():
                    email_task.status = 'Pending'
                    email_task.next_retry_at = None
                    email_task.save()
                    retry_count += 1
            
            logger.info(f"Retried {retry_count} failed emails")
            return retry_count
            
        except Exception as e:
            logger.error(f"Error retrying failed emails: {str(e)}")
            return 0
    
    def cleanup_old_emails(self, days=30):
        """Clean up old completed emails"""
        try:
            return EmailTrackingManager.cleanup_old_emails(days=days)
        except Exception as e:
            logger.error(f"Error cleaning up old emails: {str(e)}")
            return 0
    
    def stop_worker(self):
        """Stop the email worker"""
        self.processing = False
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        logger.info("Database email queue worker stopped")

# Global database email queue instance
database_email_queue = DatabaseEmailQueue()

def send_admission_emails_async_database(email_data):
    """Send admission emails asynchronously using database queue"""
    try:
        payment_receipt = email_data.get('payment_receipt', {})
        
        # Create acknowledgment email task with ALL fields from session
        ack_task_id = database_email_queue.add_email_task(
            email_code='ADMISSION_ACKNOWLEDGMENT',
            to_email=email_data.get('email'),
            placeholders=payment_receipt,
            school_id=email_data.get('school_id'),
            priority=5,
            user_id=email_data.get('user_id'),
            student_code=email_data.get('student_code'),
            has_attachments=True,
            session_id=email_data.get('session_id'),
            request_id=email_data.get('request_id'),
            school_code=email_data.get('school_code')
        )
        
        # Create payment receipt email task with ALL fields
        receipt_task_id = database_email_queue.add_email_task(
            email_code='PAYMENT_RECEIPT',
            to_email=email_data.get('email'),
            placeholders=payment_receipt,
            school_id=email_data.get('school_id'),
            priority=5,
            user_id=email_data.get('user_id'),
            student_code=email_data.get('student_code'),
            receipt_number=payment_receipt.get('receipt_number'),
            has_attachments=True,
            session_id=email_data.get('session_id'),
            request_id=email_data.get('request_id'),
            school_code=email_data.get('school_code')
        )
        
        logger.info(f"Created email tasks: Acknowledgment={ack_task_id}, Receipt={receipt_task_id}")
        return [ack_task_id, receipt_task_id]
        
    except Exception as e:
        logger.error(f"Failed to create email tasks: {str(e)}")
        raise
