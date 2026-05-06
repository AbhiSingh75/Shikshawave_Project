from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from .views import custom_login_required, get_context
from .utils import get_school_dropdown
import logging

logger = logging.getLogger(__name__)

@custom_login_required
def admission_instructions(request):
    context = get_context(request)
    
    # Get session info
    school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else None
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Fallback
    if not school_id:
        school_id = request.session.get('SchoolID')

    # Super Admin Logic
    if profile_id == 1:
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
        
        # If no school selected, show empty or prompt
        if not school_id:
            context['instructions'] = []
            context['selected_school_id'] = ''
            return render(request, 'admission_instructions.html', context)
    else:
        context['is_super_admin'] = False

    context['selected_school_id'] = school_id
    
    # Fetch Instructions
    instructions = []
    if school_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_AdmissionInstructions_List"(%s)
                """, [school_id])
                
                # Columns: InstructionID, InstructionTitle, InstructionText, DisplayOrder, IsActive, CreatedAt
                rows = cursor.fetchall()
                for row in rows:
                    instructions.append({
                        'InstructionID': row[0],
                        'InstructionTitle': row[1],
                        'InstructionText': row[2],
                        'DisplayOrder': row[3],
                        'IsActive': bool(row[4]),
                        'CreatedAt': row[5]
                    })
        except Exception as e:
            logger.error(f"Error fetching instructions: {e}")
    
    context['instructions'] = instructions
    return render(request, 'admission_instructions.html', context)

@custom_login_required
def admission_instructions_save(request):
    if request.method != 'POST':
        return redirect('admission_instructions')
    
    # Get user info
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    # Get school_id - from POST for Super Admin, from session for others
    school_id = request.POST.get('school_id')
    if not school_id:
        school_id = request.session.get('SchoolID')
    
    instruction_id = request.POST.get('instruction_id') or None
    title = request.POST.get('title')
    text = request.POST.get('text')
    display_order = request.POST.get('display_order', 0)
    is_active = True if request.POST.get('is_active') else False
    
    # Convert instruction_id to int or None
    try:
        instruction_id = int(instruction_id) if instruction_id else None
    except (ValueError, TypeError):
        instruction_id = None
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_AdmissionInstructions_Save"(%s, %s, %s, %s, %s, %s, %s)
            """, [instruction_id, school_id, title, text, display_order, is_active, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                messages.success(request, result[1])
            else:
                msg = result[1] if result else 'Failed to save instruction'
                messages.error(request, msg)
    except Exception as e:
        logger.error(f"Error saving instruction: {e}")
        messages.error(request, f'Failed to save instruction: {str(e)}')
    
    # Redirect back, preserving school selection for super admin
    if school_id and request.POST.get('school_id'):
        return redirect(f"/master-data/admission-instructions/?school_id={school_id}")
    
    return redirect('admission_instructions')

@custom_login_required
def admission_instructions_delete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    # Get school_id - from POST for Super Admin, from session for others
    school_id = request.POST.get('school_id')
    if not school_id:
        school_id = request.session.get('SchoolID')
        
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    instruction_id = request.POST.get('instruction_id')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_AdmissionInstructions_Delete"(%s, %s, %s)
            """, [instruction_id, school_id, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                return JsonResponse({'status': 'SUCCESS', 'message': result[1]})
            else:
                msg = result[1] if result else 'Failed to delete'
                return JsonResponse({'status': 'ERROR', 'message': msg})
    except Exception as e:
        logger.error(f"Error deleting instruction: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})

@custom_login_required
def admission_instructions_load(request):
    """AJAX endpoint to load instructions for a specific school (Super Admin use)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    school_id = request.POST.get('school_id')
    
    try:
        instructions = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_AdmissionInstructions_List"(%s)
            """, [school_id])
            
            rows = cursor.fetchall()
            for row in rows:
                instructions.append({
                    'InstructionID': row[0],
                    'InstructionTitle': row[1],
                    'InstructionText': row[2],
                    'DisplayOrder': row[3],
                    'IsActive': 1 if row[4] else 0,
                    'CreatedAt': str(row[5]) if row[5] else None
                })
        
        return JsonResponse({'status': 'SUCCESS', 'data': instructions})
    except Exception as e:
        logger.error(f"Error loading instructions: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
