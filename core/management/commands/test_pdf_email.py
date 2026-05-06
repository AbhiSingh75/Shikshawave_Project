"""Test sending PDF email attachments for student STU0000003"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Test sending PDF emails for a student'

    def handle(self, *args, **options):
        from core.database_email_queue import send_admission_emails_async_database
        
        student_code = 'STU0000003'
        
        # Get student info from database - using simpler query
        with connection.cursor() as cursor:
            # First check Student table columns
            cursor.execute('''
                SELECT "StudentID", "FullName", "Email", "SchoolID"
                FROM "Student"
                WHERE "StudentCode" = %s
            ''', [student_code])
            row = cursor.fetchone()
            
            if not row:
                self.stdout.write(self.style.ERROR(f"Student {student_code} not found!"))
                return
            
            student_id, student_name, email, school_id = row
            self.stdout.write(f"Student: {student_name} ({student_code})")
            self.stdout.write(f"Email: {email}")
            self.stdout.write(f"School ID: {school_id}")
            
            # Get school code
            school_code = 'SCH001'
            if school_id:
                cursor.execute('SELECT "SchoolCode" FROM "SchoolMaster" WHERE "SchoolID" = %s', [school_id])
                sc_row = cursor.fetchone()
                if sc_row:
                    school_code = sc_row[0]
                    self.stdout.write(f"School Code: {school_code}")
            
            # Get payment info if exists
            cursor.execute('''
                SELECT "ReceiptNumber", "PaymentDate", "PaymentMode", "PaidAmount", "TransactionRef"
                FROM "Payment"
                WHERE "EntityID" = %s AND "EntityType" = 'Student'
                ORDER BY "PaymentDate" DESC
                LIMIT 1
            ''', [student_id])
            payment_row = cursor.fetchone()
            
            receipt_number = 'TEST-RECEIPT-001'
            payment_date = '2026-01-21'
            payment_mode = 'Cash'
            amount_paid = '5000'
            transaction_ref = ''
            
            if payment_row:
                receipt_number = payment_row[0] or receipt_number
                payment_date = str(payment_row[1]) if payment_row[1] else payment_date
                payment_mode = payment_row[2] or payment_mode
                amount_paid = str(payment_row[3]) if payment_row[3] else amount_paid
                transaction_ref = payment_row[4] or ''
                self.stdout.write(f"Last Payment: {receipt_number} - Rs.{amount_paid}")
        
        # Use the student's email or fallback to test email
        target_email = email if email else 'myabhishek75@gmail.com'
        
        # Build email data
        email_data = {
            'email': target_email,
            'school_id': school_id or 1,
            'school_code': school_code,
            'student_code': student_code,
            'user_id': None,
            'payment_receipt': {
                'student_code': student_code,
                'student_name': student_name,
                'receipt_number': receipt_number,
                'payment_date': payment_date,
                'payment_mode': payment_mode,
                'amount_paid': amount_paid,
                'transaction_ref': transaction_ref
            }
        }
        
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Sending emails to: {target_email}")
        self.stdout.write(f"{'='*50}")
        
        try:
            task_ids = send_admission_emails_async_database(email_data)
            self.stdout.write(self.style.SUCCESS(f"Email tasks created: {task_ids}"))
            self.stdout.write("\nCheck the running server console for email processing logs...")
            self.stdout.write("Look for 'Generating acknowledgment PDF' and 'Generating receipt PDF' messages")
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f"Failed: {e}"))
            traceback.print_exc()
