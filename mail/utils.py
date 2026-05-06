# mail/utils.py
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.core.signing import Signer, BadSignature
from datetime import datetime
import logging
import json
import threading

logger = logging.getLogger(__name__)
signer = Signer()


from core.smtp_encryption import decrypt_smtp_password


def get_smtp_connection_for_school(school_id):
    """
    Get SMTP connection for a specific school.
    Returns a Django email connection configured with school's SMTP settings,
    or None to use Django's default settings.
    
    Fallback order:
    1. School-specific SMTP configuration
    2. Default ShikshaWave SMTP (SchoolID IS NULL)
    3. Django settings (if no database config found)
    """
    try:
        with connection.cursor() as cursor:
            # Try to get school-specific or default SMTP config
            cursor.execute('''
                SELECT "SMTPHost", "SMTPPort", "UseTLS", "UseSSL", 
                       "Username", "Password", "FromEmail", "FromName"
                FROM "SMTPConfiguration"
                WHERE (
                    "SchoolID" = %s 
                    OR ("SchoolID" IS NULL AND "ConfigName" = 'ShikshaWave Default')
                )
                AND "IsActive" = TRUE
                AND "IsDeleted" = FALSE
                ORDER BY "SchoolID" NULLS LAST
                LIMIT 1
            ''', [school_id])
            
            row = cursor.fetchone()
            
            if row:
                smtp_host, smtp_port, use_tls, use_ssl, username, password, from_email, from_name = row
                
                # Decrypt password
                decrypted_password = decrypt_smtp_password(password)
                
                logger.info(f"Using SMTP config for school {school_id}: {smtp_host}:{smtp_port}")
                
                # Return connection object and from email info
                smtp_connection = get_connection(
                    host=smtp_host,
                    port=smtp_port,
                    username=username,
                    password=decrypted_password,
                    use_tls=use_tls,
                    use_ssl=use_ssl,
                    fail_silently=False
                )
                
                return {
                    'connection': smtp_connection,
                    'from_email': from_email,
                    'from_name': from_name
                }
        
        # No config found, return None to use Django settings
        logger.info(f"No SMTP config found for school {school_id}, using Django settings")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching SMTP config for school {school_id}: {e}", exc_info=True)
        return None


