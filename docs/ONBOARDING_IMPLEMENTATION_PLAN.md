# School Onboarding & Legacy Data Load Process - Implementation Plan

## Overview
Complete implementation of school onboarding workflow and legacy data import system for ShikshaWave ERP.

## Architecture Analysis

### Existing Database Schema
Based on analysis of the codebase:

**Core Tables:**
- `SchoolMaster` - School information with logo (binary)
- `UserMaster` - Users with ProfileID (1=Super Admin, 2=School Admin, 3=Teacher, 4=Student)
- `ProfileMaster` - Role definitions
- `ClassMaster` - Class definitions per school
- `SectionMaster` - Sections per class
- `Student` - Student records
- `EmployeeMaster` - Teacher/staff records
- `EmployeeSalaryBreakup` - Salary component assignments
- `SalaryComponentMaster` - Salary components per school
- `FeeType_Master` - Fee types per school/class
- `Student_Fee_Assignment` - Fee assignments to students
- `Payment` - Payment records
- `ExamMaster` - Exam definitions
- `AcademicYear` - Academic sessions
- `SubjectMaster` - Subjects (inferred)
- `AttendanceMaster` - Attendance records (inferred)
- `TemplateSettings` - Template preferences per school

### Tech Stack
- **Backend:** Django 4.x + Python 3.x
- **Database:** SQL Server (using pyodbc)
- **Frontend:** HTML/CSS/JavaScript (Bootstrap-based)
- **File Processing:** pandas, openpyxl for Excel
- **Authentication:** Custom session-based with ProfileMaster roles

---

## Phase 1: School Onboarding Workflow

### 1.1 Super Admin Onboarding Interface

**URL:** `/onboarding/school/create/`

**Features:**
1. School basic information form
2. Logo upload (binary storage in SchoolLogo column)
3. School Admin user creation
4. Academic session setup
5. Template design preferences

**Form Fields:**
- School Name, Registration Number, Address
- District, State, Country (from Geographical_Master)
- Phone, Email, Website
- Board, Medium
- Principal/Director details
- Logo upload (max 5MB, jpg/png)
- School Admin credentials (auto-generate UserCode)
- Academic Year setup
- Template preferences (Fee Receipt, Result Card, Admission Ack, Timetable)

---

## Phase 2: Legacy Data Load Module

### 2.1 Role-Based Access

**Super Admin View:**
- School dropdown → Select school → Upload data
- Can import data for any school

**School Admin View:**
- No school dropdown
- All imports automatically mapped to their SchoolID
- Cannot import for other schools

### 2.2 Data Import Types

#### A. Students Import
**Template Columns (based on Student table):**
- StudentCode* (auto-generate if empty)
- FullName*
- Gender* (Male/Female/Other)
- DateOfBirth* (YYYY-MM-DD)
- Age (auto-calculate if empty)
- BloodGroup
- Category
- Religion
- Nationality
- MotherTongue
- StudentAadhaar (12 digits, unique)
- PresentAddress
- ParentMobile* (10 digits)
- AlternateNumber
- Email
- FatherName*
- FatherMobile
- MotherName
- MotherMobile
- GuardianName
- GuardianMobile
- AdmissionClass* (ClassID - must exist)
- Section* (SectionID - must exist)
- Stream
- AdmissionDate* (YYYY-MM-DD)
- Photo (base64 or file path)

**Validations:**
- Required fields marked with *
- Aadhaar: 12 digits, unique check
- Mobile: 10 digits, starts with 6-9
- Email: valid format
- ClassID/SectionID: must exist in ClassMaster/SectionMaster
- DateOfBirth: not future date
- Age: 3-25 years

**FK Mappings:**
- AdmissionClass → ClassMaster.ClassID (WHERE SchoolID = @SchoolID)
- Section → SectionMaster.SectionID (WHERE ClassID = @ClassID)

#### B. Teachers Import
**Template Columns (based on EmployeeMaster - inferred):**
- EmployeeCode* (auto-generate if empty)
- EmployeeName*
- Email*
- Phone* (10 digits)
- ProfileID* (3=Teacher, default)
- DateOfJoining* (YYYY-MM-DD)
- Qualification
- Experience
- Address
- Photo (base64 or file path)

**Validations:**
- Email: unique per school
- Phone: 10 digits
- ProfileID: must be 3 (Teacher)
- DateOfJoining: not future date

#### C. Salary Import
**Template Columns:**
- EmployeeCode* (must exist)
- ComponentName* (from SalaryComponentMaster)
- Amount* (decimal, > 0)

**Validations:**
- EmployeeCode: must exist in EmployeeMaster for this school
- ComponentName: must exist in SalaryComponentMaster for this school
- Amount: positive decimal

**Process:**
- Insert into EmployeeSalaryBreakup
- Link to existing SalaryComponentMaster.ComponentID

