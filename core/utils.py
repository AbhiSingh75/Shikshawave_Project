import logging
import base64
import json
import os
from datetime import datetime
from django.db import connection
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

# File upload validation constants
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Config / constants
SESSION_COOKIE_NAME = "shsw_sess"         # custom session cookie name
SESSION_LIFETIME_SECONDS = 3600           # 1 hour
OTP_COOKIE_NAME = 'shsw_otp_token'        # OTP verification cookie
OTP_COOKIE_MAX_AGE = 900                  # 15 minutes (match OTP expiry)
ERP_DEFAULT_LOGO_STATIC = "/static/images/ShikshaWave_Logo.png"

def sanitize_input(value):
    """Basic input sanitization to prevent common injection/XSS attempts"""
    if not isinstance(value, str):
        return value
    return value.strip()

def safe_json_obj(obj):
    """
    Convert `obj` into a JSON-serializable Python structure using
    DjangoJSONEncoder (which handles Decimal, date, datetime, UUID, etc.).
    Returns the Python object (not a JSON string) ready for session storage or DB.
    """
    return json.loads(json.dumps(obj, cls=DjangoJSONEncoder))

def get_school_dropdown():
    """
    Universal function to get school dropdown data.
    Returns list of dictionaries with SchoolID and SchoolName.
    """
    try:
        with connection.cursor() as cursor:
            # PostgreSQL compatible query with quoted identifiers
            cursor.execute("""
                SELECT "SchoolID", "SchoolName", "SchoolCode" 
                FROM "SchoolMaster" 
                WHERE "IsDeleted" = FALSE 
                ORDER BY "SchoolName"
            """)
            
            schools = []
            for row in cursor.fetchall():
                code = row[2] if len(row) > 2 and row[2] else ''
                name = row[1]
                display_name = f"[{code}] {name}" if code else name
                
                schools.append({
                    'SchoolID': row[0],
                    'SchoolName': name,
                    'SchoolCode': code,
                    'DisplayName': display_name
                })
            
            return schools
            
    except Exception as e:
        logger.error(f"Error getting school dropdown data: {e}")
        return []

def get_class_dropdown(school_id=None):
    """
    Universal function to get class dropdown data for a specific school.
    Returns list of dictionaries with ClassID and ClassName.
    """
    try:
        with connection.cursor() as cursor:
            if school_id:
                # PostgreSQL compatible query with quoted identifiers
                cursor.execute("""
                    SELECT "ClassID", "ClassName" FROM "ClassMaster" 
                    WHERE "SchoolID" = %s AND "IsDeleted" = FALSE 
                    ORDER BY "ClassName"
                """, [school_id])
            else:
                cursor.execute("""
                    SELECT "ClassID", "ClassName" FROM "ClassMaster" 
                    WHERE "IsDeleted" = FALSE 
                    ORDER BY "ClassName"
                """)
            
            classes = []
            for row in cursor.fetchall():
                classes.append({
                    'ClassID': row[0],
                    'ClassName': row[1]
                })
            
            return classes
            
    except Exception as e:
        logger.error(f"Error getting class dropdown data: {e}")
        return []

def bytes_to_data_uri(blob, mime: str = None) -> str:
    """
    Converts a byte blob into a base64 encoded data URI string.
    Automatically detects MIME type (JPEG, PNG, GIF) if not provided.
    Handles memoryview objects from PostgreSQL bytea fields.
    """
    if not blob:
        return ""
    
    # Ensure we have bytes (PostgreSQL often returns memoryview for bytea)
    if isinstance(blob, memoryview):
        blob = blob.tobytes()
    elif not isinstance(blob, (bytes, bytearray)):
        return ""

    # Detect MIME type if not explicitly provided
    if not mime:
        if blob.startswith(b'\xff\xd8\xff'):
            mime = "image/jpeg"
        elif blob.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = "image/png"
        elif blob.startswith(b'GIF87a') or blob.startswith(b'GIF89a'):
            mime = "image/gif"
        else:
            mime = "image/png"  # Fallback

    try:
        encoded = base64.b64encode(blob).decode('utf-8')
        return f"data:{mime};base64,{encoded}"
    except Exception as e:
        logger.error(f"Error encoding data URI: {e}")
        return ""

