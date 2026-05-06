from django.db import models
from core.models import UserMaster, SchoolMaster

class TicketCategory(models.Model):
    category_id = models.AutoField(primary_key=True, db_column='CategoryID')
    category_name = models.CharField(max_length=100, db_column='CategoryName')
    description = models.CharField(max_length=255, null=True, blank=True, db_column='Description')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    created_by = models.IntegerField(null=True, db_column='CreatedBy')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'TicketCategory'
        managed = False

    def __str__(self):
        return self.category_name


class TicketPriority(models.Model):
    priority_id = models.AutoField(primary_key=True, db_column='PriorityID')
    priority_name = models.CharField(max_length=50, db_column='PriorityName')
    priority_level = models.IntegerField(db_column='PriorityLevel')
    color_code = models.CharField(max_length=20, null=True, db_column='ColorCode')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'TicketPriority'
        managed = False

    def __str__(self):
        return self.priority_name


class TicketManager(models.Manager):
    def for_user(self, user):
        """Return tickets visible to the user based on their role"""
        if user.profile_id == 1:  # Super Admin
            return self.filter(is_deleted=False)
        elif user.profile_id == 2:  # School Admin
            return self.filter(school_id=user.school_id, is_deleted=False)
        elif user.profile_id == 4:  # Support Executive
            return self.filter(assigned_to_user_id=user.user_id, is_deleted=False)
        return self.none()


class TicketMaster(models.Model):
    ticket_id = models.BigAutoField(primary_key=True, db_column='TicketID')
    ticket_number = models.CharField(max_length=20, db_column='TicketNumber', editable=False)
    school = models.ForeignKey(SchoolMaster, on_delete=models.PROTECT, db_column='SchoolID')
    created_by_user = models.ForeignKey(UserMaster, on_delete=models.PROTECT, db_column='CreatedByUserID', related_name='created_tickets')
    assigned_to_user = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, blank=True, db_column='AssignedToUserID', related_name='assigned_tickets')
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, db_column='CategoryID')
    priority = models.IntegerField(default=2, db_column='Priority')
    subject = models.CharField(max_length=255, db_column='Subject')
    description = models.TextField(db_column='Description')
    current_status = models.CharField(max_length=20, default='Open', db_column='CurrentStatus')
    attachment_path = models.CharField(max_length=500, null=True, blank=True, db_column='AttachmentPath')
    reopened_count = models.IntegerField(default=0, db_column='ReopenedCount')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    resolved_at = models.DateTimeField(null=True, blank=True, db_column='ResolvedAt')
    closed_at = models.DateTimeField(null=True, blank=True, db_column='ClosedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    objects = TicketManager()

    class Meta:
        db_table = 'TicketMaster'
        managed = False
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"

    @property
    def priority_name(self):
        return {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical'}.get(self.priority, 'Unknown')

    @property
    def priority_color(self):
        return {1: '#10b981', 2: '#f59e0b', 3: '#ef4444', 4: '#dc2626'}.get(self.priority, '#6b7280')

    @property
    def status_color(self):
        return {
            'Open': '#3b82f6',
            'In Progress': '#f59e0b',
            'Resolved': '#8b5cf6',
            'Closed': '#10b981',
            'Reopened': '#ef4444'
        }.get(self.current_status, '#6b7280')


class TicketActivityLog(models.Model):
    activity_id = models.BigAutoField(primary_key=True, db_column='ActivityID')
    ticket = models.ForeignKey(TicketMaster, on_delete=models.CASCADE, db_column='TicketID', related_name='activities')
    action_by_user = models.ForeignKey(UserMaster, on_delete=models.PROTECT, db_column='ActionByUserID')
    action_type = models.CharField(max_length=50, db_column='ActionType')
    old_status = models.CharField(max_length=20, null=True, blank=True, db_column='OldStatus')
    new_status = models.CharField(max_length=20, null=True, blank=True, db_column='NewStatus')
    old_assignee = models.IntegerField(null=True, blank=True, db_column='OldAssignee')
    new_assignee = models.IntegerField(null=True, blank=True, db_column='NewAssignee')
    comment = models.TextField(null=True, blank=True, db_column='Comment')
    timestamp = models.DateTimeField(auto_now_add=True, db_column='Timestamp')

    class Meta:
        db_table = 'TicketActivityLog'
        managed = False
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.ticket.ticket_number}"


class TicketComments(models.Model):
    comment_id = models.BigAutoField(primary_key=True, db_column='CommentID')
    ticket = models.ForeignKey(TicketMaster, on_delete=models.CASCADE, db_column='TicketID', related_name='comments')
    comment_by_user = models.ForeignKey(UserMaster, on_delete=models.PROTECT, db_column='CommentByUserID')
    comment_text = models.TextField(db_column='CommentText')
    is_internal = models.BooleanField(default=False, db_column='IsInternal')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'TicketComments'
        managed = False
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment on {self.ticket.ticket_number}"


class TicketAttachments(models.Model):
    attachment_id = models.BigAutoField(primary_key=True, db_column='AttachmentID')
    ticket = models.ForeignKey(TicketMaster, on_delete=models.CASCADE, db_column='TicketID', related_name='attachments')
    file_name = models.CharField(max_length=255, db_column='FileName')
    file_path = models.CharField(max_length=500, db_column='FilePath')
    file_size = models.BigIntegerField(null=True, blank=True, db_column='FileSize')
    content_type = models.CharField(max_length=100, null=True, blank=True, db_column='ContentType')
    uploaded_by_user = models.ForeignKey(UserMaster, on_delete=models.PROTECT, db_column='UploadedByUserID')
    uploaded_at = models.DateTimeField(auto_now_add=True, db_column='UploadedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'TicketAttachments'
        managed = False
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} - {self.ticket.ticket_number}"
