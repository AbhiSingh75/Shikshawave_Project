# SMTP Configuration Management Views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.core.signing import Signer, BadSignature
from django.core.mail import get_connection
from django.core.mail import EmailMessage
import logging
import json
from .url_encryption import encrypt_id, decrypt_id

logger = logging.getLogger(__name__)
signer = Signer()

from .smtp_encryption import encrypt_smtp_password, decrypt_smtp_password

def encrypt_password(password):
    """Bridge for backward compatibility in this file"""
    return encrypt_smtp_password(password)

def decrypt_password(password):
    """Bridge for backward compatibility in this file"""
    return decrypt_smtp_password(password)


def smtp_config_list(request):
    """List all SMTP configurations with modal for add/edit"""
    from .views import custom_login_required, get_context
    from .subject_views import get_school_dropdown
    
    @custom_login_required
    def _view(request):
        context = get_context(request)
        
        school_id = request.session.get('SchoolID')
        profile_id = request.session.get('ProfileID')
        is_super_admin = profile_id == 1
        
        # Get and decrypt selected school ID (for super admin filtering)
        enc_selected_school_id = request.GET.get('sid')
        selected_school_id = None
        show_default = request.GET.get('show_default') == '1'
        
        if enc_selected_school_id:
            if enc_selected_school_id == 'default':
                selected_school_id = None
                show_default = True
            else:
                selected_school_id = decrypt_id(enc_selected_school_id)
        
        # For non-super admin, always use their school
        if not is_super_admin:
            selected_school_id = school_id

        configs = []
        schools = []
        school_id_to_enc = {}
        
        # Super Admin needs to apply a filter to see data.
        # Non-Super Admins always see their own school's data.
        should_fetch_data = not is_super_admin or selected_school_id or show_default

        try:
            with connection.cursor() as cursor:
                # Always get schools for dropdown if super admin (and for ID mapping consistency)
                if is_super_admin:
                    raw_schools = get_school_dropdown()
                    for s in raw_schools:
                        enc = encrypt_id(s['SchoolID'])
                        s['EncSchoolID'] = enc
                        school_id_to_enc[s['SchoolID']] = enc
                        schools.append(s)

                if should_fetch_data:
                    if show_default:
                        # Show default ShikshaWave SMTP (SchoolID IS NULL)
                        cursor.execute('''
                            SELECT s."ConfigID", s."SchoolID", 
                                   COALESCE(sch."SchoolName", 'ShikshaWave Default') AS "SchoolName",
                                   s."ConfigName", s."SMTPHost", s."SMTPPort", s."UseTLS", s."UseSSL",
                                   s."Username", s."Password", s."FromEmail", s."FromName", s."IsActive", s."IsDefault",
                                   s."IsDeleted", s."CreatedBy", s."CreatedAt", s."Purpose"
                            FROM "SMTPConfiguration" s
                            LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
                            WHERE s."SchoolID" IS NULL
                            ORDER BY s."ConfigName"
                        ''')
                    else:
                        cursor.execute('''
                            SELECT s."ConfigID", s."SchoolID", 
                                   COALESCE(sch."SchoolName", 'ShikshaWave Default') AS "SchoolName",
                                   s."ConfigName", s."SMTPHost", s."SMTPPort", s."UseTLS", s."UseSSL",
                                   s."Username", s."Password", s."FromEmail", s."FromName", s."IsActive", s."IsDefault",
                                   s."IsDeleted", s."CreatedBy", s."CreatedAt", s."Purpose"
                            FROM "SMTPConfiguration" s
                            LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
                            WHERE s."SchoolID" = %s
                            ORDER BY s."ConfigName"
                        ''', [selected_school_id])
                    
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        config = dict(zip(columns, row))
                        config['EncConfigID'] = encrypt_id(config['ConfigID'])
                        
                        # Use the same encrypted ID as the dropdown for consistency
                        sid = config['SchoolID']
                        if sid:
                            config['EncSchoolID'] = school_id_to_enc.get(sid, encrypt_id(sid))
                        else:
                            config['EncSchoolID'] = 'default'
                        
                        # Decrypt password for editing (as requested by user)
                        try:
                            if config.get('Password'):
                                config['DecryptedPassword'] = decrypt_password(config['Password'])
                            else:
                                config['DecryptedPassword'] = ''
                        except Exception as e:
                            logger.error(f"Error decrypting password for config {config['ConfigID']}: {e}")
                            config['DecryptedPassword'] = ''
                            
                        configs.append(config)
                
                # Always get schools for dropdown if super admin
        
        except Exception as e:
            logger.error(f"Error fetching SMTP configurations: {e}", exc_info=True)
            messages.error(request, "Error loading SMTP configurations", extra_tags='smtp_config')
        
        context.update({
            'configs': configs,
            'schools': schools,
            'is_super_admin': is_super_admin,
            'selected_school_id': enc_selected_school_id,
            'selected_school_id_raw': selected_school_id,
            'show_default': show_default,
        })
        
        return render(request, 'core/smtp_configuration.html', context)
    
    return _view(request)


