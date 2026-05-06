from django.core.mail.backends.smtp import EmailBackend
from django.db import connection
import logging
from core.smtp_encryption import decrypt_smtp_password

logger = logging.getLogger(__name__)

class DynamicEmailBackend(EmailBackend):
    """
    A custom SMTP email backend that loads settings from the database.
    Falls back to settings.py if no active configuration exists in the database.
    """
    def __init__(self, school_id=None, **kwargs):
        # Check if parameters are already provided (e.g. from get_connection arguments)
        # Only load default from database if 'host' is NOT explicitly provided.
        if not kwargs.get('host'):
            try:
                # Fetch default (SchoolID IS NULL) SMTP from database
                with connection.cursor() as cursor:
                    # Try fetching school specific config first if school_id provided
                    row = None
                    if school_id:
                        cursor.execute('''
                            SELECT "SMTPHost", "SMTPPort", "UseTLS", "UseSSL", 
                                   "Username", "Password", "FromEmail", "FromName"
                            FROM "SMTPConfiguration"
                            WHERE "SchoolID" = %s
                            AND "IsActive" = TRUE
                            AND "IsDeleted" = FALSE
                            LIMIT 1
                        ''', [school_id])
                        row = cursor.fetchone()
                        if row:
                            logger.info(f"DynamicEmailBackend: Loaded School SMTP configuration for SchoolID={school_id}")

                    # Fallback to default if no school specific config found
                    if not row:
                        cursor.execute('''
                            SELECT "SMTPHost", "SMTPPort", "UseTLS", "UseSSL", 
                                   "Username", "Password", "FromEmail", "FromName"
                            FROM "SMTPConfiguration"
                            WHERE "SchoolID" IS NULL
                            AND "ConfigName" = 'ShikshaWave Default'
                            AND "IsActive" = TRUE
                            AND "IsDeleted" = FALSE
                            LIMIT 1
                        ''')
                        row = cursor.fetchone()
                        if row:
                            logger.info(f"DynamicEmailBackend: Loaded 'ShikshaWave Default' SMTP configuration")
                    
                    if row:
                        host, port, tls, ssl, user, pwd, from_email, from_name = row
                        kwargs['host'] = host
                        kwargs['port'] = port
                        kwargs['use_tls'] = tls
                        kwargs['use_ssl'] = ssl
                        kwargs['username'] = user
                        kwargs['password'] = decrypt_smtp_password(pwd)
                        
                        # Store from_email context for later use if needed
                        self.from_email_config = from_email
                        self.from_name_config = from_name
                    else:
                        logger.warning("DynamicEmailBackend: No active default SMTP config found in database, using settings.py")
            except Exception as e:
                logger.error(f"DynamicEmailBackend: Error loading SMTP config from database: {e}")
            
        super().__init__(**kwargs)