#### D. Fee History Import
**Template Columns:**
- StudentCode* (must exist)
- FeeTypeName* (from FeeType_Master)
- FeeMonth* (YYYYMM format)
- FeeAmount* (decimal)
- DiscountPercentage (0-100)
- FinalAmount* (decimal)

**Validations:**
- StudentCode: must exist for this school
- FeeTypeName: must exist in FeeType_Master for this school
- FeeMonth: valid format YYYYMM
- Amounts: positive decimals

**Process:**
- Insert into Student_Fee_Assignment
- Auto-calculate FinalAmount if not provided

#### E. Attendance History Import
**Template Columns:**
- StudentCode* (must exist)
- AttendanceDate* (YYYY-MM-DD)
- Status* (Present/Absent/Leave/Holiday)
- Remarks

**Validations:**
- StudentCode: must exist
- AttendanceDate: not future date
- Status: valid enum value

#### F. Exams Import
**Template Columns (based on ExamMaster):**
- ExamName*
- ExamType (Unit Test/Mid Term/Final)
- ClassID* (must exist)
- StartDate* (YYYY-MM-DD)
- EndDate* (YYYY-MM-DD)
- AcademicYearId* (must exist)
- IsActive (1/0, default 1)

**Validations:**
- ClassID: must exist for this school
- AcademicYearId: must exist for this school
- EndDate >= StartDate

#### G. Exam Results Import
**Template Columns:**
- StudentCode* (must exist)
- ExamID* (must exist)
- SubjectName* (from SubjectMaster)
- MarksObtained* (decimal)
- MaxMarks* (decimal)
- Grade
- Remarks

**Validations:**
- StudentCode: must exist
- ExamID: must exist for this school
- MarksObtained <= MaxMarks
- MarksObtained >= 0

#### H. Class/Section/Subject Masters Import
**Class Template:**
- ClassName*
- ClassCode*
- EducationLevel
- Description

**Section Template:**
- ClassName* (must exist)
- SectionName*
- Capacity (integer)
- RoomNumber

**Subject Template:**
- SubjectName*
- SubjectCode*
- ClassID* (must exist)
- Description

---

## Phase 3: Implementation Structure

### 3.1 Folder Structure
```
ShikshaWave_Project/
├── core/
│   ├── onboarding/
│   │   ├── __init__.py
│   │   ├── views.py              # Onboarding views
│   │   ├── forms.py              # School creation forms
│   │   └── utils.py              # Helper functions
│   ├── data_import/
│   │   ├── __init__.py
│   │   ├── views.py              # Import views
│   │   ├── validators.py         # Data validation logic
│   │   ├── processors.py         # Bulk insert logic
│   │   ├── templates_generator.py # Excel template generator
│   │   └── models.py             # Import tracking models
│   ├── templates/
│   │   ├── onboarding/
│   │   │   ├── school_create.html
│   │   │   └── school_setup_complete.html
│   │   └── data_import/
│   │       ├── import_dashboard.html
│   │       ├── upload_form.html
│   │       ├── preview_data.html
│   │       ├── import_progress.html
│   │       └── import_summary.html
│   └── static/
│       └── js/
│           ├── onboarding.js
│           └── data_import.js
├── database/
│   ├── procedures/
│   │   ├── Proc_School_Onboard.sql
│   │   ├── Proc_Student_Bulk_Import.sql
│   │   ├── Proc_Teacher_Bulk_Import.sql
│   │   ├── Proc_Salary_Bulk_Import.sql
│   │   ├── Proc_Fee_Bulk_Import.sql
│   │   ├── Proc_Attendance_Bulk_Import.sql
│   │   ├── Proc_Exam_Bulk_Import.sql
│   │   └── Proc_ExamResult_Bulk_Import.sql
│   └── tables/
│       ├── DataImportLog.sql
│       └── DataImportErrors.sql
└── uploads/
    └── import_files/
        └── .gitkeep
```

### 3.2 Database Tables for Import Tracking

**DataImportLog:**
```sql
CREATE TABLE DataImportLog (
    ImportID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL,
    ImportType NVARCHAR(50) NOT NULL, -- Students, Teachers, Salary, etc.
    FileName NVARCHAR(255) NOT NULL,
    TotalRows INT NOT NULL,
    SuccessRows INT DEFAULT 0,
    FailedRows INT DEFAULT 0,
    Status NVARCHAR(20) NOT NULL, -- Pending, Processing, Completed, Failed
    StartedAt DATETIME DEFAULT GETDATE(),
    CompletedAt DATETIME NULL,
    CreatedBy INT NOT NULL,
    ErrorFilePath NVARCHAR(500) NULL,
    FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
    FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID)
);
```

**DataImportErrors:**
```sql
CREATE TABLE DataImportErrors (
    ErrorID INT IDENTITY(1,1) PRIMARY KEY,
    ImportID INT NOT NULL,
    RowNumber INT NOT NULL,
    ColumnName NVARCHAR(100) NULL,
    ErrorMessage NVARCHAR(1000) NOT NULL,
    RowData NVARCHAR(MAX) NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ImportID) REFERENCES DataImportLog(ImportID)
);
```

