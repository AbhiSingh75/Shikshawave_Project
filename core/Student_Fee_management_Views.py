from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .decorators import custom_login_required
from .utils import get_context
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import connection, transaction
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from .models import *
import json, datetime, os, calendar, random, base64
from decimal import Decimal
from urllib.parse import urlencode
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from psycopg2.extras import Json
import logging

logger = logging.getLogger(__name__)


@custom_login_required
def fee_collection_new(request):
    """
    New Fee Collection page - Simple student code search interface
    """
    # Get user context for header
    context = get_context(request)
    
    # Get user information
    user_id = request.session.get('UserId')
    school_id = request.session.get('SchoolID')
    
    if not user_id:
        messages.error(request, "Please login to access fee collection")
        return redirect('login')
    
    if not school_id:
        messages.error(request, "School ID is required to access fee collection")
        return redirect('login')
    
    context.update({
        'user_id': user_id,
        'school_id': school_id,
    })
    
    return render(request, 'core/fee_collection_new.html', context)


@custom_login_required
def get_student_fee_details(request):
    """
    Get student fee details using Proc_Student_fee_Details_get procedure
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request method'})
    
    try:
        # Get parameters
        student_code = request.POST.get('student_code', '').strip()
        if not student_code:
            return JsonResponse({'status': 'ERROR', 'message': 'Student code is required'})
        
        school_id = request.session.get('SchoolID')
        if not school_id:
            return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
            
        student_info = {}
        fee_structure = []
        paid_months = []
        
        # 1. Try Procedure First (Isolated)
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # In Postgres, stored procedures returning SETOF refcursors are called via SELECT * FROM "ProcName"(args)
                    # This returns a row for EACH cursor name (rs1, rs2, rs3).
                    cursor.execute('SELECT * FROM "Proc_Student_fee_Details_get"(%s, %s)', [student_code, None])
                    
                    # fetchall() to get all cursor names [('rs1',), ('rs2',), ('rs3',)]
                    rows = cursor.fetchall()
                    if rows and len(rows) >= 3:
                        # Normalize names into a simple list ['rs1', 'rs2', 'rs3']
                        names = [row[0] for row in rows]
                        
                        # 1. Fetch Student Info (from 'rs1')
                        cursor.execute(f'FETCH ALL IN "{names[0]}"')
                        if cursor.description:
                            columns = [col[0] for col in cursor.description]
                            student_row = cursor.fetchone()
                            if student_row:
                                student_info = dict(zip(columns, student_row))
                        
                        # 2. Fetch Fee Structure (from 'rs2')
                        cursor.execute(f'FETCH ALL IN "{names[1]}"')
                        if cursor.description:
                            columns = [col[0] for col in cursor.description]
                            for row in cursor.fetchall():
                                fee_structure.append(dict(zip(columns, row)))
                        
                        # 3. Fetch Paid Months (from 'rs3')
                        cursor.execute(f'FETCH ALL IN "{names[2]}"')
                        if cursor.description:
                            columns = [col[0] for col in cursor.description]
                            for row in cursor.fetchall():
                                paid_months.append(dict(zip(columns, row)))
        except Exception as proc_err:
            logger.warning(f"Procedure search failed: {proc_err}")
            # student_info remains empty, triggering the fallback below

        # 2. Robust Fallback via Direct SQL
        if not student_info:
            with connection.cursor() as fallback_cursor:
                # Fetch Student Info - Enhanced with Class, Section and Photo from StudentDocuments
                fallback_cursor.execute("""
                    SELECT 
                        s."StudentID", s."StudentCode", s."FullName", s."FatherName", sa."RollNumber",
                        cm."ClassName", sm."SectionName", SD."DocumentData" AS "StudentPhoto"
                    FROM "Student" AS s
                    LEFT JOIN "StudentAcademicTrack" AS sa 
                        ON s."StudentID" = sa."StudentID" AND sa."IsCurrent" = TRUE
                    LEFT JOIN "ClassMaster" AS cm 
                        ON sa."ClassID" = cm."ClassID"
                    LEFT JOIN "SectionMaster" AS sm 
                        ON sa."SectionID" = sm."SectionID"
                    LEFT JOIN "StudentDocuments" AS SD
                        ON SD."StudentID" = s."StudentID" AND SD."DocumentType" = 'Student Passport Photo'
                    WHERE s."StudentCode" = %s AND s."SchoolID" = %s AND s."IsDeleted" = FALSE
                """, [student_code, school_id])
                if fallback_cursor.description:
                    columns = [col[0] for col in fallback_cursor.description]
                    row = fallback_cursor.fetchone()
                    if row:
                        student_info = dict(zip(columns, row))
                
                if student_info:
                    sid = student_info.get('StudentID')
                    # Fetch Fee Structure Fallback
                    try:
                        fallback_cursor.execute("""
                            SELECT 
                                sfa."StudentFeeId" as "FeeAssignmentID",
                                fs."FeeTypeId",
                                fs."FeeTypeName" AS "fee_name",
                                fs."DefaultAmount" AS "default_amount",
                                sfa."DiscountPercentage" AS "discount_percentage",
                                sfa."FeeAmount" AS "amount",
                                sfa."FeeMonth"
                            FROM "Student_Fee_Assignment" sfa
                            LEFT JOIN "FeeType_Master" fs ON sfa."FeeTypeId" = fs."FeeTypeId"
                            WHERE sfa."StudentId" = %s AND sfa."IsDeleted" = FALSE
                        """, [sid])
                        if fallback_cursor.description:
                            columns = [col[0] for col in fallback_cursor.description]
                            for row in fallback_cursor.fetchall():
                                res = dict(zip(columns, row))
                                # Standardize for frontend mapping
                                std_res = {
                                    'FeeAssignmentID': res.get('FeeAssignmentID'),
                                    'FeeTypeName': res.get('fee_name') or 'N/A',
                                    'Amount': float(res.get('amount') or 0),
                                    'FeeMonth': res.get('FeeMonth'),
                                    'FeeTypeId': res.get('FeeTypeId'),
                                    'DefaultAmount': float(res.get('default_amount') or 0),
                                    'DiscountPercentage': float(res.get('discount_percentage') or 0)
                                }
                                fee_structure.append(std_res)
                    except Exception as e: logger.error(f"Fallback fee retrieval error: {e}")
                    
                    # Fetch Paid Months
                    try:
                        fallback_cursor.execute("""
                            SELECT DISTINCT "PaymentMonth" FROM "Payment" 
                            WHERE "EntityID" = %s AND "EntityType" = 'Student' AND "IsDeleted" = FALSE
                        """, [sid])
                        if fallback_cursor.description:
                            columns = [col[0] for col in fallback_cursor.description]
                            for row in fallback_cursor.fetchall():
                                res = dict(zip(columns, row))
                                paid_months.append(res)
                    except Exception as e: logger.error(f"Fallback 3 error: {e}")

        # Final check if student was found
        if not student_info:
            return JsonResponse({'status': 'ERROR', 'message': 'No Student Record Found'})

        # Format the database-provided Base64 or Hex (due to ::TEXT cast of bytea) correctly
        candidate_b64 = student_info.get('StudentPhotoBase64')
        if candidate_b64:
            if isinstance(candidate_b64, str) and candidate_b64.startswith('\\x'):
                try:
                    import binascii, base64
                    hex_str = candidate_b64[2:] # remove '\x'
                    raw_bytes = binascii.unhexlify(hex_str)
                    student_info['StudentPhotoBase64'] = f"data:image/jpeg;base64,{base64.b64encode(raw_bytes).decode('utf-8')}"
                except Exception as e:
                    logger.error(f"Hex doc parsing error: {e}")
                    student_info['StudentPhotoBase64'] = None
            elif isinstance(candidate_b64, str) and not candidate_b64.startswith('data:image') and len(candidate_b64) > 100:
                student_info['StudentPhotoBase64'] = f"data:image/jpeg;base64,{candidate_b64}"

        # Handle student photo (Note: StudentPhoto omitted from query above if not present)
        if not student_info.get('StudentPhotoBase64') and not student_info.get('StudentPhoto'):
            try:
                with connection.cursor() as photo_cursor:
                    photo_cursor.execute("""
                        SELECT "DocumentData" FROM "StudentDocuments" 
                        WHERE "StudentID" = %s AND "DocumentType" = 'Student Passport Photo' 
                        LIMIT 1
                    """, [student_info.get('StudentID')])
                    photo_row = photo_cursor.fetchone()
                    if photo_row and photo_row[0]:
                        student_info['StudentPhoto'] = photo_row[0]
            except Exception as e:
                logger.error(f"Error fetching direct photo: {e}")

        if student_info.get('StudentPhoto'):
            try:
                import base64
                photo_data = student_info['StudentPhoto']
                if isinstance(photo_data, (bytes, bytearray)):
                    student_info['StudentPhotoBase64'] = f"data:image/jpeg;base64,{base64.b64encode(photo_data).decode('utf-8')}"
                elif isinstance(photo_data, memoryview):
                    student_info['StudentPhotoBase64'] = f"data:image/jpeg;base64,{base64.b64encode(photo_data.tobytes()).decode('utf-8')}"
            except Exception as e:
                logger.error(f"Error processing photo: {e}")
                
        if 'StudentPhoto' in student_info:
            del student_info['StudentPhoto']
            
        # Standardize paid_months format if it's just strings
        standard_paid = []
        for pm in paid_months:
            if isinstance(pm, dict): standard_paid.append(pm)
            else: standard_paid.append({'PaymentMonth': pm[0] if isinstance(pm, (list, tuple)) else str(pm)})
        paid_months = standard_paid

        # Return Success
        return JsonResponse({
            'status': 'SUCCESS',
            'student_code': student_code,
            'student_info': student_info,
            'fee_structure': fee_structure,
            'paid_months': paid_months,
            'school_info': {
                'SchoolName': request.session.get('SchoolName', 'ShikshaWave School'),
                'SchoolLogo': request.session.get('SchoolLogo', ''),
                'SchoolContact': request.session.get('SchoolContact', ''),
                'SchoolAddress': request.session.get('SchoolAddress', '')
            },
            'user_info': {
                'UserName': request.session.get('UserName', 'Unknown'),
                'UserRole': request.session.get('ProfileName', 'Staff')
            }
        })
                    
    except Exception as e:
            return JsonResponse({
                'status': 'ERROR',
                'message': f'Error getting student fee details: {str(e)}'
            })

@custom_login_required
def get_student_fee_history(request):
    """
    Get student fee history using Proc_Student_fee_Details_get procedure with Action='History'
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request method'})
    
    try:
        student_code = request.POST.get('student_code', '').strip()
        if not student_code:
            return JsonResponse({'status': 'ERROR', 'message': 'Student code is required'})
        
        school_id = request.session.get('SchoolID')
        
        if not school_id:
            return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
        
        # Call stored procedure with Action='History' (Postgres Syntax) with fallback
        with connection.cursor() as cursor:
            fee_history = []
            try:
                # 1. Call the procedure to open the cursors
                cursor.execute('SELECT "Proc_Student_fee_Details_get"(%s, %s)', [student_code, 'History'])
                
                # 2. Fetch the 3rd cursor (rs3) which contains the payment history
                # We need to fetch it in the same transaction
                cursor.execute('FETCH ALL FROM "rs3"')
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        fee_history.append(dict(zip(columns, row)))
                
                # Close all cursors to avoid resource leaks
                cursor.execute('CLOSE "rs1"')
                cursor.execute('CLOSE "rs2"')
                cursor.execute('CLOSE "rs3"')
                
            except Exception as proc_err:
                logger.warning(f"Fee history procedure failed, using fallback: {proc_err}")
                
                # FALLBACK: Fetch from Payment table using direct SQL
                cursor.execute("""
                    SELECT 
                        "PaymentID" as "FeeAssignmentID",
                        "ReceiptNumber",
                        "TotalAmount",
                        "PaidAmount",
                        "PaymentMode",
                        "PaymentDate",
                        "PaymentMonth"
                    FROM "Payment"
                    WHERE "EntityID" = (SELECT "StudentID" FROM "Student" WHERE "StudentCode" = %s)
                      AND "EntityType" = 'Student'
                      AND "IsDeleted" = FALSE
                    ORDER BY "PaymentDate" DESC
                """, [student_code])
                
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        fee_history.append(dict(zip(columns, row)))
            
            # Debug logging
            print(f"Debug: Student Code: {student_code}")
            print(f"Debug: Fee History Count: {len(fee_history)}")
            print(f"Debug: Fee History Data: {fee_history}")
            
            # Check for invalid month formats
            for fee in fee_history:
                if 'PaymentMonth' in fee:
                    print(f"Debug: PaymentMonth '{fee['PaymentMonth']}' - Type: {type(fee['PaymentMonth'])}")
            
            return JsonResponse({
                'status': 'SUCCESS',
                'student_code': student_code,
                'fee_history': fee_history
            })
                    
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'message': f'Error getting student fee history: {str(e)}'
        })

