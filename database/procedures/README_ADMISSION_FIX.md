# Admission Document & Fee Structure Fix

## Problem Fixed
1. **Email documents not matching preview/print** - Missing accurate student data
2. **Fee structure not saving correctly** - Wrong values in Student_Fee_Assignment table

## Solution

### Step 1: Run These SQL Procedures (IN ORDER)

Execute these 3 procedures in your SQL Server database:

```sql
-- 1. First, run this to get acknowledgment data
EXEC sp_executesql N'
-- File: Proc_Student_Acknowledgment_Get.sql
CREATE OR ALTER PROCEDURE Proc_Student_Acknowledgment_Get
    @StudentCode NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        s.StudentID, s.StudentCode, s.FullName AS student_name,
        s.Gender AS gender, s.DateOfBirth AS date_of_birth, s.Age AS age,
        s.BloodGroup AS blood_group, s.Category AS category, s.Religion AS religion,
        s.Nationality AS nationality, s.MotherTongue AS mother_tongue,
        s.StudentAadhaar AS student_aadhaar,
        s.PresentAddress AS present_address, s.PermanentAddress AS permanent_address,
        s.ParentMobile AS parent_mobile, s.AlternateNumber AS alternate_number, s.Email AS email,
        s.FatherName AS father_name, s.FatherOccupation AS father_occupation,
        s.FatherQualification AS father_qualification, s.FatherAadhaar AS father_aadhaar,
        s.FatherMobile AS father_mobile, s.MotherName AS mother_name,
        s.MotherOccupation AS mother_occupation, s.MotherQualification AS mother_qualification,
        s.MotherAadhaar AS mother_aadhaar, s.MotherMobile AS mother_mobile,
        s.GuardianName AS guardian_name, s.GuardianRelation AS guardian_relation,
        s.GuardianMobile AS guardian_mobile, s.LastSchool AS last_school,
        s.LastClass AS last_class, s.TCNumber AS tc_number,
        s.MediumOfInstruction AS medium_of_instruction,
        c.ClassName AS admission_class, sec.SectionName AS section,
        s.Stream AS stream, s.ModeOfAdmission AS mode_of_admission,
        CONVERT(VARCHAR(10), s.AdmissionDate, 120) AS admission_date,
        sch.SchoolName AS school_name, sch.SchoolLogo AS school_logo,
        dist.Geog_Name AS district_name, st.Geog_Name AS state_name, cnt.Geog_Name AS country_name,
        u.PasswordHash AS student_password,
        CONVERT(VARCHAR(10), GETDATE(), 120) AS current_date,
        FORMAT(GETDATE(), ''yyyy'') + ''-'' + FORMAT(DATEADD(YEAR, 1, GETDATE()), ''yy'') AS academic_year
    FROM Student s
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN SchoolMaster sch ON s.SchoolID = sch.SchoolID
    LEFT JOIN Geographical_Master dist ON s.District = dist.Geog_Id
    LEFT JOIN Geographical_Master st ON s.State = st.Geog_Id
    LEFT JOIN Geographical_Master cnt ON s.Country = cnt.Geog_Id
    LEFT JOIN UserMaster u ON s.StudentCode = u.UserCode
    WHERE s.StudentCode = @StudentCode AND ISNULL(s.IsDeleted, 0) = 0;
END
'

-- 2. Then, run this to get fee structure
EXEC sp_executesql N'
CREATE OR ALTER PROCEDURE Proc_Student_Fee_Structure_Get
    @StudentID INT = NULL,
    @StudentCode NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @ActualStudentID INT;
    
    IF @StudentCode IS NOT NULL
        SELECT @ActualStudentID = StudentID FROM Student WHERE StudentCode = @StudentCode AND ISNULL(IsDeleted, 0) = 0;
    ELSE
        SET @ActualStudentID = @StudentID;
    
    SELECT 
        sfa.FeeAssignmentID, sfa.StudentID, s.StudentCode, s.FullName AS student_name,
        sfa.FeeTypeId, ft.FeeTypeName AS fee_name,
        sfa.FeeAmount AS default_amount, sfa.DiscountPercentage AS discount_percentage,
        sfa.FinalAmount AS amount, sfa.FeeMonth, sfa.AssignedDate,
        sfa.SchoolId, sch.SchoolName AS school_name
    FROM Student_Fee_Assignment sfa
    INNER JOIN Student s ON sfa.StudentID = s.StudentID
    INNER JOIN FeeType_Master ft ON sfa.FeeTypeId = ft.FeeTypeId
    LEFT JOIN SchoolMaster sch ON sfa.SchoolId = sch.SchoolID
    WHERE sfa.StudentID = @ActualStudentID AND ISNULL(sfa.IsDeleted, 0) = 0
    ORDER BY sfa.AssignedDate DESC, ft.FeeTypeName;
END
'

-- 3. Finally, run this to get payment receipt data
EXEC sp_executesql N'
CREATE OR ALTER PROCEDURE Proc_Payment_Receipt_Get
    @ReceiptNumber NVARCHAR(50) = NULL,
    @StudentCode NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        p.PaymentID, p.ReceiptNumber AS receipt_number, p.TotalAmount AS total_amount,
        p.PaidAmount AS amount_paid, p.PaymentMode AS payment_mode,
        CONVERT(VARCHAR(20), p.PaymentDate, 120) AS payment_date,
        p.TransactionRef AS transaction_ref, p.FeeBreakdown AS fee_breakdown,
        s.StudentID, s.StudentCode AS student_code, s.FullName AS student_name,
        s.Gender AS gender, s.DateOfBirth AS date_of_birth, s.Age AS age,
        s.BloodGroup AS blood_group, s.Category AS category, s.Religion AS religion,
        s.Nationality AS nationality, s.MotherTongue AS mother_tongue,
        s.StudentAadhaar AS student_aadhaar,
        s.PresentAddress AS present_address, s.PermanentAddress AS permanent_address,
        s.ParentMobile AS parent_mobile, s.AlternateNumber AS alternate_number, s.Email AS email,
        s.FatherName AS father_name, s.FatherOccupation AS father_occupation,
        s.FatherMobile AS father_mobile, s.MotherName AS mother_name,
        s.MotherOccupation AS mother_occupation, s.MotherMobile AS mother_mobile,
        s.GuardianName AS guardian_name, s.GuardianRelation AS guardian_relation,
        s.GuardianMobile AS guardian_mobile, s.LastSchool AS last_school, s.LastClass AS last_class,
        c.ClassName AS admission_class, sec.SectionName AS section,
        s.Stream AS stream, s.ModeOfAdmission AS mode_of_admission,
        CONVERT(VARCHAR(10), s.AdmissionDate, 120) AS admission_date,
        sch.SchoolName AS school_name, sch.SchoolLogo AS school_logo
    FROM Payment p
    INNER JOIN Student s ON p.EntityID = s.StudentID AND p.EntityType = ''Student''
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN SchoolMaster sch ON p.SchoolID = sch.SchoolID
    WHERE (@ReceiptNumber IS NOT NULL AND p.ReceiptNumber = @ReceiptNumber)
       OR (@StudentCode IS NOT NULL AND s.StudentCode = @StudentCode)
    ORDER BY p.PaymentDate DESC;
END
'
```

