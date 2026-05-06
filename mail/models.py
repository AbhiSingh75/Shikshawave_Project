from django.db import models

class EmailTemplate(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    code = models.CharField(db_column='Code', max_length=100)
    school_id = models.IntegerField(db_column='SchoolId', null=True, blank=True)
    language = models.CharField(db_column='Language', max_length=10, default='en')
    subject_template = models.TextField(db_column='SubjectTemplate')
    body_text_template = models.TextField(db_column='BodyTextTemplate', null=True, blank=True)
    body_html_template = models.TextField(db_column='BodyHtmlTemplate', null=True, blank=True)
    default_from = models.CharField(db_column='DefaultFrom', max_length=255, null=True, blank=True)
    cc = models.TextField(db_column='Cc', null=True, blank=True)
    bcc = models.TextField(db_column='Bcc', null=True, blank=True)
    placeholders = models.TextField(db_column='Placeholders', null=True, blank=True)
    is_active = models.BooleanField(db_column='IsActive', default=True)
    created_at = models.DateTimeField(db_column='CreatedAt', auto_now_add=True)
    updated_at = models.DateTimeField(db_column='UpdatedAt', auto_now=True)

    class Meta:
        managed = False
        db_table = 'EmailTemplate'

class EmailTracking(models.Model):
    email_tracking_id = models.AutoField(db_column='EmailTrackingID', primary_key=True)
    email_code = models.CharField(db_column='EmailCode', max_length=100)
    to_email = models.CharField(db_column='ToEmail', max_length=500)
    from_email = models.CharField(db_column='FromEmail', max_length=255, null=True)
    subject = models.TextField(db_column='Subject', null=True)
    school_id = models.IntegerField(db_column='SchoolID', null=True)
    email_body = models.TextField(db_column='EmailBody', null=True)
    email_html_body = models.TextField(db_column='EmailHtmlBody', null=True)
    placeholders = models.TextField(db_column='Placeholders', null=True)
    has_attachments = models.BooleanField(db_column='HasAttachments', default=False)
    attachment_count = models.IntegerField(db_column='AttachmentCount', default=0)
    attachment_details = models.TextField(db_column='AttachmentDetails', null=True)
    status = models.CharField(db_column='Status', max_length=50, default='Pending')
    attempt_count = models.IntegerField(db_column='AttemptCount', default=0)
    created_at = models.DateTimeField(db_column='CreatedAt', auto_now_add=True)
    completed_at = models.DateTimeField(db_column='CompletedAt', null=True)
    last_error = models.TextField(db_column='LastError', null=True)

    class Meta:
        managed = False
        db_table = 'EmailTracking'