@custom_login_required
def submit_fee_collection(request):
    """
    Submit fee collection using Proc_Payment_Insert procedure
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request method'})
    
    try:
        # Get session data
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        if not school_id or not user_id:
            return JsonResponse({'status': 'ERROR', 'message': 'Session data not found'})
        
        # Get form data
        student_id = request.POST.get('student_id')
        total_amount = request.POST.get('total_amount', '0')
        paid_amount = request.POST.get('paid_amount', '0')
        discount_value = request.POST.get('discount_value', '0')
        payment_mode = request.POST.get('payment_mode', 'Cash')
        transaction_ref = request.POST.get('transaction_ref', '')
        payment_month = request.POST.get('payment_month', '')
        fee_breakdown = request.POST.get('fee_breakdown', '[]')
        remarks = request.POST.get('remarks', '')
        
        # Validate required fields
        if not student_id:
            return JsonResponse({'status': 'ERROR', 'message': 'Student ID is required'})
        
        if not payment_month:
            return JsonResponse({'status': 'ERROR', 'message': 'Payment month is required'})
        
        # Generate unique receipt number
        import uuid
        receipt_number = f"RCP-{school_id}-{student_id}-{uuid.uuid4().hex[:8].upper()}"
        
        # Convert amounts to decimal
        from decimal import Decimal
        total_amount_decimal = Decimal(total_amount)
        paid_amount_decimal = Decimal(paid_amount)
        discount_value_decimal = Decimal(discount_value)
        
        # Parse fee breakdown to get total after discount
        import json
        fee_breakdown_data = json.loads(fee_breakdown) if fee_breakdown else []
        total_after_discount = sum(item.get('userEnterAmount', 0) for item in fee_breakdown_data if not item.get('isSummary', False))
        
        # Determine payment status based on total after discount
        payment_status = 'Paid' if paid_amount_decimal >= Decimal(str(total_after_discount)) else 'Not Paid'
        
        # Get current date
        from datetime import datetime
        payment_date = datetime.now()
        
        # Call stored procedure
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT public."Proc_Payment_Insert"(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
            """, [
                school_id,                 # p_SchoolID
                'Fees',                    # p_PaymentFor
                student_id,                # p_EntityID
                'Student',                 # p_EntityType
                receipt_number,            # p_ReceiptNumber
                total_amount_decimal,      # p_TotalAmount
                paid_amount_decimal,       # p_PaidAmount
                payment_mode,              # p_PaymentMode
                transaction_ref,           # p_TransactionRef
                payment_status,            # p_PaymentStatus
                payment_date,              # p_PaymentDate
                payment_month,             # p_PaymentMonth
                fee_breakdown,             # p_FeeBreakdown
                remarks,                   # p_Remarks
                user_id,                   # p_CreatedBy
                False,                     # p_IsDeleted
                discount_value_decimal     # p_discountValue
            ])
            
            result = cursor.fetchone()
            if result and result[0]:
                import json
                result_data = json.loads(result[0])
                
                # If successful, get the actual receipt number from database
                if result_data.get('status') == 'Success':
                    cursor.execute("""
                        SELECT "ReceiptNumber" FROM "Payment" 
                        WHERE "PaymentID" = %s AND "IsDeleted" = FALSE
                    """, [result_data.get('PaymentID')])
                    
                    receipt_result = cursor.fetchone()
                    if receipt_result:
                        result_data['ReceiptNumber'] = receipt_result[0]
                
                # If successful, store receipt data in session for receipt page
                if result_data.get('status') == 'Success':
                    from datetime import datetime
                    import json
                    
                    # Store receipt data in session
                    receipt_data = {
                        'receipt_number': result_data.get('ReceiptNumber', receipt_number),
                        'student_code': request.POST.get('student_code', ''),
                        'payment_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'payment_mode': payment_mode,
                        'transaction_ref': transaction_ref,
                        'amount_paid': str(total_amount_decimal),
                        'fee_breakdown': json.loads(fee_breakdown) if fee_breakdown else []
                    }
                    request.session['fee_collection_receipt'] = safe_json_obj(receipt_data)
                
                return JsonResponse(result_data)
            else:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': 'No result returned from procedure'
                })
                
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'message': f'Error submitting fee collection: {str(e)}'
        })


