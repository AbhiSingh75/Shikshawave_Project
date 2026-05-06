import json
import logging
import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from .utils import bytes_to_data_uri, get_school_dropdown
from .url_encryption import encrypt_id, decrypt_id_int
from .decorators import custom_login_required

logger = logging.getLogger(__name__)

@custom_login_required
def payment_account_list(request):
    """View to list payment accounts for institutions."""
    try:
        profile_id = request.session.get('ProfileID')
        school_id = request.session.get('SchoolID')
        selected_school_id_raw = request.GET.get('sid')
        show_default = request.GET.get('show_default') == '1'
        
        target_school_id = school_id
        if profile_id == 1: # Super Admin
            if show_default:
                target_school_id = 0
            elif selected_school_id_raw:
                target_school_id = decrypt_id_int(selected_school_id_raw)
                if target_school_id is None: target_school_id = 0
            else:
                target_school_id = 0 # Default fallback
        
        accounts = []
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM public."Proc_PaymentAccountDetails_Get"(%s)', [target_school_id])
            
            for row in cursor.fetchall():
                accounts.append({
                    'PaymentId': row[0],
                    'EncPaymentID': encrypt_id(row[0]),
                    'SchoolId': row[1],
                    'PaymentMethod': str(row[2]).strip().upper(),
                    'AccountName': row[3],
                    'AccountNumber': row[4],
                    'IFSCCode': row[5],
                    'BranchName': row[6],
                    'AccountHolderName': row[7],
                    'UPIId': row[8],
                    'UPIQRCodeUrl': row[9],
                    'GatewayName': row[10],
                    'GatewayKey': row[11],
                    'GatewaySecret': row[12],
                    'WebhookUrl': row[13],
                    'ExtraConfig': row[14],
                    'IsActive': row[15],
                    'IsDefault': row[16],
                    'IsDeleted': row[17],
                    'CreatedOn': row[18],
                    'UPIQRCodeBinary': f"data:image/png;base64,{base64.b64encode(bytes(row[19])).decode('utf-8')}" if row[19] else None,
                    'SchoolName': row[20],
                    'SchoolCode': row[21]
                })

        # Fetch schools for Super Admin dropdown using Global API logic
        schools = []
        is_super = str(profile_id) == '1'
        if is_super:
            try:
                raw_schools = get_school_dropdown()
                for s in raw_schools:
                    schools.append({
                        'SchoolID': s['SchoolID'],
                        'EncSchoolID': encrypt_id(s['SchoolID']),
                        'DisplayName': s['DisplayName']
                    })
            except Exception as e:
                logger.error(f"Error fetching global school dropdown in views: {e}")

        # Determine display name for the selected school
        current_school_name = ""
        if target_school_id == 0:
            current_school_name = "ShikshaWave Default"
        else:
            for s in schools:
                if str(s['SchoolID']) == str(target_school_id):
                    current_school_name = s['DisplayName']
                    break

        context = {
            'accounts': accounts,
            'schools': schools,
            'selected_school_id': encrypt_id(target_school_id) if target_school_id != 0 else None,
            'selected_school_id_raw': target_school_id,
            'show_default': show_default or (target_school_id == 0 and is_super),
            'current_school_name': current_school_name,
            'is_super_admin': is_super
        }

        
        return render(request, 'core/payment_account_setup.html', context)
    except Exception as e:
        logger.error(f"Error in payment_account_list: {e}")
        return render(request, 'core/payment_account_setup.html', {'error': str(e)})

