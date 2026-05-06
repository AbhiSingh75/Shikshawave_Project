import logging
import os
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.conf import settings
from .views import custom_login_required, get_context, strict_permission_required
from .utils import get_school_dropdown, get_class_dropdown, safe_int, sanitize_input
from .url_encryption import encrypt_id, decrypt_id

logger = logging.getLogger(__name__)

@strict_permission_required('/master-data/subject/', action='view')
def subject_master(request):
    context = get_context(request)
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    profile_name = request.custom_user.get('profile_name') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileName')
    is_super_admin = profile_name and profile_name.lower() == 'super admin'
    
    if not is_super_admin:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Prioritize GET encrypted ID
        enc_school_id = request.GET.get('school_id')
        school_id = None
        if enc_school_id:
            decrypted = decrypt_id(enc_school_id)
            school_id = decrypted if decrypted else safe_int(enc_school_id, None)
        
        # Finally fallback to session
        if not school_id:
            school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')

    context['is_super_admin'] = is_super_admin
    school_list = []
    if is_super_admin:
        raw_schools = get_school_dropdown()
        for s in raw_schools:
            s['EncSchoolID'] = encrypt_id(s['SchoolID'])
            school_list.append(s)
        context['schools'] = school_list

    # Get and decrypt class_id from GET
    enc_class_id = request.GET.get('class_id')
    class_id = None
    if enc_class_id:
        class_id = decrypt_id(enc_class_id)
        if class_id is None:
            class_id = safe_int(enc_class_id, None)

    context['selected_school_id'] = encrypt_id(school_id) if school_id else ''
    context['raw_school_id'] = school_id # For internal use if needed
    
    subjects = []
    classes = []
    enc_class_map = {}
    
    if school_id:
        try:
            # Always fetch classes for the dropdowns
            classes = get_class_dropdown(school_id)
            enc_class_map = {}
            for c in classes:
                raw_cid = c['ID'] if 'ID' in c else c.get('ClassID')
                enc_cid = encrypt_id(raw_cid)
                c['EncClassID'] = enc_cid
                enc_class_map[raw_cid] = enc_cid
            
            # Only fetch subjects if Class is selected
            if class_id:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM "Proc_SubjectMaster_List"(%s, %s)
                    """, [school_id, class_id])
                    
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    for row in rows:
                        subj = dict(zip(columns, row))
                        subj['EncSubjectID'] = encrypt_id(subj['SubjectID'])
                        # Use the cached encrypted ID for consistency
                        subj['EncClassID'] = enc_class_map.get(subj.get('ClassId'), '')
                        subjects.append(subj)
        except Exception as e:
            logger.error(f"Error fetching subjects in subject_master: {e}", exc_info=True)
    
    context.update({
        'subjects': subjects,
        'classes': classes,
        'selected_class_id': str(class_id) if class_id else '',
        'selected_school_id_raw': str(school_id) if school_id else ''
    })
    
    return render(request, 'core/subject_master.html', context)

@strict_permission_required('/master-data/subject/', action='add')
def subject_save(request):
    if request.method != 'POST':
        return redirect('subject_master')
    
    # Get user info
    # Authorization check
    profile_name = request.custom_user.get('profile_name') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileName')
    is_super_admin = profile_name and profile_name.lower() == 'super admin'
    
    if not is_super_admin:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Post data school_id check
        enc_school_id = request.POST.get('school_id')
        school_id = decrypt_id(enc_school_id)
        if school_id is None:
            school_id = safe_int(enc_school_id, None)
        
        # Fallback to session
        if not school_id:
            school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    
    school_id = safe_int(school_id, None)
    if not school_id:
        messages.error(request, 'School selection is required', extra_tags='subject_master')
        return redirect('subject_master')
        
    # Get and decrypt filter_class_id (for redirection)
    enc_filter_class_id = request.POST.get('filter_class_id')
    
    # Get and decrypt IDs from form
    enc_subject_id = request.POST.get('subject_id')
    subject_id = decrypt_id(enc_subject_id) if enc_subject_id else None
    
    enc_class_id = request.POST.get('class_id')
    class_id = decrypt_id(enc_class_id) if enc_class_id else None
    
    subject_name = sanitize_input(request.POST.get('subject_name', ''))
    subject_code = sanitize_input(request.POST.get('subject_code', '')) or None
    description = sanitize_input(request.POST.get('description', '')) or None
    
    # Validation: ALL IDs must be correctly decrypted (No raw ID fallback for security)
    if enc_subject_id and subject_id is None:
        logger.error(f"Potential ID tampering: Invalid subject_id '{enc_subject_id}'")
        messages.error(request, 'Invalid operation requested.', extra_tags='subject_master')
        return redirect('subject_master')

    if enc_class_id and class_id is None:
        logger.error(f"Potential ID tampering: Invalid class_id '{enc_class_id}'")
        messages.error(request, 'Invalid class selected.', extra_tags='subject_master')
        return redirect('subject_master')

    # Ownership Check (IDOR Prevention)
    if subject_id:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1 FROM "SubjectMaster" WHERE "SubjectID" = %s AND "SchoolID" = %s', [subject_id, school_id])
            if not cursor.fetchone():
                logger.warning(f"IDOR Attempt: User {user_id_int} tried to edit Subject {subject_id} not belonging to School {school_id}")
                messages.error(request, 'Unauthorized access to this record.', extra_tags='subject_master')
                return redirect('subject_master')
        
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    user_id_int = safe_int(user_id, None)

    if not subject_name:
        messages.error(request, 'Subject name is required', extra_tags='subject_master')
        return redirect('subject_master')
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_SubjectMaster_Save"(%s, %s, %s, %s, %s, %s, %s)
            """, [subject_id, school_id, class_id, subject_name, subject_code, description, user_id_int])
            
            result = cursor.fetchone()
            
            if result and result[0] == 'SUCCESS':
                messages.success(request, result[1], extra_tags='subject_master')
            else:
                msg = result[1] if result else 'Failed to save subject'
                messages.error(request, msg, extra_tags='subject_master')
                logger.warning(f"Subject save failed: {msg}")
    except Exception as e:
        logger.error(f"Error in subject_save: {e}", exc_info=True)
        messages.error(request, f'Error saving subject: {str(e)}', extra_tags='subject_master')
    
    # Redirect back with encrypted IDs to preserve filters
    redirect_url = '/master-data/subject/'
    params = []
    
    if is_super_admin and school_id:
        params.append(f'school_id={encrypt_id(school_id)}')
    
    # Carry over class filter to keep view consistent
    if enc_filter_class_id:
        params.append(f'class_id={enc_filter_class_id}')
    
    if params:
        redirect_url += '?' + '&'.join(params)
    
    return redirect(redirect_url)

