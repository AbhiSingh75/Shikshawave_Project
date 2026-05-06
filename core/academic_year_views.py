from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from .views import custom_login_required, get_context
from .utils import get_school_dropdown, execute_procedure_with_messages
import logging

logger = logging.getLogger(__name__)

@custom_login_required
def academic_year(request):
    try:
        context = get_context(request)
        
        # Get session info
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else None
        profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
        
        # Fallback
        if not school_id:
            school_id = request.session.get('SchoolID')

        # Super Admin / Support Executive Logic
        if profile_id in [1, 11]:
            context['is_super_admin'] = True
            
            # Get schools for dropdown
            schools = get_school_dropdown()
            context['schools'] = schools
            
            # Check for school_id filter
            filter_school_id = request.GET.get('school_id')
            if filter_school_id:
                try:
                    school_id = int(filter_school_id)
                except ValueError:
                    pass
            
            # If no school selected, show organization-wide for Super Admin
            if not school_id:
                school_id = 0
                context['selected_school_id'] = ''
            else:
                context['selected_school_id'] = school_id
        else:
            context['is_super_admin'] = False

        # Fetch Academic Years using new procedure
        academic_years = []
        if school_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_AcademicYear_List"(%s)
                """, [school_id])
                
                # Fetch all rows
                rows = cursor.fetchall()
                
                # Manual mapping since procedure returns table
                # Columns: AcademicYearID, SchoolID, AcademicYear, StartDate, EndDate, IsCurrent, IsActive
                for row in rows:
                    academic_years.append({
                        'AcademicYearID': row[0],
                        'SchoolID': row[1],
                        'AcademicYear': row[2],
                        'StartDate': row[3],
                        'EndDate': row[4],
                        'IsCurrent': bool(row[5]),  # Convert to proper Python bool
                        'IsActive': bool(row[6])    # Convert to proper Python bool
                    })

        context['academic_years'] = academic_years
        return render(request, 'academic_year.html', context)
        
    except Exception as e:
        logger.error(f"Error in academic_year view: {str(e)}", exc_info=True)
        messages.error(request, f"Error processing request: {str(e)}")
        return redirect('dashboard')

@custom_login_required
def academic_year_save(request):
    if request.method != 'POST':
        return redirect('academic_year')
    
    try:
        # Get user info
        user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
        
        # Get form data
        school_id = request.POST.get('school_id') 
        # For non-super admin, get from session
        if not school_id:
             school_id = request.session.get('SchoolID')
             
        academic_year_id = request.POST.get('academic_year_id')
        academic_year = request.POST.get('academic_year')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_current = True if request.POST.get('is_current') else False
        is_active = True if request.POST.get('is_active') else False
        
        if not school_id:
            messages.error(request, "School ID is missing.")
            return redirect('academic_year')
            
        with connection.cursor() as cursor:
            # Use Proc_AcademicYear_Set for both Insert (ID=None) and Update
            # Procedure params: ID, SchoolID, Year, Start, End, IsCurrent, IsActive, UserID
            
            # Handle empty ID for insert
            params_id = int(academic_year_id) if academic_year_id else None
            
            # Debug logging
            logger.info(f"Academic Year Save - ID: {params_id}, School: {school_id}, Year: {academic_year}, Start: {start_date}, End: {end_date}, IsCurrent: {is_current}, IsActive: {is_active}, UserID: {user_id}")
            
            cursor.execute("""
                SELECT * FROM "Proc_AcademicYear_Set"(%s, %s, %s, %s, %s, %s, %s, %s)
            """, [params_id, school_id, academic_year, start_date, end_date, is_current, is_active, user_id])
            
            result = cursor.fetchone()
            logger.info(f"Academic Year Save - Result: {result}")
            
            if result and result[0] == 'SUCCESS':
                messages.success(request, result[1])
            else:
                msg = result[1] if result else "Unknown error"
                messages.error(request, f"Failed: {msg}")
                
    except Exception as e:
        logger.error(f"Error saving academic year: {e}", exc_info=True)
        messages.error(request, f"Error saving academic year: {str(e)}")
    
    # Redirect back, preserving school selection for super admin
    redirect_url = 'academic_year'
    if school_id and request.POST.get('school_id'): # If it was posted (Super Admin context)
         return redirect(f"/master-data/academic-year/?school_id={school_id}")

    return redirect(redirect_url)

@custom_login_required
def academic_year_delete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    try:
        school_id = request.POST.get('school_id') # Changed to accept from POST to support Super Admin deletions
        if not school_id:
             school_id = request.session.get('SchoolID')
             
        academic_year_id = request.POST.get('academic_year_id')
        user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_AcademicYear_Delete"(%s, %s, %s)
            """, [academic_year_id, school_id, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                return JsonResponse({'status': 'SUCCESS', 'message': result[1]})
            else:
                msg = result[1] if result else "Failed to delete"
                return JsonResponse({'status': 'ERROR', 'message': msg})
                
    except Exception as e:
        logger.error(f"Error deleting academic year: {e}", exc_info=True)
        return JsonResponse({'status': 'ERROR', 'message': str(e)})

@custom_login_required
def academic_year_load(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    school_id = request.POST.get('school_id')
    
    try:
        academic_years = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_AcademicYear_List"(%s)
            """, [school_id])
            
            rows = cursor.fetchall()
            for row in rows:
                academic_years.append({
                    'AcademicYearID': row[0],
                    'SchoolID': row[1],
                    'AcademicYear': row[2],
                    'StartDate': str(row[3]) if row[3] else None, # Convert date to string
                    'EndDate': str(row[4]) if row[4] else None,   # Convert date to string
                    'IsCurrent': 1 if row[5] else 0,
                    'IsActive': 1 if row[6] else 0
                })
        
        return JsonResponse({'status': 'SUCCESS', 'data': academic_years})
    except Exception as e:
        logger.error(f"Error loading academic years: {e}", exc_info=True)
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
