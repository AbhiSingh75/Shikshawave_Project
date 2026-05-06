# core/data_import/views.py
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_http_methods
from core.views import custom_login_required, get_context
from .models import DataImportLog, DataImportError
from .processors import get_processor
from .templates_generator import generate_excel_template
import logging

logger = logging.getLogger(__name__)


@custom_login_required
def import_dashboard(request):
    """Main dashboard for data imports"""
    context = get_context(request)
    
    school_id = request.session.get('SchoolID')
    profile_id = request.session.get('ProfileID')
    
    # Get import history
    if profile_id == 1:  # Super Admin
        imports = DataImportLog.objects.all()[:50]
    else:  # School Admin
        imports = DataImportLog.objects.filter(school_id=school_id)[:50]
    
    # Get import type choices
    import_types = [
        {'value': 'Students', 'label': 'Students'},
        {'value': 'Teachers', 'label': 'Teachers'},
        {'value': 'Salary', 'label': 'Salary Components'},
        {'value': 'Fee', 'label': 'Fee History'},
        {'value': 'Attendance', 'label': 'Attendance History'},
        {'value': 'Exam', 'label': 'Exams'},
        {'value': 'ExamResult', 'label': 'Exam Results'},
        {'value': 'ClassMaster', 'label': 'Class Master'},
        {'value': 'SectionMaster', 'label': 'Section Master'},
        {'value': 'SubjectMaster', 'label': 'Subject Master'},
    ]
    
    context.update({
        'imports': imports,
        'import_types': import_types,
        'show_school_dropdown': profile_id == 1
    })
    
    return render(request, 'data_import/import_dashboard.html', context)


@custom_login_required
@require_http_methods(["GET"])
def download_template(request, import_type):
    """Download Excel template for specific import type"""
    try:
        file_path = generate_excel_template(import_type)
        
        if not file_path or not os.path.exists(file_path):
            messages.error(request, "Template not found")
            return redirect('import_dashboard')
        
        response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{import_type}_Import_Template.xlsx"'
        return response
        
    except Exception as e:
        logger.error(f"Error downloading template: {e}")
        messages.error(request, f"Error downloading template: {str(e)}")
        return redirect('import_dashboard')


