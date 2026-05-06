from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.views.decorators.clickjacking import xframe_options_exempt
from .views import custom_login_required, get_context
import base64
import logging

logger = logging.getLogger(__name__)

@custom_login_required
@xframe_options_exempt
def student_id_card_view(request, student_id):
    """Display student ID card with school's selected template"""
    school_id = request.session.get('SchoolID')
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT StudentCode FROM Student WHERE StudentID=%s", [student_id])
        code_row = cursor.fetchone()
        if not code_row:
            return HttpResponse('Student not found', status=404)
        
        student_code = code_row[0]
        
        cursor.execute("""
            SELECT * FROM "Proc_Student_Cards_Full_Get"(
                %s, NULL, NULL, %s, 1, 1
            )
        """, [school_id, student_code])
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        if not rows:
            return HttpResponse('Student not found', status=404)
        
        student = dict(zip(columns, rows[0]))
        
        # Convert Photo varbinary to PhotoBase64
        if student.get('Photo') and isinstance(student['Photo'], bytes):
            student['PhotoBase64'] = base64.b64encode(student['Photo']).decode('utf-8')
        else:
            student['PhotoBase64'] = None
        
        # Convert SchoolLogo
        if student.get('SchoolLogo') and isinstance(student['SchoolLogo'], bytes):
            student['SchoolLogoBase64'] = base64.b64encode(student['SchoolLogo']).decode('utf-8')
        else:
            student['SchoolLogoBase64'] = None
        
        student['ParentMobile'] = student.get('MobileNo', 'N/A')
        
        cursor.execute("""
            SELECT "TemplateFile" FROM "TemplateSettings" 
            WHERE "SchoolID"=%s AND "TemplateType"='StudentCard' 
            AND "IsActive"=TRUE AND "IsDeleted"=FALSE
        """, [school_id])
        template_row = cursor.fetchone()
        if template_row and template_row[0]:
            full_template_path = template_row[0]
            # Remove the path prefix if it exists
            template_file = full_template_path.replace('core/document_templates/student_id_card/', '')
            logger.info(f"Found template in database: {full_template_path} -> {template_file}")
        else:
            template_file = 'student_card_horizontal_1.html'
            logger.warning(f"No template found in database for SchoolID={school_id}, using default: {template_file}")
        
        # Debug logging
        logger.info(f"Loading template: {template_file} for student: {student_code}")
        
        # Render the template and add CSS fixes for text visibility
        from django.template.loader import render_to_string
        
        try:
            card_html = render_to_string(f'core/document_templates/student_id_card/{template_file}', {'student': student})
            logger.info(f"Successfully loaded template: {template_file} for student: {student_code}")
            
            # Debug: Check if it's a vertical template and add identifier
            if 'vertical_8' in template_file or 'vertical_9' in template_file:
                logger.info(f"Loading vertical template: {template_file}")
                # Add a debug comment to verify correct template is loaded
                card_html = f'<!-- Template: {template_file} -->\n{card_html}'
                
        except Exception as e:
            logger.error(f"Error loading template {template_file}: {e}")
            # Fallback to default template
            card_html = render_to_string('core/document_templates/student_id_card/student_card_horizontal_1.html', {'student': student})
        
        # Add CSS overrides to ensure text is visible in modal
        import time
        cache_buster = int(time.time())
        enhanced_html = f'''<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css?v={cache_buster}">
<style>
body {{
    margin: 0;
    padding: 20px;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Arial, sans-serif;
}}

/* Ensure text visibility for all templates */
.v6 h3, .v8 h3, .v9 h3 {{
    color: #1f2937 !important;
    font-weight: 600 !important;
}}

.v6 .cd, .v8 .student-code, .v9 .student-code {{
    color: #8b5cf6 !important;
    background: #f3f4f6 !important;
}}

.v6 .i, .v8 .info-row, .v9 .info-row {{
    color: #374151 !important;
    background: #f9fafb !important;
}}

.v6 .i i, .v8 .info-row i, .v9 .info-row i {{
    color: #8b5cf6 !important;
}}

/* Specific fixes for V8 template */
.v8 .student-code {{
    color: #1e40af !important;
    background: #f3f4f6 !important;
    text-align: center !important;
    padding: 6px !important;
    border-radius: 6px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    margin-bottom: 12px !important;
}}

.v8 .info-row {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 8px 10px !important;
    background: #f9fafb !important;
    margin-bottom: 6px !important;
    border-radius: 6px !important;
    border-left: 3px solid #1e40af !important;
}}

.v8 .info-label {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    font-size: 9px !important;
    font-weight: 600 !important;
    color: #1e40af !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}}

.v8 .info-label i {{
    font-family: "Font Awesome 6 Free" !important;
    font-weight: 900 !important;
    color: #1e40af !important;
    width: 14px !important;
    text-align: center !important;
    font-size: 10px !important;
}}

.v8 .info-value {{
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #1f2937 !important;
    text-align: right !important;
}}

/* Specific fixes for V9 template */
.v9 .student-code {{
    color: #991b1b !important;
    background: #f3f4f6 !important;
    text-align: center !important;
    padding: 6px !important;
    border-radius: 6px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    margin-bottom: 12px !important;
}}

.v9 .info-row {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 8px 10px !important;
    background: #f9fafb !important;
    margin-bottom: 6px !important;
    border-radius: 6px !important;
    border-left: 3px solid #991b1b !important;
}}

.v9 .info-label {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    font-size: 9px !important;
    font-weight: 600 !important;
    color: #991b1b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}}

.v9 .info-label i {{
    font-family: "Font Awesome 6 Free" !important;
    font-weight: 900 !important;
    color: #991b1b !important;
    width: 14px !important;
    text-align: center !important;
    font-size: 10px !important;
}}

.v9 .info-value {{
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #1f2937 !important;
    text-align: right !important;
}}

/* Fix for horizontal templates */
.template-h1 .detail-row {{
    color: white !important;
}}

.template-h1 .detail-row .label {{
    color: white !important;
}}

.template-h1 .detail-row .value {{
    color: white !important;
}}

.template-h1 .card-title {{
    color: #ffd700 !important;
}}

.template-h1 .school-name {{
    color: white !important;
}}

/* FontAwesome icon fixes */
.v8 i, .v9 i {{
    font-family: "Font Awesome 6 Free" !important;
    font-weight: 900 !important;
    display: inline-block !important;
    -webkit-font-smoothing: antialiased !important;
}}

/* General text visibility fixes */
.id-card * {{
    font-weight: 500 !important;
}}

/* Ensure proper text rendering */
.v8 *, .v9 * {{
    text-rendering: optimizeLegibility !important;
}}
</style>
</head>
<body>{card_html}</body></html>'''
        
        return HttpResponse(enhanced_html)