### Step 2: Verify Procedures Created

```sql
-- Check if procedures exist
SELECT name FROM sys.procedures 
WHERE name IN ('Proc_Student_Acknowledgment_Get', 'Proc_Student_Fee_Structure_Get', 'Proc_Payment_Receipt_Get')
```

### Step 3: Test the Procedures

```sql
-- Test with a student code
DECLARE @TestStudentCode NVARCHAR(20) = 'STU001'  -- Replace with actual student code

-- Test acknowledgment
EXEC Proc_Student_Acknowledgment_Get @StudentCode = @TestStudentCode

-- Test fee structure
EXEC Proc_Student_Fee_Structure_Get @StudentCode = @TestStudentCode

-- Test payment receipt
EXEC Proc_Payment_Receipt_Get @StudentCode = @TestStudentCode
```

## What Changed in Code

### 1. Fee Structure Fix
- Fees are now ALWAYS inserted directly into `Student_Fee_Assignment` table
- Exact values from form (amount, discount%, final amount) are saved
- No dependency on stored procedure JSON parsing

### 2. Document Data Fix
- After payment, system calls procedures to get accurate data from database
- Email PDFs use the same accurate data as preview/print
- All student fields are included (personal, parent, address, etc.)

## How It Works Now

1. **Form Submission** → Student data saved to database
2. **Fee Assignment** → Direct insert with exact form values
3. **Payment** → Calls `Proc_Student_Acknowledgment_Get` and `Proc_Student_Fee_Structure_Get`
4. **Email Queue** → Receives complete accurate data from database
5. **PDF Generation** → Uses same data as preview/print

## Verify Fix Working

After running procedures, submit a new admission and check:

1. **Fee Table**: 
   ```sql
   SELECT * FROM Student_Fee_Assignment WHERE StudentCode = 'YOUR_STUDENT_CODE'
   ```
   Should show exact amounts and discounts from form

2. **Email Documents**: Should match preview/print exactly

3. **Acknowledgment**: Should have all student details

4. **Receipt**: Should have accurate fee breakdown
