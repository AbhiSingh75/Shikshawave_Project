# ShikshaWave - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Database Design](#database-design)
5. [Module Documentation](#module-documentation)
6. [Data Flow Diagrams](#data-flow-diagrams)
7. [API Documentation](#api-documentation)
8. [Security Implementation](#security-implementation)
9. [Deployment Guide](#deployment-guide)

---

## 1. Project Overview

### 1.1 Introduction
ShikshaWave is an enterprise-grade School Management System (SMS) designed to streamline educational operations across multiple schools. It provides comprehensive solutions for student management, staff administration, financial operations, academic tracking, and communication.

### 1.2 Key Features
- **Multi-Tenancy**: Support for multiple schools with complete data isolation
- **Role-Based Access Control**: 7 distinct user profiles with granular permissions
- **Financial Management**: Fee collection, payroll processing, and financial reporting
- **Academic Management**: Admission, attendance, examinations, and result processing
- **Communication**: Email queue system, notifications, and ticketing support
- **Security**: Face recognition, OTP authentication, URL encryption
- **Customization**: Template-based document generation and customizable receipts

### 1.3 User Roles
1. **Super Admin**: System-wide administration and configuration
2. **School Admin**: School-level management and operations
3. **Teacher**: Academic operations and student management
4. **Student**: Access to personal academic information
5. **Accountant**: Financial operations and reporting
6. **Driver**: Transportation management
7. **Librarian**: Library operations

---

## 2. System Architecture

### 2.1 Architecture Pattern
**Hybrid Modular Monolith Architecture**
- Django handles routing, middleware, authentication, and presentation
- SQL Server stored procedures handle complex business logic and data operations
- Asynchronous processing for heavy operations (PDF generation, email sending)

### 2.2 Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (Browser)                   │
│  HTML/CSS/JavaScript + AJAX + Dark Mode + Responsive UI     │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                   Django Application Layer                   │
├─────────────────────────────────────────────────────────────┤
│  Middleware Stack:                                           │
│  - CustomAuthenticationMiddleware                            │
│  - URLEncryptionMiddleware                                   │
│  - SessionCleanupMiddleware                                  │
│  - ErrorPageMiddleware                                       │
├─────────────────────────────────────────────────────────────┤
│  Core Modules:                                               │
│  - Authentication & Security                                 │
│  - Student Management                                        │
│  - Staff Management                                          │
│  - Financial Operations                                      │
│  - Academic Operations                                       │
│  - Communication (Mail, Notifications, Tickets)              │
└─────────────────────────────────────────────────────────────┘
                            ↓ ODBC
┌─────────────────────────────────────────────────────────────┐
│              SQL Server Database Layer                       │
├─────────────────────────────────────────────────────────────┤
│  - Tables (40+ entities)                                     │
│  - Stored Procedures (100+ procedures)                       │
│  - Views and Functions                                       │
│  - Triggers for audit trails                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  - SMTP (Gmail) for email delivery                           │
│  - File Storage for documents and media                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Request Flow
```
User Request → Django URL Router → Middleware Chain → View Function
     ↓
Authentication Check → Permission Validation → Business Logic
     ↓
Stored Procedure Call → Data Processing → Response Generation
     ↓
Template Rendering → JSON/HTML Response → Client
```

---

## 3. Technology Stack

### 3.1 Backend Technologies
- **Framework**: Django 5.2.5
- **Language**: Python 3.13
- **Database**: Microsoft SQL Server
- **Database Driver**: mssql-django with ODBC Driver 17
- **Session Management**: Custom database-backed sessions
- **Cache**: Django LocMem Cache

### 3.2 Frontend Technologies
- **HTML5**: Semantic markup
- **CSS3**: Custom styling with dark mode support
- **JavaScript**: Vanilla JS with AJAX
- **UI Components**: Custom modals, dropdowns, and notifications

### 3.3 Key Python Libraries
```
Django==5.2.5
mssql-django
Pillow (Image processing)
xhtml2pdf (PDF generation)
WeasyPrint (Advanced PDF rendering)
cryptography (Encryption)
```

### 3.4 Database Components
- **Tables**: 40+ normalized tables
- **Stored Procedures**: 100+ procedures for business logic
- **Views**: Optimized views for reporting
- **Functions**: Utility functions for calculations

---

## 4. Database Design

### 4.1 Core Entities

#### 4.1.1 User Management
```
SchoolMaster
├── SchoolID (PK)
├── SchoolCode
├── SchoolName
├── RegistrationNumber
├── Address, District, State, Country
├── Phone, Email, Website
├── SchoolLogo (Binary)
└── Audit Fields (CreatedBy, CreatedAt, etc.)

UserMaster
├── UserID (PK)
├── UserCode (Unique)
├── UserName
├── PasswordHash
├── Email, Phone
├── ProfileID (FK → ProfileMaster)
├── SchoolID (FK → SchoolMaster)
├── UserPhoto (Binary)
└── Audit Fields

ProfileMaster
├── ProfileID (PK)
├── ProfileName
└── Description

MenuMaster
├── MenuID (PK)
├── MenuName
├── ParentMenuID (FK → Self)
├── MenuURL
├── Icon
└── DisplayOrder

ProfileMenuMapping
├── MappingID (PK)
├── ProfileID (FK)
├── MenuID (FK)
├── CanView, CanAdd, CanEdit, CanDelete
└── Audit Fields
```

#### 4.1.2 Academic Entities
```
ClassMaster
├── ClassID (PK)
├── SchoolID (FK)
├── ClassName
├── ClassCode
├── EducationLevel
└── Audit Fields

SectionMaster
├── SectionID (PK)
├── ClassID (FK)
├── SectionName
├── Capacity
├── RoomNumber
└── Audit Fields

SubjectMaster
├── SubjectID (PK)
├── SchoolID (FK)
├── ClassID (FK)
├── SubjectName
├── SubjectCode
└── Audit Fields

AcademicYear
├── AcademicYearID (PK)
├── SchoolID (FK)
├── YearName
├── StartDate
├── EndDate
├── IsActive
└── Audit Fields
```

#### 4.1.3 Student Management
```
Student
├── StudentID (PK)
├── StudentCode (Unique)
├── UserID (FK → UserMaster)
├── SchoolID (FK)
├── ClassID (FK)
├── SectionID (FK)
├── AcademicYearID (FK)
├── FirstName, MiddleName, LastName
├── DateOfBirth, Gender
├── AadhaarNumber
├── BloodGroup, Religion, Category
├── FatherName, MotherName
├── GuardianPhone, GuardianEmail
├── CurrentAddress, PermanentAddress
├── PreviousSchool, PreviousClass
└── Audit Fields

StudentDocuments
├── DocumentID (PK)
├── StudentID (FK)
├── DocumentType
├── DocumentName
├── DocumentData (Binary)
├── MimeType
└── UploadedAt

StudentAcademicTrack
├── TrackID (PK)
├── StudentID (FK)
├── AcademicYearID (FK)
├── ClassID (FK)
├── SectionID (FK)
├── PromotionStatus
└── Audit Fields
```

#### 4.1.4 Financial Entities
```
FeeType_Master
├── FeeTypeId (PK)
├── SchoolId (FK)
├── ClassId (FK)
├── FeeTypeName
├── DefaultAmount
└── IsActive

Payment
├── PaymentID (PK)
├── SchoolID (FK)
├── StudentID (FK)
├── ReceiptNumber (Unique)
├── PaymentDate
├── TotalAmount
├── PaymentMode
├── PaymentFor
├── TransactionID
├── Remarks
└── CreatedBy

SalaryComponentMaster
├── ComponentID (PK)
├── SchoolID (FK)
├── ComponentName
├── ComponentType (Earning/Deduction)
└── Audit Fields

EmployeeSalaryBreakup
├── BreakupID (PK)
├── SchoolID (FK)
├── EmployeeID (FK)
├── ComponentID (FK)
├── Amount
└── Audit Fields

SalaryPayment
├── PaymentID (PK)
├── SchoolID (FK)
├── EmployeeID (FK)
├── PaymentMonth
├── PaymentYear
├── GrossAmount
├── Deductions
├── NetAmount
├── PaymentDate
└── Audit Fields
```

#### 4.1.5 Examination Entities
```
ExamMaster
├── ExamID (PK)
├── SchoolID (FK)
├── ExamName
├── ExamType
├── StartDate, EndDate
├── IsPublished
└── Audit Fields

ExamTimetable
├── TimetableID (PK)
├── ExamID (FK)
├── ClassID (FK)
├── SubjectID (FK)
├── ExamDate
├── StartTime, EndTime
├── MaxMarks
└── Audit Fields

ExamResult
├── ResultID (PK)
├── ExamID (FK)
├── StudentID (FK)
├── SubjectID (FK)
├── MarksObtained
├── MaxMarks
├── Grade
└── Remarks
```

#### 4.1.6 Communication Entities
```
EmailTemplate
├── Id (PK)
├── Code
├── SchoolId (FK)
├── Language
├── SubjectTemplate
├── BodyTextTemplate
├── BodyHtmlTemplate
├── Placeholders
└── IsActive

EmailTracking
├── EmailTrackingID (PK)
├── EmailCode
├── ToEmail
├── FromEmail
├── Subject
├── SchoolID (FK)
├── EmailBody
├── Status
├── AttemptCount
├── CreatedAt
├── CompletedAt
└── LastError

Notification
├── NotificationID (PK)
├── SchoolID (FK)
├── NotificationType
├── Title
├── Message
├── TargetURL
├── RecipientUserID (FK)
├── IsRead
├── CreatedAt
└── ReadAt

Ticket
├── TicketID (PK)
├── TicketNumber (Unique)
├── SchoolID (FK)
├── Subject
├── Description
├── Priority
├── Status
├── CreatedBy (FK)
├── AssignedTo (FK)
└── Audit Fields
```

### 4.2 Database Relationships
```
SchoolMaster (1) ──→ (N) UserMaster
SchoolMaster (1) ──→ (N) ClassMaster
SchoolMaster (1) ──→ (N) Student
SchoolMaster (1) ──→ (N) FeeType_Master
SchoolMaster (1) ──→ (N) Payment

UserMaster (1) ──→ (1) ProfileMaster
UserMaster (1) ──→ (N) Student

ClassMaster (1) ──→ (N) SectionMaster
ClassMaster (1) ──→ (N) SubjectMaster
ClassMaster (1) ──→ (N) Student

Student (1) ──→ (N) StudentDocuments
Student (1) ──→ (N) Payment
Student (1) ──→ (N) ExamResult
Student (1) ──→ (N) StudentAcademicTrack

ProfileMaster (1) ──→ (N) ProfileMenuMapping
MenuMaster (1) ──→ (N) ProfileMenuMapping
```

---

## 5. Module Documentation

### 5.1 Authentication & Security Module

#### Purpose
Secure user authentication, session management, and access control across the platform.

#### Components
- **Views**: `login_view`, `verify_otp_view`, `logout_view`
- **Middleware**: `CustomAuthenticationMiddleware`, `URLEncryptionMiddleware`
- **Models**: `UserMaster`, `ProfileMaster`, `OTPRecord`, `FaceTemplate`
- **Utilities**: `auth_utils.py`, `url_encryption.py`, `decorators.py`

#### Key Features
1. **Multi-Factor Authentication**
   - Password-based login with SHA-256 hashing
   - Time-bound 6-digit OTP verification
   - OTP expiry: 5 minutes
   - Maximum 3 OTP attempts

2. **Face Recognition**
   - 128-dimensional face descriptor vectors
   - Stored as JSON in database
   - Device-agnostic verification
   - Template versioning support

3. **Session Management**
   - Custom database-backed sessions
   - 48-character CSPRNG tokens
   - Configurable timeout (default: 1 hour)
   - Automatic session cleanup
   - Activity tracking

4. **Permission System**
   - Role-based access control (RBAC)
   - Menu-level permissions
   - Action-level permissions (View, Add, Edit, Delete)
   - URL-based permission validation

#### Security Features
- **Password Security**: SHA-256 hashing with salt
- **URL Encryption**: Sensitive IDs encrypted in URLs
- **CSRF Protection**: Django CSRF middleware
- **Session Security**: HttpOnly cookies, SameSite policy
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Template auto-escaping

---


## 6. Data Flow Diagrams

### 6.1 Authentication Flow

#### 6.1.1 Login Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Enter UserCode/Password
     ↓
┌────────────────────────────┐
│  login_view                │
│  (core/views.py)           │
└────┬───────────────────────┘
     │ 2. Validate credentials
     ↓
┌────────────────────────────┐
│  UserMaster Table          │
│  - Check UserCode exists   │
│  - Verify PasswordHash     │
│  - Check IsActive          │
│  - Check SchoolID          │
└────┬───────────────────────┘
     │ 3. Generate OTP
     ↓
┌────────────────────────────┐
│  OTPRecord Table           │
│  - Generate 6-digit OTP    │
│  - Set expiry (5 min)      │
│  - Store IP & device info  │
└────┬───────────────────────┘
     │ 4. Send OTP Email
     ↓
┌────────────────────────────┐
│  Email Queue System        │
│  - Queue email task        │
│  - Use OTP template        │
│  - Send via SMTP           │
└────┬───────────────────────┘
     │ 5. Redirect to OTP page
     ↓
┌────────────────────────────┐
│  verify_otp_view           │
│  - User enters OTP         │
│  - Validate OTP            │
│  - Check expiry            │
│  - Mark as used            │
└────┬───────────────────────┘
     │ 6. Create session
     ↓
┌────────────────────────────┐
│  user_sessions Table       │
│  - Generate session token  │
│  - Store user metadata     │
│  - Set expiry time         │
└────┬───────────────────────┘
     │ 7. Set cookie & redirect
     ↓
┌────────────────────────────┐
│  Dashboard                 │
└────────────────────────────┘
```

#### 6.1.2 Face Recognition Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Capture face image
     ↓
┌────────────────────────────┐
│  JavaScript (face-api.js)  │
│  - Detect face             │
│  - Extract 128D descriptor │
└────┬───────────────────────┘
     │ 2. Send descriptor array
     ↓
┌────────────────────────────┐
│  register_face_template    │
│  (API endpoint)            │
└────┬───────────────────────┘
     │ 3. Store template
     ↓
┌────────────────────────────┐
│  FaceTemplate Table        │
│  - UserID                  │
│  - FaceDescriptor (JSON)   │
│  - TemplateVersion         │
└────────────────────────────┘

Verification Flow:
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Capture face
     ↓
┌────────────────────────────┐
│  JavaScript                │
│  - Extract descriptor      │
└────┬───────────────────────┘
     │ 2. Request stored template
     ↓
┌────────────────────────────┐
│  get_face_template API     │
│  - Fetch from database     │
└────┬───────────────────────┘
     │ 3. Compare descriptors
     ↓
┌────────────────────────────┐
│  JavaScript                │
│  - Calculate Euclidean     │
│    distance                │
│  - Threshold: 0.6          │
└────┬───────────────────────┘
     │ 4. Grant/Deny access
     ↓
┌────────────────────────────┐
│  Login Success/Failure     │
└────────────────────────────┘
```

#### 6.1.3 Session Management Flow
```
Every Request:
┌──────────┐
│  Request │
└────┬─────┘
     │ 1. Extract session cookie
     ↓
┌────────────────────────────┐
│  CustomAuthenticationMW    │
│  - Read session token      │
└────┬───────────────────────┘
     │ 2. Validate session
     ↓
┌────────────────────────────┐
│  user_sessions Table       │
│  - Check token exists      │
│  - Verify not expired      │
│  - Check last_activity     │
└────┬───────────────────────┘
     │ 3. Load user data
     ↓
┌────────────────────────────┐
│  UserMaster + SchoolMaster │
│  - Attach to request       │
│  - Load permissions        │
└────┬───────────────────────┘
     │ 4. Update activity
     ↓
┌────────────────────────────┐
│  user_sessions Table       │
│  - Update last_activity    │
└────┬───────────────────────┘
     │ 5. Continue to view
     ↓
┌────────────────────────────┐
│  View Function             │
└────────────────────────────┘
```

---

### 6.2 Student Admission Flow

#### 6.2.1 Complete Admission Process
```
┌──────────┐
│  User    │
│ (Admin)  │
└────┬─────┘
     │ 1. Navigate to admission page
     ↓
┌────────────────────────────────────────┐
│  student_admission view                │
│  (admission_views.py)                  │
├────────────────────────────────────────┤
│  Load Data:                            │
│  - Classes (via api_classes)           │
│  - Academic Years                      │
│  - Countries, States, Districts        │
│  - Fee Types for selected class        │
└────┬───────────────────────────────────┘
     │ 2. Fill admission form (50+ fields)
     ↓
┌────────────────────────────────────────┐
│  Form Sections:                        │
│  ├─ Student Information                │
│  │  - Name, DOB, Gender                │
│  │  - Aadhaar, Blood Group             │
│  │  - Religion, Category               │
│  ├─ Parent Information                 │
│  │  - Father/Mother details            │
│  │  - Guardian contact                 │
│  ├─ Address Information                │
│  │  - Current & Permanent address      │
│  ├─ Previous School                    │
│  │  - School name, class, board        │
│  ├─ Documents                          │
│  │  - Photo, Birth Certificate         │
│  │  - Aadhaar, Transfer Certificate    │
│  └─ Fee Selection                      │
│     - Admission fees                   │
│     - Monthly fees                     │
└────┬───────────────────────────────────┘
     │ 3. Submit form with documents
     ↓
┌────────────────────────────────────────┐
│  Validation Layer                      │
│  - Check required fields               │
│  - Validate Aadhaar uniqueness         │
│  - Validate file types (PDF, JPG)      │
│  - Check file size (max 5MB)           │
│  - Validate email format               │
│  - Validate phone numbers              │
└────┬───────────────────────────────────┘
     │ 4. Process documents
     ↓
┌────────────────────────────────────────┐
│  Document Processing                   │
│  - Read file as binary                 │
│  - Encode to Base64                    │
│  - Validate MIME type                  │
│  - Prepare JSON array                  │
└────┬───────────────────────────────────┘
     │ 5. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Student_Admission_With_Documents │
│  (SQL Server Stored Procedure)         │
├────────────────────────────────────────┤
│  BEGIN TRANSACTION                     │
│                                        │
│  Step 1: Create User Account          │
│  ├─ Generate UserCode                 │
│  ├─ Hash password                     │
│  ├─ Insert into UserMaster            │
│  └─ Get @UserID                       │
│                                        │
│  Step 2: Create Student Record        │
│  ├─ Generate StudentCode              │
│  ├─ Insert into Student table         │
│  ├─ Link to UserID                    │
│  └─ Get @StudentID                    │
│                                        │
│  Step 3: Assign to Class/Section      │
│  ├─ Insert StudentAcademicTrack       │
│  └─ Set current academic year         │
│                                        │
│  Step 4: Store Documents              │
│  ├─ Parse JSON document array         │
│  ├─ Insert each into StudentDocuments │
│  └─ Store binary data                 │
│                                        │
│  Step 5: Create Fee Structure         │
│  ├─ Insert admission fees             │
│  ├─ Insert monthly fees               │
│  └─ Apply discounts if any            │
│                                        │
│  Step 6: Generate Receipt Number      │
│  ├─ Format: ADM-SchoolID-StudentID    │
│  └─ Return receipt details            │
│                                        │
│  COMMIT TRANSACTION                    │
│                                        │
│  Return: StudentCode, ReceiptNumber    │
└────┬───────────────────────────────────┘
     │ 6. Generate acknowledgment
     ↓
┌────────────────────────────────────────┐
│  PDF Generation                        │
│  - Load acknowledgment template        │
│  - Populate student data               │
│  - Render HTML to PDF                  │
│  - Store in session                    │
└────┬───────────────────────────────────┘
     │ 7. Queue email
     ↓
┌────────────────────────────────────────┐
│  Email Queue System                    │
│  - Create EmailTracking record         │
│  - Attach PDF acknowledgment           │
│  - Attach payment receipt              │
│  - Set status: Pending                 │
└────┬───────────────────────────────────┘
     │ 8. Background email processing
     ↓
┌────────────────────────────────────────┐
│  Email Worker (Async)                  │
│  - Fetch pending emails                │
│  - Send via SMTP                       │
│  - Update status: Sent/Failed          │
│  - Retry on failure (max 3 attempts)   │
└────┬───────────────────────────────────┘
     │ 9. Redirect to success page
     ↓
┌────────────────────────────────────────┐
│  admission_complete view               │
│  - Display success message             │
│  - Show student code                   │
│  - Provide download links              │
│  - Print acknowledgment option         │
└────────────────────────────────────────┘
```

#### 6.2.2 Document Upload Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Select file
     ↓
┌────────────────────────────┐
│  JavaScript Validation     │
│  - Check file type         │
│  - Check file size         │
│  - Preview image           │
└────┬───────────────────────┘
     │ 2. Submit form
     ↓
┌────────────────────────────┐
│  Django View               │
│  - request.FILES           │
│  - Read file content       │
└────┬───────────────────────┘
     │ 3. Encode to Base64
     ↓
┌────────────────────────────┐
│  Python Processing         │
│  - base64.b64encode()      │
│  - Create JSON structure   │
└────┬───────────────────────┘
     │ 4. Store in database
     ↓
┌────────────────────────────┐
│  StudentDocuments Table    │
│  - StudentID               │
│  - DocumentType            │
│  - DocumentData (Binary)   │
│  - MimeType                │
└────────────────────────────┘
```

---

### 6.3 Fee Collection Flow

#### 6.3.1 Fee Payment Process
```
┌──────────┐
│  User    │
│(Accountant)
└────┬─────┘
     │ 1. Navigate to fee collection
     ↓
┌────────────────────────────────────────┐
│  fee_collection_new view               │
│  - Load classes and sections           │
│  - Load students                       │
└────┬───────────────────────────────────┘
     │ 2. Select student
     ↓
┌────────────────────────────────────────┐
│  get_student_fee_details API           │
│  (AJAX call)                           │
└────┬───────────────────────────────────┘
     │ 3. Fetch fee structure
     ↓
┌────────────────────────────────────────┐
│  Proc_Student_Fee_Structure_Get        │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  SELECT fee types for student          │
│  - Admission fees                      │
│  - Monthly fees                        │
│  - Calculate total due                 │
│  - Calculate paid amount               │
│  - Calculate outstanding               │
│  - Apply discounts                     │
│                                        │
│  Return JSON:                          │
│  {                                     │
│    "feeTypes": [...],                  │
│    "totalDue": 50000,                  │
│    "totalPaid": 20000,                 │
│    "outstanding": 30000                │
│  }                                     │
└────┬───────────────────────────────────┘
     │ 4. Display fee details
     ↓
┌────────────────────────────────────────┐
│  Fee Details UI                        │
│  - Show fee breakdown                  │
│  - Show payment history                │
│  - Input payment amount                │
│  - Select payment mode                 │
│  - Enter transaction details           │
└────┬───────────────────────────────────┘
     │ 5. Submit payment
     ↓
┌────────────────────────────────────────┐
│  submit_fee_collection view            │
│  - Validate payment amount             │
│  - Validate payment mode               │
└────┬───────────────────────────────────┘
     │ 6. Process payment
     ↓
┌────────────────────────────────────────┐
│  Proc_Payment_Insert                   │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  BEGIN TRANSACTION                     │
│                                        │
│  Step 1: Generate Receipt Number       │
│  - Format: RCP-SchoolID-StudentID-Seq  │
│                                        │
│  Step 2: Insert Payment Record         │
│  INSERT INTO Payment (                 │
│    SchoolID, StudentID,                │
│    ReceiptNumber, PaymentDate,         │
│    TotalAmount, PaymentMode,           │
│    PaymentFor, TransactionID,          │
│    CreatedBy                           │
│  )                                     │
│                                        │
│  Step 3: Update Fee Balances           │
│  - Update student fee records          │
│  - Mark fees as paid/partial           │
│                                        │
│  Step 4: Create Audit Trail            │
│  - Log payment transaction             │
│                                        │
│  COMMIT TRANSACTION                    │
│                                        │
│  Return: ReceiptNumber, PaymentID      │
└────┬───────────────────────────────────┘
     │ 7. Generate receipt
     ↓
┌────────────────────────────────────────┐
│  Proc_Payment_Receipt_Get              │
│  - Fetch payment details               │
│  - Fetch student details               │
│  - Fetch school details                │
│  - Calculate amounts                   │
└────┬───────────────────────────────────┘
     │ 8. Render receipt
     ↓
┌────────────────────────────────────────┐
│  Template Engine                       │
│  - Load receipt template               │
│  - Populate data                       │
│  - Apply school branding               │
│  - Generate PDF                        │
└────┬───────────────────────────────────┘
     │ 9. Queue email
     ↓
┌────────────────────────────────────────┐
│  Email Queue                           │
│  - Send receipt to parent email        │
│  - Attach PDF receipt                  │
└────┬───────────────────────────────────┘
     │ 10. Display receipt
     ↓
┌────────────────────────────────────────┐
│  fee_collection_receipt view           │
│  - Show receipt preview                │
│  - Print option                        │
│  - Download option                     │
│  - Email sent confirmation             │
└────────────────────────────────────────┘
```

#### 6.3.2 Fee Report Generation Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Navigate to fee reports
     ↓
┌────────────────────────────┐
│  fee_report view           │
│  - Load filter options     │
└────┬───────────────────────┘
     │ 2. Apply filters
     ↓
┌────────────────────────────┐
│  Filter Options:           │
│  - Date range              │
│  - Class/Section           │
│  - Payment status          │
│  - Payment mode            │
└────┬───────────────────────┘
     │ 3. Fetch report data
     ↓
┌────────────────────────────┐
│  Proc_Payment_Report_Get   │
│  - Aggregate payments      │
│  - Group by class          │
│  - Calculate totals        │
│  - Calculate outstanding   │
└────┬───────────────────────┘
     │ 4. Display report
     ↓
┌────────────────────────────┐
│  Report UI                 │
│  - Tabular data            │
│  - Charts/graphs           │
│  - Export options          │
└────────────────────────────┘
```

---


### 6.4 Payroll Management Flow

#### 6.4.1 Salary Component Setup
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. Navigate to salary components
     ↓
┌────────────────────────────────────────┐
│  salary_component_list view            │
│  - Display existing components         │
└────┬───────────────────────────────────┘
     │ 2. Add/Edit component
     ↓
┌────────────────────────────────────────┐
│  Component Form:                       │
│  - Component Name (e.g., Basic, HRA)   │
│  - Component Type (Earning/Deduction)  │
│  - School-specific                     │
└────┬───────────────────────────────────┘
     │ 3. Save component
     ↓
┌────────────────────────────────────────┐
│  Proc_SalaryComponentMaster_Manage     │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  IF @Action = 'INSERT'                 │
│    INSERT INTO SalaryComponentMaster   │
│  ELSE IF @Action = 'UPDATE'            │
│    UPDATE SalaryComponentMaster        │
│  ELSE IF @Action = 'DELETE'            │
│    Soft delete (IsDeleted = 1)         │
└────┬───────────────────────────────────┘
     │ 4. Assign to employees
     ↓
┌────────────────────────────────────────┐
│  Employee Salary Breakup               │
│  - Select employee                     │
│  - Select component                    │
│  - Enter amount                        │
│  - Save breakup                        │
└────┬───────────────────────────────────┘
     │ 5. Store breakup
     ↓
┌────────────────────────────────────────┐
│  EmployeeSalaryBreakup Table           │
│  - EmployeeID                          │
│  - ComponentID                         │
│  - Amount                              │
└────────────────────────────────────────┘
```

#### 6.4.2 Salary Generation & Payment Flow
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. Navigate to salary management
     ↓
┌────────────────────────────────────────┐
│  salary_management view                │
│  - Select month/year                   │
│  - View employee list                  │
└────┬───────────────────────────────────┘
     │ 2. Generate salary records
     ↓
┌────────────────────────────────────────┐
│  generate_salary_records view          │
│  - Trigger bulk generation             │
└────┬───────────────────────────────────┘
     │ 3. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_SalaryRelease_Generate           │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  FOR each active employee:             │
│                                        │
│  Step 1: Fetch Salary Breakup          │
│  SELECT * FROM EmployeeSalaryBreakup   │
│  WHERE EmployeeID = @EmpID             │
│                                        │
│  Step 2: Calculate Earnings            │
│  SUM(Amount) WHERE ComponentType =     │
│    'Earning'                           │
│                                        │
│  Step 3: Calculate Deductions          │
│  SUM(Amount) WHERE ComponentType =     │
│    'Deduction'                         │
│                                        │
│  Step 4: Calculate Net Salary          │
│  @NetSalary = @Earnings - @Deductions  │
│                                        │
│  Step 5: Check Attendance              │
│  - Fetch attendance for month          │
│  - Calculate working days              │
│  - Apply deductions for absences       │
│                                        │
│  Step 6: Create Salary Record          │
│  INSERT INTO SalaryRelease (           │
│    EmployeeID, PaymentMonth,           │
│    PaymentYear, GrossAmount,           │
│    Deductions, NetAmount,              │
│    Status = 'Generated'                │
│  )                                     │
│                                        │
│  Return: Total records generated       │
└────┬───────────────────────────────────┘
     │ 4. Display generated salaries
     ↓
┌────────────────────────────────────────┐
│  Salary List UI                        │
│  - Employee name                       │
│  - Gross amount                        │
│  - Deductions                          │
│  - Net amount                          │
│  - Status                              │
│  - Actions (Pay, Preview)              │
└────┬───────────────────────────────────┘
     │ 5. Pay salary
     ↓
┌────────────────────────────────────────┐
│  pay_salary view                       │
│  - Confirm payment                     │
│  - Enter payment details               │
└────┬───────────────────────────────────┘
     │ 6. Process payment
     ↓
┌────────────────────────────────────────┐
│  Proc_Salary_Pay                       │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  BEGIN TRANSACTION                     │
│                                        │
│  Step 1: Update Salary Status          │
│  UPDATE SalaryRelease                  │
│  SET Status = 'Paid',                  │
│      PaymentDate = GETDATE(),          │
│      PaymentMode = @Mode,              │
│      TransactionID = @TxnID            │
│  WHERE SalaryID = @SalaryID            │
│                                        │
│  Step 2: Create Payment Record         │
│  INSERT INTO SalaryPayment             │
│                                        │
│  Step 3: Update Employee Balance       │
│  - Update any advance/loan records     │
│                                        │
│  COMMIT TRANSACTION                    │
└────┬───────────────────────────────────┘
     │ 7. Generate salary slip
     ↓
┌────────────────────────────────────────┐
│  Proc_SalarySlip_Get                   │
│  - Fetch employee details              │
│  - Fetch salary breakup                │
│  - Fetch payment details               │
│  - Calculate totals                    │
└────┬───────────────────────────────────┘
     │ 8. Render salary slip
     ↓
┌────────────────────────────────────────┐
│  Salary Slip Template                  │
│  - Company header                      │
│  - Employee details                    │
│  - Earnings table                      │
│  - Deductions table                    │
│  - Net salary                          │
│  - Payment details                     │
└────┬───────────────────────────────────┘
     │ 9. Generate PDF
     ↓
┌────────────────────────────────────────┐
│  PDF Generator (WeasyPrint)            │
│  - Render HTML to PDF                  │
│  - Apply styling                       │
│  - Add page numbers                    │
└────┬───────────────────────────────────┘
     │ 10. Queue email
     ↓
┌────────────────────────────────────────┐
│  Email Queue System                    │
│  - Create email record                 │
│  - Attach salary slip PDF              │
│  - Set recipient: employee email       │
│  - Use SALARY_SLIP template            │
└────┬───────────────────────────────────┘
     │ 11. Background processing
     ↓
┌────────────────────────────────────────┐
│  Email Worker (Async Thread)           │
│  - Fetch pending emails                │
│  - Send via SMTP                       │
│  - Update status                       │
│  - Retry on failure                    │
└────┬───────────────────────────────────┘
     │ 12. Confirmation
     ↓
┌────────────────────────────────────────┐
│  Success Message                       │
│  - Salary paid successfully            │
│  - Slip sent to employee email         │
│  - Download/Print options              │
└────────────────────────────────────────┘
```

#### 6.4.3 Salary Slip Preview Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Click preview
     ↓
┌────────────────────────────┐
│  preview_salary_slip view  │
│  - Get PaymentID           │
└────┬───────────────────────┘
     │ 2. Fetch data
     ↓
┌────────────────────────────┐
│  Proc_SalarySlip_Get       │
│  - Return salary details   │
└────┬───────────────────────┘
     │ 3. Render template
     ↓
┌────────────────────────────┐
│  salary_slip.html          │
│  - Display in browser      │
│  - Print-friendly CSS      │
└────────────────────────────┘
```

---

### 6.5 Examination Management Flow

#### 6.5.1 Exam Creation & Scheduling
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. Navigate to exam management
     ↓
┌────────────────────────────────────────┐
│  exam_management view                  │
│  - Display existing exams              │
│  - Add new exam button                 │
└────┬───────────────────────────────────┘
     │ 2. Create exam
     ↓
┌────────────────────────────────────────┐
│  Exam Form:                            │
│  - Exam Name (e.g., Term 1)            │
│  - Exam Type (Term/Monthly/Unit)       │
│  - Start Date                          │
│  - End Date                            │
│  - Classes (Multi-select)              │
│  - Is Published (Yes/No)               │
└────┬───────────────────────────────────┘
     │ 3. Save exam
     ↓
┌────────────────────────────────────────┐
│  Proc_ExamMaster_Set                   │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  IF @Action = 'INSERT'                 │
│    INSERT INTO ExamMaster (            │
│      SchoolID, ExamName, ExamType,     │
│      StartDate, EndDate,               │
│      IsPublished, CreatedBy            │
│    )                                   │
│    Return @ExamID                      │
│                                        │
│  ELSE IF @Action = 'UPDATE'            │
│    UPDATE ExamMaster                   │
│    SET ExamName = @ExamName, ...       │
│                                        │
│  ELSE IF @Action = 'DELETE'            │
│    UPDATE ExamMaster                   │
│    SET IsDeleted = 1                   │
└────┬───────────────────────────────────┘
     │ 4. Create timetable
     ↓
┌────────────────────────────────────────┐
│  exam_timetable view                   │
│  - Select exam                         │
│  - Select class                        │
│  - Add subject entries                 │
└────┬───────────────────────────────────┘
     │ 5. Add timetable entries
     ↓
┌────────────────────────────────────────┐
│  Timetable Entry Form:                 │
│  - Subject                             │
│  - Exam Date                           │
│  - Start Time                          │
│  - End Time                            │
│  - Max Marks                           │
│  - Room Number (optional)              │
└────┬───────────────────────────────────┘
     │ 6. Save timetable
     ↓
┌────────────────────────────────────────┐
│  exam_timetable_save view              │
│  - Validate entries                    │
│  - Check date conflicts                │
└────┬───────────────────────────────────┘
     │ 7. Insert into database
     ↓
┌────────────────────────────────────────┐
│  ExamTimetable Table                   │
│  INSERT INTO ExamTimetable (           │
│    ExamID, ClassID, SubjectID,         │
│    ExamDate, StartTime, EndTime,       │
│    MaxMarks, CreatedBy                 │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 8. Generate timetable PDF
     ↓
┌────────────────────────────────────────┐
│  exam_timetable_print view             │
│  - Fetch timetable entries             │
│  - Group by date                       │
│  - Render template                     │
│  - Generate PDF                        │
└────────────────────────────────────────┘
```

#### 6.5.2 Marks Entry Flow
```
┌──────────┐
│ Teacher  │
└────┬─────┘
     │ 1. Navigate to result entry
     ↓
┌────────────────────────────────────────┐
│  exam_result_entry view                │
│  - Select exam                         │
│  - Select class                        │
│  - Select subject                      │
└────┬───────────────────────────────────┘
     │ 2. Load students
     ↓
┌────────────────────────────────────────┐
│  exam_result_students API              │
│  - Fetch students for class            │
│  - Check existing marks                │
└────┬───────────────────────────────────┘
     │ 3. Display marks entry grid
     ↓
┌────────────────────────────────────────┐
│  Marks Entry UI:                       │
│  ┌──────────────────────────────────┐  │
│  │ Student Name | Marks | Grade     │  │
│  ├──────────────────────────────────┤  │
│  │ John Doe     | [85]  | A         │  │
│  │ Jane Smith   | [92]  | A+        │  │
│  │ ...                              │  │
│  └──────────────────────────────────┘  │
│  - Max Marks displayed                 │
│  - Auto-calculate grade                │
│  - Validation on input                 │
└────┬───────────────────────────────────┘
     │ 4. Submit marks
     ↓
┌────────────────────────────────────────┐
│  exam_result_save view                 │
│  - Validate marks <= max marks         │
│  - Calculate grades                    │
│  - Prepare batch insert                │
└────┬───────────────────────────────────┘
     │ 5. Save to database
     ↓
┌────────────────────────────────────────┐
│  ExamResult Table                      │
│  FOR each student:                     │
│    IF marks exist:                     │
│      UPDATE ExamResult                 │
│    ELSE:                               │
│      INSERT INTO ExamResult (          │
│        ExamID, StudentID, SubjectID,   │
│        MarksObtained, MaxMarks,        │
│        Grade, CreatedBy                │
│      )                                 │
└────┬───────────────────────────────────┘
     │ 6. Calculate statistics
     ↓
┌────────────────────────────────────────┐
│  Result Statistics:                    │
│  - Class average                       │
│  - Highest marks                       │
│  - Lowest marks                        │
│  - Pass percentage                     │
└────────────────────────────────────────┘
```

#### 6.5.3 Result Publication & Report Card Flow
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. Review results
     ↓
┌────────────────────────────────────────┐
│  exam_result_view                      │
│  - Select exam                         │
│  - Select class                        │
│  - View all results                    │
└────┬───────────────────────────────────┘
     │ 2. Publish results
     ↓
┌────────────────────────────────────────┐
│  Proc_ExamMaster_Set                   │
│  UPDATE ExamMaster                     │
│  SET IsPublished = 1                   │
│  WHERE ExamID = @ExamID                │
└────┬───────────────────────────────────┘
     │ 3. Generate report cards
     ↓
┌────────────────────────────────────────┐
│  exam_result_print view                │
│  - Select student(s)                   │
│  - Trigger report generation           │
└────┬───────────────────────────────────┘
     │ 4. Fetch result data
     ↓
┌────────────────────────────────────────┐
│  Proc_ExamResult_Get                   │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  SELECT                                │
│    s.StudentName,                      │
│    s.ClassName,                        │
│    sub.SubjectName,                    │
│    er.MarksObtained,                   │
│    er.MaxMarks,                        │
│    er.Grade                            │
│  FROM ExamResult er                    │
│  JOIN Student s ON er.StudentID = ...  │
│  JOIN SubjectMaster sub ON ...         │
│  WHERE er.ExamID = @ExamID             │
│    AND er.StudentID = @StudentID       │
│                                        │
│  Calculate:                            │
│  - Total marks obtained                │
│  - Total max marks                     │
│  - Percentage                          │
│  - Overall grade                       │
│  - Rank in class                       │
└────┬───────────────────────────────────┘
     │ 5. Render report card
     ↓
┌────────────────────────────────────────┐
│  Report Card Template                  │
│  ┌──────────────────────────────────┐  │
│  │ School Header & Logo             │  │
│  │ Student Details                  │  │
│  │ ┌────────────────────────────┐   │  │
│  │ │ Subject | Marks | Grade    │   │  │
│  │ ├────────────────────────────┤   │  │
│  │ │ Math    | 85/100 | A       │   │  │
│  │ │ Science | 92/100 | A+      │   │  │
│  │ │ ...                        │   │  │
│  │ └────────────────────────────┘   │  │
│  │ Total: 450/500 (90%)             │  │
│  │ Grade: A+                        │  │
│  │ Rank: 3/50                       │  │
│  │ Remarks: Excellent Performance   │  │
│  │ Principal Signature              │  │
│  └──────────────────────────────────┘  │
└────┬───────────────────────────────────┘
     │ 6. Generate PDF
     ↓
┌────────────────────────────────────────┐
│  PDF Generator                         │
│  - Apply school template               │
│  - Add watermark                       │
│  - Digital signature (optional)        │
└────┬───────────────────────────────────┘
     │ 7. Distribute
     ↓
┌────────────────────────────────────────┐
│  Distribution Options:                 │
│  - Download PDF                        │
│  - Print directly                      │
│  - Email to parents                    │
│  - Bulk generation for class           │
└────────────────────────────────────────┘
```

---

### 6.6 Attendance Management Flow

#### 6.6.1 Student Attendance Flow
```
┌──────────┐
│ Teacher  │
└────┬─────┘
     │ 1. Navigate to attendance
     ↓
┌────────────────────────────────────────┐
│  student_attendance view               │
│  - Select date                         │
│  - Select class                        │
│  - Select section                      │
└────┬───────────────────────────────────┘
     │ 2. Load students
     ↓
┌────────────────────────────────────────┐
│  load_students_ajax API                │
│  - Fetch students for class/section    │
│  - Check existing attendance           │
└────┬───────────────────────────────────┘
     │ 3. Display attendance grid
     ↓
┌────────────────────────────────────────┐
│  Attendance UI:                        │
│  ┌──────────────────────────────────┐  │
│  │ Roll | Name      | Status        │  │
│  ├──────────────────────────────────┤  │
│  │ 1    | John Doe  | [P] [A] [L]  │  │
│  │ 2    | Jane      | [P] [A] [L]  │  │
│  │ ...                              │  │
│  └──────────────────────────────────┘  │
│  - Quick actions: Mark All Present    │
│  - Remarks field                      │
└────┬───────────────────────────────────┘
     │ 4. Submit attendance
     ↓
┌────────────────────────────────────────┐
│  submit_attendance_ajax view           │
│  - Validate data                       │
│  - Prepare batch insert                │
└────┬───────────────────────────────────┘
     │ 5. Save to database
     ↓
┌────────────────────────────────────────┐
│  StudentAttendance Table               │
│  FOR each student:                     │
│    INSERT INTO StudentAttendance (     │
│      StudentID, AttendanceDate,        │
│      Status, Remarks,                  │
│      MarkedBy, SchoolID                │
│    )                                   │
└────┬───────────────────────────────────┘
     │ 6. Send notifications
     ↓
┌────────────────────────────────────────┐
│  Notification System                   │
│  IF status = 'Absent':                 │
│    - Send SMS to parent                │
│    - Send email notification           │
│    - Create in-app notification        │
└────────────────────────────────────────┘
```

#### 6.6.2 Staff Attendance Flow
```
┌──────────┐
│  Staff   │
└────┬─────┘
     │ 1. Mark attendance
     ↓
┌────────────────────────────────────────┐
│  mark_staff_attendance view            │
│  - Auto-detect user                    │
│  - Show current date/time              │
│  - Check-in/Check-out buttons          │
└────┬───────────────────────────────────┘
     │ 2. Submit attendance
     ↓
┌────────────────────────────────────────┐
│  Proc_StaffAttendance_Mark             │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  IF @Action = 'CheckIn'                │
│    INSERT INTO StaffAttendance (       │
│      EmployeeID, AttendanceDate,       │
│      CheckInTime, Status = 'Pending'   │
│    )                                   │
│                                        │
│  ELSE IF @Action = 'CheckOut'          │
│    UPDATE StaffAttendance              │
│    SET CheckOutTime = GETDATE(),       │
│        TotalHours = DATEDIFF(...)      │
│    WHERE EmployeeID = @EmpID           │
│      AND AttendanceDate = @Date        │
│                                        │
│  Calculate Late Coming:                │
│  IF CheckInTime > '09:30 AM'           │
│    SET IsLate = 1                      │
└────┬───────────────────────────────────┘
     │ 3. Approval workflow
     ↓
┌────────────────────────────────────────┐
│  Admin Dashboard                       │
│  - View pending attendance             │
│  - Approve/Reject                      │
└────┬───────────────────────────────────┘
     │ 4. Approve attendance
     ↓
┌────────────────────────────────────────┐
│  Proc_StaffAttendance_Approve          │
│  UPDATE StaffAttendance                │
│  SET Status = 'Approved',              │
│      ApprovedBy = @AdminID,            │
│      ApprovedAt = GETDATE()            │
│  WHERE AttendanceID = @ID              │
└────┬───────────────────────────────────┘
     │ 5. Update salary calculation
     ↓
┌────────────────────────────────────────┐
│  Salary Calculation Impact:            │
│  - Count working days                  │
│  - Deduct for absences                 │
│  - Apply late penalties                │
└────────────────────────────────────────┘
```

---


### 6.7 Communication Systems Flow

#### 6.7.1 Email Queue System Flow
```
┌──────────────────┐
│  Any Module      │
│  (Admission,     │
│   Salary, etc.)  │
└────┬─────────────┘
     │ 1. Trigger email event
     ↓
┌────────────────────────────────────────┐
│  Email Service Layer                   │
│  (database_email_queue.py)             │
├────────────────────────────────────────┤
│  def queue_email(                      │
│    email_code,                         │
│    to_email,                           │
│    placeholders,                       │
│    attachments                         │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 2. Fetch email template
     ↓
┌────────────────────────────────────────┐
│  EmailTemplate Table                   │
│  SELECT * FROM EmailTemplate           │
│  WHERE Code = @EmailCode               │
│    AND SchoolId = @SchoolId            │
│    AND IsActive = 1                    │
│                                        │
│  Template Fields:                      │
│  - SubjectTemplate                     │
│  - BodyHtmlTemplate                    │
│  - BodyTextTemplate                    │
│  - Placeholders                        │
└────┬───────────────────────────────────┘
     │ 3. Replace placeholders
     ↓
┌────────────────────────────────────────┐
│  Template Processing                   │
│  Subject = SubjectTemplate             │
│    .replace('{{StudentName}}', name)   │
│    .replace('{{SchoolName}}', school)  │
│                                        │
│  Body = BodyHtmlTemplate               │
│    .replace('{{StudentCode}}', code)   │
│    .replace('{{Amount}}', amount)      │
│    ... (all placeholders)              │
└────┬───────────────────────────────────┘
     │ 4. Create email record
     ↓
┌────────────────────────────────────────┐
│  EmailTracking Table                   │
│  INSERT INTO EmailTracking (           │
│    EmailCode,                          │
│    ToEmail,                            │
│    FromEmail,                          │
│    Subject,                            │
│    SchoolID,                           │
│    EmailBody,                          │
│    EmailHtmlBody,                      │
│    Placeholders (JSON),                │
│    HasAttachments,                     │
│    AttachmentCount,                    │
│    AttachmentDetails (JSON),           │
│    Status = 'Pending',                 │
│    AttemptCount = 0,                   │
│    CreatedAt = GETDATE()               │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 5. Background worker picks up
     ↓
┌────────────────────────────────────────┐
│  Email Worker Thread                   │
│  (Runs every 30 seconds)               │
├────────────────────────────────────────┤
│  WHILE True:                           │
│    emails = fetch_pending_emails()     │
│                                        │
│    FOR each email:                     │
│      try:                              │
│        send_via_smtp(email)            │
│        update_status('Sent')           │
│      except Exception as e:            │
│        increment_attempt_count()       │
│        log_error(e)                    │
│        if attempt_count >= 3:          │
│          update_status('Failed')       │
│        else:                           │
│          retry_later()                 │
│                                        │
│    sleep(30)                           │
└────┬───────────────────────────────────┘
     │ 6. SMTP delivery
     ↓
┌────────────────────────────────────────┐
│  SMTP Server (Gmail)                   │
│  - Connect to smtp.gmail.com:587       │
│  - Authenticate with credentials       │
│  - Send email with attachments         │
│  - Get delivery status                 │
└────┬───────────────────────────────────┘
     │ 7. Update tracking
     ↓
┌────────────────────────────────────────┐
│  EmailTracking Table                   │
│  UPDATE EmailTracking                  │
│  SET Status = 'Sent',                  │
│      CompletedAt = GETDATE(),          │
│      LastError = NULL                  │
│  WHERE EmailTrackingID = @ID           │
└────┬───────────────────────────────────┘
     │ 8. Admin monitoring
     ↓
┌────────────────────────────────────────┐
│  email_queue_status view               │
│  - View all emails                     │
│  - Filter by status                    │
│  - Retry failed emails                 │
│  - Cleanup old records                 │
│  - View error logs                     │
└────────────────────────────────────────┘
```

#### 6.7.2 Notification System Flow
```
┌──────────────────┐
│  Event Trigger   │
│  (Any module)    │
└────┬─────────────┘
     │ 1. Create notification
     ↓
┌────────────────────────────────────────┐
│  NotificationHelper                    │
│  (notification_helper.py)              │
├────────────────────────────────────────┤
│  def create_notification(              │
│    notification_type,                  │
│    title,                              │
│    message,                            │
│    target_url,                         │
│    recipient_user_ids,                 │
│    school_id                           │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 2. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Notification_Create              │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  FOR each recipient:                   │
│    INSERT INTO Notification (          │
│      SchoolID,                         │
│      NotificationType,                 │
│      Title,                            │
│      Message,                          │
│      TargetURL,                        │
│      RecipientUserID,                  │
│      IsRead = 0,                       │
│      CreatedAt = GETDATE()             │
│    )                                   │
│                                        │
│  Return: Notification IDs created      │
└────┬───────────────────────────────────┘
     │ 3. Client polling
     ↓
┌────────────────────────────────────────┐
│  JavaScript (notifications.js)         │
│  - Poll every 30 seconds               │
│  - GET /notifications/api/unread-count/│
└────┬───────────────────────────────────┘
     │ 4. Fetch unread count
     ↓
┌────────────────────────────────────────┐
│  Proc_Notification_GetUnreadCount      │
│  SELECT COUNT(*)                       │
│  FROM Notification                     │
│  WHERE RecipientUserID = @UserID       │
│    AND SchoolID = @SchoolID            │
│    AND IsRead = 0                      │
│    AND IsDeleted = 0                   │
└────┬───────────────────────────────────┘
     │ 5. Update badge
     ↓
┌────────────────────────────────────────┐
│  UI Update                             │
│  - Update notification badge           │
│  - Show count (e.g., "5")              │
│  - Highlight bell icon                 │
└────┬───────────────────────────────────┘
     │ 6. User clicks bell
     ↓
┌────────────────────────────────────────┐
│  GET /notifications/api/list/          │
│  - Fetch recent notifications          │
│  - Pagination: 10 per page             │
└────┬───────────────────────────────────┘
     │ 7. Fetch notifications
     ↓
┌────────────────────────────────────────┐
│  Proc_Notification_GetList             │
│  SELECT TOP 10                         │
│    NotificationID,                     │
│    NotificationType,                   │
│    Title,                              │
│    Message,                            │
│    TargetURL,                          │
│    IsRead,                             │
│    CreatedAt                           │
│  FROM Notification                     │
│  WHERE RecipientUserID = @UserID       │
│    AND SchoolID = @SchoolID            │
│  ORDER BY CreatedAt DESC               │
└────┬───────────────────────────────────┘
     │ 8. Display dropdown
     ↓
┌────────────────────────────────────────┐
│  Notification Dropdown UI              │
│  ┌──────────────────────────────────┐  │
│  │ Notifications (5)                │  │
│  ├──────────────────────────────────┤  │
│  │ • New ticket assigned            │  │
│  │   TKT-2024-001                   │  │
│  │   2 minutes ago                  │  │
│  ├──────────────────────────────────┤  │
│  │ • Fee payment received           │  │
│  │   ₹5000 from John Doe            │  │
│  │   1 hour ago                     │  │
│  ├──────────────────────────────────┤  │
│  │ Mark all as read                 │  │
│  └──────────────────────────────────┘  │
└────┬───────────────────────────────────┘
     │ 9. User clicks notification
     ↓
┌────────────────────────────────────────┐
│  Mark as Read                          │
│  POST /notifications/api/mark-read/ID/ │
└────┬───────────────────────────────────┘
     │ 10. Update database
     ↓
┌────────────────────────────────────────┐
│  Proc_Notification_MarkRead            │
│  UPDATE Notification                   │
│  SET IsRead = 1,                       │
│      ReadAt = GETDATE()                │
│  WHERE NotificationID = @ID            │
│    AND RecipientUserID = @UserID       │
└────┬───────────────────────────────────┘
     │ 11. Navigate to target
     ↓
┌────────────────────────────────────────┐
│  Redirect to TargetURL                 │
│  - Ticket details page                 │
│  - Payment details page                │
│  - Exam results page                   │
│  - etc.                                │
└────────────────────────────────────────┘
```

#### 6.7.3 Ticket Management Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Create ticket
     ↓
┌────────────────────────────────────────┐
│  Ticket Creation Form                  │
│  - Subject                             │
│  - Description                         │
│  - Priority (Low/Medium/High/Critical) │
│  - Category                            │
│  - Attachments                         │
└────┬───────────────────────────────────┘
     │ 2. Submit ticket
     ↓
┌────────────────────────────────────────┐
│  TicketService.create_ticket()         │
│  (tickets/services.py)                 │
└────┬───────────────────────────────────┘
     │ 3. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Ticket_Insert                    │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  BEGIN TRANSACTION                     │
│                                        │
│  Step 1: Generate Ticket Number        │
│  - Format: TKT-YYYY-NNNN               │
│  - Auto-increment sequence             │
│                                        │
│  Step 2: Insert Ticket                 │
│  INSERT INTO Ticket (                  │
│    TicketNumber,                       │
│    SchoolID,                           │
│    Subject,                            │
│    Description,                        │
│    Priority,                           │
│    Status = 'Open',                    │
│    CreatedBy                           │
│  )                                     │
│                                        │
│  Step 3: Store Attachments             │
│  IF attachments exist:                 │
│    INSERT INTO TicketAttachments       │
│                                        │
│  Step 4: Auto-assign                   │
│  - Find available support executive    │
│  - Based on workload balancing         │
│  - INSERT INTO TicketAssignment        │
│                                        │
│  COMMIT TRANSACTION                    │
│                                        │
│  Return: TicketID, TicketNumber        │
└────┬───────────────────────────────────┘
     │ 4. Send notifications
     ↓
┌────────────────────────────────────────┐
│  Notification Integration              │
│  - Notify ticket creator               │
│  - Notify assigned executive           │
│  - Notify school admin                 │
└────┬───────────────────────────────────┘
     │ 5. View ticket
     ↓
┌────────────────────────────────────────┐
│  Proc_Ticket_GetDetails                │
│  - Fetch ticket details                │
│  - Fetch comments/chat                 │
│  - Fetch attachments                   │
│  - Fetch assignment history            │
└────┬───────────────────────────────────┘
     │ 6. Add comment
     ↓
┌────────────────────────────────────────┐
│  TicketComment Table                   │
│  INSERT INTO TicketComment (           │
│    TicketID,                           │
│    CommentText,                        │
│    IsInternal,                         │
│    CreatedBy                           │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 7. Update status
     ↓
┌────────────────────────────────────────┐
│  Proc_Ticket_UpdateStatus              │
│  UPDATE Ticket                         │
│  SET Status = @NewStatus,              │
│      UpdatedBy = @UserID,              │
│      UpdatedAt = GETDATE()             │
│                                        │
│  Status Flow:                          │
│  Open → In Progress → Resolved → Closed│
└────┬───────────────────────────────────┘
     │ 8. Close ticket
     ↓
┌────────────────────────────────────────┐
│  Final Notification                    │
│  - Notify ticket creator               │
│  - Request feedback                    │
│  - Update KPIs                         │
└────────────────────────────────────────┘
```

---

### 6.8 Dashboard & Analytics Flow

#### 6.8.1 Dashboard Data Loading Flow
```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Login & navigate to dashboard
     ↓
┌────────────────────────────────────────┐
│  dashboard_view                        │
│  (dashboard_views.py)                  │
├────────────────────────────────────────┤
│  - Check user role                     │
│  - Load role-specific dashboard        │
│  - Initialize empty cards              │
└────┬───────────────────────────────────┘
     │ 2. Async data loading (AJAX)
     ↓
┌────────────────────────────────────────┐
│  JavaScript Dashboard Loader           │
│  - Load students data                  │
│  - Load employees data                 │
│  - Load attendance data                │
│  - Load revenue data                   │
│  - Load expense data                   │
│  - All parallel AJAX calls             │
└────┬───────────────────────────────────┘
     │ 3. Students analytics
     ↓
┌────────────────────────────────────────┐
│  api_dashboard_students                │
│  GET /api/dashboard/students/          │
└────┬───────────────────────────────────┘
     │ 4. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Dashboard_Students_Get           │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  -- Total Students                     │
│  SELECT COUNT(*) as TotalStudents      │
│  FROM Student                          │
│  WHERE SchoolID = @SchoolID            │
│    AND IsDeleted = 0                   │
│                                        │
│  -- Gender Distribution                │
│  SELECT Gender, COUNT(*) as Count      │
│  FROM Student                          │
│  WHERE SchoolID = @SchoolID            │
│  GROUP BY Gender                       │
│                                        │
│  -- Class-wise Distribution            │
│  SELECT c.ClassName, COUNT(*) as Count │
│  FROM Student s                        │
│  JOIN ClassMaster c ON s.ClassID = ... │
│  WHERE s.SchoolID = @SchoolID          │
│  GROUP BY c.ClassName                  │
│                                        │
│  -- Category Distribution              │
│  SELECT Category, COUNT(*) as Count    │
│  FROM Student                          │
│  WHERE SchoolID = @SchoolID            │
│  GROUP BY Category                     │
│                                        │
│  Return JSON with all metrics          │
└────┬───────────────────────────────────┘
     │ 5. Render student card
     ↓
┌────────────────────────────────────────┐
│  Student Analytics Card                │
│  ┌──────────────────────────────────┐  │
│  │ 👥 Students                      │  │
│  │ Total: 1,250                     │  │
│  │ ┌────────────────────────────┐   │  │
│  │ │ Gender: M: 650 | F: 600    │   │  │
│  │ │ New This Month: +45        │   │  │
│  │ └────────────────────────────┘   │  │
│  │ [View Details]                   │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

#### 6.8.2 Revenue Analytics Flow
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. View revenue dashboard
     ↓
┌────────────────────────────────────────┐
│  api_dashboard_revenue                 │
│  GET /api/dashboard/revenue/           │
│  Parameters:                           │
│  - start_date (optional)               │
│  - end_date (optional)                 │
│  - class_id (optional)                 │
└────┬───────────────────────────────────┘
     │ 2. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Dashboard_Revenue_Get            │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  -- Total Revenue                      │
│  SELECT SUM(TotalAmount) as Revenue    │
│  FROM Payment                          │
│  WHERE SchoolID = @SchoolID            │
│    AND PaymentDate BETWEEN @Start      │
│      AND @End                          │
│                                        │
│  -- Monthly Trend                      │
│  SELECT                                │
│    MONTH(PaymentDate) as Month,        │
│    SUM(TotalAmount) as Amount          │
│  FROM Payment                          │
│  WHERE SchoolID = @SchoolID            │
│    AND YEAR(PaymentDate) = @Year       │
│  GROUP BY MONTH(PaymentDate)           │
│  ORDER BY Month                        │
│                                        │
│  -- Class-wise Breakdown               │
│  SELECT                                │
│    c.ClassName,                        │
│    SUM(p.TotalAmount) as Amount,       │
│    COUNT(DISTINCT p.StudentID) as      │
│      StudentsPaid                      │
│  FROM Payment p                        │
│  JOIN Student s ON p.StudentID = ...   │
│  JOIN ClassMaster c ON s.ClassID = ... │
│  WHERE p.SchoolID = @SchoolID          │
│  GROUP BY c.ClassName                  │
│                                        │
│  -- Payment Mode Distribution          │
│  SELECT PaymentMode, SUM(TotalAmount)  │
│  FROM Payment                          │
│  WHERE SchoolID = @SchoolID            │
│  GROUP BY PaymentMode                  │
│                                        │
│  -- Outstanding Fees                   │
│  SELECT SUM(OutstandingAmount)         │
│  FROM StudentFeeStructure              │
│  WHERE SchoolID = @SchoolID            │
│                                        │
│  Return comprehensive JSON             │
└────┬───────────────────────────────────┘
     │ 3. Render revenue dashboard
     ↓
┌────────────────────────────────────────┐
│  Revenue Dashboard                     │
│  ┌──────────────────────────────────┐  │
│  │ 💰 Revenue Overview              │  │
│  │ Total: ₹12,50,000                │  │
│  │ Outstanding: ₹3,50,000           │  │
│  │ Collection Rate: 78%             │  │
│  │                                  │  │
│  │ Monthly Trend Chart:             │  │
│  │ [Line Chart showing 12 months]   │  │
│  │                                  │  │
│  │ Class-wise Collection:           │  │
│  │ [Bar Chart by class]             │  │
│  │                                  │  │
│  │ Payment Mode Distribution:       │  │
│  │ [Pie Chart]                      │  │
│  │ Cash: 45% | Online: 35%          │  │
│  │ Cheque: 15% | Card: 5%           │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

#### 6.8.3 Attendance Analytics Flow
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. View attendance dashboard
     ↓
┌────────────────────────────────────────┐
│  api_dashboard_attendance              │
│  GET /api/dashboard/attendance/        │
└────┬───────────────────────────────────┘
     │ 2. Call stored procedure
     ↓
┌────────────────────────────────────────┐
│  Proc_Dashboard_Attendance_Get         │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  -- Today's Attendance                 │
│  SELECT                                │
│    COUNT(*) as TotalStudents,          │
│    SUM(CASE WHEN Status = 'P'          │
│      THEN 1 ELSE 0 END) as Present,    │
│    SUM(CASE WHEN Status = 'A'          │
│      THEN 1 ELSE 0 END) as Absent,     │
│    SUM(CASE WHEN Status = 'L'          │
│      THEN 1 ELSE 0 END) as Leave       │
│  FROM StudentAttendance                │
│  WHERE SchoolID = @SchoolID            │
│    AND AttendanceDate = CAST(          │
│      GETDATE() AS DATE)                │
│                                        │
│  -- Attendance Percentage              │
│  DECLARE @Percentage DECIMAL(5,2)      │
│  SET @Percentage = (Present * 100.0)   │
│    / TotalStudents                     │
│                                        │
│  -- Weekly Trend                       │
│  SELECT                                │
│    AttendanceDate,                     │
│    COUNT(*) as Total,                  │
│    SUM(CASE WHEN Status = 'P'          │
│      THEN 1 ELSE 0 END) as Present     │
│  FROM StudentAttendance                │
│  WHERE SchoolID = @SchoolID            │
│    AND AttendanceDate >= DATEADD(      │
│      DAY, -7, GETDATE())               │
│  GROUP BY AttendanceDate               │
│  ORDER BY AttendanceDate               │
│                                        │
│  -- Low Attendance Students            │
│  SELECT TOP 10                         │
│    s.StudentName,                      │
│    s.StudentCode,                      │
│    COUNT(*) as TotalDays,              │
│    SUM(CASE WHEN sa.Status = 'P'       │
│      THEN 1 ELSE 0 END) as PresentDays,│
│    (SUM(CASE WHEN sa.Status = 'P'      │
│      THEN 1 ELSE 0 END) * 100.0)       │
│      / COUNT(*) as Percentage          │
│  FROM Student s                        │
│  JOIN StudentAttendance sa ON ...      │
│  WHERE s.SchoolID = @SchoolID          │
│  GROUP BY s.StudentName, s.StudentCode │
│  HAVING (SUM(CASE WHEN sa.Status = 'P' │
│    THEN 1 ELSE 0 END) * 100.0)         │
│    / COUNT(*) < 75                     │
│  ORDER BY Percentage ASC               │
│                                        │
│  Return comprehensive attendance data  │
└────┬───────────────────────────────────┘
     │ 3. Render attendance dashboard
     ↓
┌────────────────────────────────────────┐
│  Attendance Dashboard                  │
│  ┌──────────────────────────────────┐  │
│  │ 📊 Today's Attendance            │  │
│  │ Present: 1,150 (92%)             │  │
│  │ Absent: 85 (6.8%)                │  │
│  │ Leave: 15 (1.2%)                 │  │
│  │                                  │  │
│  │ Weekly Trend:                    │  │
│  │ [Line Chart showing 7 days]      │  │
│  │                                  │  │
│  │ ⚠️ Low Attendance Alert:         │  │
│  │ - John Doe (65%)                 │  │
│  │ - Jane Smith (70%)               │  │
│  │ [View All]                       │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

---


### 6.9 Data Import System Flow

#### 6.9.1 Bulk Student Import Flow
```
┌──────────┐
│  Admin   │
└────┬─────┘
     │ 1. Navigate to data import
     ↓
┌────────────────────────────────────────┐
│  data_import view                      │
│  - Download template option            │
│  - Upload file option                  │
│  - View import history                 │
└────┬───────────────────────────────────┘
     │ 2. Download Excel template
     ↓
┌────────────────────────────────────────┐
│  Template Generator                    │
│  - Generate Excel with headers         │
│  - Add validation rules                │
│  - Add sample data                     │
│  - Include instructions sheet          │
└────┬───────────────────────────────────┘
     │ 3. Fill template & upload
     ↓
┌────────────────────────────────────────┐
│  File Upload Handler                   │
│  - Validate file format (xlsx/csv)     │
│  - Check file size                     │
│  - Read file content                   │
└────┬───────────────────────────────────┘
     │ 4. Parse & validate
     ↓
┌────────────────────────────────────────┐
│  Data Validation Layer                 │
│  (processors.py)                       │
├────────────────────────────────────────┤
│  FOR each row:                         │
│    - Validate required fields          │
│    - Check data types                  │
│    - Validate email format             │
│    - Validate phone numbers            │
│    - Check Aadhaar uniqueness          │
│    - Validate class/section exists     │
│    - Check date formats                │
│                                        │
│  Collect errors:                       │
│    - Row number                        │
│    - Field name                        │
│    - Error message                     │
│    - Severity (Error/Warning)          │
└────┬───────────────────────────────────┘
     │ 5. Store in staging table
     ↓
┌────────────────────────────────────────┐
│  Student_Staging Table                 │
│  INSERT INTO Student_Staging (         │
│    ImportBatchID,                      │
│    RowNumber,                          │
│    FirstName, LastName,                │
│    DateOfBirth, Gender,                │
│    ... (all fields),                   │
│    ValidationStatus,                   │
│    ValidationErrors,                   │
│    IsProcessed = 0                     │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 6. Display validation results
     ↓
┌────────────────────────────────────────┐
│  Validation Results UI                 │
│  ┌──────────────────────────────────┐  │
│  │ Import Summary                   │  │
│  │ Total Rows: 500                  │  │
│  │ Valid: 485                       │  │
│  │ Errors: 15                       │  │
│  │                                  │  │
│  │ Errors:                          │  │
│  │ Row 23: Invalid email format     │  │
│  │ Row 45: Duplicate Aadhaar        │  │
│  │ Row 67: Class not found          │  │
│  │ ...                              │  │
│  │                                  │  │
│  │ [Fix Errors] [Proceed Anyway]    │  │
│  └──────────────────────────────────┘  │
└────┬───────────────────────────────────┘
     │ 7. Commit import
     ↓
┌────────────────────────────────────────┐
│  Proc_Student_Staging_Commit           │
│  (Stored Procedure)                    │
├────────────────────────────────────────┤
│  BEGIN TRANSACTION                     │
│                                        │
│  DECLARE @ProcessedCount INT = 0       │
│  DECLARE @ErrorCount INT = 0           │
│                                        │
│  -- Cursor through staging records     │
│  FOR each valid staging record:        │
│                                        │
│    BEGIN TRY                           │
│      -- Create User Account            │
│      INSERT INTO UserMaster            │
│      SET @UserID = SCOPE_IDENTITY()    │
│                                        │
│      -- Create Student Record          │
│      INSERT INTO Student               │
│      SET @StudentID = SCOPE_IDENTITY() │
│                                        │
│      -- Assign to Class                │
│      INSERT INTO StudentAcademicTrack  │
│                                        │
│      -- Mark as processed              │
│      UPDATE Student_Staging            │
│      SET IsProcessed = 1,              │
│          ProcessedAt = GETDATE(),      │
│          StudentID = @StudentID        │
│                                        │
│      SET @ProcessedCount += 1          │
│                                        │
│    END TRY                             │
│    BEGIN CATCH                         │
│      -- Log error                      │
│      INSERT INTO DataImportError       │
│      SET @ErrorCount += 1              │
│    END CATCH                           │
│                                        │
│  COMMIT TRANSACTION                    │
│                                        │
│  Return:                               │
│    @ProcessedCount,                    │
│    @ErrorCount                         │
└────┬───────────────────────────────────┘
     │ 8. Log import activity
     ↓
┌────────────────────────────────────────┐
│  DataImportLog Table                   │
│  INSERT INTO DataImportLog (           │
│    ImportBatchID,                      │
│    ImportType = 'Student',             │
│    FileName,                           │
│    TotalRows,                          │
│    SuccessCount,                       │
│    ErrorCount,                         │
│    ImportedBy,                         │
│    ImportedAt                          │
│  )                                     │
└────┬───────────────────────────────────┘
     │ 9. Display results
     ↓
┌────────────────────────────────────────┐
│  Import Complete                       │
│  ✓ Successfully imported 485 students  │
│  ✗ Failed to import 15 records         │
│  [View Details] [Download Error Log]   │
└────────────────────────────────────────┘
```

---

## 7. API Documentation

### 7.1 Authentication APIs

#### 7.1.1 Login API
```
Endpoint: POST /login/
Content-Type: application/x-www-form-urlencoded

Request:
{
  "user_code": "ADMIN001",
  "password": "password123"
}

Response (Success):
{
  "status": "success",
  "message": "OTP sent to your email",
  "redirect": "/verify-otp/"
}

Response (Error):
{
  "status": "error",
  "message": "Invalid credentials"
}
```

#### 7.1.2 OTP Verification API
```
Endpoint: POST /verify-otp/
Content-Type: application/x-www-form-urlencoded

Request:
{
  "otp": "123456"
}

Response (Success):
{
  "status": "success",
  "redirect": "/dashboard/"
}

Response (Error):
{
  "status": "error",
  "message": "Invalid or expired OTP"
}
```

#### 7.1.3 Face Template Registration API
```
Endpoint: POST /api/register-face-template/
Content-Type: application/json

Request:
{
  "user_id": 123,
  "face_descriptor": [0.123, 0.456, ...], // 128D array
  "template_version": "1.0"
}

Response (Success):
{
  "status": "success",
  "message": "Face template registered successfully",
  "template_id": 456
}
```

#### 7.1.4 Face Template Retrieval API
```
Endpoint: GET /api/get-face-template/
Parameters: identifier=ADMIN001

Response (Success):
{
  "status": "success",
  "face_descriptor": [0.123, 0.456, ...],
  "template_version": "1.0"
}
```

---

### 7.2 Student Management APIs

#### 7.2.1 Get Classes API
```
Endpoint: GET /api/classes/
Parameters: school_id=3

Response:
{
  "status": "success",
  "classes": [
    {
      "class_id": 1,
      "class_name": "Class 1",
      "class_code": "CLS1",
      "education_level": "Primary"
    },
    ...
  ]
}
```

#### 7.2.2 Get Sections API
```
Endpoint: GET /api/sections/
Parameters: class_id=1

Response:
{
  "status": "success",
  "sections": [
    {
      "section_id": 1,
      "section_name": "A",
      "capacity": 40,
      "room_number": "101"
    },
    ...
  ]
}
```

#### 7.2.3 Get Students API
```
Endpoint: GET /api/students/
Parameters: class_id=1&section_id=1

Response:
{
  "status": "success",
  "students": [
    {
      "student_id": 1,
      "student_code": "STU001",
      "student_name": "John Doe",
      "roll_number": 1,
      "gender": "Male",
      "date_of_birth": "2010-05-15"
    },
    ...
  ]
}
```

#### 7.2.4 Check Aadhaar Duplicate API
```
Endpoint: GET /api/check-aadhaar-duplicate/
Parameters: aadhaar=123456789012&school_id=3

Response (Not Duplicate):
{
  "is_duplicate": false
}

Response (Duplicate):
{
  "is_duplicate": true,
  "student_code": "STU001",
  "student_name": "John Doe"
}
```

---

### 7.3 Fee Management APIs

#### 7.3.1 Get Student Fee Details API
```
Endpoint: GET /fees/get-student-fee-details/
Parameters: student_id=123

Response:
{
  "status": "success",
  "student": {
    "student_code": "STU001",
    "student_name": "John Doe",
    "class_name": "Class 5",
    "section_name": "A"
  },
  "fee_structure": [
    {
      "fee_type_id": 1,
      "fee_type_name": "Tuition Fee",
      "amount": 5000,
      "paid_amount": 2000,
      "outstanding": 3000
    },
    ...
  ],
  "total_due": 10000,
  "total_paid": 4000,
  "total_outstanding": 6000
}
```

#### 7.3.2 Submit Fee Collection API
```
Endpoint: POST /fees/submit-fee-collection/
Content-Type: application/json

Request:
{
  "student_id": 123,
  "payment_amount": 5000,
  "payment_mode": "Cash",
  "payment_for": "Monthly Fee",
  "transaction_id": "TXN123456",
  "remarks": "Payment for May 2024"
}

Response (Success):
{
  "status": "success",
  "receipt_number": "RCP-3-123-001",
  "payment_id": 456,
  "message": "Payment recorded successfully"
}
```

#### 7.3.3 Get Receipt Data API
```
Endpoint: GET /api/get-receipt-data/
Parameters: receipt_id=RCP-3-123-001

Response:
{
  "status": "success",
  "receipt": {
    "receipt_number": "RCP-3-123-001",
    "payment_date": "2024-05-15",
    "student_name": "John Doe",
    "class_name": "Class 5",
    "amount": 5000,
    "payment_mode": "Cash",
    "received_by": "Admin User"
  },
  "school": {
    "school_name": "ABC School",
    "address": "123 Main St",
    "phone": "1234567890",
    "logo": "data:image/png;base64,..."
  }
}
```

---

### 7.4 Dashboard APIs

#### 7.4.1 Dashboard Students API
```
Endpoint: GET /api/dashboard/students/
Parameters: school_id=3

Response:
{
  "status": "success",
  "total_students": 1250,
  "gender_distribution": {
    "Male": 650,
    "Female": 600
  },
  "class_distribution": [
    {"class_name": "Class 1", "count": 120},
    {"class_name": "Class 2", "count": 115},
    ...
  ],
  "category_distribution": {
    "General": 500,
    "OBC": 400,
    "SC": 200,
    "ST": 150
  },
  "new_admissions_this_month": 45
}
```

#### 7.4.2 Dashboard Revenue API
```
Endpoint: GET /api/dashboard/revenue/
Parameters: school_id=3&start_date=2024-01-01&end_date=2024-12-31

Response:
{
  "status": "success",
  "total_revenue": 1250000,
  "total_outstanding": 350000,
  "collection_rate": 78.12,
  "monthly_trend": [
    {"month": "Jan", "amount": 95000},
    {"month": "Feb", "amount": 102000},
    ...
  ],
  "class_wise_collection": [
    {"class_name": "Class 1", "amount": 150000, "students_paid": 115},
    ...
  ],
  "payment_mode_distribution": {
    "Cash": 562500,
    "Online": 437500,
    "Cheque": 187500,
    "Card": 62500
  }
}
```

#### 7.4.3 Dashboard Attendance API
```
Endpoint: GET /api/dashboard/attendance/
Parameters: school_id=3&date=2024-05-15

Response:
{
  "status": "success",
  "date": "2024-05-15",
  "total_students": 1250,
  "present": 1150,
  "absent": 85,
  "leave": 15,
  "attendance_percentage": 92.0,
  "weekly_trend": [
    {"date": "2024-05-09", "percentage": 91.5},
    {"date": "2024-05-10", "percentage": 93.2},
    ...
  ],
  "low_attendance_students": [
    {
      "student_code": "STU001",
      "student_name": "John Doe",
      "attendance_percentage": 65.5
    },
    ...
  ]
}
```

---

### 7.5 Notification APIs

#### 7.5.1 Get Notifications API
```
Endpoint: GET /notifications/api/list/
Parameters: page=1&per_page=10

Response:
{
  "status": "success",
  "notifications": [
    {
      "notification_id": 123,
      "notification_type": "TicketAssigned",
      "title": "New Ticket Assigned",
      "message": "Ticket TKT-2024-001 has been assigned to you",
      "target_url": "/tickets/123/",
      "is_read": false,
      "created_at": "2024-05-15T10:30:00"
    },
    ...
  ],
  "total_count": 45,
  "unread_count": 12,
  "page": 1,
  "per_page": 10,
  "total_pages": 5
}
```

#### 7.5.2 Get Unread Count API
```
Endpoint: GET /notifications/api/unread-count/

Response:
{
  "status": "success",
  "unread_count": 12
}
```

#### 7.5.3 Mark Notification as Read API
```
Endpoint: POST /notifications/api/mark-read/123/

Response:
{
  "status": "success",
  "message": "Notification marked as read"
}
```

#### 7.5.4 Mark All as Read API
```
Endpoint: POST /notifications/api/mark-all-read/

Response:
{
  "status": "success",
  "message": "All notifications marked as read",
  "count": 12
}
```

---

### 7.6 Exam Management APIs

#### 7.6.1 Get Exams API
```
Endpoint: GET /api/exams/
Parameters: school_id=3&academic_year_id=1

Response:
{
  "status": "success",
  "exams": [
    {
      "exam_id": 1,
      "exam_name": "Term 1 Examination",
      "exam_type": "Term",
      "start_date": "2024-06-01",
      "end_date": "2024-06-15",
      "is_published": true
    },
    ...
  ]
}
```

#### 7.6.2 Get Subjects by Class API
```
Endpoint: GET /api/subjects-by-class/
Parameters: class_id=5

Response:
{
  "status": "success",
  "subjects": [
    {
      "subject_id": 1,
      "subject_name": "Mathematics",
      "subject_code": "MATH"
    },
    {
      "subject_id": 2,
      "subject_name": "Science",
      "subject_code": "SCI"
    },
    ...
  ]
}
```

---

## 8. Security Implementation

### 8.1 Authentication Security

#### 8.1.1 Password Security
```python
# Password Hashing
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Stored in database as PasswordHash
# Never stored in plain text
```

#### 8.1.2 OTP Security
```python
# OTP Generation
import random
import datetime

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

# OTP Properties:
# - 6 digits
# - Valid for 5 minutes
# - Single use only
# - Stored with expiry timestamp
# - IP address tracking
# - Device info logging
```

#### 8.1.3 Session Security
```python
# Session Token Generation
import secrets

def generate_session_token():
    """Generate cryptographically secure session token"""
    return secrets.token_urlsafe(48)

# Session Properties:
# - 48-character random token
# - Stored in database
# - HttpOnly cookie
# - SameSite=Lax
# - Configurable timeout (default: 1 hour)
# - Activity tracking
# - Automatic cleanup of expired sessions
```

### 8.2 URL Encryption

#### 8.2.1 Encryption Implementation
```python
# url_encryption.py
from cryptography.fernet import Fernet
from django.conf import settings

class URLEncryption:
    def __init__(self):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
    
    def encrypt_id(self, id_value):
        """Encrypt ID for URL"""
        data = str(id_value).encode()
        encrypted = self.cipher.encrypt(data)
        return encrypted.decode()
    
    def decrypt_id(self, encrypted_value):
        """Decrypt ID from URL"""
        encrypted = encrypted_value.encode()
        decrypted = self.cipher.decrypt(encrypted)
        return int(decrypted.decode())

# Usage in URLs:
# /student/<encrypted_id>/
# Instead of: /student/123/
```

### 8.3 SQL Injection Prevention

#### 8.3.1 Parameterized Queries
```python
# Always use parameterized queries
from django.db import connection

def get_student(student_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "EXEC Proc_Student_Get @StudentID=%s",
            [student_id]
        )
        return cursor.fetchone()

# NEVER use string concatenation:
# cursor.execute(f"EXEC Proc_Student_Get @StudentID={student_id}")
```

### 8.4 XSS Prevention

#### 8.4.1 Template Auto-Escaping
```django
<!-- Django templates auto-escape by default -->
<p>{{ user_input }}</p>  <!-- Automatically escaped -->

<!-- To render HTML (use with caution): -->
<p>{{ trusted_html|safe }}</p>

<!-- Always validate and sanitize user input -->
```

### 8.5 CSRF Protection

#### 8.5.1 CSRF Token Usage
```django
<!-- All POST forms must include CSRF token -->
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>

<!-- AJAX requests must include CSRF token -->
<script>
$.ajax({
    url: '/api/endpoint/',
    method: 'POST',
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    },
    data: {...}
});
</script>
```

### 8.6 File Upload Security

#### 8.6.1 File Validation
```python
# File upload validation
ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file):
    # Check file extension
    ext = file.name.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file type")
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise ValidationError("File too large")
    
    # Validate MIME type
    import magic
    mime = magic.from_buffer(file.read(1024), mime=True)
    if mime not in ['application/pdf', 'image/jpeg', 'image/png']:
        raise ValidationError("Invalid file content")
    
    file.seek(0)  # Reset file pointer
    return True
```

### 8.7 Permission Validation

#### 8.7.1 Decorator-Based Permissions
```python
# decorators.py
from functools import wraps
from django.http import HttpResponseForbidden

def strict_permission_required(menu_url, action='view'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user has permission
            has_permission = check_user_permission(
                request.user_id,
                menu_url,
                action
            )
            
            if not has_permission:
                return HttpResponseForbidden(
                    "You don't have permission to access this resource"
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@strict_permission_required('/students/list/', 'view')
def view_students(request):
    # View logic
    pass
```

---


## 9. Deployment Guide

### 9.1 System Requirements

#### 9.1.1 Server Requirements
```
Operating System:
- Windows Server 2016 or later
- Linux (Ubuntu 20.04 LTS or later)

Hardware:
- CPU: 4+ cores (8+ recommended for production)
- RAM: 8GB minimum (16GB+ recommended)
- Storage: 100GB+ SSD
- Network: 100Mbps+ connection

Software:
- Python 3.13+
- SQL Server 2016 or later
- ODBC Driver 17 for SQL Server
- IIS or Nginx (for production)
```

#### 9.1.2 Database Requirements
```
SQL Server Edition:
- SQL Server 2016 or later
- Express Edition (for small deployments)
- Standard/Enterprise (for production)

Configuration:
- Mixed Mode Authentication
- TCP/IP enabled
- Default port: 1433
- Collation: SQL_Latin1_General_CP1_CI_AS
```

### 9.2 Installation Steps

#### 9.2.1 Environment Setup
```bash
# 1. Clone repository
git clone https://github.com/yourorg/shikshawave.git
cd shikshawave

# 2. Create virtual environment
python -m venv env

# 3. Activate virtual environment
# Windows:
env\Scripts\activate
# Linux:
source env/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install ODBC Driver
# Windows: Download from Microsoft
# Linux:
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

#### 9.2.2 Database Setup
```sql
-- 1. Create database
CREATE DATABASE ShikshaWave;
GO

-- 2. Create login and user
CREATE LOGIN ShikshaWave_Dev 
WITH PASSWORD = 'YourStrongPassword123!';
GO

USE ShikshaWave;
GO

CREATE USER ShikshaWave_Dev 
FOR LOGIN ShikshaWave_Dev;
GO

-- 3. Grant permissions
ALTER ROLE db_owner ADD MEMBER ShikshaWave_Dev;
GO

-- 4. Run table creation scripts
-- Execute all scripts in database/tables/ folder

-- 5. Run stored procedure scripts
-- Execute all scripts in database/procedures/ folder

-- 6. Insert master data
-- Execute initialization scripts
```

#### 9.2.3 Django Configuration
```python
# ShikshaWave/settings.py

# Update database settings
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'ShikshaWave',
        'USER': 'ShikshaWave_Dev',
        'PASSWORD': 'YourStrongPassword123!',
        'HOST': 'your-server-name\\instance',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}

# Update email settings
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

# Update secret key (generate new one)
SECRET_KEY = 'your-secret-key-here'

# Set debug to False for production
DEBUG = False

# Update allowed hosts
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

#### 9.2.4 Static Files Collection
```bash
# Collect static files
python manage.py collectstatic --noinput

# This will copy all static files to staticfiles/ directory
```

#### 9.2.5 Database Migrations
```bash
# Run migrations (if any)
python manage.py migrate

# Note: Most tables are managed=False
# They should already exist from SQL scripts
```

### 9.3 Production Deployment

#### 9.3.1 Using Gunicorn (Linux)
```bash
# Install Gunicorn
pip install gunicorn

# Create Gunicorn configuration
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "/var/log/shikshawave/error.log"
accesslog = "/var/log/shikshawave/access.log"
loglevel = "info"

# Run Gunicorn
gunicorn ShikshaWave.wsgi:application -c gunicorn_config.py
```

#### 9.3.2 Nginx Configuration
```nginx
# /etc/nginx/sites-available/shikshawave

upstream shikshawave {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Static files
    location /static/ {
        alias /path/to/shikshawave/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /path/to/shikshawave/media/;
        expires 7d;
    }
    
    # Proxy to Django
    location / {
        proxy_pass http://shikshawave;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # File upload size limit
    client_max_body_size 10M;
}
```

#### 9.3.3 Systemd Service (Linux)
```ini
# /etc/systemd/system/shikshawave.service

[Unit]
Description=ShikshaWave Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/shikshawave
Environment="PATH=/path/to/shikshawave/env/bin"
ExecStart=/path/to/shikshawave/env/bin/gunicorn \
    --config /path/to/gunicorn_config.py \
    ShikshaWave.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable shikshawave
sudo systemctl start shikshawave
sudo systemctl status shikshawave
```

#### 9.3.4 IIS Deployment (Windows)
```xml
<!-- web.config -->
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" 
           path="*" 
           verb="*" 
           modules="FastCgiModule" 
           scriptProcessor="C:\path\to\env\Scripts\python.exe|C:\path\to\env\Lib\site-packages\wfastcgi.py" 
           resourceType="Unspecified" 
           requireAccess="Script" />
    </handlers>
    <rewrite>
      <rules>
        <rule name="Static Files" stopProcessing="true">
          <match url="^static/.*" />
          <action type="Rewrite" url="{R:0}" />
        </rule>
        <rule name="Django Application" stopProcessing="true">
          <match url="(.*)" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
  <appSettings>
    <add key="WSGI_HANDLER" value="ShikshaWave.wsgi.application" />
    <add key="PYTHONPATH" value="C:\path\to\shikshawave" />
    <add key="DJANGO_SETTINGS_MODULE" value="ShikshaWave.settings" />
  </appSettings>
</configuration>
```

### 9.4 Monitoring & Maintenance

#### 9.4.1 Log Monitoring
```bash
# Application logs
tail -f /var/log/shikshawave/error.log
tail -f /var/log/shikshawave/access.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# System logs
journalctl -u shikshawave -f
```

#### 9.4.2 Database Maintenance
```sql
-- Regular maintenance tasks

-- 1. Update statistics
EXEC sp_updatestats;

-- 2. Rebuild indexes
ALTER INDEX ALL ON Student REBUILD;
ALTER INDEX ALL ON Payment REBUILD;
-- Repeat for all major tables

-- 3. Cleanup old sessions
DELETE FROM user_sessions 
WHERE expires_at < DATEADD(DAY, -7, GETDATE());

-- 4. Cleanup old OTP records
DELETE FROM OTPRecords 
WHERE expires_at < DATEADD(DAY, -1, GETDATE());

-- 5. Cleanup old email tracking
DELETE FROM EmailTracking 
WHERE Status = 'Sent' 
  AND CreatedAt < DATEADD(MONTH, -3, GETDATE());

-- 6. Backup database
BACKUP DATABASE ShikshaWave 
TO DISK = 'C:\Backups\ShikshaWave_Full.bak' 
WITH COMPRESSION, INIT;
```

#### 9.4.3 Performance Monitoring
```python
# Add monitoring middleware
# middleware.py

import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > 2.0:  # 2 seconds
            logger.warning(
                f"Slow request: {request.path} took {duration:.2f}s"
            )
        
        return response
```

#### 9.4.4 Backup Strategy
```bash
# Daily backup script
#!/bin/bash

# Database backup
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/shikshawave"

# Full database backup
sqlcmd -S localhost -U sa -P 'password' -Q \
  "BACKUP DATABASE ShikshaWave TO DISK='$BACKUP_DIR/db_$DATE.bak' WITH COMPRESSION"

# Application files backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /path/to/shikshawave

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /path/to/shikshawave/media

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.bak" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Upload to cloud storage (optional)
# aws s3 sync $BACKUP_DIR s3://your-bucket/backups/
```

### 9.5 Security Hardening

#### 9.5.1 SSL/TLS Configuration
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### 9.5.2 Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Fail2ban for brute force protection
sudo apt-get install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### 9.5.3 Database Security
```sql
-- Disable sa account
ALTER LOGIN sa DISABLE;

-- Create application-specific login
CREATE LOGIN ShikshaWave_App 
WITH PASSWORD = 'StrongPassword123!',
     CHECK_POLICY = ON,
     CHECK_EXPIRATION = ON;

-- Grant minimal permissions
USE ShikshaWave;
GRANT EXECUTE ON SCHEMA::dbo TO ShikshaWave_App;
GRANT SELECT, INSERT, UPDATE ON SCHEMA::dbo TO ShikshaWave_App;
-- Do NOT grant DELETE or DDL permissions

-- Enable encryption
ALTER DATABASE ShikshaWave 
SET ENCRYPTION ON;
```

### 9.6 Scaling Considerations

#### 9.6.1 Horizontal Scaling
```
Load Balancer (Nginx/HAProxy)
    ↓
┌───────────┬───────────┬───────────┐
│ App       │ App       │ App       │
│ Server 1  │ Server 2  │ Server 3  │
└───────────┴───────────┴───────────┘
    ↓           ↓           ↓
┌─────────────────────────────────────┐
│     Database Server (SQL Server)    │
│     - Read Replicas for reporting   │
│     - Always On Availability Groups │
└─────────────────────────────────────┘
```

#### 9.6.2 Caching Strategy
```python
# settings.py

# Redis cache for production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache session data
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

#### 9.6.3 Database Optimization
```sql
-- Create indexes for frequently queried columns
CREATE NONCLUSTERED INDEX IX_Student_SchoolID_ClassID 
ON Student(SchoolID, ClassID) 
INCLUDE (StudentCode, StudentName);

CREATE NONCLUSTERED INDEX IX_Payment_SchoolID_PaymentDate 
ON Payment(SchoolID, PaymentDate) 
INCLUDE (TotalAmount, PaymentMode);

CREATE NONCLUSTERED INDEX IX_StudentAttendance_Date 
ON StudentAttendance(SchoolID, AttendanceDate) 
INCLUDE (StudentID, Status);

-- Partition large tables
CREATE PARTITION FUNCTION PF_PaymentDate (DATE)
AS RANGE RIGHT FOR VALUES 
('2024-01-01', '2024-02-01', '2024-03-01', ...);

CREATE PARTITION SCHEME PS_PaymentDate
AS PARTITION PF_PaymentDate ALL TO ([PRIMARY]);

-- Apply partition to Payment table
CREATE TABLE Payment_Partitioned (
    -- columns
) ON PS_PaymentDate(PaymentDate);
```

---

## 10. Troubleshooting Guide

### 10.1 Common Issues

#### 10.1.1 Database Connection Issues
```
Error: "Login failed for user 'ShikshaWave_Dev'"

Solution:
1. Verify SQL Server is running
2. Check SQL Server Authentication mode (Mixed Mode)
3. Verify login credentials
4. Check firewall rules
5. Verify ODBC Driver installation

Test connection:
sqlcmd -S server\instance -U username -P password
```

#### 10.1.2 Email Sending Issues
```
Error: "SMTPAuthenticationError"

Solution:
1. Verify email credentials
2. Enable "Less secure app access" (Gmail)
3. Use App Password instead of regular password
4. Check SMTP server and port
5. Verify TLS/SSL settings

Test email:
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@email.com', ['to@email.com'])
```

#### 10.1.3 Static Files Not Loading
```
Error: 404 on static files

Solution:
1. Run collectstatic: python manage.py collectstatic
2. Verify STATIC_ROOT setting
3. Check web server configuration
4. Verify file permissions
5. Clear browser cache
```

#### 10.1.4 Session Timeout Issues
```
Error: "Session expired" too frequently

Solution:
1. Increase SESSION_COOKIE_AGE in settings.py
2. Check session cleanup middleware
3. Verify database session table
4. Check server time synchronization
```

### 10.2 Performance Issues

#### 10.2.1 Slow Page Load
```
Diagnosis:
1. Enable Django Debug Toolbar
2. Check database query count
3. Profile slow queries
4. Check network latency

Solutions:
1. Add database indexes
2. Optimize stored procedures
3. Implement caching
4. Use select_related() and prefetch_related()
5. Paginate large result sets
```

#### 10.2.2 High Database Load
```
Diagnosis:
1. Check SQL Server Activity Monitor
2. Identify long-running queries
3. Check for missing indexes
4. Review execution plans

Solutions:
1. Optimize queries
2. Add appropriate indexes
3. Update statistics
4. Consider read replicas
5. Implement query caching
```

---

## 11. Conclusion

### 11.1 Project Summary

ShikshaWave is a comprehensive, enterprise-grade School Management System that successfully addresses the complex needs of modern educational institutions. The system demonstrates:

**Technical Excellence:**
- Hybrid architecture leveraging Django and SQL Server
- Robust security with multi-factor authentication
- Scalable design supporting multiple schools
- Comprehensive API ecosystem
- Real-time notifications and communication

**Functional Completeness:**
- Complete student lifecycle management
- Integrated financial operations
- Advanced HR and payroll processing
- Examination and result management
- Communication and support systems

**Operational Efficiency:**
- Automated workflows reducing manual effort
- Real-time analytics and reporting
- Template-based document generation
- Bulk data import capabilities
- Email queue system for reliable delivery

### 11.2 Key Achievements

1. **Multi-Tenancy**: Complete data isolation for multiple schools
2. **Security**: Face recognition, OTP, URL encryption, RBAC
3. **Automation**: Automated fee calculation, salary processing, result computation
4. **Communication**: Integrated email, notifications, and ticketing
5. **Scalability**: Designed for horizontal and vertical scaling
6. **Customization**: Template-based receipts, certificates, and reports

### 11.3 Future Enhancements

**Planned Features:**
- Mobile application (iOS/Android)
- Parent portal with real-time updates
- Online examination system
- Library management module
- Transport management with GPS tracking
- Alumni management system
- AI-powered analytics and predictions
- Integration with payment gateways
- SMS gateway integration
- Biometric attendance integration

**Technical Improvements:**
- Microservices architecture migration
- GraphQL API implementation
- Real-time WebSocket notifications
- Progressive Web App (PWA)
- Machine learning for predictive analytics
- Blockchain for certificate verification

### 11.4 Support & Maintenance

**Documentation:**
- Complete API documentation
- Database schema documentation
- Deployment guides
- User manuals
- Video tutorials

**Support Channels:**
- Email: support@shikshawave.in
- Phone: +91-XXXXXXXXXX
- Ticketing system within application
- Knowledge base and FAQ

**Maintenance Schedule:**
- Daily: Automated backups
- Weekly: Log review and cleanup
- Monthly: Security updates
- Quarterly: Performance optimization
- Annually: Major version upgrades

### 11.5 License & Credits

**License:** Proprietary Software
**Version:** 2.0
**Last Updated:** 2024

**Development Team:**
- Project Lead: [Name]
- Backend Developers: [Names]
- Frontend Developers: [Names]
- Database Architects: [Names]
- QA Team: [Names]

**Technologies Used:**
- Django 5.2.5
- Python 3.13
- Microsoft SQL Server
- HTML5/CSS3/JavaScript
- Bootstrap (UI Framework)
- Chart.js (Data Visualization)

---

## Appendix

### A. Glossary

**RBAC**: Role-Based Access Control
**OTP**: One-Time Password
**SMTP**: Simple Mail Transfer Protocol
**CSRF**: Cross-Site Request Forgery
**XSS**: Cross-Site Scripting
**SQL Injection**: Database attack technique
**MFA**: Multi-Factor Authentication
**API**: Application Programming Interface
**AJAX**: Asynchronous JavaScript and XML
**JSON**: JavaScript Object Notation
**PDF**: Portable Document Format
**SMS**: Short Message Service

### B. Database Schema Diagram

```
[Refer to separate database schema documentation]
- Entity-Relationship Diagrams
- Table structures
- Stored procedure documentation
- Index definitions
```

### C. API Postman Collection

```
[Refer to separate Postman collection file]
- All API endpoints
- Request/Response examples
- Authentication examples
- Error handling examples
```

### D. Change Log

**Version 2.0 (Current)**
- Added notification system
- Implemented ticket management
- Enhanced dashboard analytics
- Added bulk import functionality
- Improved email queue system

**Version 1.5**
- Added examination module
- Implemented salary management
- Added template customization
- Enhanced security features

**Version 1.0**
- Initial release
- Basic student management
- Fee collection
- User authentication

---

**End of Documentation**

For the latest updates and detailed technical documentation, visit:
https://docs.shikshawave.in

© 2024 ShikshaWave. All rights reserved.
