from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from core.decorators import custom_login_required
from core.utils import execute_procedure_with_messages, get_school_dropdown, safe_int, get_context
from core.url_encryption import encrypt_id, decrypt_id
import logging
import json

logger = logging.getLogger(__name__)

@csrf_exempt
@custom_login_required
def add_class(request):
    """
    Add Class page - Create new class and sections
    """
    # Get session info
    context = get_context(request)
    # Corrected session access: use custom_user (lowercase keys) or fallback to standard session
    school_id = None
    user_id = None
    
    if hasattr(request, 'custom_user') and request.custom_user:
        school_id = request.custom_user.get('school_id')
        user_id = request.custom_user.get('user_id')
    
    # Fallback to standard session if custom_user doesn't have it
    if not school_id:
        school_id = request.session.get('SchoolID')
    if not user_id:
        user_id = request.session.get('UserId')
    
    # Security Enforcement: Non-Super Admins (profile_id != 1) MUST use their session school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin Logic: Allow override via POST/GET
        school_id_param = request.POST.get('school_id') or request.GET.get('school_id')
        if school_id_param:
            decrypted = decrypt_id(school_id_param)
            school_id = decrypted if decrypted else (int(school_id_param) if str(school_id_param).isdigit() else school_id)
        
        if not school_id:
            school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')

    school_list = []
    if profile_id == 1:
        raw_schools = get_school_dropdown()
        for s in raw_schools:
            s['EncryptedSchoolID'] = encrypt_id(s['SchoolID'])
            school_list.append(s)

    if not school_id and not (profile_id == 1):
        messages.error(request, "School information not found. Please contact support if this persists.")
        return redirect('dashboard')
    
    # Update context with schools if available
    if school_list:
        context['schools_list'] = school_list
        context['selected_school_id'] = school_id # Raw ID for comparison
        
    if request.method == 'POST':
        try:
            # For POST requests, prioritize form data for school_id
            post_school_id = request.POST.get('school_id')
            if post_school_id:
                decrypted_school_id = decrypt_id(post_school_id)
                if decrypted_school_id:
                    school_id = decrypted_school_id
                else:
                     try:
                        school_id = int(post_school_id)
                     except:
                        pass
            
            # If still no school_id, validation error
            if not school_id:
                 messages.error(request, "Please select a school to add/edit classes for.")
                 return redirect('view_class')

            # Get form data
            class_name = request.POST.get('class_name', '').strip()
            class_code = request.POST.get('class_code', '').strip()
            education_level = request.POST.get('education_level', '').strip()
            description = request.POST.get('description', '').strip()
            
            # Check if this is an update operation
            edit_mode = request.POST.get('edit_mode') in ['1', 'true']
            encrypted_class_id = request.POST.get('class_id', '')
            class_id = None
            if encrypted_class_id:
                decrypted = decrypt_id(encrypted_class_id)
                if decrypted:
                    class_id = decrypted
                else:
                    try:
                        class_id = int(encrypted_class_id)
                    except:
                        pass
            
            # Get sections data
            section_names = request.POST.getlist('section_name[]')
            section_capacities = request.POST.getlist('section_capacity[]')
            section_rooms = request.POST.getlist('section_room[]')
            
            # Validation
            if not class_name or not class_code or (edit_mode and not class_id):
                if not class_name: messages.error(request, "Class name is required.")
                if not class_code: messages.error(request, "Class code is required.")
                if edit_mode and not class_id: messages.error(request, "Class ID is required for update.")
                
                url = reverse('view_class')
                if profile_id == 1 and school_id:
                    url += f"?school_id={encrypt_id(school_id)}"
                return redirect(url)
            
            # Handle update or create operation
            if edit_mode:
                try:
                    # Update existing class
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT * FROM "Proc_Class_Set"(%s, %s, %s, %s, %s, %s, %s, %s)
                        """, [class_id, school_id, class_name, class_code, education_level, description, True, user_id])
                        
                        result = cursor.fetchone()
                        if result and result[0]:
                            messages.success(request, f"Class '{class_name}' updated successfully!")
                            
                            # Handle sections update
                            if section_names:
                                section_ids = request.POST.getlist('section_id[]')
                                
                                # 1. Sync Delete: Delete sections not in the submitted list
                                decoded_section_ids = []
                                for sid in section_ids:
                                    if sid and sid.strip():
                                        try:
                                            dec_sid = decrypt_id(sid)
                                            if dec_sid:
                                                decoded_section_ids.append(int(dec_sid))
                                            else:
                                                decoded_section_ids.append(int(sid))
                                        except:
                                            pass

                                if decoded_section_ids:
                                    cursor.execute("""
                                        UPDATE "SectionMaster" 
                                        SET "IsDeleted" = TRUE, "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                                        WHERE "ClassID" = %s AND "IsDeleted" = FALSE AND "SectionID" NOT IN %s
                                    """, [user_id, class_id, tuple(decoded_section_ids)])
                                else:
                                    cursor.execute("""
                                        UPDATE "SectionMaster" 
                                        SET "IsDeleted" = TRUE, "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                                        WHERE "ClassID" = %s AND "IsDeleted" = FALSE
                                    """, [user_id, class_id])
                                
                                # 2. Upsert sections
                                for i, section_name in enumerate(section_names):
                                    if section_name.strip():
                                        raw_sid = section_ids[i] if i < len(section_ids) and section_ids[i].strip() else None
                                        sid = None
                                        if raw_sid:
                                            try:
                                                dec_sid = decrypt_id(raw_sid)
                                                sid = int(dec_sid) if dec_sid else int(raw_sid)
                                            except:
                                                sid = None

                                        try:
                                            capacity = int(section_capacities[i]) if i < len(section_capacities) and section_capacities[i].strip() else None
                                        except (ValueError, TypeError):
                                            capacity = None

                                        room = section_rooms[i].strip() if i < len(section_rooms) and section_rooms[i] else None
                                        
                                        cursor.execute("""
                                            SELECT * FROM "Proc_Section_Set"(%s, %s, %s, %s, %s, %s, %s)
                                        """, [sid, class_id, section_name.strip(), capacity, room, True, user_id])
                            
                            url = reverse('view_class')
                            if profile_id == 1 and school_id:
                                url += f"?school_id={encrypt_id(school_id)}"
                            return redirect(url)
                        else:
                            error_msg = result[1] if result and len(result) > 1 else "Unknown error occurred"
                            messages.error(request, f"Error updating class: {error_msg}")
                            
                except Exception as e:
                    error_message = str(e)
                    if "already exists" in error_message.lower():
                        messages.error(request, f"Class with name '{class_name}' or code '{class_code}' already exists.")
                    else:
                        messages.error(request, f"Error updating class: {error_message}")
                    
                    url = reverse('view_class')
                    if profile_id == 1 and school_id:
                        url += f"?school_id={encrypt_id(school_id)}"
                    return redirect(url)
            else:
                # Create new class
                try:
                    with connection.cursor() as cursor:
                        procedure_sql = """
                            SELECT * FROM "Proc_Class_Set"(%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        params = [None, school_id, class_name, class_code, education_level or None, description or None, True, user_id]
                        result, proc_messages = execute_procedure_with_messages(cursor, procedure_sql, params)
                    
                        if result:
                            class_id = result[0]
                            
                            # Create sections
                            if section_names:
                                for i, section_name in enumerate(section_names):
                                    if section_name.strip():
                                        try:
                                            capacity = int(section_capacities[i]) if i < len(section_capacities) and section_capacities[i].strip() else None
                                        except (ValueError, TypeError):
                                            capacity = None
                                        room_number = section_rooms[i] if i < len(section_rooms) and section_rooms[i] else None
                                        
                                        cursor.execute("""
                                            SELECT * FROM "Proc_Section_Set"(%s, %s, %s, %s, %s, %s, %s)
                                        """, [None, class_id, section_name.strip(), capacity, room_number, True, user_id])
                            
                            messages.success(request, f"Class '{class_name}' created successfully!")
                            url = reverse('add_class')
                            if profile_id == 1 and school_id:
                                url += f"?school_id={encrypt_id(school_id)}"
                            return redirect(url)
                        else:
                            raise ValueError("Failed to create class")
                        
                except Exception as e:
                    error_message = str(e)
                    if "already exists" in error_message.lower():
                        messages.error(request, f"Class with name '{class_name}' or code '{class_code}' already exists.")
                    else:
                        messages.error(request, f"Error creating class: {error_message}")
                    
                    url = reverse('view_class')
                    if profile_id == 1 and school_id:
                        url += f"?school_id={encrypt_id(school_id)}"
                    return redirect(url)
                    
        except Exception as e:
            logger.error(f"Error in add_class POST: {str(e)}", exc_info=True)
            messages.error(request, "An unexpected error occurred.")
    
    # Final fallback: redirect to view_class
    url = reverse('view_class')
    if profile_id == 1 and school_id:
        url += f"?school_id={encrypt_id(school_id)}"
    return redirect(url)


@csrf_exempt
@custom_login_required
def view_class(request):
    """
    View Class page - Display all classes and their sections
    """
    # Get session info
    context = get_context(request)
    
    # Check Profile ID
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Prioritize GET/URL school_id
        school_id_param = request.GET.get('school_id')
        school_id = None
        if school_id_param:
            decrypted = decrypt_id(school_id_param)
            school_id = decrypted if decrypted else (int(school_id_param) if str(school_id_param).isdigit() else None)
        
        # Finally fallback to session if no specific school selected
        if not school_id:
             school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')

    # Fetch school list for Super Admin dropdown
    school_list = []
    if profile_id == 1:
        raw_schools = get_school_dropdown()
        for s in raw_schools:
            s['EncryptedSchoolID'] = encrypt_id(s['SchoolID'])
            school_list.append(s)

    # Finalize school context ensuring proper types for template comparison
    if school_id:
        try:
            school_id = int(school_id)
        except (ValueError, TypeError):
            pass

    # Ensure context contains both variables for maximum template backward/forward compatibility
    context['selected_school_id'] = school_id
    context['school_id'] = school_id  # Update global context for this view
    context['schools_list'] = school_list
    
    if not school_id and not (profile_id == 1):
        messages.error(request, "School information not found. Please contact support if this persists.")
        return redirect('dashboard')
        
    # If Super Admin and no school selected yet, render empty view with dropdown
    if not school_id and profile_id == 1:
        context.update({
            'classes': [],
            'class_sections': {},
            'dark_mode': request.session.get('dark_mode', False)
        })
        return render(request, 'view_class.html', context)
    
    # Get all classes with their sections using the new stored procedure
    try:
        with connection.cursor() as cursor:
            # Get class list
            cursor.execute("""
                SELECT * FROM "Proc_Class_List"(%s)
            """, [school_id])
            classes = cursor.fetchall()
            
            # Get sections for each class using the same procedure
            class_sections = {}
            processed_classes = []
            
            for class_data in classes:
                class_id = class_data[0] # Raw ID
                enc_id = encrypt_id(class_id)
                # Append encrypted ID to class tuple
                processed_classes.append(class_data + (enc_id,))
                
                cursor.execute("""
                    SELECT * FROM "Proc_Section_List"(%s, %s)
                """, [school_id, class_id])
                sections = cursor.fetchall()
                # Encrypt section IDs (which are at index 0)
                processed_sections = []
                for sec in sections:
                     processed_sections.append(sec + (encrypt_id(sec[0]),))
                
                class_sections[class_id] = processed_sections
            
            classes = processed_classes
                
    except Exception as e:
        logger.error(f"Error fetching classes: {str(e)}", exc_info=True)
        messages.error(request, "Error loading class data. Please try again.")
        classes = []
        class_sections = {}
    
    context.update({
        'classes': classes,
        'class_sections': class_sections,
        'dark_mode': request.session.get('dark_mode', False)
    })
    
    return render(request, 'view_class.html', context)


@custom_login_required
def get_class_sections(request, class_id):
    """
    Get sections for a specific class via AJAX
    """
    # Decrypt class_id
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
         # Try raw if decrypt fails (temporary fallback or error)
         try:
             decrypted_id = int(class_id)
         except:
             return JsonResponse({'error': 'Invalid Class ID', 'success': False}, status=400)
    
    class_id = decrypted_id

    # Authorization check
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Prioritize GET encrypted ID
        encrypted_school_id = request.GET.get('school_id')
        school_id = None
        if encrypted_school_id:
            decrypted = decrypt_id(encrypted_school_id)
            school_id = decrypted if decrypted else (int(encrypted_school_id) if str(encrypted_school_id).isdigit() else None)
        
        # Finally fallback to session
        if not school_id:
            school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    
    if not school_id:
        return JsonResponse({'error': 'School authorization failed', 'success': False}, status=403)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_Section_List"(%s, %s)
            """, [school_id, class_id])
            sections = cursor.fetchall()
            
            # Convert to list of dictionaries for JSON response
            sections_data = []
            for section in sections:
                sections_data.append({
                    'section_id': encrypt_id(section[0]), # Encrypt ID
                    'class_id': encrypt_id(section[1]),   # Encrypt ID
                    'section_name': section[2],
                    'capacity': section[3],
                    'room_number': section[4],
                    'status': section[5]
                })
            
            return JsonResponse({
                'success': True,
                'sections': sections_data
            })
            
    except Exception as e:
        logger.error(f"Error fetching sections for class {class_id}: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Error loading section data'}, status=500)


@custom_login_required
def get_class_data(request, class_id):
    """
    Get class data for inline editing via AJAX
    """
    # Decrypt ID
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
        try:
             decrypted_id = int(class_id)
        except:
             return JsonResponse({'error': 'Invalid Class ID'}, status=400)
    class_id = decrypted_id

    # Authorization check
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Fallback to session if no specific context provided (GET param could be added if needed)
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    
    if not school_id:
        return JsonResponse({'error': 'School authorization failed'}, status=403)
    
    try:
        with connection.cursor() as cursor:
            # 1. Get Class Details
            try:
                logger.info(f"Executing query to get class data for class_id: {class_id}")
                cursor.execute("""
                    SELECT * FROM "Proc_Class_List"(%s) WHERE "ClassID" = %s
                """, [school_id, class_id])
                class_data = cursor.fetchone()
                
                if not class_data:
                    logger.error(f"Class not found for class_id: {class_id}, school_id: {school_id}")
                    return JsonResponse({'error': 'Class not found'}, status=404)
                
                # Map tuple to dict (based on func_class_list return columns)
                class_dict = {
                    'class_id': class_data[0],
                    'class_name': class_data[1],
                    'class_code': class_data[2],
                    'education_level': class_data[3],
                    'description': class_data[4],
                    'is_active': class_data[5]
                }
            except Exception as e:
                logger.error(f"Error getting class details: {e}")
                return JsonResponse({'error': 'Error loading class details'}, status=500)
            
            # 2. Get Sections
            try:
                logger.info(f"Executing query to get sections for class_id: {class_id}")
                cursor.execute("""
                    SELECT * FROM "Proc_Section_List"(%s, %s)
                """, [school_id, class_id])
                sections = cursor.fetchall()
            except Exception as e:
                logger.error(f"Error getting sections: {e}")
                return JsonResponse({'error': 'Error loading sections'}, status=500)
            
            # Convert sections to list of dicts
            sections_list = []
            for section in sections:
                sections_list.append({
                    'section_id': section[0],
                    'section_name': section[2],
                    'capacity': section[3],
                    'room_number': section[4],
                    'is_active': section[5]
                })

            response_data = {
                'success': True,
                'class_data': class_dict,
                'sections': sections_list
            }
            logger.info(f"Returning response data: {response_data}")
            return JsonResponse(response_data)
            
    except Exception as e:
        logger.error(f"Error fetching class data: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Error loading data'}, status=500)


@custom_login_required
def edit_class(request, class_id):
    """
    Edit Class page - Display form to edit existing class and handle updates
    """
    # Decrypt ID
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
        try:
             decrypted_id = int(class_id)
        except:
             messages.error(request, "Invalid Class ID")
             return redirect('view_class')
    class_id = decrypted_id

    # Get session info
    # Authorization check
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their authorized school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        school_id = request.session.get('SchoolID') # Or retrieve from specific context if available
    
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    if not school_id:
        messages.error(request, "School authorization failed. Please login again.")
        return redirect('login')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        try:
            # Get form data
            class_name = request.POST.get('class_name', '').strip()
            class_code = request.POST.get('class_code', '').strip()
            education_level = request.POST.get('education_level', '').strip()
            description = request.POST.get('description', '').strip()
            
            # Get sections data
            section_names = request.POST.getlist('section_name[]')
            section_capacities = request.POST.getlist('section_capacity[]')
            section_rooms = request.POST.getlist('section_room[]')
            
            # Validation
            if not class_name:
                messages.error(request, "Class name is required.")
                return redirect('edit_class', class_id=class_id)
            
            if not class_code:
                messages.error(request, "Class code is required.")
                return redirect('edit_class', class_id=class_id)
            
            # Update class using stored procedure (Proc_Class_Set with existing ClassID)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_Class_Set"(%s, %s, %s, %s, %s, %s, %s, %s)
                """, [class_id, school_id, class_name, class_code, education_level, description, True, user_id])
                
                result = cursor.fetchone()
                # Proc_Class_Set returns TABLE(ClassID, ...) so result[0] is the ID
                if result and result[0]:
                    messages.success(request, f"Class '{class_name}' updated successfully!")
                    
                    # Handle sections update
                    if section_names:
                        # Delete existing sections first
                        cursor.execute("""
                            UPDATE SectionMaster 
                            SET IsDeleted = 1, UpdatedBy = %s, UpdatedAt = CURRENT_TIMESTAMP
                            WHERE ClassID = %s AND IsDeleted = FALSE
                        """, [user_id, class_id])
                        
                        # Add new sections
                        for i, section_name in enumerate(section_names):
                            if section_name.strip():
                                capacity = section_capacities[i] if i < len(section_capacities) else None
                                room = section_rooms[i] if i < len(section_rooms) else None
                                
                                cursor.execute("""
                                    SELECT * FROM "Proc_Section_Set"(%s, %s, %s, %s, %s, %s, %s)
                                """, [None, class_id, section_name.strip(), capacity, room, True, user_id])
                    
                    return redirect('add_class')
                else:
                    error_msg = result[1] if result and len(result) > 1 else "Unknown error occurred"
                    messages.error(request, f"Error updating class: {error_msg}")
                    
        except Exception as e:
            logger.error(f"Error updating class {class_id}: {str(e)}", exc_info=True)
            messages.error(request, "Error updating class. Please try again.")
        
        return redirect('edit_class', class_id=class_id)
    
    # Handle GET request (display form)
    try:
        # Get class details
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC Proc_Class_Section_List 
                    @SchoolID = %s,
                    @ClassID = %s
            """, [school_id, class_id])
            class_data = cursor.fetchone()
            
            if not class_data:
                messages.error(request, "Class not found.")
                return redirect('add_class')
            
            # Get sections for this class
            cursor.execute("""
                EXEC Proc_Class_Section_List 
                    @SchoolID = %s,
                    @ClassID = %s
            """, [school_id, class_id])
            sections = cursor.fetchall()
            
    except Exception as e:
        logger.error(f"Error fetching class {class_id}: {str(e)}", exc_info=True)
        messages.error(request, "Error loading class data. Please try again.")
        return redirect('add_class')
    
    context.update({
        'class_data': class_data,
        'sections': sections,
        'dark_mode': request.session.get('dark_mode', False)
    })
    
    return render(request, 'edit_class.html', context)


@custom_login_required
def update_class(request, class_id):
    """
    Update Class - Handle POST request to update class details (AJAX)
    """
    # Decrypt ID
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
        try:
             decrypted_id = int(class_id)
        except:
             return JsonResponse({'error': 'Invalid Class ID'}, status=400)
    class_id = decrypted_id

    # Authorization check
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their authorized school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # For Super Admin, check POST data as they might be updating a different school's class
        school_id_param = request.POST.get('school_id')
        if school_id_param:
             decrypted = decrypt_id(school_id_param)
             school_id = decrypted if decrypted else (int(school_id_param) if str(school_id_param).isdigit() else request.session.get('SchoolID'))
        else:
             school_id = request.session.get('SchoolID')

    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    if not school_id:
        return JsonResponse({'error': 'School authorization failed'}, status=403)
    
    if request.method == 'POST':
        try:
            # Get form data
            class_name = request.POST.get('class_name', '').strip()
            class_code = request.POST.get('class_code', '').strip()
            education_level = request.POST.get('education_level', '').strip()
            description = ''  # Description not editable in inline mode
            
            # Debug logging
            logger.info(f"Update class {class_id}: name='{class_name}', code='{class_code}', level='{education_level}'")
            
            # Validation
            if not class_name:
                return JsonResponse({'error': 'Class name is required.'}, status=400)
            
            if not class_code:
                return JsonResponse({'error': 'Class code is required.'}, status=400)
            
            
            # Update class using stored procedure (Proc_Class_Set with existing ClassID)
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC Proc_Class_Set
                        @ClassID = %s,
                        @SchoolID = %s,
                        @ClassName = %s,
                        @ClassCode = %s,
                        @EducationLevel = %s,
                        @Description = %s,
                        @IsActive = TRUE,
                        @UserID = %s
                """, [class_id, school_id, class_name, class_code, education_level, description, user_id])
                
                result = cursor.fetchone()
                logger.info(f"Proc_Class_Set result: {result}")
                if result:
                    # Proc_Class_Set returns the updated class record, not a success message
                    return JsonResponse({'success': True, 'message': f"Class '{class_name}' updated successfully!"})
                else:
                    return JsonResponse({'error': "Failed to update class - no result returned"}, status=400)
                    
        except Exception as e:
            logger.error(f"Error updating class {class_id}: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Error updating class. Please try again.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@custom_login_required
def delete_class(request, class_id):
    """
    Delete Class - Handle POST request to delete class (soft delete)
    """
    # Decrypt ID
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
        try:
             decrypted_id = int(class_id)
        except:
             return JsonResponse({'error': 'Invalid Class ID'}, status=400)
    class_id = decrypted_id

    # Authorization check
    profile_id = request.custom_user.get('profile_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileID')
    
    # Security Enforcement: Non-Super Admins MUST use their authorized school_id
    if profile_id != 1:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admins might pass school_id in GET/POST for multi-school context
        school_id_param = request.POST.get('school_id') or request.GET.get('school_id')
        if school_id_param:
            decrypted = decrypt_id(school_id_param)
            school_id = decrypted if decrypted else (int(school_id_param) if str(school_id_param).isdigit() else request.session.get('SchoolID'))
        else:
            school_id = request.session.get('SchoolID')

    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    
    if not school_id:
        return JsonResponse({'error': 'School authorization failed. Please login again.'}, status=403)
    
    if request.method == 'POST':
        try:
            logger.info(f"Attempting to delete class {class_id} for school {school_id} by user {user_id}")
            # Soft delete class by setting IsDeleted = 1
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE ClassMaster 
                    SET IsDeleted = 1
                    WHERE ClassID = %s AND SchoolID = %s AND IsDeleted = FALSE
                """, [class_id, school_id])
                
                # Also soft delete all associated sections
                cursor.execute("""
                    UPDATE SectionMaster 
                    SET IsDeleted = 1
                    WHERE ClassID = %s AND IsDeleted = FALSE
                """, [class_id])
                
                if cursor.rowcount > 0:
                    return JsonResponse({'success': True, 'message': 'Class and associated sections deleted successfully!'})
                else:
                    return JsonResponse({'error': 'Class not found or already deleted'}, status=404)
                    
        except Exception as e:
            logger.error(f"Error deleting class {class_id}: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Error deleting class. Please try again.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@custom_login_required
def restore_class(request, class_id):
    """
    Restore a soft-deleted class and its sections
    """
    # Decrypt ID
    decrypted_id = decrypt_id(class_id)
    if not decrypted_id:
        try:
             decrypted_id = int(class_id)
        except:
             return JsonResponse({'error': 'Invalid Class ID'}, status=400)
    class_id = decrypted_id

    school_id = request.session.get('SchoolID')
    user_id = request.session.get('UserID')
    
    if not school_id:
        return JsonResponse({'error': 'School information not found. Please login again.'}, status=400)
    
    if request.method == 'POST':
        try:
            logger.info(f"Attempting to restore class {class_id} for school {school_id} by user {user_id}")
            
            with connection.cursor() as cursor:
                # Restore the class
                cursor.execute("""
                    UPDATE ClassMaster 
                    SET IsDeleted = FALSE
                    WHERE ClassID = %s AND SchoolID = %s AND IsDeleted = 1
                """, [class_id, school_id])
                
                # Restore associated sections
                cursor.execute("""
                    UPDATE SectionMaster 
                    SET IsDeleted = FALSE
                    WHERE ClassID = %s AND IsDeleted = 1
                """, [class_id])
                
                if cursor.rowcount > 0:
                    return JsonResponse({'success': True, 'message': 'Class and associated sections restored successfully!'})
                else:
                    return JsonResponse({'error': 'Class not found or not deleted'}, status=404)
                    
        except Exception as e:
            logger.error(f"Error restoring class {class_id}: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Error restoring class. Please try again.'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