def validate_uploaded_file(file, allowed_types=None, max_size=MAX_FILE_SIZE):
    """
    Enhanced validation for uploaded files (CWE-434).
    Checks:
    1. File presence
    2. File size
    3. Extension whitelist & double extension prevention
    4. MIME type whitelist (browser-reported)
    5. Content signature (Magic Number) verification for images and PDFs
    """
    if not file:
        return False, "No file provided"
    
    # 1. Size Check
    if file.size > max_size:
        return False, f"File size exceeds {max_size / (1024*1024):.0f}MB limit"
    
    # 2. Extension & Filename Sanitization
    from django.utils.text import get_valid_filename
    original_name = file.name
    sanitized_name = get_valid_filename(original_name)
    
    # Check for double extensions or suspicious patterns
    if sanitized_name.count('.') > 1:
        # Check if the last part is a common dangerous extension
        parts = sanitized_name.lower().split('.')
        dangerous = ['exe', 'dll', 'so', 'sh', 'bat', 'php', 'js', 'html', 'htm', 'py']
        if any(d in parts[1:] for d in dangerous):
            return False, "Dangerous file pattern detected"

    file_ext = os.path.splitext(sanitized_name)[1].lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
    if file_ext not in allowed_extensions:
        return False, f"File extension {file_ext} not allowed"
    
    # 3. MIME Type Whitelist
    if allowed_types is None:
        allowed_types = ALLOWED_IMAGE_TYPES + ['application/pdf']
    
    if file.content_type not in allowed_types:
        return False, f"File type {file.content_type} not allowed"
    
    # 4. Content Signature (Magic Number) Verification
    # Read the first 2KB for signature checking
    try:
        header = file.read(2048)
        file.seek(0)  # Reset pointer for subsequent processing
        
        # Signatures
        is_pdf = header.startswith(b'%PDF-')
        is_jpg = header.startswith(b'\xff\xd8\xff')
        is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
        is_gif = header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
        
        # Map detected signature to expected extension/mime
        detected_ext = None
        if is_pdf: detected_ext = '.pdf'
        elif is_jpg: detected_ext = '.jpg' # includes .jpeg
        elif is_png: detected_ext = '.png'
        elif is_gif: detected_ext = '.gif'
        
        if not detected_ext:
            return False, "Invalid file content signature"
            
        # Cross-verify extension with signature
        if detected_ext == '.jpg' and file_ext not in ['.jpg', '.jpeg']:
            return False, "File extension does not match content signature"
        if detected_ext != '.jpg' and detected_ext != file_ext:
            return False, "File extension does not match content signature"
            
    except Exception as e:
        logger.error(f"Error verifying file signature: {e}")
        return False, "Internal error during file validation"
    
    return True, "File is valid"