@custom_login_required
@transaction.atomic
def save_payment_account(request):
    """Create or Update a payment account with multi-tenant security and validation."""
    try:
        if request.method != 'POST':
            return JsonResponse({'status': 'FAILED', 'message': 'Method not allowed'})

        # Handle both JSON and Multipart
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
            data['is_active'] = data.get('is_active') in ['true', 'on', '1', True]
            data['is_default'] = data.get('is_default') in ['true', 'on', '1', True]
        
        # 1. Access Control & Identification
        user_id = request.session.get('UserId')
        profile_id = request.session.get('ProfileID')
        session_school_id = request.session.get('SchoolID')
        is_super = str(profile_id) == '1'
        
        payment_id = decrypt_id_int(data.get('enc_id')) if data.get('enc_id') else None
        
        # 2. Multi-tenant Target Resolution
        target_school_id = session_school_id
        if is_super:
            req_school = data.get('school_id')
            if req_school == 'default' or not req_school:
                target_school_id = 0
            else:
                target_school_id = decrypt_id_int(req_school)
                if target_school_id is None: 
                    return JsonResponse({'status': 'FAILED', 'message': 'Invalid School ID'})
        
        # 3. Input Sanitation
        sanitized_data = {
            'method': str(data.get('payment_method', 'BANK')).strip().upper(),
            'account_name': strip_tags(str(data.get('account_name', ''))).strip(),
            'account_number': strip_tags(str(data.get('account_number', ''))).strip(),
            'ifsc_code': strip_tags(str(data.get('ifsc_code', ''))).strip().upper(),
            'branch_name': strip_tags(str(data.get('branch_name', ''))).strip(),
            'holder_name': strip_tags(str(data.get('holder_name', ''))).strip(),
            'upi_id': strip_tags(str(data.get('upi_id', ''))).strip(),
            'gateway_name': strip_tags(str(data.get('gateway_name', ''))).strip(),
            'gateway_key': str(data.get('gateway_key', '')).strip(),
            'gateway_secret': str(data.get('gateway_secret', '')).strip(),
            'webhook_url': str(data.get('webhook_url', '')).strip(),
            'is_default': bool(data.get('is_default')),
            'is_active': bool(data.get('is_active', True))
        }

        # 4. File Guardrails
        qr_file = request.FILES.get('upi_qr_file')
        qr_binary = None
        if qr_file:
            if qr_file.size > 2 * 1024 * 1024: # 2MB Limit
                return JsonResponse({'status': 'FAILED', 'message': 'QR Image too large (Max 2MB)'})
            if not qr_file.content_type.startswith('image/'):
                return JsonResponse({'status': 'FAILED', 'message': 'Only image files are allowed for QR codes'})
            qr_binary = qr_file.read()

        # 5. Database Logic
        with connection.cursor() as cursor:
            # Sync Default status
            if sanitized_data['is_default']:
                cursor.execute('UPDATE "PaymentAccountDetails" SET "IsDefault" = FALSE WHERE "SchoolId" = %s', [target_school_id])

            if payment_id: # UPDATE
                # SECURITY CHECK: Ownership Verification
                if not is_super:
                    cursor.execute('SELECT "SchoolId" FROM "PaymentAccountDetails" WHERE "PaymentId" = %s', [payment_id])
                    row = cursor.fetchone()
                    if not row or row[0] != session_school_id:
                        return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized bypass attempt detected.'})

                if qr_binary:
                    cursor.execute("""
                        UPDATE "PaymentAccountDetails" SET
                            "PaymentMethod" = %s, "AccountName" = %s, "AccountNumber" = %s,
                            "IFSCCode" = %s, "BranchName" = %s, "AccountHolderName" = %s,
                            "UPIId" = %s, "GatewayName" = %s,
                            "GatewayKey" = %s, "GatewaySecret" = %s, "WebhookUrl" = %s,
                            "IsActive" = %s, "IsDefault" = %s, "UPIQRCode" = %s,
                            "UpdatedBy" = %s, "UpdatedOn" = CURRENT_TIMESTAMP, "VersionNo" = "VersionNo" + 1
                        WHERE "PaymentId" = %s
                    """, [
                        sanitized_data['method'], sanitized_data['account_name'], sanitized_data['account_number'],
                        sanitized_data['ifsc_code'], sanitized_data['branch_name'], sanitized_data['holder_name'],
                        sanitized_data['upi_id'], sanitized_data['gateway_name'],
                        sanitized_data['gateway_key'], sanitized_data['gateway_secret'], sanitized_data['webhook_url'],
                        sanitized_data['is_active'], sanitized_data['is_default'], qr_binary, user_id, payment_id
                    ])
                else:
                    cursor.execute("""
                        UPDATE "PaymentAccountDetails" SET
                            "PaymentMethod" = %s, "AccountName" = %s, "AccountNumber" = %s,
                            "IFSCCode" = %s, "BranchName" = %s, "AccountHolderName" = %s,
                            "UPIId" = %s, "GatewayName" = %s,
                            "GatewayKey" = %s, "GatewaySecret" = %s, "WebhookUrl" = %s,
                            "IsActive" = %s, "IsDefault" = %s, "UpdatedBy" = %s,
                            "UpdatedOn" = CURRENT_TIMESTAMP, "VersionNo" = "VersionNo" + 1
                        WHERE "PaymentId" = %s
                    """, [
                        sanitized_data['method'], sanitized_data['account_name'], sanitized_data['account_number'],
                        sanitized_data['ifsc_code'], sanitized_data['branch_name'], sanitized_data['holder_name'],
                        sanitized_data['upi_id'], sanitized_data['gateway_name'],
                        sanitized_data['gateway_key'], sanitized_data['gateway_secret'], sanitized_data['webhook_url'],
                        sanitized_data['is_active'], sanitized_data['is_default'], user_id, payment_id
                    ])
                message = "Configuration updated securely"
            else: # INSERT
                cursor.execute("""
                    INSERT INTO "PaymentAccountDetails" (
                        "SchoolId", "PaymentMethod", "AccountName", "AccountNumber",
                        "IFSCCode", "BranchName", "AccountHolderName", "UPIId",
                        "UPIQRCode", "GatewayName", "GatewayKey", "GatewaySecret",
                        "WebhookUrl", "IsActive", "IsDefault", "CreatedBy"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    target_school_id, sanitized_data['method'], sanitized_data['account_name'], 
                    sanitized_data['account_number'], sanitized_data['ifsc_code'], 
                    sanitized_data['branch_name'], sanitized_data['holder_name'],
                    sanitized_data['upi_id'], qr_binary, sanitized_data['gateway_name'],
                    sanitized_data['gateway_key'], sanitized_data['gateway_secret'], 
                    sanitized_data['webhook_url'], sanitized_data['is_active'], 
                    sanitized_data['is_default'], user_id
                ])
                message = "New configuration saved securely"

        return JsonResponse({'status': 'SUCCESS', 'message': message})
    except Exception as e:
        logger.error(f"Security error in save_payment_account: {e}")
        return JsonResponse({'status': 'FAILED', 'message': 'Action blocked for security reasons.'})

@custom_login_required
@require_POST
@transaction.atomic
def delete_payment_account(request):
    """Soft-delete a payment account configuration with ownership verification."""
    try:
        data = json.loads(request.body)
        payment_id = decrypt_id_int(data.get('enc_id'))
        user_id = request.session.get('UserId')
        profile_id = request.session.get('ProfileID')
        session_school_id = request.session.get('SchoolID')
        
        if not payment_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Invalid Account ID'})

        with connection.cursor() as cursor:
            # SECURITY CHECK: Ownership Verification
            if str(profile_id) != '1': # If not Super Admin
                cursor.execute('SELECT "SchoolId" FROM "PaymentAccountDetails" WHERE "PaymentId" = %s', [payment_id])
                record = cursor.fetchone()
                if not record or record[0] != session_school_id:
                    return JsonResponse({'status': 'FAILED', 'message': 'Action blocked: Unauthorized deletion attempt.'})

            cursor.execute("""
                UPDATE "PaymentAccountDetails" 
                SET "IsDeleted" = TRUE, "UpdatedBy" = %s, "UpdatedOn" = CURRENT_TIMESTAMP 
                WHERE "PaymentId" = %s
            """, [user_id, payment_id])

        return JsonResponse({'status': 'SUCCESS', 'message': 'Configuration removed securely'})
    except Exception as e:
        logger.error(f"Security error in delete_payment_account: {e}")
        return JsonResponse({'status': 'FAILED', 'message': 'Action blocked for security reasons.'})