@custom_login_required
def fee_collection_receipt(request):
    """
    Display fee collection receipt
    """
    try:
        # Get receipt data from session or parameters
        receipt_data = request.session.get('fee_collection_receipt')
        if not receipt_data:
            return JsonResponse({'status': 'ERROR', 'message': 'No receipt data found'})
        
        # Get student details
        student_code = receipt_data.get('student_code')
        if not student_code:
            return JsonResponse({'status': 'ERROR', 'message': 'Student code not found'})
        
        # Get student information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.StudentID, s.StudentCode, s.FullName, s.StudentPhoto, 
                       c.ClassName, sec.SectionName, sm.SchoolName, sm.SchoolLogo
                FROM Student s
                LEFT JOIN Class_Master c ON s.AdmissionClass = c.ClassId
                LEFT JOIN Section_Master sec ON s.Section = sec.SectionId
                LEFT JOIN SchoolMaster sm ON s.SchoolID = sm.SchoolID
                WHERE s.StudentCode = %s AND s.SchoolID = %s
            """, [student_code, request.session.get('SchoolID')])
            
            student_result = cursor.fetchone()
            if not student_result:
                return JsonResponse({'status': 'ERROR', 'message': 'Student not found'})
            
            student_id, student_code, student_name, student_photo, class_name, section_name, school_name, school_logo = student_result
            
            # Build receipt data
            payment_receipt = {
                'receipt_number': receipt_data.get('receipt_number', 'Generated'),
                'student_name': student_name,
                'student_code': student_code,
                'payment_date': receipt_data.get('payment_date', ''),
                'payment_mode': receipt_data.get('payment_mode', 'Cash'),
                'transaction_ref': receipt_data.get('transaction_ref', ''),
                'amount_paid': receipt_data.get('amount_paid', '0'),
                'fee_breakdown': receipt_data.get('fee_breakdown', []),
                'school_name': school_name,
                'school_logo': None
            }
            
            # Convert school logo to data URI if exists
            if school_logo:
                try:
                    import base64
                    school_logo_data = base64.b64encode(school_logo).decode('utf-8')
                    payment_receipt['school_logo'] = f"data:image/png;base64,{school_logo_data}"
                except:
                    pass
        
        return render(request, 'payment_success.html', {'payment_receipt': payment_receipt})
        
    except Exception as e:
        return JsonResponse({'status': 'ERROR', 'message': f'Error loading receipt: {str(e)}'})

@require_POST
@custom_login_required
def clear_fee_receipt_session(request):
    """Clear fee collection receipt data from session."""
    try:
        if 'fee_collection_receipt' in request.session:
            del request.session['fee_collection_receipt']
        return JsonResponse({'status': 'SUCCESS', 'message': 'Receipt data cleared'})
    except Exception as e:
        return JsonResponse({'status': 'ERROR', 'message': f'Error clearing receipt data: {str(e)}'})

@custom_login_required
def fee_collection_new_submit(request):
    """
    Submit fee collection using Payment table
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request method'})
    
    try:
        # Get parameters
        student_code = request.POST.get('student_code')
        payment_month = request.POST.get('payment_month')
        payment_mode = request.POST.get('payment_mode')
        transaction_ref = request.POST.get('transaction_ref', '')
        fee_data = request.POST.get('fee_data')  # JSON string with fee collection data
        
        if not all([student_code, payment_month, payment_mode, fee_data]):
            return JsonResponse({'status': 'ERROR', 'message': 'Missing required parameters'})
        
        # Parse fee data
        import json
        fee_collections = json.loads(fee_data)
        
        # Get user context
        user_id = request.session.get('UserId')
        school_id = request.session.get('SchoolID')
        
        if not user_id:
            return JsonResponse({'status': 'ERROR', 'message': 'User ID is required'})
        
        if not school_id:
            return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
        
        # Get student ID
        with connection.cursor() as cursor:
            cursor.execute("SELECT StudentID FROM Student WHERE StudentCode = %s", [student_code])
            student_result = cursor.fetchone()
            
            if not student_result:
                return JsonResponse({'status': 'ERROR', 'message': 'Student not found'})
            
            student_id = student_result[0]
            
            # Calculate total amount
            total_amount = sum(collection.get('amount', 0) for collection in fee_collections)
            
            if total_amount <= 0:
                return JsonResponse({'status': 'ERROR', 'message': 'No valid fee amounts provided'})
            
            # Generate receipt number
            import time
            receipt_number = f"RCP-{student_id}-{int(time.time())}"
            
            # Create fee breakdown JSON
            fee_breakdown = []
            for collection in fee_collections:
                if collection.get('amount', 0) > 0:
                    fee_breakdown.append({
                        'fee_type_id': collection.get('fee_type_id'),
                        'fee_type_name': collection.get('fee_type_name'),
                        'amount': collection.get('amount')
                    })
            
            # Insert payment record
            cursor.execute("""
                INSERT INTO Payment (
                    SchoolID, PaymentFor, EntityID, EntityType, ReceiptNumber,
                    TotalAmount, PaidAmount, PaymentMode, TransactionRef, PaymentStatus,
                    PaymentDate, PaymentMonth, FeeBreakdown, Remarks, CreatedBy, CreatedAt, IsDeleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                school_id, 'Monthly Fee', student_id, 'Student', receipt_number,
                total_amount, total_amount, payment_mode, transaction_ref, 'Paid',
                timezone.now(), payment_month, json.dumps(fee_breakdown), 
                f'Fee collection for {student_code}', user_id, timezone.now(), 0
            ])
        
        return JsonResponse({
            'status': 'SUCCESS',
            'message': f'Fee collection of ₹{total_amount:.2f} submitted successfully for student {student_code}',
            'receipt_number': receipt_number
        })
                    
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'message': f'Error submitting fee collection: {str(e)}'
        })


def convert_bytes_to_base64(data_dict):
    """
    Convert bytes objects in dictionary to base64 strings for JSON serialization
    """
    if not isinstance(data_dict, dict):
        return data_dict
        
    converted = {}
    for key, value in data_dict.items():
        if isinstance(value, bytes):
            try:
                # Convert bytes to base64 string
                converted[key] = base64.b64encode(value).decode('utf-8')
            except Exception as e:
                print(f"Error converting {key} to base64: {e}")
                converted[key] = None
        elif isinstance(value, memoryview):
            try:
                # Convert memoryview to base64 string
                converted[key] = base64.b64encode(value.tobytes()).decode('utf-8')
            except Exception as e:
                print(f"Error converting {key} memoryview to base64: {e}")
                converted[key] = None
        else:
            converted[key] = value
    return converted

@require_POST
@custom_login_required
def get_receipt_data(request):
    """
    Get receipt data using Proc_Student_Fee_receipt_get procedure for dynamic receipt generation
    """
    try:
        import json
        
        # Parse request data
        data = json.loads(request.body)
        receipt_id = data.get('receipt_id', '').strip()
        
        if not receipt_id:
            return JsonResponse({'status': 'ERROR', 'message': 'Receipt ID is required'})
        
        # Get user context
        school_id = request.session.get('SchoolID')
        user_id = request.session.get('UserId')
        
        if not school_id or not user_id:
            return JsonResponse({'status': 'ERROR', 'message': 'Session data not found'})
        
        # Call stored procedure
        with connection.cursor() as cursor:
            # Execute the stored procedure
            print(f"DEBUG: Executing procedure with receipt_id: {receipt_id}")
            cursor.execute("EXEC Proc_Student_Fee_receipt_get @mstr_ReceiptId = %s", [receipt_id])
            
            # Fetch School Info (Table 1)
            school_info = {}
            school_results = cursor.fetchall()
            print(f"DEBUG: School results count: {len(school_results) if school_results else 0}")
            if school_results:
                columns = [desc[0] for desc in cursor.description]
                school_info_raw = dict(zip(columns, school_results[0]))
                school_info = convert_bytes_to_base64(school_info_raw)
                print(f"DEBUG: School info processed")
            
            # Move to next result set - Student Info (Table 2)
            cursor.nextset()
            student_info = {}
            student_results = cursor.fetchall()
            print(f"DEBUG: Student results count: {len(student_results) if student_results else 0}")
            if student_results:
                columns = [desc[0] for desc in cursor.description]
                student_info_raw = dict(zip(columns, student_results[0]))
                student_info = convert_bytes_to_base64(student_info_raw)
                print(f"DEBUG: Student info processed")
            
            # Move to next result set - Previous Payments (Table 3)
            cursor.nextset()
            previous_payments = []
            payment_results = cursor.fetchall()
            print(f"DEBUG: Payment results count: {len(payment_results) if payment_results else 0}")
            if payment_results:
                columns = [desc[0] for desc in cursor.description]
                previous_payments_raw = [dict(zip(columns, row)) for row in payment_results]
                previous_payments = [convert_bytes_to_base64(payment) for payment in previous_payments_raw]
                print(f"DEBUG: Previous payments processed")
        
        # Format response
        response_data = {
            'status': 'SUCCESS',
            'school_info': school_info,
            'student_info': student_info,
            'previous_payments': previous_payments[:5]  # Limit to last 5 payments
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR', 
            'message': f'Error fetching receipt data: {str(e)}'
        })


@custom_login_required  
def test_receipt_procedure(request):
    """
    Test the stored procedure with a known receipt ID
    """
    receipt_id = 'RCP-3-31-AA7BDE66'
    
    try:
        with connection.cursor() as cursor:
            print(f"Testing procedure with receipt_id: {receipt_id}")
            
            # First, check if the receipt exists in the Payment table
            cursor.execute("""
                SELECT ReceiptNumber, EntityID, SchoolID, TotalAmount, PaidAmount, PaymentDate, PaymentMonth
                FROM Payment 
                WHERE ReceiptNumber = %s AND IsDeleted = FALSE
            """, [receipt_id])
            
            payment_record = cursor.fetchone()
            print(f"Payment record found: {payment_record}")
            
            if not payment_record:
                return JsonResponse({
                    'status': 'ERROR', 
                    'message': f'No payment record found for receipt {receipt_id}',
                    'payment_record': None
                })
            
            # Now test the stored procedure
            cursor.execute("EXEC Proc_Student_Fee_receipt_get @mstr_ReceiptId = %s", [receipt_id])
            
            # Get all result sets
            result_sets = []
            
            # School info
            school_results = cursor.fetchall()
            if school_results:
                columns = [desc[0] for desc in cursor.description]
                school_data_raw = dict(zip(columns, school_results[0]))
                school_data = convert_bytes_to_base64(school_data_raw)
                result_sets.append(('school_info', school_data))
            else:
                result_sets.append(('school_info', None))
            
            # Student info  
            cursor.nextset()
            student_results = cursor.fetchall()
            if student_results:
                columns = [desc[0] for desc in cursor.description]
                student_data_raw = dict(zip(columns, student_results[0]))
                student_data = convert_bytes_to_base64(student_data_raw)
                result_sets.append(('student_info', student_data))
            else:
                result_sets.append(('student_info', None))
            
            # Previous payments
            cursor.nextset()
            payment_results = cursor.fetchall()
            if payment_results:
                columns = [desc[0] for desc in cursor.description]
                payments_data_raw = [dict(zip(columns, row)) for row in payment_results]
                payments_data = [convert_bytes_to_base64(payment) for payment in payments_data_raw]
                result_sets.append(('previous_payments', payments_data))
            else:
                result_sets.append(('previous_payments', []))
        
        return JsonResponse({
            'status': 'SUCCESS',
            'message': 'Procedure test completed',
            'payment_record': payment_record,
            'result_sets': result_sets
        })
        
    except Exception as e:
        print(f"Procedure test error: {str(e)}")
        return JsonResponse({
            'status': 'ERROR',
            'message': f'Error testing procedure: {str(e)}'
        })


# =============================================
# Student Attendance Management Views
# =============================================

@custom_login_required
def fee_receipt_view(request, receipt_id):
    """
    Generate fee receipt using the stored procedure Proc_Student_Fee_receipt_get
    """
    try:
        with connection.cursor() as cursor:
            # Call the stored procedure
            cursor.execute("EXEC Proc_Student_Fee_receipt_get @mstr_ReceiptId = %s", [receipt_id])
            
            # Get the three result sets from the stored procedure
            # First result set: School Info
            school_info = None
            if cursor.description:
                school_row = cursor.fetchone()
                if school_row:
                    school_info = {
                        'school_code': school_row[0],
                        'school_name': school_row[1],
                        'school_logo': f'data:image/jpeg;base64,{base64.b64encode(school_row[2]).decode("utf-8")}' if school_row[2] else None,
                        'phone': school_row[3],
                        'address': school_row[4],
                        'district': school_row[5],
                        'state': school_row[6],
                        'country': school_row[7]
                    }
            
            # Move to next result set: Student Info
            cursor.nextset()
            student_info = None
            if cursor.description:
                student_row = cursor.fetchone()
                if student_row:
                    student_info = {
                        'student_logo': f'data:image/jpeg;base64,{base64.b64encode(student_row[0]).decode("utf-8")}' if student_row[0] else None,
                        'student_code': student_row[1],
                        'full_name': student_row[2],
                        'guardian_name': student_row[3],
                        'class_name': student_row[4],
                        'section_name': student_row[5],
                        'receipt_no': student_row[6],
                        'date_of_submission': student_row[7],
                        'fees_month': student_row[8],
                        'total_amount': student_row[9],
                        'total_paid_amount': student_row[10],
                        'remaining_amount': student_row[11]
                    }
            
            # Move to next result set: Previous Fee History
            cursor.nextset()
            previous_fees = []
            if cursor.description:
                previous_fees_rows = cursor.fetchall()
                for row in previous_fees_rows:
                    previous_fees.append({
                        'receipt_number': row[0],
                        'payment_date': row[1],
                        'payment_month': row[2],
                        'payment_mode': row[3],
                        'total_amount': row[4],
                        'paid_amount': row[5]
                    })
            
            # Move to next result set: Fee Breakdown
            cursor.nextset()
            fee_breakdown = []
            if cursor.description:
                fee_breakdown_rows = cursor.fetchall()
                for row in fee_breakdown_rows:
                    fee_breakdown.append({
                        'name': row[0] or 'Unknown Fee',
                        'amount': float(row[1] or 0),
                        'user_enter_amount': float(row[2] or 0),
                        'fee_type': row[3] or 'Regular'
                    })
            
            # If no fee breakdown from procedure, create a basic one
            if not fee_breakdown and student_info:
                fee_breakdown = [
                    {'name': 'MONTHLY FEE', 'amount': float(student_info.get('total_amount', 0)), 'user_enter_amount': float(student_info.get('total_paid_amount', 0)), 'fee_type': 'Regular'},
                    {'name': 'ADMISSION FEE', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'REGISTRATION FEE', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'ART MATERIAL', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'TRANSPORT', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'BOOKS', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'UNIFORM', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'FINE', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'OTHERS', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Regular'},
                    {'name': 'PREVIOUS BALANCE', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Previous Due'},
                    {'name': 'DISCOUNT IN FEE', 'amount': 0, 'user_enter_amount': 0, 'fee_type': 'Discount'},
                ]
            
            # Calculate total and remaining
            total_amount = sum(item['user_enter_amount'] for item in fee_breakdown)
            paid_amount = student_info['total_paid_amount'] if student_info else 0
            remaining_amount = student_info['remaining_amount'] if student_info else 0
            
            context = {
                'school_info': school_info,
                'student_info': student_info,
                'previous_fees': previous_fees,
                'fee_breakdown': fee_breakdown,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'receipt_id': receipt_id
            }
            
            return render(request, 'core/fee_receipt.html', context)
            
    except Exception as e:
        logger.error(f"Error generating fee receipt: {str(e)}")
        messages.error(request, f"Error generating fee receipt: {str(e)}")
        return redirect('dashboard')


@custom_login_required
def print_fee_receipt(request, receipt_id):
    """
    Print version of fee receipt with dynamic data from stored procedure
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC Proc_Payment_Receipt_Get @ReceiptNumber = %s", [receipt_id])
            
            # Get the four result sets from the stored procedure
            # First result set: School Info
            school_info = None
            if cursor.description:
                school_row = cursor.fetchone()
                if school_row:
                    school_info = {
                        'school_code': school_row[0],
                        'school_name': school_row[1],
                        'school_logo': f'data:image/jpeg;base64,{base64.b64encode(school_row[2]).decode("utf-8")}' if school_row[2] else None,
                        'phone': school_row[3],
                        'address': school_row[4],
                        'district': school_row[5],
                        'state': school_row[6],
                        'country': school_row[7]
                    }
            
            # Move to next result set: Student Info
            cursor.nextset()
            student_info = None
            if cursor.description:
                student_row = cursor.fetchone()
                if student_row:
                    student_info = {
                        'student_logo': f'data:image/jpeg;base64,{base64.b64encode(student_row[0]).decode("utf-8")}' if student_row[0] else None,
                        'student_code': student_row[1],
                        'full_name': student_row[2],
                        'guardian_name': student_row[3],
                        'class_name': student_row[4],
                        'section_name': student_row[5],
                        'receipt_no': student_row[6],
                        'date_of_submission': student_row[7],
                        'fees_month': student_row[8],
                        'total_amount': student_row[9],
                        'total_paid_amount': student_row[10],
                        'remaining_amount': student_row[11]
                    }
            
            # Move to next result set: Previous Fee History (Top 10)
            cursor.nextset()
            previous_fees = []
            if cursor.description:
                previous_fees_rows = cursor.fetchall()
                for row in previous_fees_rows:
                    previous_fees.append({
                        'receipt_number': row[0],
                        'payment_date': row[1],
                        'payment_month': row[2],
                        'payment_mode': row[3],
                        'total_amount': row[4],
                        'paid_amount': row[5]
                    })
            
            # Get fee breakdown from session data (from fee submission form)
            fee_breakdown = []
            session_receipt_data = request.session.get('fee_collection_receipt', {})
            
            if session_receipt_data and session_receipt_data.get('receipt_number') == receipt_id:
                # Use fee breakdown from session if it matches the current receipt
                session_fee_breakdown = session_receipt_data.get('fee_breakdown', [])
                for item in session_fee_breakdown:
                    if not item.get('isSummary', False):  # Skip summary items
                        fee_breakdown.append({
                            'name': item.get('feeTypeName', 'Unknown Fee'),
                            'amount': float(item.get('amount', 0)),
                            'user_enter_amount': float(item.get('userEnterAmount', 0)),
                            'fee_type': 'Discount' if item.get('isDiscount', False) else 'Previous Due' if item.get('isPreviousDue', False) else 'Regular'
                        })
            
            # If no fee breakdown from session, try to get from database Payment table
            if not fee_breakdown:
                try:
                    cursor.execute("""
                        SELECT FeeBreakdown FROM Payment 
                        WHERE ReceiptNumber = %s AND IsDeleted = FALSE
                    """, [receipt_id])
                    
                    fee_breakdown_result = cursor.fetchone()
                    if fee_breakdown_result and fee_breakdown_result[0]:
                        import json
                        db_fee_breakdown = json.loads(fee_breakdown_result[0])
                        for item in db_fee_breakdown:
                            if not item.get('isSummary', False):  # Skip summary items
                                fee_breakdown.append({
                                    'name': item.get('feeTypeName', 'Unknown Fee'),
                                    'amount': float(item.get('amount', 0)),
                                    'user_enter_amount': float(item.get('userEnterAmount', 0)),
                                    'fee_type': 'Discount' if item.get('isDiscount', False) else 'Previous Due' if item.get('isPreviousDue', False) else 'Regular'
                                })
                except Exception as e:
                    logger.warning(f"Could not fetch fee breakdown from database: {str(e)}")
            
            # If still no fee breakdown, create a basic one based on student info
            if not fee_breakdown and student_info:
                total_amount = float(student_info.get('total_amount', 0))
                paid_amount = float(student_info.get('total_paid_amount', 0))
                
                # Create a basic fee breakdown structure
                fee_breakdown = [
                    {'name': 'MONTHLY FEE', 'amount': total_amount, 'user_enter_amount': paid_amount, 'fee_type': 'Regular'},
                ]
            
            # Calculate totals
            total_amount = sum(item['user_enter_amount'] for item in fee_breakdown)
            paid_amount = student_info['total_paid_amount'] if student_info else 0
            remaining_amount = student_info['remaining_amount'] if student_info else 0
            
            # Get school logo from session if available
            school_logo_from_session = request.session.get('school_logo')
            if school_logo_from_session and school_info:
                school_info['school_logo'] = school_logo_from_session
            
            context = {
                'school_info': school_info,
                'student_info': student_info,
                'previous_fees': previous_fees,
                'fee_breakdown': fee_breakdown,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'receipt_id': receipt_id
            }
            
            return render(request, 'receipt_template.html', context)
            
    except Exception as e:
        logger.error(f"Error printing fee receipt: {str(e)}")
        messages.error(request, f"Error printing fee receipt: {str(e)}")
        return redirect('dashboard')


@custom_login_required
def test_fee_receipt_procedure(request):
    """
    Test view to verify the stored procedure works correctly
    """
    try:
        # Get receipt ID from request parameter or use default
        receipt_id = request.GET.get('receipt_id', 'RCP-3-31-2272E4D9')
        
        with connection.cursor() as cursor:
            cursor.execute("EXEC Proc_Student_Fee_receipt_get @mstr_ReceiptId = %s", [receipt_id])
            
            # Get the four result sets from the stored procedure
            school_info = None
            if cursor.description:
                school_row = cursor.fetchone()
                if school_row:
                    school_info = {
                        'school_code': school_row[0],
                        'school_name': school_row[1],
                        'school_logo': f'data:image/jpeg;base64,{base64.b64encode(school_row[2]).decode("utf-8")}' if school_row[2] else None,
                        'phone': school_row[3],
                        'address': school_row[4],
                        'district': school_row[5],
                        'state': school_row[6],
                        'country': school_row[7]
                    }
            
            # Move to next result set: Student Info
            cursor.nextset()
            student_info = None
            if cursor.description:
                student_row = cursor.fetchone()
                if student_row:
                    student_info = {
                        'student_logo': f'data:image/jpeg;base64,{base64.b64encode(student_row[0]).decode("utf-8")}' if student_row[0] else None,
                        'student_code': student_row[1],
                        'full_name': student_row[2],
                        'guardian_name': student_row[3],
                        'class_name': student_row[4],
                        'section_name': student_row[5],
                        'receipt_no': student_row[6],
                        'date_of_submission': student_row[7],
                        'fees_month': student_row[8],
                        'total_amount': student_row[9],
                        'total_paid_amount': student_row[10],
                        'remaining_amount': student_row[11]
                    }
            
            # Move to next result set: Previous Fee History
            cursor.nextset()
            previous_fees = []
            if cursor.description:
                previous_fees_rows = cursor.fetchall()
                for row in previous_fees_rows:
                    previous_fees.append({
                        'receipt_number': row[0],
                        'payment_date': row[1],
                        'payment_month': row[2],
                        'payment_mode': row[3],
                        'total_amount': row[4],
                        'paid_amount': row[5]
                    })
            
            # Fee breakdown is now handled from session/form data, not from stored procedure
            fee_breakdown = []
            
            return JsonResponse({
                'status': 'success',
                'school_info': school_info,
                'student_info': student_info,
                'previous_fees': previous_fees,
                'fee_breakdown': fee_breakdown,
                'message': 'Stored procedure executed successfully'
            })
            
    except Exception as e:
        logger.error(f"Error testing fee receipt procedure: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })


@custom_login_required
def generate_fee_receipt(request):
    """
    Generate fee receipt for a specific receipt ID
    """
    try:
        receipt_id = request.GET.get('receipt_id')
        if not receipt_id:
            return JsonResponse({'status': 'error', 'message': 'Receipt ID is required'})
        
        # Redirect to the print_fee_receipt view
        return print_fee_receipt(request, receipt_id)
        
    except Exception as e:
        logger.error(f"Error generating fee receipt: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })


@custom_login_required
def test_fee_receipt_with_session(request):
    """
    Test fee receipt with sample session data to demonstrate fee breakdown from form
    """
    try:
        # Create sample fee breakdown data as it would come from the form
        sample_fee_breakdown = [
            {
                'feeTypeId': 1,
                'feeTypeName': 'MONTHLY FEE',
                'amount': 1000.0,
                'userEnterAmount': 1000.0,
                'isDiscount': False,
                'isPreviousDue': False
            },
            {
                'feeTypeId': 2,
                'feeTypeName': 'ADMISSION FEE',
                'amount': 500.0,
                'userEnterAmount': 500.0,
                'isDiscount': False,
                'isPreviousDue': False
            },
            {
                'feeTypeId': 3,
                'feeTypeName': 'TRANSPORT FEE',
                'amount': 200.0,
                'userEnterAmount': 200.0,
                'isDiscount': False,
                'isPreviousDue': False
            },
            {
                'feeTypeId': 4,
                'feeTypeName': 'DISCOUNT IN FEE',
                'amount': 100.0,
                'userEnterAmount': 100.0,
                'isDiscount': True,
                'isPreviousDue': False
            },
            {
                'feeTypeId': 5,
                'feeTypeName': 'PREVIOUS BALANCE',
                'amount': 300.0,
                'userEnterAmount': 300.0,
                'isDiscount': False,
                'isPreviousDue': True
            }
        ]
        
        # Store sample data in session
        request.session['fee_collection_receipt'] = {
            'receipt_number': 'RCP-TEST-12345',
            'student_code': 'STU001',
            'payment_date': '2024-01-15 10:30',
            'payment_mode': 'Cash',
            'transaction_ref': 'TXN123456',
            'amount_paid': '1900.00',
            'fee_breakdown': sample_fee_breakdown
        }
        
        # Generate receipt with sample data
        return print_fee_receipt(request, 'RCP-TEST-12345')
        
    except Exception as e:
        logger.error(f"Error testing fee receipt with session: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error: {str(e)}'
        })


    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'message': str(e)
        })


