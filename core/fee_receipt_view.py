from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
import base64
import json

def print_fee_receipt(request, receipt_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC Proc_Fee_Receipt_Print_Get @ReceiptNumber = %s", [receipt_id])
            
            row = cursor.fetchone()
            if not row:
                return HttpResponse("Receipt not found")
            
            fee_breakdown = json.loads(row[6]) if row[6] else []
            school_logo = f'data:image/png;base64,{base64.b64encode(row[19]).decode()}' if row[19] else None
            
            cursor.nextset()
            previous_payments = [{'receipt_number': r[0], 'payment_date': r[1], 'payment_month': r[2],
                                 'payment_mode': r[3], 'total_amount': r[4], 'discount_value': r[5], 'paid_amount': r[6]}
                                for r in cursor.fetchall()]
            
            # Get school's preferred template
            school_id = request.session.get('SchoolID')
            template_path = 'core/document_templates/fee_receipt/fee_receipt_template1.html'
            
            if school_id:
                cursor.execute("""
                    SELECT "TemplateFile" FROM "TemplateSettings" 
                    WHERE "SchoolID" = %s AND "TemplateType" = 'FeeReceipt' 
                    AND "IsActive" = TRUE AND "IsDeleted" = FALSE
                """, [school_id])
                result = cursor.fetchone()
                if result and result[0]:
                    template_path = result[0]
            
            context = {
                'receipt_no': row[0],
                'date_of_submission': row[1],
                'payment_mode': row[2],
                'total_amount': row[3],
                'paid_amount': row[4],
                'remaining_amount': row[5],
                'fee_breakdown': fee_breakdown,
                'fees_month': row[7] or '',
                'transaction_ref': row[8] or '',
                'student_code': row[9],
                'full_name': row[10],
                'father_name': row[11] or '',
                'mother_name': row[12] or '',
                'class_name': row[13] or '',
                'section_name': row[14] or '',
                'school_name': row[15] or '',
                'school_address': row[16] or '',
                'school_phone': row[17] or '',
                'school_email': row[18] or '',
                'school_logo': school_logo,
                'previous_payments': previous_payments
            }
            
            return render(request, template_path, context)
            
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