def get_default_smtp_from_email():
    """Get default from email from database or settings"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT "FromEmail", "FromName"
                FROM "SMTPConfiguration"
                WHERE "SchoolID" IS NULL 
                AND "ConfigName" = 'ShikshaWave Default'
                AND "IsActive" = TRUE
                AND "IsDeleted" = FALSE
                LIMIT 1
            ''')
            row = cursor.fetchone()
            if row:
                from_email, from_name = row
                if from_name:
                    return f"{from_name} <{from_email}>"
                return from_email
    except Exception as e:
        logger.error(f"Error fetching default SMTP from email: {e}")
    
    return settings.DEFAULT_FROM_EMAIL


def get_fallback_template(code):
    """Provides hardcoded fallback templates for critical system emails"""
    fallbacks = {
        'ADMISSION_ACKNOWLEDGMENT': {
            'subject': 'Admission Acknowledgment - {{ student_name }}',
            'text': 'Dear Parent, \n\nWe have received your admission application for {{ student_name }} for class {{ admission_class }}. \n\nRegistration Number: {{ student_code }}\nSchool: {{ school_name }}\n\nThank you for choosing us!',
            'html': '<h2>Admission Acknowledgment</h2><p>Dear Parent,</p><p>We have received your admission application for <strong>{{ student_name }}</strong> for class <strong>{{ admission_class }}</strong>.</p><p>Registration Number: <strong>{{ student_code }}</strong><br>School: <strong>{{ school_name }}</strong></p><p>Thank you for choosing us!</p>'
        },
        'PAYMENT_RECEIPT': {
            'subject': 'Payment Receipt - {{ receipt_number }}',
            'text': 'Dear Parent, \n\nThank you for your payment. \n\nReceipt Number: {{ receipt_number }}\nAmount: {{ amount_paid }}\nStudent: {{ student_name }}\n\nRegards,\n{{ school_name }}',
            'html': '<h2>Payment Receipt</h2><p>Dear Parent,</p><p>Thank you for your payment.</p><p>Receipt Number: <strong>{{ receipt_number }}</strong><br>Amount: <strong>{{ amount_paid }}</strong><br>Student: <strong>{{ student_name }}</strong></p><p>Regards,<br>{{ school_name }}</p>'
        },
        'EXAM_TIMETABLE_NOTIFICATION': {
            'subject': 'Exam Timetable - {{ exam_name }}',
            'text': 'Dear {{ student_name }},\n\nThe examination timetable for "{{ exam_name }}" has been released for class {{ class_name }}.\n\nSchedule Summary:\n{{ timetable_text }}\n\nBest of luck!\n{{ school_name }}',
            'html': '<h2>Exam Timetable Notification</h2><p>Dear <strong>{{ student_name }}</strong>,</p><p>The examination timetable for <strong>"{{ exam_name }}"</strong> has been released for class <strong>{{ class_name }}</strong>.</p><h3>Schedule Summary:</h3><div style="background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #e2e8f0;">{{ timetable_html|safe }}</div><p>Best of luck for your exams!</p><p>Regards,<br><strong>{{ school_name }}</strong></p>'
        },
        'ACCOUNT_BLOCKED': {
            'subject': 'Security Alert: Your ShikshaWave Account is Blocked',
            'text': 'Dear {{ full_name }},\n\nYour account has been temporarily blocked for 24 hours due to 3 consecutive failed login attempts. This is a security measure to protect your account.\n\nBlocked at: {{ blocked_at }}\nUsername: {{ user_name }}\n\nIf this was not you, please contact your school administrator immediately.\n\nRegards,\nTeam ShikshaWave',
            'html': '<div style="font-family:Poppins, sans-serif; padding:20px; color:#333;">' +
                    '<h2 style="color:#d32f2f;">Security Alert: Account Blocked</h2>' +
                    '<p>Dear <strong>{{ full_name }}</strong>,</p>' +
                    '<p>Your account has been temporarily blocked for <strong>24 hours</strong> due to 3 consecutive failed login attempts. This is a security measure to protect your account from unauthorized access.</p>' +
                    '<div style="background:#fff3e0; padding:15px; border-radius:8px; border-left:4px solid #ef6c00; margin:20px 0;">' +
                    '<strong>Blocked at:</strong> {{ blocked_at }}<br>' +
                    '<strong>Username:</strong> {{ user_name }}' +
                    '</div>' +
                    '<p>If this was you, please wait for the 24-hour period to expire or contact your school administrator for urgent assistance.</p>' +
                    '<p>If this was <strong>not you</strong>, please alert your school administrator immediately.</p>' +
                    '<hr style="border:none; border-top:1px solid #eee; margin:20px 0;">' +
                    '<p style="font-size:0.8rem; color:#666;">Regards,<br>Team ShikshaWave</p></div>'
        },
        'LOGIN_OTP': {
            'subject': '{{ school_name|default:"ShikshaWave" }} - Your Login OTP Code',
            'text': 'Dear {{ user_name }},\n\nYour Code is: {{ otp }}\n\nValid for {{ valid_minutes }} minutes.\nRequested from IP: {{ ip_address }}\n\nIf you did not request this, please ignore this email or contact security.\n\nRegards,\nTeam ShikshaWave',
            'html': '<div style="font-family:Poppins, sans-serif; max-width:500px; margin:0 auto; border:1px solid #eee; border-radius:12px; padding:30px; color:#333;">' +
                    '<div style="text-align:center; margin-bottom:20px;"><h2 style="color:#1976D2; margin:0;">Login Verification</h2></div>' +
                    '<p>Hello <strong>{{ user_name }}</strong>,</p>' +
                    '<p>Use the following One-Time Password (OTP) to complete your login process:</p>' +
                    '<div style="background:#f4f7fa; padding:20px; text-align:center; border-radius:10px; margin:25px 0;">' +
                    '<span style="font-size:32px; font-weight:bold; letter-spacing:8px; color:#1976D2;">{{ otp }}</span>' +
                    '</div>' +
                    '<p style="font-size:0.9rem; color:#666;">This code is valid for <strong>{{ valid_minutes }} minutes</strong>.</p>' +
                    '<p style="font-size:0.8rem; color:#999; margin-top:20px; border-top:1px solid #eee; padding-top:15px;">' +
                    'Requested from IP: {{ ip_address }}<br>If you did not request this code, please secure your account.</p></div>'
        },
        'PASSWORD_RESET_OTP': {
            'subject': '{{ school_name|default:"ShikshaWave" }} - Password Reset Code',
            'text': 'Dear {{ user_name }},\n\nYour Password Reset OTP is: {{ otp }}\n\nValid for {{ valid_minutes }} minutes.\nRequested from IP: {{ ip_address }}\n\nIf you did not request this change, please ignore this email.\n\nRegards,\nTeam ShikshaWave',
            'html': '<div style="font-family:Poppins, sans-serif; max-width:500px; margin:0 auto; border:1px solid #eee; border-radius:12px; padding:30px; color:#333;">' +
                    '<div style="text-align:center; margin-bottom:20px;"><h2 style="color:#D32F2F; margin:0;">Password Reset</h2></div>' +
                    '<p>Hello <strong>{{ user_name }}</strong>,</p>' +
                    '<p>You have requested to reset your password. Use the following OTP to continue:</p>' +
                    '<div style="background:#fdf2f2; padding:20px; text-align:center; border-radius:10px; margin:25px 0; border:1px solid #ffcdd2;">' +
                    '<span style="font-size:32px; font-weight:bold; letter-spacing:8px; color:#D32F2F;">{{ otp }}</span>' +
                    '</div>' +
                    '<p style="font-size:0.9rem; color:#666;">This code is valid for <strong>{{ valid_minutes }} minutes</strong>.</p>' +
                    '<p style="font-size:0.8rem; color:#999; margin-top:20px; border-top:1px solid #eee; padding-top:15px;">' +
                    'Requested from IP: {{ ip_address }}<br>If you did not request this, please ignore this email.</p></div>'
        },
        'PASSWORD_CHANGED_NOTIFICATION': {
            'subject': 'Security Update: Your Password Was Changed',
            'text': 'Hello {{ user_name }},\n\nThis is a confirmation that the password for your ShikshaWave account was recently changed.\n\nIf you did not make this change, please contact your administrator immediately.\n\nRegards,\nTeam ShikshaWave',
            'html': '<div style="font-family:Poppins, sans-serif; padding:20px; color:#333;">' +
                    '<h2 style="color:#2e7d32;">Password Changed Successfully</h2>' +
                    '<p>Hello <strong>{{ user_name }}</strong>,</p>' +
                    '<p>This email confirms that your account password has been successfully updated.</p>' +
                    '<p><strong>If you did not perform this action, please contact your school administrator or support immediately to secure your account.</strong></p>' +
                    '<hr style="border:none; border-top:1px solid #eee; margin:20px 0;">' +
                    '<p style="font-size:0.8rem; color:#666;">Regards,<br>Team ShikshaWave</p></div>'
        },
        'NEW_LOGIN_ALERT': {
            'subject': 'Security Alert: New Login to Your ShikshaWave Account',
            'text': 'Hello {{ user_name }},\n\nWe detected a new login to your account from {{ browser }} on {{ timestamp }} (IP: {{ ip_address }}).\n\nIf this was not you, please secure your account immediately.\n\nRegards,\nTeam ShikshaWave',
            'html': '<div style="font-family:Poppins, sans-serif; padding:20px; color:#333;">' +
                    '<h2 style="color:#1976D2;">New Login Alert</h2>' +
                    '<p>Hello <strong>{{ user_name }}</strong>,</p>' +
                    '<p>We detected a new login to your account from a new device or location.</p>' +
                    '<div style="background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #e2e8f0; margin:20px 0;">' +
                    '<strong>Time:</strong> {{ timestamp }}<br>' +
                    '<strong>Device:</strong> {{ browser }}<br>' +
                    '<strong>IP:</strong> {{ ip_address }}' +
                    '</div>' +
                    '<p>If this was you, you can safely ignore this email. If not, please <strong>change your password immediately</strong>.</p>' +
                    '<hr style="border:none; border-top:1px solid #eee; margin:20px 0;">' +
                    '<p style="font-size:0.8rem; color:#666;">Regards,<br>Team ShikshaWave</p></div>'
        },
        'DEFAULT': {
            'subject': 'Notification - {{ code }}',
            'text': 'This is an automated notification from ShikshaWave for code: {{ code }}.',
            'html': '<h2>Notification</h2><p>This is an automated notification from ShikshaWave for code: <strong>{{ code }}</strong>.</p>'
        }
    }
    return fallbacks.get(code) or fallbacks.get('DEFAULT')

def send_email_by_code(code, to_emails, placeholders=None, school_id=None, language='en', 
                       attachments=None, skip_tracking=False, is_async=True, template_row=None):
    """
    Send an email and log to EmailTracking.
    OPTIMIZED: Supports both async and sync execution to prevent double-threading.
    """
    if isinstance(to_emails, str):
        to_emails = [to_emails.strip()]
    to_emails = [email for email in to_emails if email]

    if not to_emails:
        logger.error("No valid recipient emails provided")
        return False

    # Actual sending logic
    def _execute_send():
        nonlocal placeholders
        # Enforce global SMTP for login/security codes
        effective_school_id = school_id
        security_codes = ['LOGIN_OTP', 'PASSWORD_RESET_OTP', 'ACCOUNT_BLOCKED', 'PASSWORD_CHANGED_NOTIFICATION', 'NEW_LOGIN_ALERT']
        if code in security_codes:
            effective_school_id = None
        
        try:
            # 0. Prep placeholders with common metadata
            if placeholders is None: placeholders = {}
            if code in security_codes:
                placeholders['school_name'] = 'ShikshaWave'
            placeholders.setdefault('current_year', datetime.now().year)
            placeholders.setdefault('code', code)
            
            # 1. Get SMTP configuration for school (with fallback to default)
            smtp_config = get_smtp_connection_for_school(effective_school_id)
            
            # 2. Check for File-Based Template Preference (Advanced System)
            template_file_pref = None
            try:
                # Use school_id for preference check, or 0 for security codes
                pref_school_id = 0 if code in security_codes else school_id
                if pref_school_id is not None:
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [pref_school_id, code])
                        pref_row = cursor.fetchone()
                        if pref_row and pref_row[0]:
                            template_file_pref = pref_row[0]
            except Exception as pref_e:
                logger.warning(f"Error checking template preference: {pref_e}")

            # 3. Fetch template if not provided (Database Fallback)
            row = template_row
            body_html_content = None
            
            # --- Initialize all template variables to avoid UnboundLocalError ---
            subject_template = None
            body_text_template = None
            body_html_template = None
            default_from = None
            cc = None
            bcc = None

            # --- A. Check for File-Based Template Content (Premium UI) ---
            if template_file_pref:
                from django.template.loader import render_to_string
                try:
                    body_html_content = render_to_string(template_file_pref, placeholders)
                    logger.info(f"Using file-based template for {code}: {template_file_pref}")
                except Exception as render_e:
                    logger.error(f"Error rendering template file {template_file_pref}: {render_e}")

            # --- B. Fetch Metadata & Base Templates from Database ---
            if not row:
                with connection.cursor() as cursor:
                    # First try school-specific template
                    cursor.execute("""
                        SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "Cc", "Bcc"
                        FROM "EmailTemplate"
                        WHERE "Code" = %s AND "SchoolId" = %s AND "Language" = %s AND "IsActive" = TRUE
                        LIMIT 1
                    """, [code, school_id, language])
                    row = cursor.fetchone()
                    
                    if not row:
                        cursor.execute("""
                            SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "Cc", "Bcc"
                            FROM "EmailTemplate"
                            WHERE "Code" = %s AND "SchoolId" IS NULL AND "Language" = %s
                            LIMIT 1
                        """, [code, language])
                        row = cursor.fetchone()

            # --- C. Unpack Database Metadata ---
            if row:
                subject_template = row[0]
                body_text_template = row[1]
                body_html_template = row[2]
                default_from = row[3]
                cc = row[4]
                bcc = row[5]

            # --- D. Apply Hardcoded Fallbacks if no DB record exists ---
            if not subject_template:
                logger.warning(f"No database metadata found for Code={code}, using hardcoded fallback.")
                fallback = get_fallback_template(code)
                subject_template = fallback['subject']
                body_text_template = body_text_template or fallback['text']
                body_html_template = body_html_template or fallback.get('html')

            # 3. Render templates
            ctx = Context(placeholders or {})
            
            # Always render subject (Essential)
            subject = Template(subject_template).render(ctx)
            
            # Render Text Body
            text_body = Template(body_text_template).render(ctx) if body_text_template else f"Email for {code}"
            
            # Use pre-rendered file content if available, otherwise render DB/fallback HTML
            if body_html_content:
                html_body = body_html_content
            else:
                html_body = Template(body_html_template).render(ctx) if body_html_template else None

            # 4. Email logic
            if smtp_config:
                # Prioritize SMTP config from_email over template default_from
                from_email = smtp_config.get('from_email') or default_from or settings.DEFAULT_FROM_EMAIL
                from_name = smtp_config.get('from_name')
                if from_name and from_email and '<' not in from_email:
                    from_email = f"{from_name} <{from_email}>"
            else:
                from_email = default_from or get_default_smtp_from_email()
            
            cc_list = [email.strip() for email in cc.split(',')] if cc else []
            bcc_list = [email.strip() for email in bcc.split(',')] if bcc else []
            email_connection = smtp_config.get('connection') if smtp_config else None

            logger.info(f"Dispatching email {code} from {from_email} to {to_emails} (Async: {is_async})")

            # 5. Tracking
            tracking_id = None
            if not skip_tracking:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO "EmailTracking" ("EmailCode", "ToEmail", "FromEmail", "Subject", "SchoolID", 
                                                       "EmailBody", "EmailHtmlBody", "Status", "CreatedAt", "IsActive")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Sending', CURRENT_TIMESTAMP, TRUE)
                            RETURNING "EmailTrackingID"
                        """, [code, ','.join(to_emails), from_email, subject, school_id, text_body, html_body])
                        res = cursor.fetchone()
                        tracking_id = res[0] if res else None
                except Exception as te:
                    logger.error(f"Tracking error: {te}")

            # 6. Send
            msg = EmailMultiAlternatives(
                subject=subject, body=text_body, from_email=from_email,
                to=to_emails, cc=cc_list, bcc=bcc_list, connection=email_connection
            )
            
            if html_body:
                msg.attach_alternative(html_body, "text/html")
            
            if attachments:
                for (filename, content, mime) in attachments:
                    msg.attach(filename, content, mime or 'application/pdf')
            
            msg.send()

            if tracking_id:
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE "EmailTracking" SET "Status" = \'Sent\', "CompletedAt" = CURRENT_TIMESTAMP WHERE "EmailTrackingID" = %s', [tracking_id])
            
            if email_connection:
                email_connection.close()

        except Exception as e:
            logger.error(f"Execution send error: {e}")
            if 'tracking_id' in locals() and tracking_id:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute('UPDATE "EmailTracking" SET "Status" = \'Failed\', "LastError" = %s WHERE "EmailTrackingID" = %s', [str(e), tracking_id])
                except: pass

    if is_async:
        thread = threading.Thread(target=_execute_send)
        thread.daemon = True
        thread.start()
    else:
        _execute_send()
        
    return True