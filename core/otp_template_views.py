# core/otp_template_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from .views import custom_login_required, get_context
import logging

logger = logging.getLogger(__name__)

@custom_login_required
def otp_template_management(request):
    """Manage OTP email templates"""
    context = get_context(request)
    school_id = request.session.get('SchoolID')
    
    # Get active template from TemplateSettings
    active_template = 'otp_template1.html'
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT "TemplateFile" FROM "TemplateSettings" 
            WHERE "SchoolID" = %s AND "TemplateType" = 'OTP_EMAIL' AND "IsActive" = TRUE AND "IsDeleted" = FALSE
        """, [school_id])
        row = cursor.fetchone()
        if row:
            active_template = row[0]
    
    # Define all 15 templates
    templates = [
        {'code': 'otp_template1.html', 'name': 'Modern Gradient'},
        {'code': 'otp_template2.html', 'name': 'Minimal Clean'},
        {'code': 'otp_template3.html', 'name': 'Professional Blue'},
        {'code': 'otp_template4.html', 'name': 'Corporate Elegant'},
        {'code': 'otp_template5.html', 'name': 'Tech Modern'},
        {'code': 'otp_template6.html', 'name': 'Classic Professional'},
        {'code': 'otp_template7.html', 'name': 'Vibrant Colorful'},
        {'code': 'otp_template8.html', 'name': 'Dark Theme'},
        {'code': 'otp_template9.html', 'name': 'Simple Minimal'},
        {'code': 'otp_template10.html', 'name': 'Premium Luxury'},
        {'code': 'otp_template11.html', 'name': 'Security Focus'},
        {'code': 'otp_template12.html', 'name': 'Cyber Security'},
        {'code': 'otp_template13.html', 'name': 'Interactive Digits'},
        {'code': 'otp_template14.html', 'name': 'Corporate Hexagon'},
        {'code': 'otp_template15.html', 'name': 'Military Grade'}
    ]
    
    context.update({'templates': templates, 'active_template': active_template, 'school_id': school_id})
    return render(request, 'core/otp_template_management.html', context)

@custom_login_required
def set_active_otp_template(request):
    """Set active OTP template"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    template_code = request.POST.get('template_code')
    school_id = request.session.get('SchoolID')
    user_id = request.session.get('UserId')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE "TemplateSettings" SET "TemplateFile" = %s, "ModifiedBy" = %s, "ModifiedAt" = CURRENT_TIMESTAMP 
                WHERE "SchoolID" = %s AND "TemplateType" = 'OTP_EMAIL'
            """, [template_code, user_id, school_id])
            
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO "TemplateSettings" ("SchoolID", "TemplateType", "TemplateFile", "IsActive", "CreatedBy", "CreatedAt", "IsDeleted")
                    VALUES (%s, 'OTP_EMAIL', %s, TRUE, %s, CURRENT_TIMESTAMP, FALSE)
                """, [school_id, template_code, user_id])
        
        return JsonResponse({'success': True, 'message': 'Template activated successfully'})
    except Exception as e:
        logger.error(f"Error setting active template: {e}")
        return JsonResponse({'success': False, 'message': str(e)})

@custom_login_required
def preview_otp_template(request, template_code):
    """Preview OTP template"""
    from django.template.loader import render_to_string
    
    try:
        template_path = f'core/document_templates/Login_OTP/{template_code}'
        html = render_to_string(template_path, {
            'user_name': 'John Doe',
            'otp': '123456',
            'valid_minutes': '15',
            'ip_address': '192.168.1.1',
            'school_name': request.session.get('SchoolName', 'ShikshaWave'),
            'current_time': 'Just now',
            'device': 'Chrome on Windows',
            'location': 'Mumbai, India'
        })
        return JsonResponse({'success': True, 'html': html})
    except Exception as e:
        logger.error(f"Error previewing template: {e}")
        return JsonResponse({'success': False, 'message': str(e)})
