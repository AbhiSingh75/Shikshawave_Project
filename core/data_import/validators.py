# core/data_import/validators.py
import re
from datetime import datetime, date
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Base validator class for data imports"""
    
    def __init__(self, school_id, import_type):
        self.school_id = school_id
        self.import_type = import_type
        self.errors = []
    
    def validate_required(self, value, field_name, row_num):
        """Validate required field"""
        if value is None or str(value).strip() == '':
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'error_type': 'Required',
                'error_message': f'{field_name} is required'
            })
            return False
        return True
    
    def validate_mobile(self, mobile, field_name, row_num):
        """Validate Indian mobile number"""
        if mobile is None:
            return True  # Optional field
        
        mobile_str = str(mobile).strip()
        if not re.match(r'^[6-9]\d{9}$', mobile_str):
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'column_value': mobile_str,
                'error_type': 'Validation',
                'error_message': f'{field_name} must be 10 digits starting with 6-9'
            })
            return False
        return True
    
    def validate_email(self, email, field_name, row_num):
        """Validate email format"""
        if email is None or str(email).strip() == '':
            return True  # Optional field
        
        email_str = str(email).strip()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email_str):
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'column_value': email_str,
                'error_type': 'Format',
                'error_message': f'{field_name} must be a valid email address'
            })
            return False
        return True
    
    def validate_date(self, date_value, field_name, row_num, allow_future=False):
        """Validate date format and range"""
        if date_value is None:
            return True
        
        try:
            if isinstance(date_value, str):
                parsed_date = datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                parsed_date = date_value.date()
            elif isinstance(date_value, date):
                parsed_date = date_value
            else:
                raise ValueError("Invalid date type")
            
            if not allow_future and parsed_date > date.today():
                self.errors.append({
                    'row_number': row_num,
                    'column_name': field_name,
                    'column_value': str(date_value),
                    'error_type': 'Validation',
                    'error_message': f'{field_name} cannot be in the future'
                })
                return False
            
            return True
        except Exception as e:
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'column_value': str(date_value),
                'error_type': 'Format',
                'error_message': f'{field_name} must be in YYYY-MM-DD format'
            })
            return False
    
    def validate_aadhaar(self, aadhaar, field_name, row_num):
        """Validate Aadhaar number"""
        if aadhaar is None or str(aadhaar).strip() == '':
            return True  # Optional field
        
        aadhaar_str = str(aadhaar).strip().replace('-', '').replace(' ', '')
        if not re.match(r'^\d{12}$', aadhaar_str):
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'column_value': aadhaar_str,
                'error_type': 'Format',
                'error_message': f'{field_name} must be 12 digits'
            })
            return False
        return True
    
    def validate_gender(self, gender, field_name, row_num):
        """Validate gender value"""
        if gender is None:
            return True
        
        gender_str = str(gender).strip()
        if gender_str not in ['Male', 'Female', 'Other']:
            self.errors.append({
                'row_number': row_num,
                'column_name': field_name,
                'column_value': gender_str,
                'error_type': 'Validation',
                'error_message': f'{field_name} must be Male, Female, or Other'
            })
            return False
        return True
    
    def validate_fk_exists(self, value, table, column, field_name, row_num, additional_filter=None):
        """Validate foreign key exists"""
        if value is None:
            return True
        
        try:
            with connection.cursor() as cursor:
                query = f"SELECT 1 FROM {table} WHERE {column} = %s AND IsDeleted = 0"
                params = [value]
                
                if additional_filter:
                    query += f" AND {additional_filter}"
                
                cursor.execute(query, params)
                if not cursor.fetchone():
                    self.errors.append({
                        'row_number': row_num,
                        'column_name': field_name,
                        'column_value': str(value),
                        'error_type': 'FK',
                        'error_message': f'{field_name} does not exist in {table}'
                    })
                    return False
            return True
        except Exception as e:
            logger.error(f"FK validation error: {e}")
            return False
    
    def check_duplicate(self, table, column, value, field_name, row_num):
        """Check for duplicate records"""
        if value is None or str(value).strip() == '':
            return True
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT 1 FROM {table} WHERE {column} = %s AND SchoolID = %s AND IsDeleted = 0",
                    [value, self.school_id]
                )
                if cursor.fetchone():
                    self.errors.append({
                        'row_number': row_num,
                        'column_name': field_name,
                        'column_value': str(value),
                        'error_type': 'Duplicate',
                        'error_message': f'Record with this {field_name} already exists'
                    })
                    return False
            return True
        except Exception as e:
            logger.error(f"Duplicate check error: {e}")
            return False


class StudentValidator(DataValidator):
    """Validator for student data imports with comprehensive field validation"""
    
    EXPECTED_COLUMNS = [
        'StudentCode', 'FullName', 'Gender', 'DateOfBirth', 'Age', 'BloodGroup',
        'Category', 'Religion', 'Nationality', 'StudentAadhaar', 'MotherTongue',
        'PresentAddress', 'PermanentAddress', 'District', 'State', 'Country',
        'ParentMobile', 'AlternateNumber', 'Email', 'FatherName', 'FatherOccupation',
        'FatherQualification', 'FatherAadhaar', 'FatherMobile', 'MotherName',
        'MotherOccupation', 'MotherQualification', 'MotherAadhaar', 'MotherMobile',
        'GuardianName', 'GuardianRelation', 'GuardianMobile', 'LastSchool',
        'LastClass', 'TCNumber', 'MediumOfInstruction', 'AdmissionClass',
        'Section', 'Stream', 'ModeOfAdmission', 'AdmissionDate'
    ]
    
    def validate_columns(self, df_columns):
        """Validate Excel columns match expected Student table structure"""
        df_cols_set = set(df_columns)
        expected_cols_set = set(self.EXPECTED_COLUMNS)
        
        missing_cols = expected_cols_set - df_cols_set
        extra_cols = df_cols_set - expected_cols_set
        
        return {
            'valid': len(missing_cols) == 0,
            'missing': list(missing_cols),
            'extra': list(extra_cols),
            'expected': self.EXPECTED_COLUMNS
        }
    
    def validate_row(self, row, row_num):
        """Validate a single student row with comprehensive checks"""
        is_valid = True
        
        # Required fields
        is_valid &= self.validate_required(row.get('FullName'), 'FullName', row_num)
        is_valid &= self.validate_required(row.get('Gender'), 'Gender', row_num)
        is_valid &= self.validate_required(row.get('DateOfBirth'), 'DateOfBirth', row_num)
        is_valid &= self.validate_required(row.get('ParentMobile'), 'ParentMobile', row_num)
        is_valid &= self.validate_required(row.get('FatherName'), 'FatherName', row_num)
        is_valid &= self.validate_required(row.get('AdmissionClass'), 'AdmissionClass', row_num)
        is_valid &= self.validate_required(row.get('Section'), 'Section', row_num)
        is_valid &= self.validate_required(row.get('AdmissionDate'), 'AdmissionDate', row_num)
        
        # Format validations
        is_valid &= self.validate_gender(row.get('Gender'), 'Gender', row_num)
        is_valid &= self.validate_date(row.get('DateOfBirth'), 'DateOfBirth', row_num, allow_future=False)
        is_valid &= self.validate_date(row.get('AdmissionDate'), 'AdmissionDate', row_num, allow_future=False)
        is_valid &= self.validate_mobile(row.get('ParentMobile'), 'ParentMobile', row_num)
        is_valid &= self.validate_mobile(row.get('AlternateNumber'), 'AlternateNumber', row_num)
        is_valid &= self.validate_mobile(row.get('FatherMobile'), 'FatherMobile', row_num)
        is_valid &= self.validate_mobile(row.get('MotherMobile'), 'MotherMobile', row_num)
        is_valid &= self.validate_mobile(row.get('GuardianMobile'), 'GuardianMobile', row_num)
        is_valid &= self.validate_email(row.get('Email'), 'Email', row_num)
        is_valid &= self.validate_aadhaar(row.get('StudentAadhaar'), 'StudentAadhaar', row_num)
        is_valid &= self.validate_aadhaar(row.get('FatherAadhaar'), 'FatherAadhaar', row_num)
        is_valid &= self.validate_aadhaar(row.get('MotherAadhaar'), 'MotherAadhaar', row_num)
        
        # FK validations
        if row.get('AdmissionClass'):
            is_valid &= self.validate_fk_exists(
                row.get('AdmissionClass'), 
                'ClassMaster', 
                'ClassID', 
                'AdmissionClass', 
                row_num,
                f"SchoolID = {self.school_id}"
            )
        
        if row.get('Section') and row.get('AdmissionClass'):
            is_valid &= self.validate_fk_exists(
                row.get('Section'), 
                'SectionMaster', 
                'SectionID', 
                'Section', 
                row_num,
                f"ClassID = {row.get('AdmissionClass')}"
            )
        
        # Duplicate checks
        if row.get('StudentAadhaar') and str(row.get('StudentAadhaar')).strip():
            is_valid &= self.check_duplicate('Student', 'StudentAadhaar', row.get('StudentAadhaar'), 'StudentAadhaar', row_num)
        
        return is_valid


class TeacherValidator(DataValidator):
    """Validator for teacher data imports"""
    
    def validate_row(self, row, row_num):
        """Validate a single teacher row"""
        is_valid = True
        
        # Required fields
        is_valid &= self.validate_required(row.get('EmployeeName'), 'EmployeeName', row_num)
        is_valid &= self.validate_required(row.get('Email'), 'Email', row_num)
        is_valid &= self.validate_required(row.get('Phone'), 'Phone', row_num)
        is_valid &= self.validate_required(row.get('DateOfJoining'), 'DateOfJoining', row_num)
        
        # Format validations
        is_valid &= self.validate_email(row.get('Email'), 'Email', row_num)
        is_valid &= self.validate_mobile(row.get('Phone'), 'Phone', row_num)
        is_valid &= self.validate_date(row.get('DateOfJoining'), 'DateOfJoining', row_num, allow_future=False)
        
        # Duplicate checks
        is_valid &= self.check_duplicate('EmployeeMaster', 'Email', row.get('Email'), 'Email', row_num)
        
        return is_valid


def get_validator(import_type, school_id):
    """Factory function to get appropriate validator"""
    validators = {
        'Students': StudentValidator,
        'Teachers': TeacherValidator,
        # Add more validators as needed
    }
    
    validator_class = validators.get(import_type, DataValidator)
    return validator_class(school_id, import_type)
