# core/auth_utils.py
from datetime import datetime, timedelta
import random
import logging
from django.db import connection
from django.conf import settings
from django.core.mail import send_mail
from mail.utils import send_email_by_code
from .branding_utils import get_branding_title

logger = logging.getLogger(__name__)

def _get_client_ip(request):
    """
    Extracts the client IP address from the Django request object.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def generate_and_store_otp(identifier, purpose, request):
    """
    Generate an OTP, store it in OTPRecords, and send it via email.
    """
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now() + timedelta(minutes=15)
    ip_address = _get_client_ip(request)
    device_info = request.META.get('HTTP_USER_AGENT', 'Unknown')[:255]

    try:
        # Fetch user details including profile and school logo
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u."UserName", 
                    u."Email", 
                    s."SchoolName", 
                    p."ProfileName",
                    u."ProfileID"
                FROM "UserMaster" u 
                LEFT JOIN "SchoolMaster" s ON u."SchoolID" = s."SchoolID" 
                LEFT JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                WHERE u."UserName" = %s OR u."UserCode" = %s OR u."Email" = %s
            """, [identifier, identifier, identifier])
            row = cursor.fetchone()
            if not row:
                raise Exception("User not found")
            user_name, email, school_name, profile, profile_id = row
            if not email:
                raise Exception("No email address associated with this account")

        # Store OTP in database
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO "OTPRecords" 
                ("Identifier", "OTP", "Purpose", "CreatedAt", "ExpiresAt", "IPAddress", "DeviceInfo")
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                identifier,
                otp,
                purpose,
                datetime.now(),
                expires_at,
                ip_address,
                device_info
            ])

        # Send OTP via email using template file
        try:
            # Determine Branding (ShikshaWave vs. Institution Name)
            branding_name = get_branding_title(profile_id, school_name)
            
            # Determine Header Title based on purpose
            header_title = "Account Recovery" if purpose == 'password_reset' else "Sign-In Authorization"
            
            placeholders = {
                'user_name': user_name,
                'login_id': identifier,
                'otp': otp,
                'valid_minutes': 15,
                'ip_address': ip_address,
                'school_name': branding_name,
                'profile': profile,
                'school_logo': None,  # Logo images removed as per user request
                'header_title': header_title,
                'browser': device_info,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"Sending OTP email to {email}")
            # Map purpose to specific EmailCode for templates and tracking
            email_code = 'PASSWORD_RESET_OTP' if purpose == 'password_reset' else 'LOGIN_OTP'
            
            send_email_by_code(
                code=email_code,
                to_emails=email,
                placeholders=placeholders
            )
            logger.info(f"OTP email queued for {email}")
        except Exception as e:
            logger.error(f"Failed to send OTP email for {email}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to send OTP email: {str(e)}")

        return otp

    except Exception as e:
        logger.error(f"Failed to generate or send OTP for {identifier}: {str(e)}", exc_info=True)
        raise
    
def verify_otp(identifier, otp, purpose):
    try:
        with connection.cursor() as cursor:
            # Verify OTP
            cursor.execute("""
                SELECT "Id" FROM "OTPRecords" 
                WHERE "Identifier" = %s 
                  AND "OTP" = %s 
                  AND "Purpose" = %s 
                  AND "IsUsed" = FALSE 
                  AND "ExpiresAt" > CURRENT_TIMESTAMP
            """, [identifier, otp, purpose])
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"Invalid or expired OTP for {identifier}: {otp}")
                return False, None

            # Mark OTP as used
            cursor.execute("""
                UPDATE "OTPRecords" 
                SET "IsUsed" = TRUE,
                    "UsedAt" = CURRENT_TIMESTAMP
                WHERE "Id" = %s
            """, [row[0]])

            # Fetch user data
            cursor.execute("""
                SELECT 
                    u."UserID",
                    u."UserName" AS FullName,
                    u."ProfileID",
                    p."ProfileName",
                    u."SchoolID",
                    s."SchoolName",
                    s."SchoolLogo",
                    u."UserPhoto"
                FROM "UserMaster" u
                INNER JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
                LEFT JOIN "SchoolMaster" s ON u."SchoolID" = s."SchoolID"
                WHERE (u."UserName" = %s OR u."UserCode" = %s or u."Email" = %s)
                  AND u."IsActive" = TRUE
                  AND u."IsDeleted" IS NOT TRUE
            """, [identifier, identifier,identifier])
            user_row = cursor.fetchone()

            if not user_row:
                logger.error(f"User not found for {identifier} after OTP verification")
                return False, None

            user_data = {
                'user_id': user_row[0],
                'user_name': user_row[1],
                'profile_id': user_row[2],
                'profile_name': user_row[3],
                'school_id': user_row[4],
                'school_name': user_row[5],
                'school_logo': user_row[6],
                'user_photo': user_row[7]
            }
            logger.info(f"OTP verified successfully for {identifier}")
            return True, user_data

    except Exception as e:
        logger.error(f"OTP verification error for {identifier}: {str(e)}", exc_info=True)
        return False, None