@custom_login_required
def fee_report(request):
    """
    Fee Report page for School Admin and Accountant roles
    """
    # Get user context for header
    context = get_context(request)
    
    # Get user information from custom session
    custom_user = getattr(request, 'custom_user', None)
    if not custom_user:
        messages.error(request, "Please login to access fee reports")
        return redirect('login')
    
    user_id = custom_user.get('user_id')
    school_id = custom_user.get('school_id')
    profile_name = custom_user.get('profile_name', '')
    
    # Check if user has permission to access fee reports
    if profile_name not in ['School Admin', 'Accountant']:
        messages.error(request, f"You don't have permission to access fee reports. Your role: {profile_name}")
        return redirect('dashboard')
    
    # Get classes for filter dropdown
    classes = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT "ClassID", "ClassName" 
                FROM "ClassMaster" 
                WHERE "SchoolID" = %s AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                ORDER BY "ClassName"
            """, [school_id])
            classes = [{'ClassID': row[0], 'ClassName': row[1]} for row in cursor.fetchall()]
    except Exception as e:
        messages.error(request, "Error loading classes")
    
    # Get sections for filter dropdown
    sections = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s."SectionID", s."SectionName", c."ClassName", c."ClassID"
                FROM "SectionMaster" s
                INNER JOIN "ClassMaster" c ON s."ClassID" = c."ClassID"
                WHERE c."SchoolID" = %s AND s."IsActive" = TRUE AND s."IsDeleted" = FALSE
                ORDER BY c."ClassName", s."SectionName"
            """, [school_id])
            sections = [{'SectionID': row[0], 'SectionName': row[1], 'ClassName': row[2], 'ClassID': row[3]} for row in cursor.fetchall()]
    except Exception as e:
        messages.error(request, "Error loading sections")
        # Get filter parameters
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    class_id = request.GET.get('class_id', '')
    section_id = request.GET.get('section_id', '')
    fee_month = request.GET.get('fee_month', '')
    student_name = request.GET.get('student_name', '')
    student_code = request.GET.get('student_code', '')
    email = request.GET.get('email', '')
    payment_status = request.GET.get('payment_status', '')
    payment_mode = request.GET.get('payment_mode', '')
    
    # --- NEW: Pagination & Sorting Params ---
    page_index = int(request.GET.get('page', 0))
    page_size = int(request.GET.get('page_size', 10))
    sort_column = request.GET.get('sort_col', 'PaymentDate')
    sort_order = request.GET.get('sort_order', 'DESC')
    
    # Initialize data variables
    overview_data = {}
    fee_reports = []
    
    # Get current month as default date range if no dates provided
    if not from_date or not to_date:
        from datetime import datetime, timedelta
        current_date = datetime.now()
        first_day = current_date.replace(day=1)
        last_day = (current_date.replace(day=28) + timedelta(days=4))
        last_day = last_day - timedelta(days=last_day.day)
        from_date = first_day.strftime('%Y-%m-%d')
        to_date = last_day.strftime('%Y-%m-%d')
    
    # Convert fee_month to YYYYMM format if provided
    fee_month_param = None
    if fee_month:
        try:
            # Convert month name to YYYYMM format
            month_map = {
                'January': '01', 'February': '02', 'March': '03', 'April': '04',
                'May': '05', 'June': '06', 'July': '07', 'August': '08',
                'September': '09', 'October': '10', 'November': '11', 'December': '12'
            }
            if fee_month in month_map:
                from datetime import datetime
                report_year = datetime.now().year
                if from_date:
                    try:
                        report_year = datetime.strptime(from_date, '%Y-%m-%d').year
                    except:
                        pass
                fee_month_param = f"{report_year}{month_map[fee_month]}"
        except:
            fee_month_param = None
    
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Execute the procedure to open the refcursors
                cursor.execute(
                    'SELECT * FROM "Proc_FeeReport_get"(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    [
                        school_id,
                        from_date if from_date else None,
                        to_date if to_date else None,
                        int(class_id) if class_id else None,
                        int(section_id) if section_id else None,
                        fee_month_param,
                        student_name if student_name else None,
                        student_code if student_code else None,
                        email if email else None,
                        payment_status if payment_status else None,
                        1, # ShowReportList = 1
                        page_size,
                        page_index,
                        sort_column,
                        sort_order
                    ]
                )
                
                # Fetch result sets from refcursors
                # 1st: rs_overview
                cursor.execute('FETCH ALL IN "rs_overview"')
                overview_row = cursor.fetchone()
                
                if overview_row:
                    overview_data = {
                        'TotalGenerated': float(overview_row[0] or 0),
                        'TotalCollected': float(overview_row[1] or 0),
                        'TotalPending': float(overview_row[2] or 0),
                        'TotalStudentsBilled': overview_row[3] or 0,
                        'CollectionPercentage': float(overview_row[4] or 0),
                        'TotalRecords': overview_row[5] or 0,
                        'PaidAmountTotal': float(overview_row[6] or 0),
                        'FromDate': from_date,
                        'ToDate': to_date
                    }
                else:
                    overview_data = {
                        'TotalGenerated': 0.0, 'TotalCollected': 0.0, 'TotalPending': 0.0,
                        'TotalStudentsBilled': 0, 'CollectionPercentage': 0.0, 'TotalRecords': 0,
                        'PaidAmountTotal': 0.0, 'FromDate': from_date, 'ToDate': to_date
                    }
                
                # 2nd: rs_details
                cursor.execute('FETCH ALL IN "rs_details"')
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall() if columns else []
                fee_reports = [dict(zip(columns, row)) for row in rows]
                
    except Exception as e:
        logger.error(f"Error calling Proc_FeeReport_get: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"Error generating reports: {str(e)}")
        # Provide fallback data if not already set
        if not overview_data:
            overview_data = {
                'TotalGenerated': 0.0, 'TotalCollected': 0.0, 'TotalPending': 0.0, 
                'TotalStudentsBilled': 0, 'CollectionPercentage': 0.0, 'TotalRecords': 0,
                'PaidAmountTotal': 0.0, 'FromDate': from_date, 'ToDate': to_date
            }
        if not fee_reports:
            fee_reports = []

    # Update context with report data
    context.update({
        'user_id': user_id,
        'school_id': school_id,
        'profile_name': profile_name,
        'classes': classes,
        'sections': sections,
        'overview_data': overview_data,
        'fee_reports': fee_reports,
        'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'filters': {
            'from_date': from_date, 'to_date': to_date, 'class_id': class_id,
            'section_id': section_id, 'fee_month': fee_month, 'student_name': student_name,
            'student_code': student_code, 'email': email, 'payment_status': payment_status,
            'payment_mode': payment_mode, 'page': page_index, 'page_size': page_size,
            'sort_col': sort_column, 'sort_order': sort_order
        }
    })

    
    return render(request, 'core/fee_report.html', context)