@custom_login_required
@require_http_methods(["POST"])
def upload_file(request):
    """Handle file upload and validation with column checking"""
    try:
        import_type = request.POST.get('import_type')
        school_id = request.POST.get('school_id') or request.session.get('SchoolID')
        uploaded_file = request.FILES.get('import_file')
        
        if not all([import_type, school_id, uploaded_file]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Validate file type
        if not uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
            return JsonResponse({'success': False, 'error': 'Only Excel (.xlsx, .xls) or CSV files are allowed'}, status=400)
        
        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size exceeds 10MB limit'}, status=400)
        
        # Save file
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'import_files')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{import_type}_{school_id}_{uploaded_file.name}")
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Create processor
        processor = get_processor(import_type, int(school_id), file_path, request.session.get('UserId'))
        
        # Read Excel/CSV
        df = processor.read_excel()
        total_rows = len(df)
        
        # Validate columns for Students
        column_validation = None
        if import_type == 'Students':
            column_validation = processor.validate_columns(df)
            if not column_validation['valid']:
                return JsonResponse({
                    'success': False,
                    'error': 'Column mismatch detected',
                    'column_validation': column_validation
                }, status=400)
        
        # Create import log
        import_id = processor.create_import_log(uploaded_file.name, uploaded_file.size, total_rows)
        
        # Validate data and save to staging
        if import_type == 'Students':
            processor.save_to_staging(df)
            
            # Count valid/invalid from staging
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN IsValid = 1 THEN 1 ELSE 0 END) as ValidCount,
                        SUM(CASE WHEN IsValid = 0 THEN 1 ELSE 0 END) as InvalidCount
                    FROM Student_Staging WHERE ImportID = %s
                """, [import_id])
                result = cursor.fetchone()
                valid_rows = result[0] or 0
                invalid_rows = result[1] or 0
        else:
            valid_rows, invalid_rows = processor.validate_data(df)
        
        return JsonResponse({
            'success': True,
            'import_id': import_id,
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'column_validation': column_validation,
            'message': f'Validation complete: {valid_rows} valid, {invalid_rows} invalid rows'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
def preview_data(request, import_id):
    """Preview validated data before import"""
    try:
        import_log = DataImportLog.objects.get(import_id=import_id)
        
        # Check access
        profile_id = request.session.get('ProfileID')
        school_id = request.session.get('SchoolID')
        
        if profile_id != 1 and import_log.school_id != school_id:
            messages.error(request, "Access denied")
            return redirect('import_dashboard')
        
        # Get errors
        errors = DataImportError.objects.filter(import_log=import_log)[:100]  # Limit to first 100
        
        context = get_context(request)
        context.update({
            'import_log': import_log,
            'errors': errors,
            'has_more_errors': errors.count() > 100
        })
        
        return render(request, 'data_import/preview_data.html', context)
        
    except DataImportLog.DoesNotExist:
        messages.error(request, "Import not found")
        return redirect('import_dashboard')
    except Exception as e:
        logger.error(f"Preview error: {e}")
        messages.error(request, f"Error loading preview: {str(e)}")
        return redirect('import_dashboard')


@custom_login_required
@require_http_methods(["POST"])
def execute_import(request, import_id):
    """Execute the actual import"""
    try:
        import_log = DataImportLog.objects.get(import_id=import_id)
        
        # Check access
        profile_id = request.session.get('ProfileID')
        school_id = request.session.get('SchoolID')
        
        if profile_id != 1 and import_log.school_id != school_id:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
        
        # Check if already imported
        if import_log.status in ['Completed', 'Importing']:
            return JsonResponse({'success': False, 'error': 'Import already in progress or completed'}, status=400)
        
        # Check if validation passed
        if import_log.invalid_rows > 0:
            return JsonResponse({'success': False, 'error': f'{import_log.invalid_rows} rows have validation errors. Please fix and re-upload.'}, status=400)
        
        # Get processor and execute
        processor = get_processor(
            import_log.import_type,
            import_log.school_id,
            import_log.file_path,
            request.session.get('UserId')
        )
        processor.import_log = import_log
        
        # Read data again
        df = processor.read_excel()
        
        # Execute import
        result = processor.execute_import(df)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'success_count': result['success_count'],
                'failure_count': result['failure_count'],
                'message': result['message']
            })
        else:
            return JsonResponse({'success': False, 'error': result['error']}, status=500)
        
    except DataImportLog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Import not found'}, status=404)
    except Exception as e:
        logger.error(f"Execute import error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
def import_status(request, import_id):
    """Get import status (for polling)"""
    try:
        import_log = DataImportLog.objects.get(import_id=import_id)
        
        return JsonResponse({
            'success': True,
            'status': import_log.status,
            'total_rows': import_log.total_rows,
            'valid_rows': import_log.valid_rows,
            'invalid_rows': import_log.invalid_rows,
            'success_rows': import_log.success_rows,
            'failed_rows': import_log.failed_rows,
            'progress': int((import_log.success_rows + import_log.failed_rows) / import_log.total_rows * 100) if import_log.total_rows > 0 else 0
        })
        
    except DataImportLog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Import not found'}, status=404)


@custom_login_required
def download_errors(request, import_id):
    """Download error report"""
    try:
        import_log = DataImportLog.objects.get(import_id=import_id)
        
        # Check access
        profile_id = request.session.get('ProfileID')
        school_id = request.session.get('SchoolID')
        
        if profile_id != 1 and import_log.school_id != school_id:
            messages.error(request, "Access denied")
            return redirect('import_dashboard')
        
        # Generate error report if not exists
        if not import_log.error_file_generated:
            processor = get_processor(
                import_log.import_type,
                import_log.school_id,
                import_log.file_path,
                request.session.get('UserId')
            )
            processor.import_log = import_log
            error_file_path = processor.generate_error_report()
        else:
            error_file_path = import_log.error_file_path
        
        if not error_file_path or not os.path.exists(error_file_path):
            messages.error(request, "Error report not found")
            return redirect('import_dashboard')
        
        response = FileResponse(open(error_file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="Import_Errors_{import_id}.xlsx"'
        return response
        
    except DataImportLog.DoesNotExist:
        messages.error(request, "Import not found")
        return redirect('import_dashboard')
    except Exception as e:
        logger.error(f"Download errors error: {e}")
        messages.error(request, f"Error downloading error report: {str(e)}")
        return redirect('import_dashboard')


@custom_login_required
@require_http_methods(["GET"])
def get_staging_preview(request, import_id):
    """Get preview of staging data with valid and invalid rows"""
    try:
        import_log = DataImportLog.objects.get(import_id=import_id)
        
        # Check access
        profile_id = request.session.get('ProfileID')
        school_id = request.session.get('SchoolID')
        
        if profile_id != 1 and import_log.school_id != school_id:
            return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
        
        # Get staging data
        with connection.cursor() as cursor:
            # Get valid rows (limit to 100 for preview)
            cursor.execute("""
                SELECT TOP 100 RowNumber, FullName, Gender, DateOfBirth, ParentMobile, 
                       FatherName, AdmissionClass, Section, AdmissionDate
                FROM Student_Staging
                WHERE ImportID = %s AND IsValid = 1
                ORDER BY RowNumber
            """, [import_id])
            
            valid_rows = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                valid_rows.append(dict(zip(columns, row)))
            
            # Get invalid rows with errors
            cursor.execute("""
                SELECT TOP 100 RowNumber, FullName, Gender, ParentMobile, ErrorMessages
                FROM Student_Staging
                WHERE ImportID = %s AND IsValid = 0
                ORDER BY RowNumber
            """, [import_id])
            
            invalid_rows = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                if row_dict['ErrorMessages']:
                    row_dict['ErrorMessages'] = json.loads(row_dict['ErrorMessages'])
                invalid_rows.append(row_dict)
        
        return JsonResponse({
            'success': True,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'valid_count': import_log.valid_rows,
            'invalid_count': import_log.invalid_rows,
            'total_count': import_log.total_rows
        })
        
    except DataImportLog.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Import not found'}, status=404)
    except Exception as e:
        logger.error(f"Preview error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
@require_http_methods(["GET"])
def get_expected_columns(request, import_type):
    """Get expected column structure for import type"""
    try:
        if import_type == 'Students':
            from .validators import StudentValidator
            validator = StudentValidator(0, import_type)
            return JsonResponse({
                'success': True,
                'columns': validator.EXPECTED_COLUMNS,
                'required_columns': [
                    'FullName', 'Gender', 'DateOfBirth', 'ParentMobile',
                    'FatherName', 'AdmissionClass', 'Section', 'AdmissionDate'
                ]
            })
        else:
            return JsonResponse({'success': False, 'error': 'Import type not supported'}, status=400)
    except Exception as e:
        logger.error(f"Get columns error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@custom_login_required
@require_http_methods(["POST"])
def save_grid_data(request):
    """Save student data from grid entry"""
    try:
        import json
        data = json.loads(request.body)
        school_id = data.get('school_id')
        students = data.get('students', [])
        
        if not school_id or not students:
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)
        
        # Create import log
        import_log = DataImportLog.objects.create(
            school_id=school_id,
            import_type='Students',
            file_name='Grid Entry',
            total_rows=len(students),
            created_by_id=request.session.get('UserId'),
            status='Pending'
        )
        
        # Save to staging
        from .processors import StudentImportProcessor
        import pandas as pd
        
        df = pd.DataFrame(students)
        processor = StudentImportProcessor(school_id, 'Students', '', request.session.get('UserId'))
        processor.import_log = import_log
        processor.save_to_staging(df)
        
        # Execute import
        result = processor.execute_import(df)
        
        return JsonResponse({
            'success': result['success'],
            'success_count': result.get('success_count', 0),
            'failure_count': result.get('failure_count', 0),
            'message': result.get('message', '')
        })
        
    except Exception as e:
        logger.error(f"Grid save error: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
