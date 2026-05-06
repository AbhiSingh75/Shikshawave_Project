# core/error_handlers.py
from django.shortcuts import render
from django.http import HttpResponseServerError, HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib import messages
from django.template import TemplateDoesNotExist
import logging

logger = logging.getLogger(__name__)

def safe_render_error(request, template_name, status_code, context=None):
    """
    Safely render error page with fallback to simple HTML
    """
    if context is None:
        context = {}
    
    try:
        # Try to render with the main template first
        return render(request, template_name, context, status=status_code)
    except (TemplateDoesNotExist, Exception) as e:
        logger.error(f"Failed to render {template_name}: {e}")
        # Ultimate fallback - return a simple HTML response
        return HttpResponseServerError("""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>An error occurred</h1>
            <p>We're sorry, but something went wrong. Please try again later.</p>
            <a href="/">Go Home</a>
        </body>
        </html>
        """)

def custom_404(request, exception=None):
    """
    Custom 404 error handler
    """
    logger.warning(f"404 error for URL: {request.path}")
    return safe_render_error(request, 'errors/404.html', 404)

def custom_500(request):
    """
    Custom 500 error handler
    """
    logger.error(f"500 error for URL: {request.path}")
    return safe_render_error(request, 'errors/500.html', 500)

def custom_403(request, exception=None):
    """
    Custom 403 error handler
    """
    logger.warning(f"403 error for URL: {request.path}")
    return safe_render_error(request, 'errors/403.html', 403)

def custom_400(request, exception=None):
    """
    Custom 400 error handler
    """
    logger.warning(f"400 error for URL: {request.path}")
    return safe_render_error(request, 'errors/400.html', 400)

def handle_error(request, error_type="general", error_message="An error occurred", status_code=500):
    """
    Utility function to handle errors gracefully in views
    """
    logger.error(f"{error_type} error: {error_message} for URL: {request.path}")
    
    # Add error message to Django messages (if possible)
    try:
        messages.error(request, error_message)
    except Exception as e:
        logger.error(f"Failed to add error message: {e}")
    
    # Return appropriate error page based on error type
    if error_type == "404":
        return safe_render_error(request, 'errors/404.html', 404)
    elif error_type == "403":
        return safe_render_error(request, 'errors/403.html', 403)
    elif error_type == "400":
        return safe_render_error(request, 'errors/400.html', 400)
    elif error_type == "500":
        return safe_render_error(request, 'errors/500.html', 500)
    else:
        return safe_render_error(request, 'errors/general_error.html', status_code)
