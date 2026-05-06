from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
import logging
import base64
from datetime import datetime
from .decorators import custom_login_required
from .email_tracking_models import EmailTrackingManager
from .utils import number_to_words

logger = logging.getLogger(__name__)

def custom_login_required(view_func):
    from functools import wraps
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('UserId'):
            messages.error(request, "Please login to continue.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wraps(view_func)(_wrapped)

def super_admin_required(view_func):
    """Decorator to ensure only Super Admins can access certain views"""
    from functools import wraps
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('UserId'):
            messages.error(request, "Please login to continue.")
            return redirect('login')
        if request.session.get('ProfileID') != 1:
            messages.error(request, "Access Denied: You do not have permission to view reporting analytics.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wraps(view_func)(_wrapped)

@custom_login_required
def subscription_plans(request):
    """Render subscription plans page"""
    from core.views import get_context
    context = get_context(request)
    
    # Fetch user menus for sidebar
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
    
    # - [x] Create and execute migration `0086` to drop the legacy 5-parameter function
    # - [x] Update `subscription_views.py` (Subscribers view) to use the 10-parameter version
    # - [ ] Verify 'Subscriber List' loads correctly
    # - [ ] Verify 'Subscription History' still loads correctly
    # - [ ] Conduct final UI sanity check for the Subscription Dashboard
    
    return render(request, 'core/subscription_plans.html', context)

def get_plans_public(request):
    """Get all subscription plans - Public endpoint"""
    try:
        plan_type = request.GET.get('plan_type')
        include_deleted = '0'
        search = request.GET.get('search', '').strip() or None
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM Proc_SubscriptionPlan_Get(NULL, %s, %s::boolean, %s)", 
                         [plan_type, include_deleted == '1', search])
            
            plans = []
            for row in cursor.fetchall():
                plans.append({
                    'PlanID': row[0],
                    'PlanName': row[1],
                    'PlanCode': row[2],
                    'PlanType': row[3],
                    'DurationMonths': row[4],
                    'Price': float(row[5]) if row[5] else 0,
                    'DiscountPercent': float(row[6]) if row[6] else 0,
                    'FinalPrice': float(row[7]) if row[7] else 0,
                    'MaxStudents': row[8],
                    'MaxTeachers': row[9],
                    'StorageLimitMB': row[10],
                    'IncludeReports': row[11],
                    'IsTrialPlan': row[12],
                    'IsDeleted': row[14]
                })
        
        return JsonResponse({'status': 'SUCCESS', 'plans': plans})
    except Exception as e:
        logger.error(f"Error fetching plans: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_plans(request):
    """Get all subscription plans via hardened v2 procedure"""
    try:
        plan_type = request.GET.get('plan_type') or None
        include_deleted = request.GET.get('include_deleted', '0') == '1'
        search = request.GET.get('search', '').strip() or None
        
        with connection.cursor() as cursor:
            # Use hardened V2 procedure
            cursor.execute("SELECT * FROM Proc_SubscriptionPlan_Get_v2(NULL, %s, %s::boolean, %s)", 
                         [plan_type, include_deleted, search])
            
            plans = []
            for row in cursor.fetchall():
                plans.append({
                    'PlanID': row[0],
                    'PlanName': row[1],
                    'PlanCode': row[2],
                    'PlanType': row[3],
                    'DurationMonths': row[4],
                    'Price': float(row[5]) if row[5] else 0,
                    'DiscountPercent': float(row[6]) if row[6] else 0,
                    'FinalPrice': float(row[7]) if row[7] else 0,
                    'MaxStudents': row[8],
                    'MaxTeachers': row[9],
                    'StorageLimitMB': row[10],
                    'IncludeReports': row[11],
                    'IsTrialPlan': row[12],
                    'Status': row[13],
                    'IsDeleted': row[14]
                })
        
        return JsonResponse({'status': 'SUCCESS', 'plans': plans})
    except Exception as e:
        logger.error(f"Error fetching plans v2: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def save_plan(request):
    """Save or update subscription plan"""
    try:
        data = json.loads(request.body)
        # Sanitize data: Convert empty strings to None for numeric fields
        def to_int(v):
            if v is None or (isinstance(v, str) and v.strip() == ''): return None
            try: return int(v)
            except: return None
        
        def to_numeric(v):
            if v is None or (isinstance(v, str) and v.strip() == ''): return None
            try: return float(v)
            except: return None

        plan_id = to_int(data.get('plan_id'))
        action = 'UPDATE' if plan_id else 'INSERT'
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            # 15 parameters exactly matching migration 0082
            cursor.execute("""
                SELECT * FROM fn_subscription_plan_iud(
                    %s::varchar, %s::int, %s::varchar, %s::varchar, %s::varchar, 
                    %s::int, %s::numeric, %s::numeric, %s::int, %s::int, 
                    %s::int, %s::boolean, %s::boolean, %s::int, %s::int
                )
            """, [
                action,
                plan_id,
                data.get('plan_name'),
                data.get('plan_code'),
                data.get('plan_type'),
                to_int(data.get('duration_months')),
                to_numeric(data.get('price')),
                to_numeric(data.get('discount_percent')),
                to_int(data.get('max_students')),
                to_int(data.get('max_teachers')),
                to_int(data.get('storage_limit_mb')),
                bool(data.get('include_reports', True)),
                bool(data.get('is_trial_plan', False)),
                to_int(data.get('grace_period_days', 0)),
                user_id
            ])
            result = cursor.fetchone()
        
        return JsonResponse({'status': result[0], 'message': result[1]})
    except Exception as e:
        logger.error(f"Error saving plan: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def delete_plan(request):
    """Delete subscription plan"""
    try:
        data = json.loads(request.body)
        plan_id = data.get('plan_id')
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fn_subscription_plan_iud(
                    'DELETE'::varchar, %s::int, NULL::varchar, NULL::varchar, NULL::varchar, 
                    NULL::int, NULL::numeric, NULL::numeric, NULL::int, NULL::int, 
                    NULL::int, NULL::boolean, NULL::boolean, NULL::int, %s::int
                )
            """, [plan_id, user_id])
            result = cursor.fetchone()
        
        return JsonResponse({'status': result[0], 'message': result[1]})
    except Exception as e:
        logger.error(f"Error deleting plan: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def subscribers(request):
    """Render subscribers page"""
    from core.views import get_context
    context = get_context(request)
    
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
    
    # Add school dropdown for Super Admin (ProfileID = 1)
    if profile_id == 1:
        from core.utils import get_school_dropdown
        context['schools'] = get_school_dropdown()
    
    return render(request, 'core/subscribers.html', context)

@custom_login_required
def get_subscribers(request):
    """Get all subscribers via hardened v2 procedure with billing telemetry"""
    try:
        plan_id = request.GET.get('plan_id')
        plan_id = int(plan_id) if plan_id and plan_id.strip() else None
        
        payment_status = request.GET.get('payment_status')
        payment_status = payment_status.strip() if payment_status and payment_status.strip() else None
        
        search = request.GET.get('search')
        search = search.strip() if search and search.strip() else None

        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 100))

        school_id = request.GET.get('school_id')
        school_id = int(school_id) if school_id and school_id not in ('0', '', 'null', 'undefined') else None
        
        with connection.cursor() as cursor:
            # Use Dedicated Activation Queue Procedure (Official Standard)
            # Hardened to support p_SchoolID filtering
            cursor.execute("""
                SELECT * FROM "Proc_subscriber_get_activation_List"(
                    p_Search := %s::varchar,
                    p_PageNumber := %s,
                    p_PageSize := %s,
                    p_SchoolID := %s
                )
            """, [search, page_number, page_size, school_id])
            
            subscribers = []
            total_count = 0
            for row in cursor.fetchall():
                subscribers.append({
                    'SubscriberID': row[0],
                    'SubscriptionNo': row[1],
                    'SubscriberName': row[2],
                    'PlanName': row[3],
                    'PlanType': row[4],
                    'PlanID': row[5],
                    'StartDate': row[6].strftime('%Y-%m-%d') if row[6] else None,
                    'EndDate': row[7].strftime('%Y-%m-%d') if row[7] else None,
                    'DurationMonths': row[8],
                    'PaymentMode': row[9],
                    'PaymentStatus': row[10],
                    'PaymentReference': row[11] if row[11] not in (None, '', 'None') else None,
                    'PaymentDate': row[12].strftime('%Y-%m-%d') if row[12] else None,
                    'FinalAmount': float(row[13]) if row[13] else 0,
                    'ReferredByName': row[14],
                    'IsActive': row[15],
                    'SchoolID': row[16],
                    'SchoolCode': row[17],
                    'BillingCompanyName': row[18],
                    'BillingGSTIN': row[19],
                    'BillingAddress': row[20],
                    'BillingStateCode': row[21],
                    'PaymentProof': row[22] if (row[22] and row[22] not in ('data:image/png;base64,', 'None', '')) else None,
                    'SchoolAddress': row[23],
                    'ReferredByUserID': row[24]
                })
                total_count = row[25]
            
            # Check if user is SuperAdmin for activation permissions
            is_superadmin = request.session.get('ProfileID') == 1
        
        return JsonResponse({
            'status': 'SUCCESS', 
            'subscribers': subscribers, 
            'total_count': total_count,
            'isSuperAdmin': is_superadmin
        })
    except Exception as e:
        logger.error(f"Error fetching subscribers v2: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_referral_partners(request):
    """Fetch all users with 'Referral Partner' profile using stored procedure"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM fn_referral_partner_get_list()")
            partners = []
            for row in cursor.fetchall():
                partners.append({
                    'UserID': row[0],
                    'UserCode': row[1],
                    'UserName': row[2],
                    'Email': row[3],
                    'ProfileName': row[4]
                })
            return JsonResponse({'status': 'SUCCESS', 'data': partners})
    except Exception as e:
        logger.error(f"Error fetching referral partners: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
@transaction.atomic
def save_subscriber(request):
    """Save or update subscriber record with multi-tenant security and payment proof support."""
    try:
        # 1. Handle both JSON and Multipart (for file upload)
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.dict()
            payment_proof_file = request.FILES.get('payment_proof')
        else:
            data = json.loads(request.body)
            payment_proof_file = None
            
        proof_binary = None
        if payment_proof_file:
            if payment_proof_file.size > 5 * 1024 * 1024: # 5MB limit
                return JsonResponse({'status': 'FAILED', 'message': 'Payment proof too large (Max 5MB)'})
            proof_binary = payment_proof_file.read()

        action = data.get('action', 'INSERT')
        subscriber_id = data.get('subscriber_id')
        plan_id = data.get('plan_id')
        school_id = data.get('school_id') or request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        profile_id = request.session.get('ProfileID')
        
        # Normalize IDs to INT
        try:
            plan_id = int(plan_id) if plan_id else None
            school_id = int(school_id or 0)
            
            # CRITICAL: Row-level lock on the school to serialize concurrent requests from same institution
            school_code = 'N/A'
            school_display_name = 'Unknown Institution'
            if school_id:
                with connection.cursor() as cursor:
                    # Optimized fetch with safe indexing
                    cursor.execute('SELECT "SchoolCode", "SchoolName" FROM "SchoolMaster" WHERE "SchoolID" = %s FOR UPDATE', [school_id])
                    school_row = cursor.fetchone()
                    if school_row:
                        school_code = school_row[0] or 'N/A'
                        school_display_name = school_row[1] or 'Unknown Institution'
        except (ValueError, TypeError) as conv_err:
            logger.error(f"ID Conversion Error: {conv_err}")
            return JsonResponse({'status': 'FAILED', 'message': 'Institutional IDs must be valid numeric values'})
        
        if not plan_id:
            return JsonResponse({'status': 'FAILED', 'message': 'Please select a valid Subscription Plan'})

        payment_status = data.get('payment_status', 'Pending')
        payment_mode = data.get('payment_mode', 'N/A')
        payment_reference = data.get('payment_reference', 'N/A')
        
        if profile_id != 1 and action == 'INSERT':
            payment_status = 'Pending'
        
        subscription_no = None
        if action == 'INSERT':
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            subscription_no = f'SUBS{timestamp}'
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT istrialplan, price, planname, durationmonths 
                FROM subscriptionplan 
                WHERE planid = %s
            """, [plan_id])
            plan_info = cursor.fetchone()
            if not plan_info:
                return JsonResponse({'status': 'FAILED', 'message': f'Invalid Plan selected (ID: {plan_id})'})
            
            is_trial = plan_info[0]
            plan_price = float(plan_info[1] or 0)
            plan_name = plan_info[2]
            plan_duration = plan_info[3]
            
            if (is_trial or plan_price == 0):
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM "Subscriber" s
                    JOIN subscriptionplan sp ON s."PlanID" = sp.planid
                    WHERE s."SchoolId" = %s AND (sp.istrialplan = TRUE OR s."FinalAmount" = 0) AND s."IsDeleted" = FALSE
                    AND s."SubscriberID" != COALESCE(%s, 0)
                """, [school_id, subscriber_id])
                tr_row = cursor.fetchone()
                trial_count = tr_row[0] if tr_row else 0
                if trial_count > 0:
                    return JsonResponse({
                        'status': 'FAILED', 
                        'message': 'This school has already used its one-time free trial subscription.'
                    })

            amount_paid = float(data.get('amount_paid') or plan_price)
            duration_months = int(data.get('duration_months') or plan_duration)

            raw_start = data.get('start_date') or data.get('subscription_start_date') or datetime.now().strftime('%Y-%m-%d')
            try:
                if ' ' in raw_start:
                    final_start_date = datetime.strptime(raw_start.strip(), '%d %b %Y').strftime('%Y-%m-%d')
                else:
                    final_start_date = datetime.strptime(raw_start.strip(), '%Y-%m-%d').strftime('%Y-%m-%d')
            except:
                final_start_date = datetime.now().strftime('%Y-%m-%d')

            # Inclusive Collision Check Logic: S1 <= E2 AND S2 <= E1
            cursor.execute("""
                SELECT COUNT(*) 
                FROM "Subscriber" 
                WHERE "SchoolId" = %s AND "IsDeleted" = FALSE
                AND (%s::date <= "SubscriptionEndDate" AND "SubscriptionStartDate" <= (%s::date + (%s || ' months')::interval - interval '1 day')::date)
                AND "SubscriberID" != COALESCE(%s, 0)
            """, [school_id, final_start_date, final_start_date, duration_months, subscriber_id])
            coll_row = cursor.fetchone()
            if coll_row and coll_row[0] > 0:
                return JsonResponse({'status': 'FAILED', 'message': 'Collision Detected: This period is already covered by another active subscription.'})

            referred_by_id = data.get('referred_by_id')
            referred_by_id = int(referred_by_id) if referred_by_id and str(referred_by_id).isdigit() else None
            referral_incentive = float(data.get('referral_incentive') or 0)
            referral_percentage = float(data.get('referral_percentage') or 0)

            # Extract Billing Metadata
            billing_info = data.get('billing_info', {})
            billing_name = billing_info.get('company_name')
            billing_gst = billing_info.get('gstin')
            billing_address = billing_info.get('address')
            billing_state = billing_info.get('state_code')

            if action == 'INSERT':
                cursor.execute("""
                    INSERT INTO "Subscriber" (
                        "SubscriptionNo", "SubscriberType", "SchoolId", "PlanID", 
                        "SubscriptionStartDate", "SubscriptionEndDate", "DurationMonths",
                        "PaymentMode", "PaymentStatus", "PaymentReference", "PaymentDate",
                        "AmountPaid", "DiscountPercent", "FinalAmount", "ReferredByUserID", "ReferralIncentive",
                        "BillingCompanyName", "BillingGSTIN", "BillingAddress", "BillingStateCode",
                        "IsActive", "IsRenewed", "RenewalParentID", "PaymentProof", "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES (%s, %s, %s, %s, %s, (%s::date + (%s || ' months')::interval)::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, FALSE)
                    RETURNING "SubscriberID"
                """, [
                    subscription_no, data.get('subscriber_type', 'School'), school_id, plan_id,
                    final_start_date, final_start_date, duration_months, duration_months,
                    data.get('payment_mode'), payment_status, data.get('payment_reference'),
                    data.get('payment_date'), amount_paid, data.get('discount_percent', 0),
                    amount_paid, referred_by_id, referral_incentive,
                    billing_name, billing_gst, billing_address, billing_state,
                    (payment_status == 'Paid'), bool(data.get('renewal_parent_id')),
                    data.get('renewal_parent_id'), proof_binary, user_id
                ])
                res_row = cursor.fetchone()
                if not res_row:
                    raise Exception("Database failed to return the new Subscriber ID")
                subscriber_id = res_row[0]
                
                # [Consolidated] Referral incentive update moved to terminal activation block for consistency

            else:
                cursor.execute("""
                    UPDATE "Subscriber" SET
                        "PlanID" = %s, "SubscriptionStartDate" = %s,
                        "SubscriptionEndDate" = (%s::date + (%s || ' months')::interval)::date,
                        "DurationMonths" = %s, "PaymentMode" = %s, "PaymentStatus" = %s,
                        "PaymentReference" = %s, "AmountPaid" = %s, "FinalAmount" = %s,
                        "ReferredByUserID" = %s, "ReferralIncentive" = %s, "IsActive" = %s,
                        "BillingCompanyName" = %s, "BillingGSTIN" = %s, "BillingAddress" = %s, "BillingStateCode" = %s,
                        "PaymentProof" = COALESCE(%s, "PaymentProof"), "UpdatedBy" = %s, "UpdatedAt" = CURRENT_TIMESTAMP
                    WHERE "SubscriberID" = %s
                """, [
                    plan_id, final_start_date, final_start_date, duration_months,
                    duration_months, data.get('payment_mode'), payment_status,
                    data.get('payment_reference'), amount_paid, amount_paid,
                    referred_by_id, referral_incentive, (payment_status == 'Paid'),
                    billing_name, billing_gst, billing_address, billing_state,
                    proof_binary, user_id, subscriber_id
                ])
                
                # [Consolidated] Referral incentive update moved to terminal activation block for consistency


            # ------------------------------------------------------------------
            # NEW: Advanced Invoicing & Transaction System
            # ------------------------------------------------------------------
            if payment_status == 'Paid':
                # Check if invoice already exists
                cursor.execute('SELECT "InvoiceID" FROM "InvoiceMaster" WHERE "SubscriptionID" = %s', [subscriber_id])
                inv_check = cursor.fetchone()
                
                # 0. Fetch Dynamic Tax from TaxMaster
                with connection.cursor() as tax_cursor:
                    tax_cursor.execute('SELECT "Proc_TaxMaster_GET"(NULL, TRUE)')
                    tax_res = tax_cursor.fetchone()
                    tax_record_list = tax_res[0] if tax_res else None
                
                if isinstance(tax_record_list, str):
                    tax_record_list = json.loads(tax_record_list)
                
                # Default to fallback values if no active tax is configured
                active_tax_percent = 18.0
                tax_is_inclusive = True
                
                if tax_record_list and isinstance(tax_record_list, list) and len(tax_record_list) > 0:
                    active_tax_percent = float(tax_record_list[0].get('TaxPercentage', 18.0))
                    tax_is_inclusive = tax_record_list[0].get('IsInclusive', True)
                
                tax_multiplier = 1 + (active_tax_percent / 100.0)
                
                # Generate Financial Values
                input_amt = float(amount_paid)
                if tax_is_inclusive:
                    final_amt = input_amt
                    tax_amt = round(final_amt - (final_amt / tax_multiplier), 2)
                    base_amt = round(final_amt - tax_amt, 2)
                else:
                    # Price + Tax logic: input_amt is the base plan value
                    base_amt = input_amt
                    tax_amt = round(base_amt * (active_tax_percent / 100.0), 2)
                    final_amt = round(base_amt + tax_amt, 2)

                discount_amt = 0.00 # Placeholder for now, can be enriched from discount_percent if needed
                
                if not inv_check:
                    # Generate unique Invoice Number
                    invoice_no = f'SW/INV/{datetime.now().strftime("%y%m")}/{subscriber_id}'
                    
                    # 0.1 Fetch Current Invoice Template Snapshot
                    invoice_template_path = 'core/document_templates/subscription_invoice/template1.html' # Default
                    cursor.execute("""
                        SELECT "TemplateFile" FROM "TemplateSettings" 
                        WHERE "TemplateType" = 'SubscriptionInvoice' AND "IsActive" = TRUE AND "IsDeleted" = FALSE AND "SchoolID" = 0
                        LIMIT 1
                    """)
                    t_row = cursor.fetchone()
                    if t_row:
                        invoice_template_path = t_row[0]

                    # 1. Insert Invoice Master
                    cursor.execute("""
                        INSERT INTO "InvoiceMaster" (
                            "InvoiceNumber", "SchoolID", "SubscriptionID", "InvoiceDate", 
                            "DueDate", "TotalAmount", "TaxAmount", "DiscountAmount", "FinalAmount", 
                            "PaymentStatus", "PaymentDate", "CreatedBy", "TemplateUrl"
                        ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, 'Paid', CURRENT_TIMESTAMP, %s, %s)
                        RETURNING "InvoiceID"
                    """, [invoice_no, school_id, subscriber_id, final_start_date, base_amt, tax_amt, discount_amt, final_amt, user_id, invoice_template_path])
                    inv_row = cursor.fetchone()
                    if not inv_row: raise Exception("Invoice generation failed: No row returned")
                    invoice_id = inv_row[0]
                    
                    # 2. Insert Invoice Item (Fetch plan name first)
                    cursor.execute('SELECT planname FROM subscriptionplan WHERE planid = %s', [plan_id])
                    plan_row = cursor.fetchone()
                    plan_name_display = plan_row[0] if plan_row else "Subscription Plan"
                    
                    cursor.execute("""
                        INSERT INTO "InvoiceItems" (
                            "InvoiceID", "ItemName", "Description", "Quantity", "UnitPrice", "TotalPrice"
                        ) VALUES (%s, %s, %s, 1, %s, %s)
                    """, [invoice_id, plan_name_display, f"License for {duration_months} Months", base_amt, base_amt])
                    
                    # 3. Insert Payment Transaction
                    cursor.execute("""
                        INSERT INTO "PaymentTransactions" (
                            "InvoiceID", "PaymentMode", "TransactionRef", "Amount", "Status"
                        ) VALUES (%s, %s, %s, %s, 'Success')
                    """, [invoice_id, data.get('payment_mode'), data.get('payment_reference'), final_amt])
                    
                    logger.info(f"Invoice {invoice_no} generated for Subscriber {subscriber_id}")
                cursor.execute("""
                    UPDATE "Subscriber" SET
                        "SubscriptionStartDate" = %s,
                        "SubscriptionEndDate" = (%s::date + (%s || ' months')::interval)::date,
                        "DurationMonths" = %s,
                        "PaymentMode" = %s,
                        "PaymentStatus" = %s,
                        "PaymentReference" = %s,
                        "PaymentDate" = %s,
                        "AmountPaid" = %s,
                        "DiscountPercent" = %s,
                        "FinalAmount" = %s,
                        "ReferredByUserID" = %s,
                        "ReferralIncentive" = %s,
                        "IsActive" = %s,
                        "PaymentProof" = COALESCE(%s, "PaymentProof"),
                        "UpdatedBy" = %s,
                        "UpdatedAt" = CURRENT_TIMESTAMP
                    WHERE "SubscriberID" = %s
                """, [
                    final_start_date,
                    final_start_date,
                    duration_months,
                    duration_months,
                    data.get('payment_mode'),
                    payment_status,
                    data.get('payment_reference'),
                    data.get('payment_date'),
                    input_amt,
                    data.get('discount_percent', 0),
                    final_amt,
                    referred_by_id,
                    referral_incentive,
                    (payment_status == 'Paid'),
                    proof_binary,
                    user_id,
                    subscriber_id
                ])

            # Synchronize ReferralIncentive Tracking Table if Active
            if payment_status == 'Paid' and referred_by_id:
                # Fetch SubscriptionNo if we don't have it (for UPDATE action)
                final_inv_no = subscription_no
                if not final_inv_no:
                    cursor.execute('SELECT "SubscriptionNo" FROM "Subscriber" WHERE "SubscriberID" = %s', [subscriber_id])
                    inv_row = cursor.fetchone()
                    final_inv_no = inv_row[0] if inv_row else 'SUB-ERR'

                cursor.execute("""
                    INSERT INTO "ReferralIncentive" (
                        "SubscriberID", "PartnerID", "Amount", "IncentivePercentage", "InvoiceID", "Status", "CreatedBy"
                    ) VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
                    ON CONFLICT ("SubscriberID") DO UPDATE SET
                        "Amount" = EXCLUDED."Amount",
                        "IncentivePercentage" = EXCLUDED."IncentivePercentage",
                        "InvoiceID" = EXCLUDED."InvoiceID",
                        "UpdatedBy" = %s,
                        "UpdatedAt" = CURRENT_TIMESTAMP
                """, [subscriber_id, referred_by_id, referral_incentive, referral_percentage, final_inv_no, user_id, user_id])

            # Mark parent as renewed if applicable
            if data.get('renewal_parent_id') and action == 'INSERT':
                cursor.execute("UPDATE \"Subscriber\" SET \"IsRenewed\" = TRUE WHERE \"SubscriberID\" = %s", [data.get('renewal_parent_id')])



            pass # Allow code to proceed to notifications and final response
        
        # Trigger Notification for Super Admin on New Request
        if action == 'INSERT' and payment_status == 'Pending':
            try:
                school_name = request.session.get('SchoolName', 'Unknown School')
                is_renewal = bool(data.get('renewal_parent_id'))
                request_type = "Subscription Renewal" if is_renewal else "New Subscription"
                
                with connection.cursor() as cursor:
                    # Find Super Admins (ProfileID = 1)
                    cursor.execute('SELECT "UserID", "Email" FROM "UserMaster" WHERE "ProfileID" = 1 AND "IsDeleted" = FALSE')
                    admin_rows = cursor.fetchall()
                    admin_ids = ",".join([str(r[0]) for r in admin_rows])
                    admin_emails = [r[1] for r in admin_rows if r[1]]

                    if admin_ids:
                        # Fetch final dates for notification content
                        cursor.execute('SELECT "SubscriptionStartDate", "SubscriptionEndDate" FROM "Subscriber" WHERE "SubscriberID" = %s', [subscriber_id])
                        dates_row = cursor.fetchone()
                        start_str = dates_row[0].strftime('%d %b %Y') if dates_row and dates_row[0] else 'N/A'
                        end_str = dates_row[1].strftime('%d %b %Y') if dates_row and dates_row[1] else 'N/A'

                        # SECURITY: Wrap notification in nested atomic block. 
                        # If notification fails, the Subscriber record (committed above in main transaction) still persists.
                        with transaction.atomic():
                            cursor.execute("""
                                SELECT * FROM "Proc_Notification_Create"(
                                    %s::int, %s::varchar, %s::varchar, %s::text, 
                                    %s::varchar, %s::varchar, %s::bigint, %s::int, %s::text, %s::timestamp
                                )
                            """, [
                                None, 
                                'SubscriptionRequest', 
                                f'{request_type} - {subscription_no}', 
                                f"{request_type} for '{plan_name}' from {school_display_name} ({school_code}). Amount: ₹{amount_paid}. Period: {start_str} to {end_str}.", 
                                '/subscription/subscribers/', 
                                'SubscriptionRequest', 
                                subscriber_id, 
                                user_id, 
                                admin_ids, 
                                None
                            ])

                        # Queue Email Notifications for Super Admins
                        placeholders = {
                            'request_type': request_type,
                            'school_name': school_name,
                            'plan_name': plan_name,
                            'duration': duration_months,
                            'amount': amount_paid,
                            'payment_mode': payment_mode,
                            'payment_reference': payment_reference or 'N/A',
                            'start_date': final_start_date,
                            'subscriber_id': subscriber_id
                        }
                        
                        for email in admin_emails:
                             EmailTrackingManager.create_email_task(
                                email_code='SUBSCRIPTION_NOTIFICATION',
                                to_email=email,
                                placeholders=placeholders,
                                school_id=None,
                                priority=10 # High Priority
                            )
            except Exception as notify_err:
                logger.error(f"Error sending subscription notification (Admin): {notify_err}")

        # Trigger Notification for School Admin on Activation (UPDATE to Paid)
        if action == 'UPDATE' and payment_status == 'Paid':
            try:
                school_name = request.session.get('SchoolName', 'Unknown School')
                with connection.cursor() as cursor:
                    # Find all School Admins (ProfileID = 2) for this school
                    cursor.execute('SELECT "UserID", "Email" FROM "UserMaster" WHERE "SchoolID" = %s AND "ProfileID" = 2 AND "IsDeleted" = FALSE', [school_id])
                    school_admin_rows = cursor.fetchall()
                    school_admin_ids = ",".join([str(r[0]) for r in school_admin_rows])
                    school_admin_emails = [r[1] for r in school_admin_rows if r[1]]

                    if school_admin_ids:
                        # Fetch final dates for notification content
                        cursor.execute('SELECT "SubscriptionStartDate", "SubscriptionEndDate" FROM "Subscriber" WHERE "SubscriberID" = %s', [subscriber_id])
                        dates_row = cursor.fetchone()
                        start_str = dates_row[0].strftime('%d %b %Y') if dates_row and dates_row[0] else 'N/A'
                        end_str = dates_row[1].strftime('%d %b %Y') if dates_row and dates_row[1] else 'N/A'

                        # System Notification to School Admins
                        with transaction.atomic():
                            cursor.execute("""
                                SELECT * FROM "Proc_Notification_Create"(
                                    %s::int, %s::varchar, %s::varchar, %s::text, 
                                    %s::varchar, %s::varchar, %s::bigint, %s::int, %s::text, %s::timestamp
                                )
                            """, [
                                school_id, 
                                'SubscriptionActivation', 
                                'Subscription Activated', 
                                f"Subscription for '{plan_name}' has been activated for {school_display_name} ({school_code}). Amount: ₹{amount_paid}. Period: {start_str} to {end_str}.", 
                                '/subscription/my/', 
                                'SubscriptionActivation', 
                                subscriber_id, 
                                user_id, 
                                school_admin_ids, 
                                None
                            ])

                        # Queue Email Notifications for School Admins
                        placeholders = {
                            'school_name': school_display_name,
                            'school_code': school_code,
                            'plan_name': plan_name,
                            'duration': duration_months,
                            'amount': amount_paid,
                            'start_date': start_str,
                            'end_date': end_str,
                            'subscriber_id': subscriber_id
                        }
                        
                        for email in school_admin_emails:
                             EmailTrackingManager.create_email_task(
                                email_code='SUBSCRIPTION_ACTIVATION',
                                to_email=email,
                                placeholders=placeholders,
                                school_id=school_id,
                                priority=10, # High Priority
                                has_attachments=True # Enable Invoice Attachment
                            )
                        logger.info(f"Subscription activation notification (with invoice) sent to {len(school_admin_emails)} admins for school {school_id}")
            except Exception as notify_err:
                logger.error(f"Error sending subscription activation notification: {notify_err}")

        return JsonResponse({'status': 'SUCCESS', 'message': 'Request submitted successfully. Waiting for admin approval.' if payment_status == 'Pending' else 'Subscription activated successfully.'})
    except Exception as e:
        import traceback
        error_msg = f"Error saving subscriber: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return JsonResponse({'status': 'FAILED', 'message': error_msg})

@custom_login_required
@require_POST
def confirm_payment(request):
    """Confirm payment and activate subscription (Super Admin Only)"""
    try:
        data = json.loads(request.body)
        subscriber_id = data.get('subscriber_id')
        user_id = request.session.get('UserId')
        
        if request.session.get('ProfileID') != 1:
            return JsonResponse({'status': 'FAILED', 'message': 'Unauthorized access'})

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fn_subscriber_iud(
                    'UPDATE', %s, NULL, NULL, NULL, NULL, %s, NULL, %s, 'Paid', %s, %s, NULL, NULL, NULL, NULL, NULL, NULL, %s
                )
            """, [
                subscriber_id,
                datetime.now().strftime('%Y-%m-%d'),
                data.get('payment_mode', 'Online'),
                data.get('payment_reference'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                user_id
            ])
            
            # Notify School Admin
            cursor.execute('SELECT "SchoolId", "PlanID" FROM "Subscriber" WHERE "SubscriberID" = %s', [subscriber_id])
            sub_info = cursor.fetchone()
            if sub_info:
                school_id = sub_info[0]
                plan_id = sub_info[1]
                cursor.execute('SELECT planname FROM subscriptionplan WHERE planid = %s', [plan_id])
                plan_name = cursor.fetchone()[0]
                
                # Find School Admins (ProfileID = 2) for this school
                cursor.execute('SELECT "UserID" FROM "UserMaster" WHERE "SchoolID" = %s AND "ProfileID" = 2 AND "IsDeleted" = FALSE', [school_id])
                school_admin_ids = ",".join([str(r[0]) for r in cursor.fetchall()])


                
                if school_admin_ids:
                    # SECURITY: Wrap notification in nested atomic block
                    with transaction.atomic():
                        cursor.execute("""
                            SELECT * FROM Proc_Notification_Create(
                                %s::int, %s::varchar, %s::varchar, %s::text, 
                                %s::varchar, %s::varchar, %s::bigint, %s::int, %s::text, %s::timestamp
                            )
                        """, [
                            school_id,
                            'Subscription',
                            'Payment Confirmed',
                            f"Payment confirmed for '{plan_name}'. Your subscription is now active!",
                            '/subscription/my/',
                            'Subscription',
                            subscriber_id,
                            user_id,
                            school_admin_ids,
                            None
                        ])

        return JsonResponse({'status': 'SUCCESS', 'message': 'Payment confirmed and subscription activated'})
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def delete_subscriber(request):
    """Delete subscriber"""
    try:
        data = json.loads(request.body)
        subscriber_id = data.get('subscriber_id')
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fn_subscriber_iud(
                    'DELETE'::varchar, %s::int, NULL, NULL, NULL, 
                    NULL, NULL, NULL, NULL, NULL, 
                    NULL, NULL, NULL, NULL, NULL, 
                    NULL, NULL, NULL, %s::int
                )
            """, [subscriber_id, user_id])
            result = cursor.fetchone()
        
        return JsonResponse({'status': result[0], 'message': result[1]})
    except Exception as e:
        logger.error(f"Error deleting subscriber: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_schools_list(request):
    """Get schools for dropdown"""
    try:
        with connection.cursor() as cursor:
            # Corrected Case-Sensitive Relation: "SchoolMaster"
            cursor.execute('SELECT "SchoolID", "SchoolCode", "SchoolName" FROM "SchoolMaster" WHERE "IsDeleted" = FALSE ORDER BY "SchoolName"')
            schools = [{'id': row[0], 'code': row[1], 'name': row[2]} for row in cursor.fetchall()]


        return JsonResponse({'status': 'SUCCESS', 'schools': schools})
    except Exception as e:
        logger.error(f"Error fetching schools: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def get_users_list(request):
    """Get users for referral dropdown"""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT "UserID", "UserName" FROM "UserMaster" WHERE "IsDeleted" = FALSE ORDER BY "UserName"')
            users = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]


        return JsonResponse({'status': 'SUCCESS', 'users': users})
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def my_subscription(request):
    """Render my subscription page"""
    from core.views import get_context
    context = get_context(request)
    
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
    
    return render(request, 'core/my_subscription.html', context)

@custom_login_required
def subscription_history(request):
    """Render subscription history page"""
    from core.views import get_context
    context = get_context(request)
    
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
        
        # Add school dropdown for Super Admin (ProfileID = 1)
        if profile_id == 1:
            from core.utils import get_school_dropdown
            context['schools'] = get_school_dropdown()
    
    return render(request, 'core/subscription_history.html', context)
@custom_login_required
def my_subscription_data(request):
    """Get summarized and paginated subscription data for schools and super admins."""
    try:
        # 1. Extract Parameters
        school_id = request.GET.get('school_id')
        profile_id = request.session.get('ProfileID')
        
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        sort_column = request.GET.get('sort_column', 'CreatedAt')
        sort_order = request.GET.get('sort_order', 'DESC').upper()
        search = request.GET.get('search', '').strip() or None
        payment_status = request.GET.get('payment_status', '').strip() or None
        
        # 2. Security & Scope Handling
        is_global = False
        if not school_id and profile_id == 1:
            is_global = True
        elif not school_id:
            school_id = request.session.get('SchoolID')
        
        # Adjust target SchoolID for the SQL call
        target_school = int(school_id) if school_id and not is_global else None
        
        with connection.cursor() as cursor:
            # 3. Fetch Comprehensive Data via joined function
            cursor.execute("""
                SELECT h.*, inv."InvoiceNumber"
                FROM fn_subscription_history_full_list(
                    p_Search := %s,
                    p_PageNumber := %s,
                    p_PageSize := %s,
                    p_SortColumn := %s,
                    p_SortOrder := %s,
                    p_SchoolID := %s,
                    p_Status := %s,
                    p_PlanID := %s
                ) h
                LEFT JOIN public."InvoiceMaster" inv ON h."SubscriberID" = inv."SubscriptionID"
            """, [
                search,
                page,
                page_size,
                sort_column,
                sort_order,
                target_school,
                request.GET.get('status', 'all'),
                request.GET.get('plan_id', None)
            ])
            
            rows = cursor.fetchall()
            
            subscriptions = []
            total_records = 0
            active_count = 0 
            paid_count = 0
            
            for row in rows:
                if not total_records:
                    total_records = row[24]
                    active_count = row[25]
                    paid_count = row[26]

                subscriptions.append({
                    'SubscriberID': row[0],
                    'SubscriptionNo': row[1],
                    'SchoolName': row[2],
                    'SchoolCode': row[3],
                    'PlanName': row[4],
                    'PlanType': row[5],
                    'StartDate': row[6].strftime('%Y-%m-%d') if row[6] else None,
                    'EndDate': row[7].strftime('%Y-%m-%d') if row[7] else None,
                    'DurationMonths': row[8],
                    'SubStatus': row[9],
                    'InvoiceID': row[10],
                    'InvoiceNo': row[27] if len(row) > 27 else row[10],
                    'InvoiceDate': row[11].strftime('%Y-%m-%d') if row[11] else None,
                    'FinalAmount': float(row[12] or 0),
                    'PaymentStatus': row[13],
                    'TransactionID': row[14],
                    'PaymentDate': row[15].strftime('%Y-%m-%d %H:%M') if row[15] else None,
                    'PaymentAmount': float(row[16] or 0),
                    'PaymentMethod': row[17],
                    'ReferenceNo': row[18],
                    'AccountName': row[19],
                    'BankName': row[20],
                    'UPIId': row[21],
                    'PartnerName': row[22],
                    'IncentiveAmount': float(row[23] or 0),
                    'IsActive': row[9] == 'Active'
                })
            
            
            # 4. Fetch Real-time Resource Usage (Students, Staff)
            usage = {'students': 0, 'staff': 0, 'storage_mb': 0}
            if target_school:
                with connection.cursor() as usage_cursor:
                    usage_cursor.execute('SELECT COUNT(*)::INT FROM "Student" WHERE "SchoolID" = %s AND "IsDeleted" = FALSE', [target_school])
                    usage['students'] = usage_cursor.fetchone()[0]
                    usage_cursor.execute('SELECT COUNT(*)::INT FROM "EmployeeMaster" WHERE "SchoolID" = %s AND "IsDeleted" = FALSE', [target_school])
                    usage['staff'] = usage_cursor.fetchone()[0]


            
            return JsonResponse({
                'status': 'SUCCESS',
                'summary': {
                    'total': total_records,
                    'active': active_count,
                    'paid': paid_count
                },
                'usage': usage,
                'subscriptions': subscriptions,
                'pagination': {
                    'total_records': total_records,
                    'total_pages': (total_records + page_size - 1) // page_size if total_records > 0 else 0,
                    'current_page': page,
                    'page_size': page_size
                }
            })
    except Exception as e:
        logger.error(f"Error fetching subscription history data: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@super_admin_required
def subscription_report(request):
    """Render subscription report page"""
    from core.views import get_context
    context = get_context(request)
    
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
    
    return render(request, 'core/subscription_report.html', context)

@custom_login_required
@super_admin_required
def subscription_report_details(request):
    """Get detailed subscriber list based on type via hardened procedure"""
    try:
        detail_type = request.GET.get('type')
        start_date = request.GET.get('start_date') or None
        end_date = request.GET.get('end_date') or None
        
        with connection.cursor() as cursor:
            # Use V2 Hardened Procedure
            cursor.execute('SELECT * FROM fn_subscription_report_details_v2(%s, %s, %s)', 
                         [detail_type, start_date, end_date])
            
            rows = []
            for row in cursor.fetchall():
                rows.append([
                    row[0],  # SubscriptionNo
                    row[1],  # SubscriberName
                    row[2],  # PlanName
                    row[3].strftime('%Y-%m-%d') if row[3] else '-',  # StartDate
                    row[4].strftime('%Y-%m-%d') if row[4] else '-',  # EndDate
                    f'₹{float(row[5] or 0):.2f}',  # Amount
                    row[6]   # Status
                ])
            
            titles = {
                'total': 'All Subscribers',
                'active': 'Active Subscribers',
                'paid': 'Paid Subscriptions',
                'pending': 'Pending Payments',
                'referral': 'Referral Incentives'
            }
            
            return JsonResponse({
                'status': 'SUCCESS',
                'title': titles.get(detail_type, 'Details'),
                'headers': ['Subscription No', 'Subscriber', 'Plan', 'Start Date', 'End Date', 'Amount', 'Status'],
                'rows': rows
            })
    except Exception as e:
        logger.error(f"Error fetching reporting details: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@super_admin_required
def subscription_report_data(request):
    """Get subscription report data using unified JSONB procedure"""
    try:
        start_date = request.GET.get('start_date') or None
        end_date = request.GET.get('end_date') or None
        
        with connection.cursor() as cursor:
            # Call Unified JSONB Report Procedure
            cursor.execute("SELECT fn_subscription_full_report_v2(%s, %s)", [start_date, end_date])
            result = cursor.fetchone()[0]
            
            # Harden: Parse JSON string if returned as such by database driver
            if isinstance(result, str):
                result = json.loads(result)
            
            if not result:
                result = {}
            
            # Extract Segments from JSONB
            summary = result.get('summary', {})
            plan_stats = result.get('plan_stats', [])
            yearly_data = result.get('yearly_growth', [])
            
            return JsonResponse({
                'status': 'SUCCESS',
                'total_subscribers': summary.get('total_subscribers', 0),
                'active_subscribers': summary.get('active_subscribers', 0),
                'total_revenue': float(summary.get('total_revenue') or 0),
                'pending_amount': float(summary.get('pending_amount') or 0),
                'total_paid': float(summary.get('total_revenue') or 0),
                'total_referral': float(summary.get('total_referral') or 0),
                'total_before_discount': float(summary.get('total_before_discount') or 0),
                'total_discount': float(summary.get('total_discount') or 0),
                'total_tax': float(summary.get('total_tax') or 0),
                'gross_income': float(summary.get('gross_income') or 0),
                'net_revenue': float(summary.get('net_revenue') or 0),
                'plan_stats': plan_stats,
                'yearly_growth': yearly_data,
                'top_performers': result.get('top_performers', []),
                'yearly_data': yearly_data # Keep both for compatibility
            })
    except Exception as e:
        logger.error(f"Error fetching full report data: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@require_POST
def save_registration_draft(request):
    """Save registration as draft - No login required"""
    try:
        from datetime import datetime
        from django.template.loader import render_to_string
        from django.core.mail import EmailMultiAlternatives
        
        data = json.loads(request.body)
        
        # Check if email already exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM dbo.RegistrationDraft WHERE Email = %s AND IsProcessed = 0", [data.get('email')])
            count = cursor.fetchone()[0]
            if count > 0:
                return JsonResponse({'status': 'FAILED', 'message': 'Registration request already received for this email. Our team will contact you soon.'})
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT Proc_RegistrationDraft_Save(%s, %s, %s, %s::int, %s::int, %s::int, %s, %s, %s, %s, %s::int, %s::int, %s::date, %s, %s, %s, %s, %s, %s, %s::int, %s::date)", 
            [
                data.get('school_name'),
                data.get('registration_number'),
                data.get('address'),
                data.get('country'),
                data.get('state'),
                data.get('district'),
                data.get('pincode'),
                data.get('phone'),
                data.get('email'),
                data.get('website'),
                data.get('board'),
                data.get('medium'),
                data.get('establish_date') or None,
                data.get('principal_name'),
                data.get('principal_contact_mail'),
                data.get('principal_contact_phone'),
                data.get('director_name'),
                data.get('director_contact_email'),
                data.get('director_contact_phone'),
                data.get('plan_id'),
                data.get('subscription_start_date') or None
            ])
            result = cursor.fetchone()
        
        # Get plan details
        plan_name = 'N/A'
        plan_price = 0
        duration_months = 0
        if data.get('plan_id'):
            with connection.cursor() as cursor:
                cursor.execute("SELECT PlanName, FinalPrice, DurationMonths FROM dbo.SubscriptionPlan WHERE PlanID = %s", [data.get('plan_id')])
                plan_row = cursor.fetchone()
                if plan_row:
                    plan_name = plan_row[0]
                    plan_price = round(float(plan_row[1]), 1) if plan_row[1] else 0
                    duration_months = plan_row[2]
        
        # Send acknowledgment email asynchronously
        from threading import Thread
        
        def send_email_async():
            email_status = 'Failed'
            error_msg = None
            started_at = datetime.now()
            try:
                email_context = {
                    'school_name': data.get('school_name'),
                    'email': data.get('email'),
                    'phone': data.get('phone'),
                    'registration_date': datetime.now().strftime('%d %B %Y'),
                    'plan_name': plan_name,
                    'plan_price': plan_price,
                    'duration_months': duration_months,
                    'subscription_start_date': data.get('subscription_start_date') or 'To be confirmed'
                }
                
                html_content = render_to_string('emails/registration_acknowledgment.html', email_context)
                subject = 'Registration Request Received - ShikshaWave ERP'
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body='Thank you for registering with ShikshaWave ERP.',
                    from_email='noreply@shikshawave.com',
                    to=[data.get('email')]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
                email_status = 'Sent'
            except Exception as email_error:
                logger.error(f"Error sending email: {email_error}")
                error_msg = str(email_error)
            finally:
                try:
                    completed_at = datetime.now()
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO EmailTracking (EmailCode, ToEmail, FromEmail, Subject, EmailHtmlBody, Status, 
                                AttemptCount, MaxAttempts, CreatedAt, StartedAt, CompletedAt, LastError, IsActive)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [
                            'REG_ACK',
                            data.get('email'),
                            'noreply@shikshawave.com',
                            subject,
                            html_content,
                            email_status,
                            1,
                            1,
                            started_at,
                            started_at,
                            completed_at,
                            error_msg,
                            1
                        ])
                except Exception as tracking_error:
                    logger.error(f"Error saving email tracking: {tracking_error}")
        
        Thread(target=send_email_async).start()
        
        return JsonResponse({'status': 'SUCCESS', 'message': 'Registration saved successfully. Our team will contact you within 24 hours.'})
    except Exception as e:
        logger.error(f"Error saving registration draft: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@require_POST
def public_registration(request):
    """Public registration endpoint - No login required"""
    try:
        from datetime import datetime
        from django.views.decorators.csrf import csrf_exempt
        
        data = json.loads(request.body)
        
        # Create school with all fields
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC dbo.Proc_School_IUD
                    @Action = 'INSERT',
                    @SchoolName = %s,
                    @RegistrationNumber = %s,
                    @Address = %s,
                    @CountryID = %s,
                    @StateID = %s,
                    @DistrictID = %s,
                    @Pincode = %s,
                    @Phone = %s,
                    @Email = %s,
                    @Website = %s,
                    @BoardID = %s,
                    @MediumID = %s,
                    @EstablishDate = %s,
                    @PrincipalName = %s,
                    @PrincipalContactMail = %s,
                    @PrincipalContactPhone = %s,
                    @DirectorName = %s,
                    @DirectorContactEmail = %s,
                    @DirectorContactPhone = %s,
                    @UserID = NULL
            """, [
                data.get('school_name'),
                data.get('registration_number'),
                data.get('address'),
                data.get('country'),
                data.get('state'),
                data.get('district'),
                data.get('pincode'),
                data.get('phone'),
                data.get('email'),
                data.get('website'),
                data.get('board'),
                data.get('medium'),
                data.get('establish_date'),
                data.get('principal_name'),
                data.get('principal_contact_mail'),
                data.get('principal_contact_phone'),
                data.get('director_name'),
                data.get('director_contact_email'),
                data.get('director_contact_phone')
            ])
            result = cursor.fetchone()
            school_id = result[0] if result else None
        
        # Create subscription
        if school_id:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            subscription_no = f'SUBS{timestamp}'
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    EXEC dbo.Proc_Subscriber_IUD
                        @Action = 'INSERT',
                        @SubscriberID = NULL,
                        @SubscriptionNo = %s,
                        @SubscriberType = 'School',
                        @schoolid = %s,
                        @PlanID = %s,
                        @DurationMonths = NULL,
                        @SubscriptionStartDate = NULL,
                        @PaymentMode = NULL,
                        @PaymentStatus = 'Pending',
                        @PaymentReference = NULL,
                        @PaymentDate = NULL,
                        @AmountPaid = NULL,
                        @DiscountPercent = NULL,
                        @ReferredByUserID = NULL,
                        @ReferralIncentive = NULL,
                        @UserID = NULL
                """, [subscription_no, school_id, data.get('plan_id')])
        
        return JsonResponse({'status': 'SUCCESS', 'message': 'Registration successful'})
    except Exception as e:
        logger.error(f"Error in public registration: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
@require_POST
def add_school(request):
    """Add new school"""
    try:
        data = json.loads(request.body)
        user_id = request.session.get('UserId')
        
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC dbo.Proc_School_IUD
                    @Action = 'INSERT',
                    @SchoolName = %s,
                    @SchoolCode = %s,
                    @Email = %s,
                    @Phone = %s,
                    @UserID = %s
            """, [
                data.get('school_name'),
                data.get('school_code'),
                data.get('email'),
                data.get('phone'),
                user_id
            ])
            result = cursor.fetchone()
            school_id = result[0] if result else None
        
        return JsonResponse({'status': 'SUCCESS', 'message': 'School added successfully', 'school_id': school_id})
    except Exception as e:
        logger.error(f"Error adding school: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def referrals(request):
    """Render referrals dashboard with auto-fix for procedure and role-based scoping"""
    # Defensive Fix: Re-deploy the procedure with correct schema
    with connection.cursor() as cursor:
        cursor.execute("""
            DROP FUNCTION IF EXISTS fn_referral_ledger_get_v1(VARCHAR, DATE, DATE, INT, INT);
            
            CREATE OR REPLACE FUNCTION Proc_Referal_insentive_Dashbaord_get(
                p_Search VARCHAR DEFAULT NULL,
                p_StartDate DATE DEFAULT NULL,
                p_EndDate DATE DEFAULT NULL,
                p_PartnerCode VARCHAR DEFAULT NULL,
                p_PartnerName VARCHAR DEFAULT NULL,
                p_SchoolID INT DEFAULT NULL,
                p_PageNumber INT DEFAULT 1,
                p_PageSize INT DEFAULT 10,
                p_LoginUserID INT DEFAULT NULL
            )
            RETURNS JSONB AS $$
            DECLARE
                v_summary JSONB;
                v_list JSONB;
                v_total_count BIGINT;
            BEGIN
                -- 1. Get Summary Stats
                SELECT jsonb_build_object(
                    'total_referrals', COUNT(*),
                    'total_incentives', COALESCE(SUM(r."Amount"), 0),
                    'unique_referrers', COUNT(DISTINCT r."PartnerID")
                ) INTO v_summary
                FROM public."ReferralIncentive" AS r
                JOIN public."UserMaster" AS u ON u."UserID" = r."PartnerID"
                LEFT JOIN public."Subscriber" AS S ON S."SubscriberID" = r."SubscriberID"
                WHERE u."IsDeleted" = FALSE
                  AND (p_LoginUserID IS NULL OR r."PartnerID" = p_LoginUserID)
                  AND (p_StartDate IS NULL OR r."CreatedAt"::DATE >= p_StartDate)
                  AND (p_EndDate IS NULL OR r."CreatedAt"::DATE <= p_EndDate)
                  AND (p_PartnerCode IS NULL OR u."UserCode" ILIKE '%' || p_PartnerCode || '%')
                  AND (p_PartnerName IS NULL OR u."UserName" ILIKE '%' || p_PartnerName || '%')
                  AND (p_SchoolID IS NULL OR S."SchoolId" = p_SchoolID);

                -- 2. Get Total Count (for pagination)
                SELECT COUNT(*) INTO v_total_count
                FROM public."ReferralIncentive" AS r
                LEFT JOIN public."UserMaster" AS u ON u."UserID" = r."PartnerID"
                LEFT JOIN public."Subscriber" AS S ON S."SubscriberID" = r."SubscriberID"
                LEFT JOIN public."InvoiceMaster" AS i ON i."SubscriptionID" = S."SubscriberID"
                WHERE u."IsDeleted" = FALSE
                  AND (p_LoginUserID IS NULL OR r."PartnerID" = p_LoginUserID)
                  AND (p_StartDate IS NULL OR r."CreatedAt"::DATE >= p_StartDate)
                  AND (p_EndDate IS NULL OR r."CreatedAt"::DATE <= p_EndDate)
                  AND (p_PartnerCode IS NULL OR u."UserCode" ILIKE '%' || p_PartnerCode || '%')
                  AND (p_PartnerName IS NULL OR u."UserName" ILIKE '%' || p_PartnerName || '%')
                  AND (p_SchoolID IS NULL OR S."SchoolId" = p_SchoolID)
                  AND (p_Search IS NULL OR u."UserName" ILIKE '%' || p_Search || '%' OR u."UserCode" ILIKE '%' || p_Search || '%' OR i."InvoiceNumber" ILIKE '%' || p_Search || '%');

                -- 3. Get Paginated Ledger List (Strictly following user's query)
                SELECT jsonb_agg(t) INTO v_list
                FROM (
                    SELECT 
                        r."PartnerID" ,
                        u."UserCode" AS "PartnerCode",
                        u."UserName" AS "PartnerName",
                        r."Amount",
                        r."InvoiceID" AS "SubscriptionNo",
                        i."InvoiceNumber",
                        sm."SchoolCode",
                        sm."SchoolName",
                        s."SubscriptionStartDate",
                        s."SubscriptionEndDate",
                        s."CreatedAt"
                    FROM public."ReferralIncentive" AS r
                    LEFT JOIN public."UserMaster" AS u ON u."UserID" = r."PartnerID"
                    LEFT JOIN public."Subscriber" AS S ON S."SubscriberID" = r."SubscriberID"
                    LEFT JOIN public."InvoiceMaster" AS i ON i."SubscriptionID" = S."SubscriberID"
                    LEFT JOIN public."SchoolMaster" AS sm ON sm."SchoolID" = S."SchoolId"
                    WHERE u."IsDeleted" = FALSE
                      AND (p_LoginUserID IS NULL OR r."PartnerID" = p_LoginUserID)
                      AND (p_StartDate IS NULL OR r."CreatedAt"::DATE >= p_StartDate)
                      AND (p_EndDate IS NULL OR r."CreatedAt"::DATE <= p_EndDate)
                      AND (p_PartnerCode IS NULL OR u."UserCode" ILIKE '%' || p_PartnerCode || '%')
                      AND (p_PartnerName IS NULL OR u."UserName" ILIKE '%' || p_PartnerName || '%')
                      AND (p_SchoolID IS NULL OR S."SchoolId" = p_SchoolID)
                      AND (p_Search IS NULL OR u."UserName" ILIKE '%' || p_Search || '%' OR u."UserCode" ILIKE '%' || p_Search || '%' OR i."InvoiceNumber" ILIKE '%' || p_Search || '%')
                    ORDER BY r."CreatedAt" DESC
                    LIMIT p_PageSize OFFSET (p_PageNumber - 1) * p_PageSize
                ) t;

                RETURN jsonb_build_object(
                    'summary', v_summary,
                    'referrals', COALESCE(v_list, '[]'::jsonb),
                    'total_count', v_total_count
                );
            END;
            $$ LANGUAGE plpgsql;
        """)

    from core.views import get_context
    context = get_context(request)
    
    # Fetch user menus for sidebar
    profile_id = request.session.get('ProfileID')
    if profile_id:
        from core.views import _fetch_user_menus
        menus = _fetch_user_menus(profile_id)
        context.update({
            'menus': menus['tree'],
            'flat_menus': menus['flat']
        })
        
    # Fetch schools for the filter dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT \"SchoolID\", \"SchoolName\" FROM \"SchoolMaster\" WHERE \"IsDeleted\" = FALSE ORDER BY \"SchoolName\"")
        schools = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    context.update({'schools': schools})
    return render(request, 'core/referrals.html', context)

@custom_login_required
def get_referral_list(request):
    """API for paginated referral data via unified JSONB procedure with role-based scoping"""
    try:
        profile_id = request.session.get('ProfileID')
        user_id = request.session.get('UserId')
        
        # Scoping: If not Super Admin (ProfileID != 1), force filter to own UserID
        login_user_id = None if profile_id == 1 else user_id

        page_number = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        search = request.GET.get('search', '').strip() or None
        start_date = request.GET.get('start_date') or None
        end_date = request.GET.get('end_date') or None
        partner_code = request.GET.get('partner_code') or None
        partner_name = request.GET.get('partner_name') or None
        school_id = request.GET.get('school_id') or None
        
        # Guard against empty string/zero for school_id
        if school_id == '0' or not school_id:
            school_id = None
        else:
            school_id = int(school_id)

        with connection.cursor() as cursor:
            # Consume the project standard procedure with 9 parameters
            cursor.execute("SELECT Proc_Referal_insentive_Dashbaord_get(%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                         [search, start_date, end_date, partner_code, partner_name, school_id, page_number, page_size, login_user_id])
            result = cursor.fetchone()[0]
            
            # Harden: Handle JSONB as string if returned by driver
            if isinstance(result, str):
                result = json.loads(result)
            
            if not result:
                result = {}
            
            return JsonResponse({
                'status': 'SUCCESS', 
                'referrals': result.get('referrals', []),
                'total_count': result.get('total_count', 0),
                'summary': result.get('summary', {})
            })
    except Exception as e:
        logger.error(f"Error fetching referral list v2: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@super_admin_required
def get_referral_stats(request):
    """API for referral summary statistics (Legacy compatibility, now wraps unified procedure)"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT fn_referral_dashboard_v2(NULL, 1, 1)")
            result = cursor.fetchone()[0]
            
            # Harden: Handle JSONB as string if returned by driver
            if isinstance(result, str):
                result = json.loads(result)
                
            return JsonResponse({
                'status': 'SUCCESS', 
                'stats': result.get('summary', {}) if result else {}
            })
    except Exception as e:
        logger.error(f"Error fetching referral stats v2: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})
@custom_login_required
def get_payment_methods(request):
    """Fetch active payment accounts for ShikshaWave Admin (SchoolId = 0)."""
    try:
        accounts = []
        with connection.cursor() as cursor:
            # Fetch active payment accounts for SchoolId = 0 (Internal/Default)
            cursor.execute('SELECT * FROM public."Proc_PaymentAccountDetails_Get"(0)')
            
            for row in cursor.fetchall():
                # Only include active accounts
                if not row[15] or row[17]: # IsActive=False or IsDeleted=True
                    continue
                    
                accounts.append({
                    'PaymentMethod': str(row[2]).strip().upper(),
                    'AccountName': row[3],
                    'AccountNumber': row[4],
                    'IFSCCode': row[5],
                    'BranchName': row[6],
                    'AccountHolderName': row[7],
                    'UPIId': row[8],
                    'IsDefault': row[16],
                    'UPIQRCodeBinary': f"data:image/png;base64,{base64.b64encode(bytes(row[19])).decode('utf-8')}" if row[19] else None
                })
        
        return JsonResponse({'status': 'SUCCESS', 'accounts': accounts})
    except Exception as e:
        logger.error(f"Error fetching payment methods: {e}")
        return JsonResponse({'status': 'FAILED', 'message': str(e)})

@custom_login_required
def view_subscription_invoice(request, subscription_id):
    """View and Print Subscription Invoice"""
    try:
        user_id = request.session.get('UserId')
        profile_id = request.session.get('ProfileID')
        session_school_id = request.session.get('SchoolID')

        with connection.cursor() as cursor:
            # 1. Fetch Structured Invoice Data via JSONB Procedure
            cursor.execute('SELECT "proc_subscription_invoice_full_get"(%s)', [subscription_id])
            row = cursor.fetchone()
            if not row or not row[0]:
                messages.error(request, "Invoice data not found or subscription not yet activated.")
                return redirect('subscribers' if profile_id == 1 else 'my_subscription')
            
            invoice_data = row[0]
            if isinstance(invoice_data, str):
                invoice_data = json.loads(invoice_data)

            # 1.1 Helper to format dates beautifully
            def format_dt(dt_str):
                if not dt_str: return "N/A"
                try:
                    # Handle raw timestamps from DB
                    if 'T' in dt_str:
                        dt = datetime.strptime(dt_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    else:
                        dt = datetime.strptime(dt_str, '%Y-%m-%d')
                    return dt.strftime('%d %b, %Y')
                except Exception:
                    return dt_str

            # 1.2 Prepare Formatted Context Data
            master = invoice_data.get('invoice_master', {})
            plan = invoice_data.get('plan_details', {})
            school_info = invoice_data.get('school_details', {})
            
            # Format critical dates
            master['FormattedDate'] = format_dt(master.get('InvoiceDate'))
            plan['FormattedStart'] = format_dt(plan.get('StartDate'))
            plan['FormattedEnd'] = format_dt(plan.get('EndDate'))

            # Fetch Tax Config from TaxMaster
            tax_rate = 18.0  # Safe Default
            try:
                cursor.execute('SELECT "TaxPercentage" FROM "TaxMaster" WHERE "IsActive" = TRUE AND "TaxName" = \'GST\' LIMIT 1')
                tax_row = cursor.fetchone()
                if tax_row:
                    tax_rate = float(tax_row[0])
            except Exception as e:
                logger.error(f"Error fetching TaxMaster: {e}")

            # Calculate Tax Split
            tax_total = float(master.get('TaxAmount', 0))
            master['CGST_Rate'] = tax_rate / 2
            master['SGST_Rate'] = tax_rate / 2
            master['CGST_Amount'] = tax_total / 2
            master['SGST_Amount'] = tax_total / 2
            
            # Amount in Words
            final_amt = float(master.get('FinalAmount', 0))
            master['FinalAmountInWords'] = number_to_words(final_amt)
            
            # 2. Security Check: School Admin can only see their own invoices
            # We check the school_id returned in the invoice data
            invoice_school_id = school_info.get('SchoolID')
            
            cursor.execute('SELECT "SchoolId" FROM "Subscriber" WHERE "SubscriberID" = %s', [subscription_id])
            sub_row = cursor.fetchone()
            if not sub_row:
                 return HttpResponse("Subscription not found", status=404)
            
            actual_school_id = sub_row[0]
            
            if profile_id != 1 and actual_school_id != session_school_id:
                messages.error(request, "Unauthorized access to this invoice.")
                return redirect('my_subscription')

            # 3. Fetch Branding (BrandProfile)
            # Use Proc_BrandProfile_GET for consistency
            cursor.execute('SELECT "Proc_BrandProfile_GET"()')
            db_brand = cursor.fetchone()[0]
            if isinstance(db_brand, str):
                db_brand = json.loads(db_brand)
            
            brand_info = {
                'BrandName': db_brand.get('BrandName', 'ShikshaWave') if db_brand else 'ShikshaWave',
                'BrandLogo': db_brand.get('BrandLogo') if db_brand else None,
                'GSTIN': db_brand.get('GSTIN', 'N/A') if db_brand else 'N/A',
                'Address': db_brand.get('Address', 'N/A') if db_brand else 'N/A',
                'Email': db_brand.get('Email', 'support@shikshawave.in') if db_brand else 'support@shikshawave.in',
                'Website': db_brand.get('Website', 'www.shikshawave.in') if db_brand else 'www.shikshawave.in',
                'Phone': db_brand.get('Phone', 'N/A') if db_brand else 'N/A',
                'AuthorizedSignature': db_brand.get('AuthorizedSignature') if db_brand else None,
                'AuthorizedSignatory': db_brand.get('AuthorizedSignatory', 'Authorised Signatory') if db_brand else 'Authorised Signatory'
            }

            context = {
                'invoice': master,
                'school': school_info,
                'plan': plan,
                'items': invoice_data.get('invoice_items', []),
                'transactions': invoice_data.get('payment_transactions', []),
                'brand': brand_info,
                'footer': invoice_data.get('footer_info', {}),
                'subscription_id': subscription_id,
                'current_year': datetime.now().year
            }

            # 4. Resolve Template Preference (Prioritize Snapshot -> Global)
            template_path = master.get('TemplateUrl') or 'core/document_templates/subscription_invoice/template1.html'
            
            # Fallback to Global Settings only if no snapshot exists (for historic data)
            if not master.get('TemplateUrl'):
                try:
                    # Strictly use Global branding (SchoolID=0) for Subscription Invoices
                    cursor.execute("""
                        SELECT "TemplateFile" FROM "TemplateSettings" 
                        WHERE "TemplateType" = 'SubscriptionInvoice' 
                          AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                          AND "SchoolID" = 0
                        LIMIT 1
                    """)
                    pref_row = cursor.fetchone()
                    if pref_row and pref_row[0]:
                        template_path = pref_row[0]
                except Exception as e:
                    logger.error(f"Error resolving template fallback: {e}")

            return render(request, template_path, context)

    except Exception as e:
        logger.error(f"Error viewing invoice: {e}")
        messages.error(request, f"System Error: {str(e)}")
        return redirect('dashboard')