@strict_permission_required('/master-data/subject/', action='delete')
def subject_delete(request, subject_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    # Decrypt subject_id strictly
    raw_subject_id = decrypt_id(subject_id)
    if raw_subject_id is None:
        logger.error(f"Potential ID tampering in delete: {subject_id}")
        return JsonResponse({'success': False, 'message': 'Invalid security token'})
    
    # Get user info
    user_id = request.custom_user.get('user_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('UserId')
    profile_name = request.custom_user.get('profile_name') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileName')
    is_super_admin = profile_name and profile_name.lower() == 'super admin'
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if not is_super_admin:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        # Super Admin: Post or JSON body check
        import json
        try:
            body = json.loads(request.body)
            enc_school_id = body.get('school_id')
        except:
            enc_school_id = request.POST.get('school_id')
        
        school_id = decrypt_id(enc_school_id)
        if school_id is None:
            school_id = safe_int(enc_school_id, request.session.get('SchoolID'))
    
    # IDOR Check: Ensure subject belongs to school
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM "SubjectMaster" WHERE "SubjectID" = %s AND "SchoolID" = %s', [raw_subject_id, school_id])
        if not cursor.fetchone():
            logger.warning(f"IDOR Alert: User {user_id} attempted to delete Subject {raw_subject_id} not belonging to School {school_id}")
            return JsonResponse({'success': False, 'message': 'Permission Denied'})

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_SubjectMaster_Delete"(%s, %s, %s)
            """, [raw_subject_id, school_id, user_id])
            
            result = cursor.fetchone()
            if result and result[0] == 'SUCCESS':
                return JsonResponse({'success': True, 'message': result[1]})
            else:
                return JsonResponse({'success': False, 'message': result[1] if result else 'Failed to delete'})
    except Exception as e:
        logger.error(f"Error deleting subject: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Error deleting subject'})

@strict_permission_required('/master-data/subject/', action='view')
def subject_get_by_class(request):
    profile_name = request.custom_user.get('profile_name') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileName')
    is_super_admin = profile_name and profile_name.lower() == 'super admin'
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if not is_super_admin:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        enc_school_id = request.GET.get('school_id')
        school_id = decrypt_id(enc_school_id) if enc_school_id else None
        if school_id is None:
            school_id = safe_int(enc_school_id, request.session.get('SchoolID'))
    
    enc_class_id = request.GET.get('class_id')
    class_id = decrypt_id(enc_class_id) if enc_class_id else None
    if class_id is None:
        class_id = safe_int(enc_class_id, None)
    
    subjects = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM "Proc_SubjectMaster_List"(%s, %s)
            """, [school_id, class_id])
            
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                subj = dict(zip(columns, row))
                subj['EncSubjectID'] = encrypt_id(subj['SubjectID'])
                subj['EncClassID'] = encrypt_id(subj['ClassId']) if subj.get('ClassId') else ''
                subjects.append(subj)
        
        return JsonResponse({'success': True, 'subjects': subjects})
    except Exception as e:
        logger.error(f"Error in subject_get_by_class: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Error loading subjects'})

@strict_permission_required('/master-data/subject/', action='view')
def subject_load(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request'})
    
    # Authorization check
    profile_name = request.custom_user.get('profile_name') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('ProfileName')
    is_super_admin = profile_name and profile_name.lower() == 'super admin'
    
    # Security Enforcement: Non-Super Admins MUST use their session school_id
    if not is_super_admin:
        school_id = request.custom_user.get('school_id') if hasattr(request, 'custom_user') and request.custom_user else request.session.get('SchoolID')
    else:
        enc_school_id = request.POST.get('school_id')
        school_id = decrypt_id(enc_school_id)
        if school_id is None:
            school_id = safe_int(enc_school_id, request.session.get('SchoolID'))
    
    enc_class_id = request.POST.get('class_id')
    class_id = decrypt_id(enc_class_id) if enc_class_id else None
    
    try:
        subjects = []
        classes = get_class_dropdown(school_id)
        enc_class_map = {}
        # Encrypt class IDs and build map
        for c in classes:
            raw_cid = c['ID'] if 'ID' in c else c.get('ClassID')
            enc_cid = encrypt_id(raw_cid)
            c['EncClassID'] = enc_cid
            enc_class_map[raw_cid] = enc_cid
             
        if class_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM "Proc_SubjectMaster_List"(%s, %s)
                """, [school_id, class_id])
                
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    subj = dict(zip(columns, row))
                    if subj.get('CreatedAt'):
                        subj['CreatedAt'] = subj['CreatedAt'].strftime('%d %b %Y') if hasattr(subj['CreatedAt'], 'strftime') else str(subj['CreatedAt'])
                    subj['EncSubjectID'] = encrypt_id(subj['SubjectID'])
                    # Use consistency cache
                    subj['EncClassID'] = enc_class_map.get(subj.get('ClassId'), '')
                    subjects.append(subj)
        
        return JsonResponse({
            'status': 'SUCCESS', 
            'data': subjects,
            'classes': classes
        })
    except Exception as e:
        logger.error(f"Error in subject_load: {e}", exc_info=True)
        return JsonResponse({'status': 'ERROR', 'message': str(e)})