def smtp_config_save(request):
    """Save (add/update) SMTP configuration"""
    from .views import custom_login_required
    
    @custom_login_required
    def _view(request):
        if request.method != 'POST':
            return redirect('smtp_config_list')
        
        school_id = request.session.get('SchoolID')
        profile_id = request.session.get('ProfileID')
        user_id = request.session.get('UserId')
        is_super_admin = profile_id == 1
        
        enc_config_id = request.POST.get('config_id')
        config_id = decrypt_id(enc_config_id) if enc_config_id else None
        
        config_name = request.POST.get('config_name', '').strip()
        smtp_host = request.POST.get('smtp_host', '').strip()
        smtp_port = int(request.POST.get('smtp_port', 587))
        use_tls = request.POST.get('use_tls') == 'on'
        use_ssl = request.POST.get('use_ssl') == 'on'
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        from_email = request.POST.get('from_email', '').strip()
        from_name = request.POST.get('from_name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        purpose = request.POST.get('purpose', 'ALL').strip()
        
        enc_school_id = request.POST.get('school_id')
        
        # Handle school ID - 'default' means NULL (system default)
        if enc_school_id == 'default':
            selected_school_id = None
        elif is_super_admin and enc_school_id:
            selected_school_id = decrypt_id(enc_school_id)
        else:
            selected_school_id = school_id
        
        action = 'UPDATE' if config_id else 'INSERT'
        
        # Encrypt password if provided
        encrypted_password = None
        if password:
            encrypted_password = encrypt_password(password)
        
        try:
            with connection.cursor() as cursor:
                if action == 'INSERT':
                    # Deactivate existing active configs for same school if new one is active
                    if is_active:
                        cursor.execute('''
                            UPDATE "SMTPConfiguration" SET "IsActive" = FALSE, "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                            WHERE ("SchoolID" = %s OR (%s IS NULL AND "SchoolID" IS NULL))
                            AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                        ''', [user_id, selected_school_id, selected_school_id])
                    
                    cursor.execute('''
                        INSERT INTO "SMTPConfiguration" (
                            "SchoolID", "ConfigName", "Purpose", "SMTPHost", "SMTPPort", "UseTLS", "UseSSL",
                            "Username", "Password", "FromEmail", "FromName", "IsActive", "IsDefault",
                            "CreatedBy", "CreatedAt", "IsDeleted"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s, CURRENT_TIMESTAMP, FALSE
                        ) RETURNING "ConfigID"
                    ''', [
                        selected_school_id, config_name, purpose, smtp_host, smtp_port,
                        use_tls, use_ssl, username, encrypted_password, from_email, from_name,
                        is_active, user_id
                    ])
                    messages.success(request, "SMTP configuration created successfully", extra_tags='smtp_config')
                else:
                    # UPDATE
                    if is_active:
                        # Deactivate other active configs for same school
                        cursor.execute('''
                            UPDATE "SMTPConfiguration" SET "IsActive" = FALSE, "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                            WHERE "ConfigID" != %s
                            AND ("SchoolID" = (SELECT "SchoolID" FROM "SMTPConfiguration" WHERE "ConfigID" = %s)
                                 OR ((SELECT "SchoolID" FROM "SMTPConfiguration" WHERE "ConfigID" = %s) IS NULL AND "SchoolID" IS NULL))
                            AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                        ''', [user_id, config_id, config_id, config_id])
                    
                    if encrypted_password:
                        cursor.execute('''
                            UPDATE "SMTPConfiguration" SET
                                "ConfigName" = %s, "Purpose" = %s, "SMTPHost" = %s, "SMTPPort" = %s,
                                "UseTLS" = %s, "UseSSL" = %s, "Username" = %s, "Password" = %s,
                                "FromEmail" = %s, "FromName" = %s, "IsActive" = %s,
                                "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                            WHERE "ConfigID" = %s
                        ''', [
                            config_name, purpose, smtp_host, smtp_port, use_tls, use_ssl,
                            username, encrypted_password, from_email, from_name, is_active,
                            user_id, config_id
                        ])
                    else:
                        cursor.execute('''
                            UPDATE "SMTPConfiguration" SET
                                "ConfigName" = %s, "Purpose" = %s, "SMTPHost" = %s, "SMTPPort" = %s,
                                "UseTLS" = %s, "UseSSL" = %s, "Username" = %s,
                                "FromEmail" = %s, "FromName" = %s, "IsActive" = %s,
                                "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                            WHERE "ConfigID" = %s
                        ''', [
                            config_name, purpose, smtp_host, smtp_port, use_tls, use_ssl,
                            username, from_email, from_name, is_active,
                            user_id, config_id
                        ])
                    messages.success(request, "SMTP configuration updated successfully", extra_tags='smtp_config')
        
        except Exception as e:
            logger.error(f"Error saving SMTP configuration: {e}", exc_info=True)
            messages.error(request, f"Error saving configuration: {str(e)}", extra_tags='smtp_config')
        
        # Redirect back with filter preserved
        redirect_url = '/master-data/smtp-configuration/'
        if is_super_admin:
            if enc_school_id == 'default':
                redirect_url += '?show_default=1'
            elif enc_school_id:
                redirect_url += f'?sid={enc_school_id}'
            
        return redirect(redirect_url)
    
    return _view(request)


def smtp_config_delete_ajax(request):
    """Delete SMTP configuration via AJAX"""
    from .views import custom_login_required
    
    @custom_login_required
    def _view(request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
        
        user_id = request.session.get('UserId')
        enc_config_id = request.POST.get('config_id')
        config_id = decrypt_id(enc_config_id)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "Proc_SMTPConfiguration_Manage"('DELETE', %s, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, %s)
                """, [config_id, user_id])
                
                result = cursor.fetchone()
                if result:
                    return JsonResponse(json.loads(result[0]))
        
        except Exception as e:
            logger.error(f"Error deleting SMTP configuration: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return _view(request)


def smtp_config_restore_ajax(request):
    """Restore SMTP configuration via AJAX"""
    from .views import custom_login_required
    
    @custom_login_required
    def _view(request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
        
        user_id = request.session.get('UserId')
        enc_config_id = request.POST.get('config_id')
        config_id = decrypt_id(enc_config_id)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT "Proc_SMTPConfiguration_Manage"('RESTORE', %s, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, %s)
                """, [config_id, user_id])
                
                result = cursor.fetchone()
                if result:
                    return JsonResponse(json.loads(result[0]))
        
        except Exception as e:
            logger.error(f"Error restoring SMTP configuration: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return _view(request)


def smtp_config_test(request):
    """Test SMTP connection with provided settings"""
    from .views import custom_login_required
    
    @custom_login_required
    def _view(request):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
        
        try:
            data = json.loads(request.body)
            config_id_enc = data.get('config_id')
            
            smtp_host = data.get('smtp_host', '').strip()
            smtp_port = int(data.get('smtp_port', 587))
            use_tls = data.get('use_tls', True)
            use_ssl = data.get('use_ssl', False)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            from_email = data.get('from_email', '').strip()
            to_email = data.get('to_email', '').strip()

            # If testing existing config by ID
            if config_id_enc:
                config_id = decrypt_id(config_id_enc)
                with connection.cursor() as cursor:
                    # Fetch from direct SQL since we need latest
                    cursor.execute('''
                        SELECT "SMTPHost", "SMTPPort", "UseTLS", "UseSSL", "Username", "Password", "FromEmail"
                        FROM "SMTPConfiguration" WHERE "ConfigID" = %s
                    ''', [config_id])
                    row = cursor.fetchone()
                    if row:
                        smtp_host, smtp_port, use_tls, use_ssl, username, encrypted_password, from_email = row
                        password = decrypt_smtp_password(encrypted_password)
            
            if not all([smtp_host, username, password, from_email]):
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Please fill in all required fields'
                })
            
            # Try to create connection
            smtp_conn = get_connection(
                host=smtp_host,
                port=smtp_port,
                username=username,
                password=password,
                use_tls=use_tls,
                use_ssl=use_ssl,
                fail_silently=False
            )
            
            # Test the connection
            smtp_conn.open()
            
            # Optionally send test email
            if to_email:
                email = EmailMessage(
                    subject='ShikshaWave SMTP Test',
                    body='This is a test email from ShikshaWave to verify SMTP configuration.',
                    from_email=from_email,
                    to=[to_email],
                    connection=smtp_conn
                )
                email.send()
                message = f'Connection successful! Test email sent to {to_email}'
            else:
                message = 'Connection successful!'
            
            smtp_conn.close()
            
            return JsonResponse({'status': 'success', 'message': message})
            
        except Exception as e:
            logger.error(f"SMTP test failed: {e}", exc_info=True)
            return JsonResponse({
                'status': 'error', 
                'message': f'Connection failed: {str(e)}'
            })
    
    return _view(request)


def get_smtp_config_for_school(school_id):
    """
    Get SMTP configuration for a school.
    Returns dict with SMTP settings or None if not found.
    Falls back to default (SchoolID=NULL) if no school-specific config.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM "Proc_SMTPConfiguration_GetBySchool"(%s::INT)
            ''', [school_id])
            
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                config = dict(zip(columns, row))
                
                # Decrypt password
                if config.get('Password'):
                    config['Password'] = decrypt_password(config['Password'])
                
                return config
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching SMTP config for school {school_id}: {e}", exc_info=True)
        return None


def get_default_smtp_config():
    """
    Get default ShikshaWave SMTP configuration (SchoolID=NULL).
    Returns dict with SMTP settings or None if not found.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM "Proc_SMTPConfiguration_GetDefault"()')
            
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                config = dict(zip(columns, row))
                
                # Decrypt password
                if config.get('Password'):
                    config['Password'] = decrypt_password(config['Password'])
                
                return config
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching default SMTP config: {e}", exc_info=True)
        return None