@custom_login_required
def fee_report_ajax(request):
    """
    AJAX endpoint for fee report data
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'ERROR', 'message': 'Invalid request method'})
    
    try:
        # Get parameters
        from_date = request.POST.get('from_date', '')
        to_date = request.POST.get('to_date', '')
        class_id = request.POST.get('class_id', '')
        section_id = request.POST.get('section_id', '')
        fee_month = request.POST.get('fee_month', '')
        student_name = request.POST.get('student_name', '')
        student_code = request.POST.get('student_code', '')
        email = request.POST.get('email', '')
        payment_status = request.POST.get('payment_status', '')
        payment_mode = request.POST.get('payment_mode', '')
        
        # Get user context from custom session
        custom_user = getattr(request, 'custom_user', None)
        if not custom_user:
            return JsonResponse({'status': 'ERROR', 'message': 'Please login to access fee reports'})
        
        school_id = custom_user.get('school_id')
        profile_name = custom_user.get('profile_name', '')
        
        if not school_id:
            return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
        
        if profile_name not in ['School Admin', 'Accountant']:
            return JsonResponse({'status': 'ERROR', 'message': 'Insufficient permissions'})
        
        # Convert parameters
        class_id_param = int(class_id) if class_id else None
        section_id_param = int(section_id) if section_id else None
        from_date_param = from_date if from_date else None
        to_date_param = to_date if to_date else None
        
        # Convert fee_month to YYYYMM format if provided
        fee_month_param = None
        if fee_month:
            try:
                # Convert month name to YYYYMM format
                month_map = {
                    'January': '01', 'February': '02', 'March': '03', 'April': '04',
                    'May': '05', 'June': '06', 'July': '07', 'August': '08',
                    'September': '09', 'October': '10', 'November': '11', 'December': '12'
                }
                if fee_month in month_map:
                    from datetime import datetime
                    current_year = datetime.now().year
                    fee_month_param = f"{current_year}{month_map[fee_month]}"
            except:
                fee_month_param = None
        
        # --- NEW: Pagination & Sorting Params ---
        page_index = int(request.POST.get('page', 0))
        page_size = int(request.POST.get('page_size', 10))
        sort_column = request.POST.get('sort_col', 'PaymentDate')
        sort_order = request.POST.get('sort_order', 'DESC')

        # Get detailed fee data using stored procedure
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM "Proc_FeeReport_get"(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        [
                            school_id,
                            from_date_param,
                            to_date_param,
                            class_id_param,
                            section_id_param,
                            fee_month_param,
                            student_name if student_name else None,
                            student_code if student_code else None,
                            email if email else None,
                            payment_status if payment_status else None,
                            1, # ShowReportList = 1
                            page_size,
                            page_index,
                            sort_column,
                            sort_order
                        ]
                    )
                
                # Fetch result sets from refcursors
                # 1st: rs_overview (we need TotalRecords from here for AJAX pagination logic)
                cursor.execute('FETCH ALL IN "rs_overview"')
                overview_row = cursor.fetchone()
                total_records = 0
                if overview_row:
                    total_records = overview_row[5] # Index 5 is TotalRecords

                # 2nd: rs_details
                cursor.execute('FETCH ALL IN "rs_details"')
                columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = cursor.fetchall() if columns else []
                
                # Convert to list of dictionaries
                fee_reports = [dict(zip(columns, row)) for row in rows]
                
                return JsonResponse({
                    'status': 'SUCCESS',
                    'data': fee_reports,
                    'total_records': total_records,
                    'page': page_index,
                    'page_size': page_size
                })
    
    except Exception as e:
        logger.error(f"Error in fee_report_ajax: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'status': 'ERROR', 
            'message': str(e),
            'data': [],
            'total_records': 0
        })

@custom_login_required
def fee_report_export(request):
    """
    Export fee report to Excel/PDF/CSV
    """
    # Support both GET and POST for flexibility, although POST is preferred for large filter sets
    params = request.POST if request.method == 'POST' else request.GET
    
    try:
        # Get parameters
        from_date = params.get('from_date', '')
        to_date = params.get('to_date', '')
        class_id = params.get('class_id', '')
        section_id = params.get('section_id', '')
        fee_month = params.get('fee_month', '')
        student_name = params.get('student_name', '')
        student_code = params.get('student_code', '')
        email = params.get('email', '')
        payment_status = params.get('payment_status', '')
        payment_mode = params.get('payment_mode', '')
        
        # Support both 'export_format' (legacy) and 'format' (global standard)
        export_format = params.get('format') or params.get('export_format', 'excel')
        
        # Get user context from custom session
        custom_user = getattr(request, 'custom_user', None)
        if not custom_user:
            return JsonResponse({'status': 'ERROR', 'message': 'Please login to access fee reports'})
        
        school_id = custom_user.get('school_id')
        profile_name = custom_user.get('profile_name', '')
        
        if not school_id:
            return JsonResponse({'status': 'ERROR', 'message': 'School ID is required'})
        
        if profile_name not in ['School Admin', 'Accountant']:
            return JsonResponse({'status': 'ERROR', 'message': 'Insufficient permissions'})
        
        # Convert parameters
        class_id_param = int(class_id) if class_id else None
        section_id_param = int(section_id) if section_id else None
        from_date_param = from_date if from_date else None
        to_date_param = to_date if to_date else None
        
        # Convert fee_month to YYYYMM format if provided
        fee_month_param = None
        if fee_month:
            try:
                # Convert month name to YYYYMM format
                month_map = {
                    'January': '01', 'February': '02', 'March': '03', 'April': '04',
                    'May': '05', 'June': '06', 'July': '07', 'August': '08',
                    'September': '09', 'October': '10', 'November': '11', 'December': '12'
                }
                if fee_month in month_map:
                    from datetime import datetime
                    current_year = datetime.now().year
                    fee_month_param = f"{current_year}{month_map[fee_month]}"
            except:
                fee_month_param = None
        
        # Get export data using stored procedure (same as page)
        with connection.cursor() as cursor:
            cursor.execute("""
                EXEC Proc_FeeReport_get 
                @mint_SchoolID = %s,
                @mvar_FromDate = %s,
                @mvar_ToDate = %s,
                @mvar_ClassID = %s,
                @mvar_SectionID = %s,
                @mvar_FeeMonth = %s,
                @mvar_StudentName = %s,
                @mvar_StudentCode = %s,
                @mvar_Email = %s,
                @mvar_PaymentStatus = %s,
                @mvar_ShowReportList = 1
            """, [
                school_id,
                from_date_param,
                to_date_param,
                class_id_param,
                section_id_param,
                fee_month_param,
                student_name if student_name else None,
                student_code if student_code else None,
                email if email else None,
                payment_status if payment_status else None
            ])
            
            # The procedure returns multiple result sets when ShowReportList = 1
            # First result set: Overview/Card data
            overview_row = cursor.fetchone()
            overview_data = None
            if overview_row:
                overview_columns = [col[0] for col in cursor.description]
                overview_data = dict(zip(overview_columns, overview_row))
                print(f"Overview data: {overview_data}")
            
            # Move to next result set (detailed data)
            export_data = []
            if cursor.nextset():
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries for export
                export_data = [dict(zip(columns, row)) for row in rows]
                
                # Debug: Print first few rows to see data structure
                print(f"Export data count: {len(export_data)}")
                if export_data:
                    print(f"First row keys: {list(export_data[0].keys())}")
                    print(f"First row sample: {export_data[0]}")
        
        if export_format == 'excel':
            # Generate Excel file
            import pandas as pd
            from django.http import HttpResponse
            import io
            
            # Create DataFrame
            df = pd.DataFrame(export_data)
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Fee Report', index=False)
            
            output.seek(0)
            
            # Create response with simple timestamp naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fee_Report_{timestamp}.xlsx"
            
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        elif export_format == 'pdf':
            # Generate PDF file with page-like structure
            from django.http import HttpResponse
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            import io
            from datetime import datetime
            
            # Create PDF in memory with smaller margins
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.3*inch, leftMargin=0.3*inch, rightMargin=0.3*inch)
            elements = []
            
            # Get custom styles
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.HexColor('#4f46e5'),
                alignment=1,  # Center alignment
                spaceAfter=12
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#374151'),
                spaceAfter=6
            )
            
            # Add main title
            title = Paragraph("📊 Fee Report", title_style)
            elements.append(title)
            elements.append(Spacer(1, 10))
            
            # Add report details
            details = f"<b>Report Period:</b> {from_date or 'N/A'} to {to_date or 'N/A'}<br/>"
            details += f"<b>Class:</b> {class_id or 'All Classes'} | <b>Section:</b> {section_id or 'All Sections'}<br/>"
            details += f"<b>Generated on:</b> {datetime.now().strftime('%d %B %Y at %I:%M %p')}"
            details_para = Paragraph(details, styles['Normal'])
            elements.append(details_para)
            elements.append(Spacer(1, 10))
            
            # Add summary cards section
            if overview_data or export_data:
                # Use overview data if available, otherwise calculate from detailed data
                if overview_data:
                    total_collected = float(overview_data.get('TotalCollected', 0) or 0)
                    total_pending = float(overview_data.get('TotalPending', 0) or 0)
                    total_students = int(overview_data.get('TotalStudentsBilled', 0) or 0)
                    collection_rate = float(overview_data.get('CollectionPercentage', 0) or 0)
                else:
                    # Calculate from detailed data as fallback
                    total_collected = sum(float(row.get('PaidAmount', 0) or 0) for row in export_data)
                    total_pending = sum(float(row.get('PendingAmount', 0) or 0) for row in export_data)
                    total_students = len(set(row.get('StudentCode', '') for row in export_data))
                    collection_rate = (total_collected / (total_collected + total_pending) * 100) if (total_collected + total_pending) > 0 else 0
                
                # Create summary table
                summary_data = [
                    ['📊 Rs Collected', f'₹{total_collected:,.2f}'],
                    ['⏰ Pending', f'₹{total_pending:,.2f}'],
                    ['👥 Students', str(total_students)],
                    ['📈 Collection Rate', f'{collection_rate:.1f}%']
                ]
                
                # Create 2x2 grid for summary cards
                summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
                    ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8fafc')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1f2937')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ]))
                
                elements.append(Paragraph("Summary Overview", header_style))
                elements.append(summary_table)
                elements.append(Spacer(1, 10))
            
            # Add detailed table section
            if export_data:
                elements.append(Paragraph("Fee Report Details", header_style))
                elements.append(Spacer(1, 10))
                
                # Prepare table data with proper column mapping
                table_data = []
                
                # Define column headers matching the page
                headers = [
                    'SN', 'Receipt No', 'Student Code', 'Student Name', 
                    'Class / Section', 'Fee Month', 'Total Amount', 
                    'Paid Amount', 'Pending Amount', 'Payment Date', 
                    'Payment Mode', 'Status'
                ]
                table_data.append(headers)
                
                # Add data rows
                for i, row in enumerate(export_data, 1):
                    class_section = f"{row.get('ClassName', '-')} / {row.get('SectionName', '-')}"
                    status = row.get('PaymentStatus', '-')
                    
                    # Format status with color coding
                    if status.lower() == 'paid':
                        status_display = f"✅ {status}"
                    elif status.lower() == 'partial':
                        status_display = f"⚠️ {status}"
                    else:
                        status_display = f"❌ {status}"
                    
                    table_data.append([
                        str(i),
                        str(row.get('ReceiptNumber', '-')),
                        str(row.get('StudentCode', '-')),
                        str(row.get('StudentName', '-')),
                        class_section,
                        str(row.get('FeeMonth', '-')),
                        f"₹{float(row.get('TotalAmount', 0) or 0):,.2f}",
                        f"₹{float(row.get('PaidAmount', 0) or 0):,.2f}",
                        f"₹{float(row.get('PendingAmount', 0) or 0):,.2f}",
                        str(row.get('PaymentDate', '-')),
                        str(row.get('PaymentMode', '-')),
                        status_display
                    ])
                
                # Create table with compact styling
                table = Table(table_data, colWidths=[0.3*inch, 0.6*inch, 0.6*inch, 1*inch, 0.8*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch])
                table.setStyle(TableStyle([
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    
                    # Data row styling
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                    ('TOPPADDING', (0, 1), (-1, -1), 3),
                    
                    # Grid lines
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
                    
                    # Alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
                    
                    # Special styling for status column
                    ('FONTNAME', (11, 1), (11, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (11, 1), (11, -1), 6),
                ]))
                
                elements.append(table)
            
            # Add footer
            elements.append(Spacer(1, 10))
            footer = Paragraph(f"<i>Report generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')} | Total Records: {len(export_data) if export_data else 0}</i>", styles['Normal'])
            elements.append(footer)
            
            # Build PDF
            doc.build(elements)
            
            # Create response with simple timestamp naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fee_Report_{timestamp}.pdf"
            
            response = HttpResponse(
                buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        elif export_format == 'csv':
            # Generate CSV file
            import csv
            from django.http import HttpResponse
            
            # Get and map delimiter
            delimiter_name = params.get('delimiter', 'comma')
            delimiter_char = ','
            if delimiter_name == 'pipe':
                delimiter_char = '|'
            elif delimiter_name == 'tab':
                delimiter_char = '\t'
                
            # Generate simple timestamp filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fee_Report_{timestamp}.csv"
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            if export_data:
                # Use the selected delimiter
                writer = csv.DictWriter(response, fieldnames=export_data[0].keys(), delimiter=delimiter_char)
                writer.writeheader()
                writer.writerows(export_data)
            
            return response
        
        else:
            return JsonResponse({'status': 'ERROR', 'message': 'Invalid export format'})
    
    except Exception as e:
        return JsonResponse({
            'status': 'ERROR',
            'message': f'Error exporting report: {str(e)}'
        })


