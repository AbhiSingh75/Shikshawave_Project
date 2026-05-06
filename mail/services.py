import logging
from django.db import connection
from django.template import Template, Context
from django.core.mail import EmailMultiAlternatives, get_connection

logger = logging.getLogger(__name__)

def send_email_from_template(code, school_id, language, placeholders):
    # Robust school_id conversion
    try:
        school_id_int = int(school_id) if school_id else None
    except (ValueError, TypeError):
        school_id_int = None
        logger.warning(f"Invalid school_id provided to send_email_from_template: {school_id}")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", "Cc", "Bcc"
            FROM "EmailTemplate"
            WHERE "Code" = %s
              AND ("SchoolId" IS NULL OR "SchoolId" = %s)
              AND "Language" = %s
              AND "IsActive" = TRUE
            ORDER BY "SchoolId" DESC
        """, [code, school_id_int, language])
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"No active email template found for Code={code}, SchoolId={school_id}, Lang={language}")

        subject_template, body_text_template, body_html_template, default_from, cc, bcc = row

        # Check for file template preference for specific codes
        file_template_type_map = {
            'STUDENT_PROMOTION': 'PromotionEmail'
        }
        
        template_file = None
        if code in file_template_type_map and school_id_int:
            try:
                mapped_type = file_template_type_map[code]
                # Use the stored procedure to get preference (handles school vs default fallback)
                cursor.execute('SELECT "TemplateFile" FROM "Proc_Template_Preference_Get"(%s) WHERE "TemplateType" = %s', [school_id_int, mapped_type])
                pref_row = cursor.fetchone()
                if pref_row and pref_row[0]:
                    template_file = pref_row[0]
                    logger.info(f"Using template file {template_file} for email {code}")
            except Exception as e:
                 logger.error(f"Error retrieving template preference for {code}: {e}")
                 # Log warning but proceed with DB template
                 pass

        # Render templates
        subject = Template(subject_template).render(Context(placeholders))
        body_text = Template(body_text_template).render(Context(placeholders))
        
        if template_file:
            from django.template.loader import render_to_string
            try:
                # Add school_name and other missing defaults to placeholders if not present
                if 'school_name' not in placeholders and school_id_int:
                    cursor.execute('SELECT "SchoolName" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id_int])
                    s_row = cursor.fetchone()
                    if s_row:
                        placeholders['school_name'] = s_row[0]
                
                body_html = render_to_string(template_file, placeholders)
                logger.info(f"Successfully rendered template file {template_file}")
            except Exception as e:
                logger.error(f"Failed to render template file {template_file}: {e}")
                # Fallback to DB template if file rendering fails
                body_html = Template(body_html_template).render(Context(placeholders)) if body_html_template else None
        else:
            logger.info(f"No template file found for {code}, using database template")
            body_html = Template(body_html_template).render(Context(placeholders)) if body_html_template else None

    # Prepare and send email
    try:
        # Use DynamicEmailBackend with school_id to load correct SMTP settings
        email_connection = get_connection(backend='mail.backend.DynamicEmailBackend', school_id=school_id)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=default_from,
            to=[placeholders.get("to")],
            cc=cc.split(",") if cc else [],
            bcc=bcc.split(",") if bcc else [],
            connection=email_connection
        )
        if body_html:
            email.attach_alternative(body_html, "text/html")
    
        email.send()
    except Exception as e:
        # Re-raise or log, but ensure we don't crash if SMTP fails? 
        # The caller (view) has try/catch, so re-raising is fine or letting it bubble up.
        # But 'connection' variable might fail if get_connection fails? No, get_connection is lazy usually for backend loading.
        # But backend.__init__ does DB calls.
        raise e
