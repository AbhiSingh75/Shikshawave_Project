"""
Email Queue System for Asynchronous Email Processing
This module handles background email sending with status tracking
"""

import threading
import logging
import time
from django.db import connection
from django.utils import timezone
from .pdf_generator import generate_pdf_from_template
from mail.utils import send_email_by_code

logger = logging.getLogger(__name__)

class EmailQueue:
    """Simple in-memory email queue for background processing"""
    
    def __init__(self):
        self.queue = []
        self.processing = False
        self.worker_thread = None
        self._lock = threading.Lock()
    
    def add_email_task(self, email_data):
        """Add email task to queue"""
        with self._lock:
            task = {
                'id': len(self.queue) + 1,
                'data': email_data,
                'status': 'pending',
                'created_at': timezone.now(),
                'attempts': 0,
                'max_attempts': 3
            }
            self.queue.append(task)
            logger.info(f"Email task {task['id']} added to queue for {email_data.get('email')}")
            
            # Start worker if not already running
            if not self.processing:
                self.start_worker()
    
    def start_worker(self):
        """Start background email worker"""
        if self.processing:
            return
            
        self.processing = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Email queue worker started")
    
    def _worker(self):
        """Background worker that processes email queue"""
        while self.processing:
            try:
                # Get next pending task
                task = None
                with self._lock:
                    for t in self.queue:
                        if t['status'] == 'pending' and t['attempts'] < t['max_attempts']:
                            task = t
                            break
                
                if task:
                    self._process_email_task(task)
                else:
                    # No pending tasks, wait a bit
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"Email worker error: {str(e)}")
                time.sleep(5)
    
    def _process_email_task(self, task):
        """Process a single email task"""
        try:
            task['status'] = 'processing'
            task['attempts'] += 1
            task['started_at'] = timezone.now()
            
            logger.info(f"Processing email task {task['id']} for {task['data'].get('email')}")
            
            email_data = task['data']
            
            # Prepare placeholders for emails
            placeholders_ack = {
                'student_name': email_data.get('student_name'),
                'student_code': email_data.get('student_code'),
                'admission_class': email_data.get('admission_class'),
                'admission_date': email_data.get('admission_date'),
                'school_name': email_data.get('school_name'),
            }
            placeholders_rcpt = {
                'student_name': email_data.get('student_name'),
                'student_code': email_data.get('student_code'),
                'receipt_number': email_data.get('payment_receipt', {}).get('receipt_number'),
                'amount_paid': email_data.get('payment_receipt', {}).get('amount_paid'),
                'payment_mode': email_data.get('payment_receipt', {}).get('payment_mode'),
                'payment_date': email_data.get('payment_receipt', {}).get('payment_date'),
                'school_name': email_data.get('school_name'),
            }

            # Try to generate PDFs and send emails with attachments
            try:
                # Generate PDFs
                logger.info(f"Task {task['id']}: Generating acknowledgment PDF...")
                ack_pdf = generate_pdf_from_template('admission_acknowledgment.html', { 
                    'acknowledgment': {
                        'student_name': email_data.get('student_name'),
                        'student_code': email_data.get('student_code'),
                        'admission_class': email_data.get('admission_class'),
                        'admission_date': email_data.get('admission_date'),
                        'school_name': email_data.get('school_name'),
                    }
                })
                
                logger.info(f"Task {task['id']}: Generating receipt PDF...")
                rcpt_pdf = generate_pdf_from_template('payment_success.html', { 
                    'payment_receipt': email_data.get('payment_receipt') 
                })

                # Send acknowledgment email with PDF
                logger.info(f"Task {task['id']}: Sending acknowledgment email...")
                send_email_by_code(
                    code='ADMISSION_ACKNOWLEDGMENT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_ack,
                    school_id=email_data.get('school_id'),
                    attachments=[(f"Acknowledgment-{email_data.get('student_code')}.pdf", ack_pdf, 'application/pdf')]
                )
                
                # Send payment receipt email with PDF
                logger.info(f"Task {task['id']}: Sending receipt email...")
                send_email_by_code(
                    code='PAYMENT_RECEIPT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_rcpt,
                    school_id=email_data.get('school_id'),
                    attachments=[(f"Receipt-{email_data.get('student_code')}.pdf", rcpt_pdf, 'application/pdf')]
                )
                
                task['status'] = 'completed'
                task['completed_at'] = timezone.now()
                logger.info(f"Task {task['id']}: Emails with PDFs sent successfully to {email_data.get('email')}")
                
            except Exception as pdf_error:
                logger.warning(f"Task {task['id']}: PDF generation failed, sending emails without attachments: {str(pdf_error)}")
                
                # Send emails without PDF attachments as fallback
                send_email_by_code(
                    code='ADMISSION_ACKNOWLEDGMENT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_ack,
                    school_id=email_data.get('school_id')
                )
                
                send_email_by_code(
                    code='PAYMENT_RECEIPT',
                    to_emails=email_data.get('email'),
                    placeholders=placeholders_rcpt,
                    school_id=email_data.get('school_id')
                )
                
                task['status'] = 'completed'
                task['completed_at'] = timezone.now()
                logger.info(f"Task {task['id']}: Emails sent without PDFs to {email_data.get('email')}")
                
        except Exception as email_error:
            logger.error(f"Task {task['id']}: Email sending failed: {str(email_error)}")
            task['status'] = 'failed'
            task['error'] = str(email_error)
            task['failed_at'] = timezone.now()
            
            # If max attempts reached, mark as permanently failed
            if task['attempts'] >= task['max_attempts']:
                task['status'] = 'permanently_failed'
                logger.error(f"Task {task['id']}: Permanently failed after {task['max_attempts']} attempts")
            else:
                # Reset to pending for retry
                task['status'] = 'pending'
                logger.info(f"Task {task['id']}: Will retry (attempt {task['attempts']}/{task['max_attempts']})")
    
    def get_queue_status(self):
        """Get current queue status"""
        with self._lock:
            return {
                'total_tasks': len(self.queue),
                'pending': len([t for t in self.queue if t['status'] == 'pending']),
                'processing': len([t for t in self.queue if t['status'] == 'processing']),
                'completed': len([t for t in self.queue if t['status'] == 'completed']),
                'failed': len([t for t in self.queue if t['status'] == 'failed']),
                'permanently_failed': len([t for t in self.queue if t['status'] == 'permanently_failed']),
                'worker_running': self.processing
            }
    
    def stop_worker(self):
        """Stop the email worker"""
        self.processing = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Email queue worker stopped")

# Global email queue instance
email_queue = EmailQueue()

def send_admission_emails_async_v2(email_data):
    """Send admission emails asynchronously using email queue"""
    email_queue.add_email_task(email_data)