---

## Phase 4: API Endpoints

### 4.1 Onboarding APIs
```
POST /api/onboarding/school/create/          # Create school + admin
GET  /api/onboarding/templates/              # Get template preferences
POST /api/onboarding/templates/save/         # Save template preferences
```

### 4.2 Data Import APIs
```
GET  /api/import/dashboard/                  # Import dashboard
GET  /api/import/template/download/<type>/   # Download Excel template
POST /api/import/upload/                     # Upload file
POST /api/import/validate/                   # Validate uploaded data
GET  /api/import/preview/<import_id>/        # Preview validated data
POST /api/import/execute/<import_id>/        # Execute import
GET  /api/import/status/<import_id>/         # Check import status
GET  /api/import/errors/<import_id>/         # Download error report
GET  /api/import/history/                    # Import history
```

---

## Phase 5: Performance Optimization

### 5.1 Bulk Insert Strategy
- Use SQL Server Table-Valued Parameters (TVP)
- Batch size: 1000 records per transaction
- Use `BULK INSERT` for large datasets (>10K rows)
- Disable indexes during import, rebuild after

### 5.2 Validation Strategy
- Client-side: Basic format validation (Excel)
- Server-side: Comprehensive validation before DB insert
- Use pandas for fast data processing
- Parallel validation for large files (multiprocessing)

### 5.3 Transaction Management
- Wrap each batch in transaction
- Rollback on error
- Continue with next batch
- Log all errors for correction

---

## Phase 6: Security & Audit

### 6.1 Security Measures
- File upload validation (size, type, content)
- SQL injection prevention (parameterized queries)
- Role-based access control (ProfileID check)
- School isolation (SchoolID filter)

### 6.2 Audit Trail
- Log all imports in DataImportLog
- Track CreatedBy for all records
- Store original file for 30 days
- Email notification on completion

---

## Phase 7: User Experience

### 7.1 Import Workflow
1. **Upload:** Drag-drop or browse Excel file
2. **Validate:** Real-time validation with progress bar
3. **Preview:** Show first 100 rows with validation status
4. **Confirm:** Review summary (total, valid, invalid)
5. **Import:** Execute with progress tracking
6. **Summary:** Show results (inserted, updated, skipped)
7. **Errors:** Download error report for corrections
8. **Re-upload:** Fix errors and re-import

### 7.2 UI Components
- Progress bars for upload/validation/import
- Color-coded validation results (green/red/yellow)
- Inline error messages with row/column reference
- Download buttons for templates and error reports
- Import history table with filters

---

## Phase 8: Testing Strategy

### 8.1 Test Cases
- Valid data import (happy path)
- Invalid data handling (missing required fields)
- Duplicate detection (Aadhaar, Email, StudentCode)
- FK validation (ClassID, SectionID, etc.)
- Large file handling (10K+ rows)
- Concurrent imports
- Role-based access (Super Admin vs School Admin)
- Transaction rollback on error

### 8.2 Test Data
- Sample Excel files for each import type
- Edge cases (special characters, long text, etc.)
- Performance test data (50K students)

---

## Phase 9: Deployment Checklist

1. Create database tables (DataImportLog, DataImportErrors)
2. Deploy stored procedures
3. Create upload directories with permissions
4. Configure file size limits (settings.py)
5. Install required packages (pandas, openpyxl)
6. Run migrations
7. Create menu entries for import module
8. Assign permissions to ProfileMenuMapping
9. Test with sample data
10. Train users (documentation + video)

---

## Phase 10: Maintenance & Support

### 10.1 Monitoring
- Track import success/failure rates
- Monitor file upload sizes
- Alert on repeated failures
- Performance metrics (import time per 1K rows)

### 10.2 Support
- User guide with screenshots
- Video tutorials for each import type
- FAQ document
- Support ticket system integration

---

## Deliverables Summary

1. ✅ Implementation plan (this document)
2. ⏳ Database schema (tables + procedures)
3. ⏳ Django backend (views, validators, processors)
4. ⏳ Frontend templates (HTML/CSS/JS)
5. ⏳ Excel templates (one per import type)
6. ⏳ API documentation
7. ⏳ User guide
8. ⏳ Test cases + test data
9. ⏳ Deployment scripts

---

## Timeline Estimate

- **Phase 1-2:** Database + Procedures (3 days)
- **Phase 3-4:** Backend Implementation (5 days)
- **Phase 5:** Frontend + UX (4 days)
- **Phase 6:** Testing + Bug Fixes (3 days)
- **Phase 7:** Documentation (2 days)
- **Total:** 17 working days

---

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Create database objects
4. Implement backend logic
5. Build frontend interfaces
6. Test with sample data
7. Deploy to staging
8. User acceptance testing
9. Production deployment
10. Training and handover
