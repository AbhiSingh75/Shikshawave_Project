# core/data_import/processors.py
import pandas as pd
import json
from datetime import datetime
from django.db import connection, transaction
from django.utils import timezone
from .models import DataImportLog, DataImportError
from .validators import get_validator
import logging

logger = logging.getLogger(__name__)


class DataImportProcessor:
    """Base processor for data imports"""
    
    def __init__(self, school_id, import_type, file_path, created_by):
        self.school_id = school_id
        self.import_type = import_type
        self.file_path = file_path
        self.created_by = created_by
        self.import_log = None
        self.validator = get_validator(import_type, school_id)
    
    def read_excel(self):
        """Read Excel file into DataFrame"""
        try:
            df = pd.read_excel(self.file_path, engine='openpyxl')
            # Clean column names
            df.columns = df.columns.str.strip()
            # Replace NaN with None
            df = df.where(pd.notnull(df), None)
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    def create_import_log(self, file_name, file_size, total_rows):
        """Create import log entry"""
        self.import_log = DataImportLog.objects.create(
            school_id=self.school_id,
            import_type=self.import_type,
            file_name=file_name,
            file_path=self.file_path,
            file_size=file_size,
            total_rows=total_rows,
            created_by_id=self.created_by,
            status='Pending'
        )
        return self.import_log.import_id
    
    def validate_data(self, df):
        """Validate all rows in DataFrame"""
        self.import_log.status = 'Validating'
        self.import_log.validation_started_at = timezone.now()
        self.import_log.save()
        
        valid_rows = 0
        invalid_rows = 0
        
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (1-indexed + header)
            row_dict = row.to_dict()
            
            if self.validator.validate_row(row_dict, row_num):
                valid_rows += 1
            else:
                invalid_rows += 1
        
        # Bulk insert errors
        if self.validator.errors:
            error_objects = [
                DataImportError(
                    import_log_id=self.import_log.import_id,
                    row_number=err['row_number'],
                    column_name=err.get('column_name'),
                    column_value=err.get('column_value'),
                    error_type=err['error_type'],
                    error_message=err['error_message'],
                    row_data=json.dumps(err.get('row_data', {}))
                )
                for err in self.validator.errors
            ]
            DataImportError.objects.bulk_create(error_objects, batch_size=1000)
        
        self.import_log.valid_rows = valid_rows
        self.import_log.invalid_rows = invalid_rows
        self.import_log.status = 'Validated'
        self.import_log.validation_completed_at = timezone.now()
        self.import_log.save()
        
        return valid_rows, invalid_rows
    
    def execute_import(self, df):
        """Execute the actual import using stored procedure"""
        raise NotImplementedError("Subclasses must implement execute_import")
    
    def generate_error_report(self):
        """Generate Excel error report"""
        errors = DataImportError.objects.filter(import_log=self.import_log)
        
        if not errors.exists():
            return None
        
        error_data = []
        for err in errors:
            error_data.append({
                'Row Number': err.row_number,
                'Column': err.column_name or 'N/A',
                'Value': err.column_value or 'N/A',
                'Error Type': err.error_type,
                'Error Message': err.error_message
            })
        
        df_errors = pd.DataFrame(error_data)
        error_file_path = self.file_path.replace('.xlsx', '_errors.xlsx')
        df_errors.to_excel(error_file_path, index=False, engine='openpyxl')
        
        self.import_log.error_file_path = error_file_path
        self.import_log.error_file_generated = True
        self.import_log.save()
        
        return error_file_path


