from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import json

DOCUMENT_TYPES = [
    'Transfer Certificate',
    'Character Certificate',
    'No Dues Certificate',
    'Participation Certificate',
    'Merit Certificate',
    'Sports Certificate',
    'Cultural Activity Certificate',
    'House Appointment Letter'
]

@require_http_methods(["GET", "POST"])
def generate_document(request):
    """Generate and send documents to students"""
    from .utils import get_context, _get_custom_session_info
    context = get_context(request)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    user = request.session.get('user', {})
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            document_type = request.POST.get('document_type')
            remarks = request.POST.get('remarks', '')
            
            # Get student details
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.FullName, s.FatherName, s.MotherName, s.DateOfBirth, s.StudentCode,
                           cm.ClassName, sm.SectionName, sch.SchoolName
                    FROM Student s
                    LEFT JOIN ClassMaster cm ON s.AdmissionClass = cm.ClassID
                    LEFT JOIN SectionMaster sm ON s.Section = sm.SectionID
                    LEFT JOIN SchoolMaster sch ON s.SchoolID = sch.SchoolID
                    WHERE s.StudentID = %s AND s.SchoolID = %s
                """, [student_id, user.get('school_id')])
                row = cursor.fetchone()
                
                if row:
                    cert_data = {
                        'student_name': row[0],
                        'father_name': row[1],
                        'mother_name': row[2],
                        'dob': row[3].strftime('%d-%m-%Y') if row[3] else '',
                        'roll_no': row[4],
                        'class': row[5],
                        'section': row[6],
                        'school_name': row[7]
                    }
                    
                    cert_number = f"{document_type[:3].upper()}/{datetime.now().year}/{student_id}"
                    
                    cursor.execute("""
                        EXEC Proc_Certificate_Insert 
                            @StudentID = %s,
                            @School_ID = %s,
                            @CertificateType = %s,
                            @CertificateNumber = %s,
                            @CertificateData = %s,
                            @GeneratedBy = %s,
                            @Remarks = %s
                    """, [student_id, user.get('school_id'), document_type, cert_number, 
                          json.dumps(cert_data), user.get('user_id'), remarks])
                    
                    messages.success(request, f'{document_type} generated and sent successfully!')
                else:
                    messages.error(request, 'Student not found')
                    
            return redirect('generate_document')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    students = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC Proc_Students_For_Documents_Get @SchoolID = %s", [user.get('school_id')])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            students = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error fetching students: {e}")
        messages.error(request, f'Error loading students: {str(e)}')
        students = []
    
    context.update({
        'user': user,
        'document_types': DOCUMENT_TYPES,
        'students': students
    })
    return render(request, 'documents/generate_document.html', context)

@require_http_methods(["GET"])
def view_documents(request):
    """View all generated documents"""
    from .utils import get_context, _get_custom_session_info
    context = get_context(request)
    sess = _get_custom_session_info(request)
    if sess:
        context['user'] = sess
    user = request.session.get('user', {})
    
    documents = []
    try:
        with connection.cursor() as cursor:
            if user.get('profile_id') in [2, 3]:  # Admin/Principal
                cursor.execute("EXEC Proc_Certificates_Get @School_ID = %s, @StudentID = NULL", [user.get('school_id')])
            else:  # Student
                cursor.execute("EXEC Proc_Certificates_Get @School_ID = %s, @StudentID = %s", 
                             [user.get('school_id'), user.get('student_id')])
            
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            documents = [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Error: {e}")
        documents = []
    
    context.update({
        'user': user,
        'documents': documents
    })
    return render(request, 'documents/view_documents.html', context)

@require_http_methods(["GET"])
def download_certificate(request, certificate_id):
    """Generate and download certificate PDF"""
    user = request.session.get('user', {})
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Certificate_ID, CertificateType, CertificateNumber, CertificateData, IssueDate, Remarks
                FROM CertificateDocuments
                WHERE Certificate_ID = %s AND School_ID = %s
            """, [certificate_id, user.get('school_id')])
            
            row = cursor.fetchone()
            if not row:
                messages.error(request, 'Certificate not found')
                return redirect('view_documents')
            
            cert_info = json.loads(row[3]) if row[3] else {}
        
        # Generate PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawCentredString(width/2, height - 1*inch, cert_info.get('school_name', ''))
        
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width/2, height - 1.5*inch, row[1])
        
        # Certificate Number
        p.setFont("Helvetica", 10)
        p.drawString(1*inch, height - 2*inch, f"Certificate No: {row[2]}")
        p.drawRightString(width - 1*inch, height - 2*inch, f"Date: {row[4].strftime('%d-%m-%Y')}")
        
        # Content
        y = height - 3*inch
        p.setFont("Helvetica", 12)
        p.drawString(1*inch, y, f"This is to certify that {cert_info.get('student_name', '')}")
        y -= 0.3*inch
        p.drawString(1*inch, y, f"S/o or D/o {cert_info.get('father_name', '')}")
        y -= 0.3*inch
        p.drawString(1*inch, y, f"Class: {cert_info.get('class', '')} {cert_info.get('section', '')}")
        y -= 0.3*inch
        p.drawString(1*inch, y, f"Roll No: {cert_info.get('roll_no', '')}")
        
        if row[5]:
            y -= 0.5*inch
            p.drawString(1*inch, y, f"Remarks: {row[5]}")
        
        # Footer
        p.setFont("Helvetica", 10)
        p.drawRightString(width - 1*inch, 2*inch, "Principal's Signature")
        p.drawRightString(width - 1*inch, 1.7*inch, "_________________")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{row[1]}_{cert_info.get("roll_no", "")}.pdf"'
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        messages.error(request, 'Error generating certificate')
        return redirect('view_documents')
