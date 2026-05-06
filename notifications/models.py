from django.db import models
from core.models import UserMaster, SchoolMaster

class NotificationTypeMaster(models.Model):
    type_id = models.AutoField(primary_key=True, db_column='TypeID')
    type_name = models.CharField(max_length=50, unique=True, db_column='TypeName')
    type_category = models.CharField(max_length=50, db_column='TypeCategory')
    icon_class = models.CharField(max_length=50, null=True, blank=True, db_column='IconClass')
    color_code = models.CharField(max_length=20, null=True, blank=True, db_column='ColorCode')
    is_active = models.BooleanField(default=True, db_column='IsActive')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'NotificationTypeMaster'
        managed = False

    def __str__(self):
        return self.type_name


class NotificationMaster(models.Model):
    notification_id = models.BigAutoField(primary_key=True, db_column='NotificationID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    type = models.ForeignKey(NotificationTypeMaster, on_delete=models.PROTECT, db_column='TypeID')
    title = models.CharField(max_length=255, db_column='Title')
    message = models.TextField(db_column='Message')
    target_url = models.CharField(max_length=500, null=True, blank=True, db_column='TargetURL')
    target_module = models.CharField(max_length=50, null=True, blank=True, db_column='TargetModule')
    target_record_id = models.BigIntegerField(null=True, blank=True, db_column='TargetRecordID')
    created_by_user = models.ForeignKey(UserMaster, on_delete=models.PROTECT, db_column='CreatedByUserID')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    expires_at = models.DateTimeField(null=True, blank=True, db_column='ExpiresAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'NotificationMaster'
        managed = False
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NotificationRecipients(models.Model):
    recipient_id = models.BigAutoField(primary_key=True, db_column='RecipientID')
    notification = models.ForeignKey(NotificationMaster, on_delete=models.CASCADE, db_column='NotificationID', related_name='recipients')
    user = models.ForeignKey(UserMaster, on_delete=models.CASCADE, db_column='UserID')
    is_read = models.BooleanField(default=False, db_column='IsRead')
    read_at = models.DateTimeField(null=True, blank=True, db_column='ReadAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'NotificationRecipients'
        managed = False
        unique_together = ('notification', 'user')

    def __str__(self):
        return f"{self.user.user_name} - {self.notification.title}"