class StudentImportProcessor(DataImportProcessor):
    """Processor for student data imports with staging support"""
    
    def validate_columns(self, df):
        """Validate DataFrame columns against expected Student table structure"""
        return self.validator.validate_columns(df.columns.tolist())
    
    def save_to_staging(self, df):
        """Save validated rows to Student_Staging table"""
        try:
            with connection.cursor() as cursor:
                for idx, row in df.iterrows():
                    row_num = idx + 2
                    row_dict = row.to_dict()
                    
                    # Convert dates to string for JSON
                    for key, value in row_dict.items():
                        if pd.isna(value):
                            row_dict[key] = None
                        elif isinstance(value, (pd.Timestamp, datetime)):
                            row_dict[key] = value.strftime('%Y-%m-%d')
                    
                    # Check if row is valid
                    is_valid = self.validator.validate_row(row_dict, row_num)
                    
                    # Get error messages for this row
                    row_errors = [err for err in self.validator.errors if err['row_number'] == row_num]
                    error_messages = json.dumps([err['error_message'] for err in row_errors]) if row_errors else None
                    
                    # Insert into staging
                    cursor.execute("""
                        INSERT INTO Student_Staging (
                            ImportID, SchoolID, RowNumber, RawJson, IsValid, ErrorMessages,
                            StudentCode, FullName, Gender, DateOfBirth, Age, BloodGroup,
                            Category, Religion, Nationality, StudentAadhaar, MotherTongue,
                            PresentAddress, PermanentAddress, District, State, Country,
                            ParentMobile, AlternateNumber, Email,
                            FatherName, FatherOccupation, FatherQualification, FatherAadhaar, FatherMobile,
                            MotherName, MotherOccupation, MotherQualification, MotherAadhaar, MotherMobile,
                            GuardianName, GuardianRelation, GuardianMobile,
                            LastSchool, LastClass, TCNumber, MediumOfInstruction,
                            AdmissionClass, Section, Stream, ModeOfAdmission, AdmissionDate,
                            UploadedBy
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
                    """, [
                        self.import_log.import_id, self.school_id, row_num, json.dumps(row_dict),
                        1 if is_valid else 0, error_messages,
                        row_dict.get('StudentCode'), row_dict.get('FullName'), row_dict.get('Gender'),
                        row_dict.get('DateOfBirth'), row_dict.get('Age'), row_dict.get('BloodGroup'),
                        row_dict.get('Category'), row_dict.get('Religion'), row_dict.get('Nationality'),
                        row_dict.get('StudentAadhaar'), row_dict.get('MotherTongue'),
                        row_dict.get('PresentAddress'), row_dict.get('PermanentAddress'),
                        row_dict.get('District'), row_dict.get('State'), row_dict.get('Country'),
                        row_dict.get('ParentMobile'), row_dict.get('AlternateNumber'), row_dict.get('Email'),
                        row_dict.get('FatherName'), row_dict.get('FatherOccupation'),
                        row_dict.get('FatherQualification'), row_dict.get('FatherAadhaar'),
                        row_dict.get('FatherMobile'), row_dict.get('MotherName'),
                        row_dict.get('MotherOccupation'), row_dict.get('MotherQualification'),
                        row_dict.get('MotherAadhaar'), row_dict.get('MotherMobile'),
                        row_dict.get('GuardianName'), row_dict.get('GuardianRelation'),
                        row_dict.get('GuardianMobile'), row_dict.get('LastSchool'),
                        row_dict.get('LastClass'), row_dict.get('TCNumber'),
                        row_dict.get('MediumOfInstruction'), row_dict.get('AdmissionClass'),
                        row_dict.get('Section'), row_dict.get('Stream'),
                        row_dict.get('ModeOfAdmission'), row_dict.get('AdmissionDate'),
                        self.created_by
                    ])
            
            return True
        except Exception as e:
            logger.error(f"Error saving to staging: {e}", exc_info=True)
            raise
    
    def execute_import(self, df):
        """Execute student import using staging commit stored procedure"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    DECLARE @SuccessCount INT;
                    DECLARE @FailureCount INT;
                    DECLARE @ErrorMessage NVARCHAR(4000);
                    
                    EXEC Proc_Student_Staging_Commit
                        @ImportID = %s,
                        @SchoolID = %s,
                        @CommittedBy = %s,
                        @SuccessCount = @SuccessCount OUTPUT,
                        @FailureCount = @FailureCount OUTPUT,
                        @ErrorMessage = @ErrorMessage OUTPUT;
                    
                    SELECT @SuccessCount AS SuccessCount, @FailureCount AS FailureCount, @ErrorMessage AS ErrorMessage;
                """, [self.import_log.import_id, self.school_id, self.created_by])
                
                result = cursor.fetchone()
                success_count = result[0] or 0
                failure_count = result[1] or 0
                error_message = result[2] or 'Import completed'
            
            self.import_log.refresh_from_db()
            
            return {
                'success': True,
                'success_count': success_count,
                'failure_count': failure_count,
                'message': error_message
            }
            
        except Exception as e:
            logger.error(f"Import execution error: {e}", exc_info=True)
            self.import_log.status = 'Failed'
            self.import_log.remarks = str(e)
            self.import_log.import_completed_at = timezone.now()
            self.import_log.save()
            
            return {
                'success': False,
                'error': str(e)
            }


class TeacherImportProcessor(DataImportProcessor):
    """Processor for teacher data imports"""
    
    def execute_import(self, df):
        """Execute teacher import"""
        # Similar implementation as StudentImportProcessor
        # Using Proc_Teacher_Bulk_Import stored procedure
        pass


def get_processor(import_type, school_id, file_path, created_by):
    """Factory function to get appropriate processor"""
    processors = {
        'Students': StudentImportProcessor,
        'Teachers': TeacherImportProcessor,
        # Add more processors as needed
    }
    
    processor_class = processors.get(import_type, DataImportProcessor)
    return processor_class(school_id, import_type, file_path, created_by)
