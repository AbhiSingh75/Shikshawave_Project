from django.shortcuts import redirect
from django.http import JsonResponse
from functools import wraps
from django.urls import reverse
from django.contrib import messages
from django.db import connection
import time
import logging
from .utils import bytes_to_data_uri

logger = logging.getLogger(__name__)

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from django.db import connection
        
        user_id = request.session.get('UserId')
        session_token = request.COOKIES.get('shsw_sess')
        
        # Check if session exists
        if not user_id:
            request.session.flush()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Session expired', 'redirect': reverse('login')}, status=401)
            next_url = request.get_full_path()
            return redirect(f"{reverse('login')}?next={next_url}")
        
        # Check session expiry from user_sessions table
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT \"expires_at\" FROM \"user_sessions\" WHERE \"user_id\" = %s AND \"expires_at\" > CURRENT_TIMESTAMP AND \"LogoutTime\" IS NULL",
                    [user_id]
                )
                result = cursor.fetchone()
                
                if not result:
                    # Session expired - update LogoutTime before flushing
                    logger.info(f"Session expired for user {user_id}, token: {session_token[:20] if session_token else None}...")
                    
                    if session_token:
                        from django.db import transaction
                        logger.info(f"Updating LogoutTime for expired session")
                        with transaction.atomic():
                            cursor.execute("UPDATE \"user_sessions\" SET \"LogoutTime\" = CURRENT_TIMESTAMP WHERE \"session_token\" = %s", [session_token])
                            affected = cursor.rowcount
                            logger.info(f"LogoutTime UPDATE affected {affected} rows")
                    else:
                        logger.warning("No session_token found in cookie for expired session")
                    
                    request.session.flush()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Session expired', 'redirect': reverse('login')}, status=401)
                    next_url = request.get_full_path()
                    return redirect(f"{reverse('login')}?next={next_url}")
                
                # Update last_activity for current session only
                if session_token:
                    from django.db import transaction
                    with transaction.atomic():
                        cursor.execute(
                            "UPDATE \"user_sessions\" SET \"last_activity\" = CURRENT_TIMESTAMP WHERE \"session_token\" = %s",
                            [session_token]
                        )
        except Exception as e:
            # If there's an error checking session, log it and redirect to login
            logger.error(f"Error checking session for user {user_id}: {e}")
            request.session.flush()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Session error', 'redirect': reverse('login')}, status=401)
            next_url = request.get_full_path()
            return redirect(f"{reverse('login')}?next={next_url}")
        
        return view_func(request, *args, **kwargs)
    return wrapper

# Session management constants and helpers
SESSION_COOKIE_NAME = 'shsw_sess'
ERP_DEFAULT_LOGO_STATIC = '/static/images/default_logo.png'

def _get_custom_session_info(request):
    """
    Returns a dict with user/session info if a valid session cookie exists; otherwise None.
    Also enriches with user photo and ERP logo (as data URIs / static).
    """
    token = request.COOKIES.get(SESSION_COOKIE_NAME)
    if not token:
        logger.debug("No session cookie found")
        return None

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT "user_id", "profile_id", "profile_name", "school_id", "school_name"
            FROM "user_sessions"
            WHERE "session_token" = %s AND "expires_at" > CURRENT_TIMESTAMP
        """, [token])
        row = cursor.fetchone()

    if not row:
        logger.debug(f"No valid session found for token: {token}")
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
        erp_logo_src = ERP_DEFAULT_LOGO_STATIC
    else:
        erp_logo_src = bytes_to_data_uri(school_logo_blob) if school_logo_blob else ERP_DEFAULT_LOGO_STATIC

    sess['user_name'] = user_name
    sess['user_photo_src'] = user_photo_src
    sess['erp_logo_src'] = erp_logo_src
    logger.debug(f"Session info retrieved: {sess}")
    return sess

def _touch_custom_session(token):
    if not token:
        return
    with connection.cursor() as cursor:
        cursor.execute("UPDATE \"user_sessions\" SET \"last_activity\" = CURRENT_TIMESTAMP WHERE \"session_token\" = %s", [token])
        logger.debug(f"Session touched for token: {token}")

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        sess = _get_custom_session_info(request)
        if not sess:
            logger.warning("Access denied: No valid session")
            if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or
                'json' in request.headers.get('Accept', '').lower()):
                return JsonResponse({'success': False, 'error': 'Session expired', 'redirect': reverse('login')}, status=401)
            messages.error(request, "Please login to continue.")
            return redirect('login')
        request.custom_user = sess
        _touch_custom_session(sess.get('session_token'))
        return view_func(request, *args, **kwargs)
    return _wrapped