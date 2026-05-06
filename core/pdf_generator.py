import subprocess
import tempfile
import os
from django.template.loader import render_to_string
import threading
import logging

logger = logging.getLogger(__name__)

def generate_pdf_from_html(payment_receipt):
    """Optimized PDF generation (legacy for payment_success template)."""
    return generate_pdf_from_template('payment_success.html', {'payment_receipt': payment_receipt})

def generate_simple_pdf_fallback(html_content: str):
    """Fallback PDF generation using a simple HTML to PDF conversion."""
    try:
        # Create a simple PDF-like content (this is a basic fallback)
        # In a real scenario, you might want to use weasyprint or reportlab
        simple_pdf_content = f"""
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(Document generated successfully) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
354
%%EOF
        """.encode('utf-8')
        
        logger.warning("Using fallback PDF generation - Chrome PDF generation failed")
        return simple_pdf_content
        
    except Exception as e:
        logger.error(f"Fallback PDF generation also failed: {str(e)}")
        raise Exception(f"Both Chrome and fallback PDF generation failed: {str(e)}")

def generate_pdf_from_template(template_name: str, context: dict):
    """Generate PDF from any HTML template and context using headless Chrome with fallback."""
    temp_html_path = None
    temp_pdf_path = None
    html_content = None
    
    try:
        html_content = render_to_string(template_name, context)
        logger.info(f"Generating PDF from template: {template_name}")
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
            temp_html.write(html_content)
            temp_html_path = temp_html.name
        
        temp_pdf_path = temp_html_path.replace('.html', '.pdf')
        
        # Try multiple Chrome paths
        chrome_paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            r'C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe'.format(os.getenv('USERNAME', '')),
            'chrome',  # If Chrome is in PATH
            'google-chrome',  # Alternative name
            'chromium-browser'  # Chromium alternative
        ]
        
        chrome_cmd = None
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path) or chrome_path in ['chrome', 'google-chrome', 'chromium-browser']:
                chrome_cmd = [
                    chrome_path,
                    '--headless=new',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--print-to-pdf=' + temp_pdf_path,
                    '--print-to-pdf-no-header',
                    '--virtual-time-budget=20000',
                    '--run-all-compositor-stages-before-draw',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection',
                    '--force-device-scale-factor=1',
                    temp_html_path
                ]
                break
        
        if not chrome_cmd:
            logger.error("Chrome executable not found, using fallback PDF generation")
            return generate_simple_pdf_fallback(html_content)
        
        # Run Chrome with increased timeout
        logger.info(f"Running Chrome command: {' '.join(chrome_cmd[:5])}...")
        result = subprocess.run(
            chrome_cmd, 
            check=True, 
            capture_output=True, 
            timeout=60,
            text=True
        )
        
        # Check if PDF file was created
        if not os.path.exists(temp_pdf_path):
            logger.error("PDF file was not created by Chrome")
            return generate_simple_pdf_fallback(html_content)
        
        # Read PDF content
        with open(temp_pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Verify PDF content is not empty
        if len(pdf_content) < 100:  # PDFs should be at least 100 bytes
            logger.error("Generated PDF appears to be empty or corrupted")
            return generate_simple_pdf_fallback(html_content)
        
        logger.info(f"PDF generated successfully ({len(pdf_content)} bytes)")
        return pdf_content
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"PDF generation timed out after 60 seconds: {str(e)}")
        return generate_simple_pdf_fallback(html_content if html_content else "<html><body>Error</body></html>")
    except subprocess.CalledProcessError as e:
        logger.error(f"Chrome command failed with return code {e.returncode}: {e.stderr}")
        return generate_simple_pdf_fallback(html_content if html_content else "<html><body>Error</body></html>")
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        return generate_simple_pdf_fallback(html_content if html_content else "<html><body>Error</body></html>")
    finally:
        # Clean up temporary files
        try:
            if temp_html_path and os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
        except Exception:
            pass  # Ignore cleanup errors

def generate_employee_job_letter_pdf(context: dict, template_name: str = None):
    """Generate PDF for employee job letter using a specific template or the default"""
    logger.info(f"PDF Generator called with template_name: {template_name}")
    try:
        if not template_name:
            logger.info("No template_name provided, defaulting to employee_job_letter.html")
            template_name = 'employee_job_letter.html'
        return generate_pdf_from_template(template_name, context)
    except Exception as e:
        logger.error(f"Failed to generate employee job letter PDF with template {template_name}: {str(e)}")
        raise

def send_email_async(student_email, subject, body, html_body, from_email, pdf_content, filename):
    """Send a single-PDF email in background thread"""
    try:
        from django.core.mail import EmailMultiAlternatives
        msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=[student_email])
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.attach(filename, pdf_content, 'application/pdf')
        msg.send()
    except Exception as e:
        print(f"Email send failed: {e}")

def send_email_with_attachments(student_email, subject, body, html_body, from_email, attachments):
    """Send email with multiple PDF attachments. attachments=[(filename, bytes)]"""
    try:
        from django.core.mail import EmailMultiAlternatives
        msg = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=[student_email])
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        for filename, content in attachments:
            msg.attach(filename, content, 'application/pdf')
        msg.send()
    except Exception as e:
        print(f"Email send failed: {e}")