def number_to_words(number):
    """
    Convert a number to Indian Rupees in words (Lakhs/Crores format).
    """
    if number == 0:
        return "Zero Rupees Only"
        
    def convert_less_than_thousand(n):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        if n == 0:
            return ""
        if n < 20:
            return units[n]
        if n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
        return units[n // 100] + " Hundred" + (" and " + convert_less_than_thousand(n % 100) if n % 100 != 0 else "")

    def convert_to_indian_format(n):
        if n == 0:
            return ""
            
        parts = []
        # Crores
        if n >= 10000000:
            parts.append(convert_less_than_thousand(n // 10000000) + " Crore")
            n %= 10000000
        # Lakhs
        if n >= 100000:
            parts.append(convert_less_than_thousand(n // 100000) + " Lakh")
            n %= 100000
        # Thousands
        if n >= 1000:
            parts.append(convert_less_than_thousand(n // 1000) + " Thousand")
            n %= 1000
        # Remaining
        if n > 0:
            parts.append(convert_less_than_thousand(n))
            
        return " ".join(parts)

    integer_part = int(number)
    fractionary_part = int(round((number - integer_part) * 100))
    
    words = convert_to_indian_format(integer_part) + " Rupees"
    if fractionary_part > 0:
        words += " and " + convert_less_than_thousand(fractionary_part) + " Paise"
    
    return words + " Only"

def safe_int(value, default=0):
    """Safely convert to int (CWE-704)"""
    try:
        return int(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert to float (CWE-704)"""
    try:
        return float(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default

def safe_strptime(date_str, fmt):
    """Safely parse date"""
    if not date_str:
        return None
    try:
        if isinstance(date_str, datetime):
            return date_str
        return datetime.strptime(date_str, fmt)
    except (ValueError, TypeError):
        return None

def _get_custom_session_info(request):
    """
    Returns a dict with user/session info if a valid session cookie exists; otherwise None.
    Also enriches with user photo and ERP logo (as data URIs / static).
    """
    token = request.COOKIES.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "user_id", "profile_id", "profile_name", "school_id", "school_name"
                FROM "user_sessions"
                WHERE "session_token" = %s AND "expires_at" > CURRENT_TIMESTAMP
            """, [token])
            row = cursor.fetchone()

        if not row:
            return None

        sess = {
            'user_id': row[0],
            'profile_id': row[1],
            'profile_name': row[2],
            'school_id': row[3],
            'school_name': row[4],
            'session_token': token
        }

        # Enrich with username, user photo & school logo from DB
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u."UserName", u."UserPhoto", s."SchoolLogo"
                FROM "UserMaster" u
                LEFT JOIN "SchoolMaster" s ON u."SchoolID" = s."SchoolID"
                WHERE u."UserID" = %s
            """, [sess['user_id']])
            urow = cursor.fetchone()

        user_name = urow[0] if urow else ""
        user_photo_blob = urow[1] if urow else None
        school_logo_blob = urow[2] if urow else None

        user_photo_src = bytes_to_data_uri(user_photo_blob) if user_photo_blob else ""
        if sess['profile_id'] == 1:
            erp_logo_src = ""
        else:
            erp_logo_src = bytes_to_data_uri(school_logo_blob) if school_logo_blob else ERP_DEFAULT_LOGO_STATIC

        sess['user_name'] = user_name
        sess['user_photo_src'] = user_photo_src
        sess['erp_logo_src'] = erp_logo_src
        return sess
    except Exception as e:
        logger.error(f"Error getting custom session info: {e}")
        return None
def hex_to_rgb(hex_color):
    """Convert hex color to 'R, G, B' string."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b
    except:
        return 0, 74, 173 # Fallback to default blue RGB

def adjust_color(hex_color, amount):
    """Lighten or darken a hex color."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        return "#{:02x}{:02x}{:02x}".format(r, g, b)
    except:
        return "#004aad"

def get_context(request):
    """Helper function to fetch session data and images for header."""
    # Priority 1: Check if custom_login_required decorator already populated custom_user
    sess = getattr(request, 'custom_user', None)
    
    # Priority 2: Try to fetch session info from cookie and DB
    if not sess:
        sess = _get_custom_session_info(request)
    
    if sess:
        # Custom session found, use its data
        user_name = sess.get('user_name') or request.session.get('UserName', 'Unknown User')
        profile_name = sess.get('profile_name') or request.session.get('ProfileName', 'Unknown Profile')
        school_name = sess.get('school_name') or request.session.get('SchoolName', '')
        user_id = sess.get('user_id') or request.session.get('UserId')
        profile_id = sess.get('profile_id') or request.session.get('ProfileID')
        user_photo_src = sess.get('user_photo_src', '')
        school_logo_src = sess.get('erp_logo_src', '')
    else:
        # Fallback to pure Django session
        user_name = request.session.get('UserName', 'Unknown User')
        profile_name = request.session.get('ProfileName', 'Unknown Profile')
        school_name = request.session.get('SchoolName', '')
        user_id = request.session.get('UserId')
        profile_id = request.session.get('ProfileID')
        user_photo_src = ''
        school_logo_src = ''

    # If profile_name is still default but we have profile_id, try fetching from DB
    if profile_name == 'Unknown Profile' and profile_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT \"ProfileName\" FROM \"ProfileMaster\" WHERE \"ProfileID\" = %s AND \"IsDeleted\" = FALSE", [profile_id])
                profile_data = cursor.fetchone()
                if profile_data and profile_data[0]:
                    profile_name = profile_data[0]
                    request.session['ProfileName'] = profile_name
        except Exception as e:
            logger.error(f"Error querying ProfileName for ProfileID {profile_id}: {str(e)}")

    # Fetch UserPhoto URL if UserID exists
    if user_id:
        user_photo_src = f"/api/user/photo/{user_id}/"
    else:
        user_photo_src = ""

    # Fetch SchoolLogo URL if SchoolID exists
    school_id = sess.get('school_id') if sess else request.session.get('SchoolID')
    if school_id:
        school_logo_src = f"/api/school/logo/{school_id}/"
    else:
        school_logo_src = ""

    school_id_to_check = sess.get('school_id') if sess else request.session.get('SchoolID')

    # Theme Logic
    primary_color = '#004aad'  # Default
    primary_hover = '#003a8c'  # Default
    theme_id = None

    try:
        with connection.cursor() as cursor:
            # 1. Try to get theme from UserMaster
            if user_id:
                cursor.execute('SELECT "ThemeID" FROM "UserMaster" WHERE "UserID" = %s', [user_id])
                row = cursor.fetchone()
                if row and row[0]:
                    theme_id = row[0]
            
            # 2. If not found, try SchoolMaster
            if not theme_id and school_id_to_check:
                cursor.execute('SELECT "ThemeID" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id_to_check])
                row = cursor.fetchone()
                if row and row[0]:
                    theme_id = row[0]
            
            # 3. Fetch theme colors
            if theme_id:
                cursor.execute('SELECT "PrimaryColor", "PrimaryHover" FROM "ThemeMaster" WHERE "ThemeID" = %s AND "IsActive" = TRUE', [theme_id])
                row = cursor.fetchone()
                if row:
                    primary_color = row[0]
                    primary_hover = row[1]
    except Exception as e:
        logger.error(f"Error fetching theme context: {e}")

    r, g, b = hex_to_rgb(primary_color)
    primary_rgb = f"{r}, {g}, {b}"
    primary_dark = adjust_color(primary_color, -30)
    primary_light = f"rgba({primary_rgb}, 0.1)"
    
    theme_styles = f"""
    <style>
        :root {{
            --primary-color: {primary_color};
            --primary-hover: {primary_hover};
            --primary-dark: {primary_dark};
            --primary-light: {primary_light};
            --header-bg: {primary_color};
            --sidebar-bg: linear-gradient(180deg, {primary_color}, {primary_hover});
            --primary-rgb: {primary_rgb};
        }}
    </style>
    """

    is_super = profile_id == 1 or profile_name == 'Super Admin' or profile_name == 'SuperAdmin'
    is_admin = profile_name == 'School Admin' or profile_name == 'SchoolAdmin'
    is_teacher = profile_name == 'Teacher'
    
    return {
        'user_name': user_name,
        'profile_id': profile_id,
        'profile_name': profile_name,
        'is_super_admin': is_super,
        'is_admin': is_admin,
        'is_teacher': is_teacher,
        'is_student': profile_name == 'Student',
        'user_photo_src': user_photo_src,
        'user_id': user_id,
        'school_logo_src': '' if is_super else school_logo_src,
        'school_name': '' if is_super else school_name,
        'school_id': 0 if is_super else school_id_to_check,
        'dark_mode': request.session.get('dark_mode', False),
        'primary_color': primary_color,
        'primary_hover': primary_hover,
        'primary_rgb': primary_rgb,
        'primary_dark': primary_dark,
        'primary_light': primary_light,
        'theme_styles': theme_styles,
    }

def execute_procedure_with_messages(cursor, procedure_name, params):
    """
    Execute a stored procedure and capture any messages or additional result sets
    """
    messages = []
    result = None
    
    try:
        # Execute the procedure
        cursor.execute(procedure_name, params)
        
        # Get the first result set
        result = cursor.fetchone()
        
        # Try to capture any additional result sets or messages
        try:
            while cursor.nextset():
                additional_result = cursor.fetchone()
                if additional_result:
                    # Check if it's a message (usually single column)
                    if len(additional_result) == 1:
                        messages.append(str(additional_result[0]))
                    else:
                        # Multiple columns, join them
                        messages.append(" | ".join([str(col) for col in additional_result if col]))
        except Exception as e:
            logger.debug(f"No additional result sets: {str(e)[:50]}")
        
        return result, messages
        
    except Exception:
        raise
