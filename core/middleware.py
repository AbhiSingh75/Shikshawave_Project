# core/middleware.py
import logging
from django.http import HttpResponseServerError, HttpResponseNotFound, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.conf import settings
from django.urls import resolve, Resolver404
from django.shortcuts import redirect
from django.contrib import messages
from core.models import UserMaster, MenuMaster, ProfileMenuMapping
from .url_token import generate_token, resolve_token

logger = logging.getLogger(__name__)

class AnonymousUser:
    @property
    def is_authenticated(self):
        return False
    
    @property
    def is_anonymous(self):
        return True

class CustomAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            user_id = request.session.get('UserId')
            if user_id:
                try:
                    request.user = UserMaster.objects.get(user_id=user_id, is_deleted=False, is_active=True)
                except UserMaster.DoesNotExist:
                    request.user = AnonymousUser()
            else:
                request.user = AnonymousUser()
        except Exception as e:
            logger.error(f"Error checking session for user: {e}")
            request.user = AnonymousUser()
        return self.get_response(request)

class EncryptContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.token = generate_token
        response = self.get_response(request)
        return response

class ErrorPageMiddleware:
    """
    Middleware to ensure error pages are always show, even when templates fail
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Handle 404 errors with custom page
        if response.status_code == 404:
            try:
                # Try to render a custom 404 page
                template = get_template('errors/404.html')
                return HttpResponseNotFound(template.render())
            except Exception as e:
                logger.error(f"Failed to render custom 404 page: {e}")
                # Return a basic HTML 404 page
                return HttpResponseNotFound("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Page Not Found</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #4f46e5; }
                        a { color: #4f46e5; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                    </style>
                </head>
                <body>
                    <h1>404 - Page Not Found</h1>
                    <p>The page you are looking for doesn't exist.</p>
                    <a href="/">Go Home</a>
                </body>
                </html>
                """)
        
        # Handle 500 errors with custom page
        if response.status_code == 500:
            try:
                # Try to render a custom 500 page
                template = get_template('errors/500.html')
                return HttpResponseServerError(template.render())
            except Exception as e:
                logger.error(f"Failed to render custom 500 page: {e}")
                # Return a basic HTML error page
                return HttpResponseServerError("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Server Error</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        h1 { color: #ef4444; }
                        a { color: #4f46e5; text-decoration: none; }
                        a:hover { text-decoration: underline; }
                    </style>
                </head>
                <body>
                    <h1>500 - Internal Server Error</h1>
                    <p>We're sorry, but something went wrong on our end.</p>
                    <p>Please try again later or contact support if the problem persists.</p>
                    <a href="/">Go Home</a>
                </body>
                </html>
                """)
        
        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions that occur during request processing
        """
        if isinstance(exception, (Http404, Resolver404)):
            return None
            
        logger.error(f"Unhandled exception: {exception}", exc_info=True)
        
        try:
            # Try to render a custom 500 page
            template = get_template('errors/500.html')
            return HttpResponseServerError(template.render())
        except Exception as e:
            logger.error(f"Failed to render custom 500 page in process_exception: {e}")
            # Return a basic HTML error page
            return HttpResponseServerError("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Server Error</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    h1 { color: #ef4444; }
                    a { color: #4f46e5; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>500 - Internal Server Error</h1>
                <p>We're sorry, but something went wrong on our end.</p>
                <p>Please try again later or contact support if the problem persists.</p>
                <a href="/">Go Home</a>
            </body>
            </html>
            """)

class URLEncryptionMiddleware:
    PARAMS = {
        'uid': 'user_id', 'eid': 'employee_id', 'sid': 'student_id', 
        'cid': 'class_id', 'tid': 'teacher_id', 'xid': 'exam_id'
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        decrypted_get = request.GET.copy()
        for short, full in self.PARAMS.items():
            if short in decrypted_get and decrypted_get[short]:
                resolved = resolve_token(decrypted_get[short], short)
                if resolved:
                    decrypted_get[full] = str(resolved)
                    del decrypted_get[short]
        request.GET = decrypted_get
        response = self.get_response(request)
        return response

class SessionCleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = 0

    def __call__(self, request):
        import time
        from django.db import connection
        from django.conf import settings
        
        # Check session activity and enforce timeout
        if request.user.is_authenticated:
            try:
                last_activity = request.session.get('last_activity')
                current_time = time.time()
                
                if last_activity:
                    inactive_time = current_time - last_activity
                    
                    # Use the user's customized timeout if available, otherwise default to SESSION_COOKIE_AGE
                    # session_timeout_minutes is typically saved during login or user settings update
                    user_timeout_minutes = request.session.get('session_timeout_minutes')
                    if user_timeout_minutes:
                        timeout_seconds = int(user_timeout_minutes) * 60
                    else:
                        timeout_seconds = settings.SESSION_COOKIE_AGE
                        
                    if inactive_time > timeout_seconds:
                        request.session.flush()
                        return redirect('login')
                
                request.session['last_activity'] = current_time
            except Exception as e:
                logger.error(f"Error checking session for user {request.user.user_id}: {e}")
        
        # Run cleanup every 60 seconds
        current_time = time.time()
        if current_time - self.last_cleanup > 60:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE "user_sessions" 
                        SET "LogoutTime" = CURRENT_TIMESTAMP 
                        WHERE "expires_at" < CURRENT_TIMESTAMP 
                        AND "LogoutTime" IS NULL
                    """)
                    connection.commit()
                self.last_cleanup = current_time
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
        
        response = self.get_response(request)
        return response

class DynamicPermissionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip permission check for these cases
        if not request.user.is_authenticated:
            return None
            
        if request.user.is_superuser:
            return None
            
        # URLs that don't need permission checks
        exempt_urls = [
            'logout',
            'password_change',
            'password_change_done',
            'unauthorized',
            'static',
            'media'
        ]
        
        resolved_url = resolve(request.path_info)
        if resolved_url.url_name in exempt_urls:
            return None
            
        # Admin URLs
        if request.path_info.startswith('/admin/'):
            return None
            
        # Static files
        if request.path_info.startswith(settings.STATIC_URL) or request.path_info.startswith(settings.MEDIA_URL):
            return None

        try:
            # Find the menu item for this URL
            menu = MenuMaster.objects.filter(menu_url=request.path_info).first()
            
            if not menu:
                # Try to match by URL name if path doesn't match exactly
                menu = MenuMaster.objects.filter(menu_url__contains=resolved_url.url_name).first()
                if not menu:
                    return None
                    
            # Check if user has permission
            has_permission = ProfileMenuMapping.objects.filter(
                profile_id=request.user.profile.profile_id,
                menu_id=menu.menu_id,
                can_view=True,
                is_deleted=False
            ).exists()
            
            if not has_permission:
                messages.error(request, "You don't have permission to access this page")
                return redirect('unauthorized')
                
        except Exception as e:
            # Log the error but don't block access (you might want to handle this differently)
            print(f"Permission check error: {str(e)}")
            return None
            
        return None