"""
Email Tracking Models for ShikshaWave
This module provides Django models for the EmailTracking table
"""

from django.db import models
from django.utils import timezone
import json
from datetime import datetime, timedelta

class EmailTracking(models.Model):
    """Model for tracking email sending with status"""
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Sent', 'Sent'),
        ('Failed', 'Failed'),
        ('PermanentlyFailed', 'Permanently Failed'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium-High'),
        (4, 'Medium'),
        (5, 'Normal'),
        (6, 'Low-Medium'),
        (7, 'Low'),
        (8, 'Very Low'),
        (9, 'Minimal'),
        (10, 'Background'),
    ]
    
    # Primary key
    email_tracking_id = models.AutoField(db_column='EmailTrackingID', primary_key=True)
    
    # Email Details
    email_code = models.CharField(db_column='EmailCode', max_length=100)
    to_email = models.EmailField(db_column='ToEmail', max_length=255)
    from_email = models.EmailField(db_column='FromEmail', max_length=255, null=True, blank=True)
    subject = models.CharField(db_column='Subject', max_length=500, null=True, blank=True)
    school_id = models.IntegerField(db_column='SchoolID', null=True, blank=True)
    
    # Email Content
    email_body = models.TextField(db_column='EmailBody', null=True, blank=True)
    email_html_body = models.TextField(db_column='EmailHtmlBody', null=True, blank=True)
    placeholders = models.TextField(db_column='Placeholders', null=True, blank=True)
    
    # Attachments
    has_attachments = models.BooleanField(db_column='HasAttachments', default=False)
    attachment_count = models.IntegerField(db_column='AttachmentCount', default=0)
    attachment_details = models.TextField(db_column='AttachmentDetails', null=True, blank=True)
    
    # Status and Processing
    status = models.CharField(db_column='Status', max_length=50, choices=STATUS_CHOICES, default='Pending')
    priority = models.IntegerField(db_column='Priority', choices=PRIORITY_CHOICES, default=5)
    attempt_count = models.IntegerField(db_column='AttemptCount', default=0)
    max_attempts = models.IntegerField(db_column='MaxAttempts', default=3)
    
    # Timing
    created_at = models.DateTimeField(db_column='CreatedAt', default=timezone.now)
    scheduled_at = models.DateTimeField(db_column='ScheduledAt', default=timezone.now)
    started_at = models.DateTimeField(db_column='StartedAt', null=True, blank=True)
    completed_at = models.DateTimeField(db_column='CompletedAt', null=True, blank=True)
    next_retry_at = models.DateTimeField(db_column='NextRetryAt', null=True, blank=True)
    
    # Error Handling
    last_error = models.TextField(db_column='LastError', null=True, blank=True)
    error_details = models.TextField(db_column='ErrorDetails', null=True, blank=True)
    
    # Context Information
    user_id = models.IntegerField(db_column='UserID', null=True, blank=True)
    session_id = models.CharField(db_column='SessionID', max_length=255, null=True, blank=True)
    request_id = models.CharField(db_column='RequestID', max_length=255, null=True, blank=True)
    student_code = models.CharField(db_column='StudentCode', max_length=50, null=True, blank=True)
    receipt_number = models.CharField(db_column='ReceiptNumber', max_length=50, null=True, blank=True)
    
    # Metadata
    created_by = models.IntegerField(db_column='CreatedBy', null=True, blank=True)
    updated_by = models.IntegerField(db_column='UpdatedBy', null=True, blank=True)
    is_active = models.BooleanField(db_column='IsActive', default=True)
    notes = models.CharField(db_column='Notes', max_length=500, null=True, blank=True)
    updated_at = models.DateTimeField(db_column='UpdatedAt', auto_now=True)
    
    class Meta:
        managed = False  # Prevent Django from altering table
        db_table = 'EmailTracking'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email_code} to {self.to_email} - {self.status}"
    
    @property
    def placeholders_dict(self):
        """Get placeholders as dictionary"""
        if self.placeholders:
            try:
                return json.loads(self.placeholders)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @placeholders_dict.setter
    def placeholders_dict(self, value):
        """Set placeholders from dictionary"""
        self.placeholders = json.dumps(value) if value else None
    
    @property
    def attachment_details_dict(self):
        """Get attachment details as dictionary"""
        if self.attachment_details:
            try:
                return json.loads(self.attachment_details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @attachment_details_dict.setter
    def attachment_details_dict(self, value):
        """Set attachment details from dictionary"""
        self.attachment_details = json.dumps(value) if value else None
    
    def can_retry(self):
        """Check if email can be retried"""
        return (
            self.status in ['Failed'] and 
            self.attempt_count < self.max_attempts and
            (self.next_retry_at is None or self.next_retry_at <= timezone.now())
        )
    
    def should_retry(self):
        """Check if email should be retried now"""
        return (
            self.status == 'Failed' and 
            self.attempt_count < self.max_attempts and
            self.next_retry_at and 
            self.next_retry_at <= timezone.now()
        )
    
    def calculate_next_retry_time(self):
        """Calculate next retry time with exponential backoff"""
        if self.attempt_count == 0:
            return timezone.now() + timedelta(minutes=1)
        elif self.attempt_count == 1:
            return timezone.now() + timedelta(minutes=5)
        elif self.attempt_count == 2:
            return timezone.now() + timedelta(minutes=15)
        else:
            return timezone.now() + timedelta(hours=1)
    
    def mark_as_processing(self):
        """Mark email as processing"""
        self.status = 'Processing'
        self.started_at = timezone.now()
        self.attempt_count += 1
        self.save()
    
    def mark_as_sent(self):
        """Mark email as sent"""
        self.status = 'Sent'
        self.completed_at = timezone.now()
        self.last_error = None
        self.error_details = None
        self.save()
    
    def mark_as_failed(self, error_message, error_details=None):
        """Mark email as failed with error information"""
        self.last_error = error_message
        self.error_details = error_details
        
        if self.attempt_count >= self.max_attempts:
            self.status = 'PermanentlyFailed'
            self.completed_at = timezone.now()
        else:
            self.status = 'Failed'
            self.next_retry_at = self.calculate_next_retry_time()
        
        self.save()
    
    def get_processing_time(self):
        """Get processing time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_total_time(self):
        """Get total time from creation to completion"""
        if self.created_at and self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None

class EmailTrackingManager:
    """Manager class for EmailTracking operations"""
    
    @staticmethod
    def create_email_task(email_code, to_email, placeholders=None, school_id=None, 
                         priority=5, max_attempts=3, user_id=None, student_code=None, 
                         receipt_number=None, has_attachments=False, attachment_details=None,
                         from_email=None, subject=None, email_body=None, email_html_body=None,
                         session_id=None, request_id=None, school_code=None):
        """Create a new email tracking task"""
        
        # Prepare placeholders JSON
        placeholders_json = json.dumps(placeholders) if placeholders else None
        
        # Prepare attachment details JSON
        attachment_details_json = json.dumps(attachment_details) if attachment_details else None
        
        # Generate request_id if not provided
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
        
        email_task = EmailTracking.objects.create(
            email_code=email_code,
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            school_id=school_id,
            email_body=email_body,
            email_html_body=email_html_body,
            placeholders=placeholders_json,
            priority=priority,
            max_attempts=max_attempts,
            user_id=user_id,
            student_code=student_code,
            receipt_number=receipt_number,
            has_attachments=has_attachments,
            attachment_count=len(attachment_details) if attachment_details else 0,
            attachment_details=attachment_details_json,
            status='Pending',
            session_id=session_id,
            request_id=request_id
        )
        
        # Update SchoolCode separately if provided (since it's not in the model create)
        # This is optional - don't fail if it doesn't work
        if school_code:
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        'UPDATE "EmailTracking" SET "SchoolCode" = %s WHERE "EmailTrackingID" = %s',
                        [school_code, email_task.email_tracking_id]
                    )
            except Exception as e:
                # Log but don't fail - SchoolCode is optional
                import logging
                logging.getLogger(__name__).warning(f"Could not set SchoolCode: {e}")
        
        return email_task
    
    @staticmethod
    def claim_pending_emails(max_emails=10, priority=None):
        """
        Atomically claim pending emails for processing using SKIP LOCKED.
        This ensures thread-safety and allows multiple workers to run concurrently.
        """
        from django.db import transaction
        
        with transaction.atomic():
            queryset = EmailTracking.objects.filter(
                is_active=True,
                status='Pending',
                scheduled_at__lte=timezone.now()
            ).filter(
                models.Q(next_retry_at__isnull=True) | 
                models.Q(next_retry_at__lte=timezone.now())
            )
            
            if priority is not None:
                queryset = queryset.filter(priority__lte=priority)
            
            # Lock rows to prevent other workers from picking them up
            # select_for_update(skip_locked=True) is the key for high-concurrency queues
            candidates = queryset.order_by('priority', 'created_at').select_for_update(skip_locked=True)[:max_emails]
            
            # Evaluate queryset to lock rows
            claimed_emails = list(candidates)
            
            if claimed_emails:
                # Mark as processing immediately so they are "claimed"
                now = timezone.now()
                candidate_ids = [e.email_tracking_id for e in claimed_emails]
                EmailTracking.objects.filter(email_tracking_id__in=candidate_ids).update(
                    status='Processing',
                    started_at=now,
                    attempt_count=models.F('attempt_count') + 1
                )
                
                # Refresh objects to get updated fields if needed, or just manually update local instances
                for email in claimed_emails:
                    email.status = 'Processing'
                    email.started_at = now
                    email.attempt_count += 1
            
            return claimed_emails

    @staticmethod
    def get_pending_emails(max_emails=10, priority=None):
        """Legacy method - prefer claim_pending_emails for concurrency"""
        return EmailTrackingManager.claim_pending_emails(max_emails, priority)
    
    @staticmethod
    def get_email_statistics(school_id=None, from_date=None, to_date=None):
        """Get email statistics"""
        try:
            # Check if table exists first
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'EmailTracking'
                """)
                table_exists = cursor.fetchone()[0] > 0
                
                if not table_exists:
                    return {}
            
            queryset = EmailTracking.objects.filter(is_active=True)
            
            if school_id:
                queryset = queryset.filter(school_id=school_id)
            if from_date:
                queryset = queryset.filter(created_at__gte=from_date)
            if to_date:
                queryset = queryset.filter(created_at__lte=to_date)
            
            stats = {}
            for email_code in queryset.values_list('email_code', flat=True).distinct():
                code_queryset = queryset.filter(email_code=email_code)
                stats[email_code] = {
                    'total': code_queryset.count(),
                    'sent': code_queryset.filter(status='Sent').count(),
                    'failed': code_queryset.filter(status='Failed').count(),
                    'permanently_failed': code_queryset.filter(status='PermanentlyFailed').count(),
                    'pending': code_queryset.filter(status='Pending').count(),
                    'processing': code_queryset.filter(status='Processing').count(),
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting email statistics: {str(e)}")
            return {}
    
    @staticmethod
    def get_recent_emails(limit=100):
        """Get recent email activity"""
        return EmailTracking.objects.filter(
            is_active=True
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def cleanup_old_emails(days=30):
        """Clean up old completed emails"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Mark old completed emails as inactive
        updated_count = EmailTracking.objects.filter(
            is_active=True,
            status__in=['Sent', 'PermanentlyFailed'],
            completed_at__lt=cutoff_date
        ).update(is_active=False)
        
        return updated_count
