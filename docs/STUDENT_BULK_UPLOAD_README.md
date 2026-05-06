# Student Bulk Data Load Feature - Complete Documentation

## Overview
Production-ready Student Bulk Upload feature for ShikshaWave ERP with 3-step workflow: Upload → Preview → Commit.

## Features
- ✅ Column validation against Student table schema
- ✅ Comprehensive row-level validation (required fields, formats, FK checks, duplicates)
- ✅ Staging table for preview before commit
- ✅ Batch processing for 10k+ rows
- ✅ Role-based access (Super Admin/School Admin)
- ✅ Error reporting with downloadable Excel
- ✅ Import audit logging

## Installation

### 1. Database Setup
```sql
-- Run the installation script
sqlcmd -S your_server -d ShikshaWave -i database/INSTALL_STUDENT_BULK_UPLOAD.sql
```

### 2. Backend Files Created
- `database/tables/Student_Staging.sql` - Staging table
- `database/procedures/Proc_Student_Staging_Commit.sql` - Commit procedure
- `core/data_import/validators.py` - Enhanced with Student validation
- `core/data_import/processors.py` - Enhanced with staging support
- `core/data_import/views.py` - New APIs: staging preview, column structure
- `core/data_import/urls.py` - New routes
- `core/data_import/templates_generator.py` - Updated Student template

### 3. Frontend Files Created
- `core/static/js/student-bulk-upload.js` - React-style component
- `core/templates/data_import/student_bulk_upload_modal.html` - 3-step UI
- `core/templates/data_import/import_dashboard.html` - Updated integration

## API Endpoints

### Upload & Validate
```
POST /data-import/upload/
Body: multipart/form-data
  - import_file: Excel/CSV file
  - import_type: "Students"
  - school_id: int (optional for School Admin)

Response:
{
  "success": true,
  "import_id": 123,
  "total_rows": 500,
  "valid_rows": 495,
  "invalid_rows": 5,
  "column_validation": {...}
}
```

### Preview Staging Data
```
GET /data-import/staging/preview/{import_id}/

Response:
{
  "success": true,
  "valid_rows": [...],
  "invalid_rows": [...],
  "valid_count": 495,
  "invalid_count": 5
}
```

### Get Expected Columns
```
GET /data-import/columns/Students/

Response:
{
  "success": true,
  "columns": ["StudentCode", "FullName", ...],
  "required_columns": ["FullName", "Gender", ...]
}
```

### Commit Import
```
POST /data-import/execute/{import_id}/

Response:
{
  "success": true,
  "success_count": 495,
  "failure_count": 5,
  "message": "Commit completed..."
}
```

### Download Errors
```
GET /data-import/errors/{import_id}/
Returns: Excel file with error details
```

## Student Table Fields

### Required Fields
- FullName, Gender, DateOfBirth, ParentMobile, FatherName, AdmissionClass, Section, AdmissionDate

### All Fields (41 columns)
StudentCode, FullName, Gender, DateOfBirth, Age, BloodGroup, Category, Religion, Nationality, StudentAadhaar, MotherTongue, PresentAddress, PermanentAddress, District, State, Country, ParentMobile, AlternateNumber, Email, FatherName, FatherOccupation, FatherQualification, FatherAadhaar, FatherMobile, MotherName, MotherOccupation, MotherQualification, MotherAadhaar, MotherMobile, GuardianName, GuardianRelation, GuardianMobile, LastSchool, LastClass, TCNumber, MediumOfInstruction, AdmissionClass, Section, Stream, ModeOfAdmission, AdmissionDate

## Validation Rules

### Format Validations
- **Gender**: Male/Female/Other
- **DateOfBirth**: YYYY-MM-DD, not future
- **Mobile**: 10 digits, starts with 6-9
- **Email**: Valid email format
- **Aadhaar**: 12 digits (optional)

### Foreign Key Validations
- **AdmissionClass**: Must exist in ClassMaster for school
- **Section**: Must exist in SectionMaster for class

### Duplicate Checks
- **StudentAadhaar**: Unique within school (if provided)

## Usage

### For Super Admin
1. Navigate to Data Import Dashboard
2. Click "Students" card
3. Select School from dropdown
4. Download template
5. Fill Excel with student data
6. Upload file
7. Review validation results
8. Preview valid/invalid rows
9. Commit valid records

### For School Admin
1. Navigate to Data Import Dashboard
2. Click "Students" card (school auto-selected)
3. Download template
4. Fill Excel with student data
5. Upload file
6. Review validation results
7. Preview valid/invalid rows
8. Commit valid records

## Excel Template Structure
Download from: `/data-import/template/download/Students/`

Sample row:
```
STU001 | John Doe | Male | 2010-05-15 | 14 | O+ | General | Hindu | Indian | 123456789012 | Hindi | 123 Main St | 123 Main St | Mumbai | Maharashtra | India | 9876543210 | 9876543211 | john@example.com | Mr. Doe | Engineer | B.Tech | 234567890123 | 9876543212 | Mrs. Doe | Teacher | M.A. | 345678901234 | 9876543213 | Mr. Guardian | Uncle | 9876543214 | ABC School | Class 5 | TC12345 | English | 1 | 1 | Science | Regular | 2024-04-01
```

## Performance
- Supports 10,000+ rows
- Batch processing in chunks of 500
- Chunked Excel parsing
- Optimized SQL with indexes

## Error Handling
- Column mismatch detection
- Row-level error tracking
- Downloadable error report
- Detailed error messages per row

## Database Tables

### Student_Staging
Temporary storage for uploaded records with validation status.

### DataImportLog
Tracks all import operations with counts and status.

### DataImportErrors
Stores individual row errors with details.

## Security
- Role-based access control
- School-level data isolation
- CSRF protection
- File size limits (10MB)
- File type validation

## Troubleshooting

### Column Mismatch Error
- Download latest template
- Ensure all column names match exactly
- Check for extra spaces in headers

### Validation Errors
- Review error report
- Fix data in Excel
- Re-upload file

### Import Fails
- Check database logs
- Verify FK references (ClassID, SectionID)
- Ensure no duplicate Aadhaar numbers

## Support
For issues, check:
1. Browser console for JS errors
2. Django logs for backend errors
3. SQL Server logs for database errors
4. DataImportErrors table for validation details
