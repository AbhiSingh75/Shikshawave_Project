# core/data_import/models.py
from django.db import models
from core.models import SchoolMaster, UserMaster

class DataImportLog(models.Model):
    """Track all data import operations"""
    
    IMPORT_TYPES = [
        ('Students', 'Students'),
        ('Teachers', 'Teachers'),
        ('Salary', 'Salary'),
        ('Fee', 'Fee History'),
        ('Attendance', 'Attendance History'),
        ('Exam', 'Exams'),
        ('ExamResult', 'Exam Results'),
        ('ClassMaster', 'Class Master'),
        ('SectionMaster', 'Section Master'),
        ('SubjectMaster', 'Subject Master'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Validating', 'Validating'),
        ('Validated', 'Validated'),
        ('Importing', 'Importing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('PartialSuccess', 'Partial Success'),
    ]
    
    import_id = models.AutoField(primary_key=True, db_column='ImportID')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    import_type = models.CharField(max_length=50, choices=IMPORT_TYPES, db_column='ImportType')
    file_name = models.CharField(max_length=255, db_column='FileName')
    file_path = models.CharField(max_length=500, null=True, blank=True, db_column='FilePath')
    file_size = models.BigIntegerField(null=True, blank=True, db_column='FileSize')
    total_rows = models.IntegerField(db_column='TotalRows')
    valid_rows = models.IntegerField(default=0, db_column='ValidRows')
    invalid_rows = models.IntegerField(default=0, db_column='InvalidRows')
    success_rows = models.IntegerField(default=0, db_column='SuccessRows')
    failed_rows = models.IntegerField(default=0, db_column='FailedRows')
    skipped_rows = models.IntegerField(default=0, db_column='SkippedRows')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_column='Status')
    validation_started_at = models.DateTimeField(null=True, blank=True, db_column='ValidationStartedAt')
    validation_completed_at = models.DateTimeField(null=True, blank=True, db_column='ValidationCompletedAt')
    import_started_at = models.DateTimeField(null=True, blank=True, db_column='ImportStartedAt')
    import_completed_at = models.DateTimeField(null=True, blank=True, db_column='ImportCompletedAt')
    created_by = models.ForeignKey(UserMaster, on_delete=models.CASCADE, db_column='CreatedBy')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    error_file_path = models.CharField(max_length=500, null=True, blank=True, db_column='ErrorFilePath')
    error_file_generated = models.BooleanField(default=False, db_column='ErrorFileGenerated')
    remarks = models.CharField(max_length=1000, null=True, blank=True, db_column='Remarks')
    
    class Meta:
        db_table = 'DataImportLog'
        managed = False
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.import_type} - {self.file_name} ({self.status})"


class DataImportError(models.Model):
    """Track individual row errors during import"""
    
    ERROR_TYPES = [
        ('Validation', 'Validation Error'),
        ('FK', 'Foreign Key Error'),
        ('Duplicate', 'Duplicate Record'),
        ('Format', 'Format Error'),
        ('Required', 'Required Field Missing'),
        ('Range', 'Value Out of Range'),
        ('Exception', 'System Exception'),
    ]
    
    SEVERITY_CHOICES = [
        ('Warning', 'Warning'),
        ('Error', 'Error'),
        ('Critical', 'Critical'),
    ]
    
    error_id = models.AutoField(primary_key=True, db_column='ErrorID')
    import_log = models.ForeignKey(DataImportLog, on_delete=models.CASCADE, db_column='ImportID', related_name='errors')
    row_number = models.IntegerField(db_column='RowNumber')
    column_name = models.CharField(max_length=100, null=True, blank=True, db_column='ColumnName')
    column_value = models.CharField(max_length=500, null=True, blank=True, db_column='ColumnValue')
    error_type = models.CharField(max_length=50, choices=ERROR_TYPES, db_column='ErrorType')
    error_message = models.CharField(max_length=1000, db_column='ErrorMessage')
    error_severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='Error', db_column='ErrorSeverity')
    row_data = models.TextField(null=True, blank=True, db_column='RowData')  # JSON
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    
    class Meta:
        db_table = 'DataImportErrors'
        managed = False
        ordering = ['row_number']
    
    def __str__(self):
        return f"Row {self.row_number}: {self.error_message}"
