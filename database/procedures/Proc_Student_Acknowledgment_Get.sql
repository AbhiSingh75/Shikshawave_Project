-- Procedure to get complete student acknowledgment information
CREATE OR ALTER PROCEDURE Proc_Student_Acknowledgment_Get
    @StudentCode NVARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        -- Basic Student Info
        s.StudentID,
        s.StudentCode,
        s.FullName AS student_name,
        s.Gender AS gender,
        s.DateOfBirth AS date_of_birth,
        s.Age AS age,
        s.BloodGroup AS blood_group,
        s.Category AS category,
        s.Religion AS religion,
        s.Nationality AS nationality,
        s.MotherTongue AS mother_tongue,
        s.StudentAadhaar AS student_aadhaar,
        
        -- Contact Info
        s.PresentAddress AS present_address,
        s.PermanentAddress AS permanent_address,
        s.ParentMobile AS parent_mobile,
        s.AlternateNumber AS alternate_number,
        s.Email AS email,
        
        -- Parent/Guardian Info
        s.FatherName AS father_name,
        s.FatherOccupation AS father_occupation,
        s.FatherQualification AS father_qualification,
        s.FatherAadhaar AS father_aadhaar,
        s.FatherMobile AS father_mobile,
        s.MotherName AS mother_name,
        s.MotherOccupation AS mother_occupation,
        s.MotherQualification AS mother_qualification,
        s.MotherAadhaar AS mother_aadhaar,
        s.MotherMobile AS mother_mobile,
        s.GuardianName AS guardian_name,
        s.GuardianRelation AS guardian_relation,
        s.GuardianMobile AS guardian_mobile,
        
        -- Previous School
        s.LastSchool AS last_school,
        s.LastClass AS last_class,
        s.TCNumber AS tc_number,
        s.MediumOfInstruction AS medium_of_instruction,
        
        -- Admission Info
        c.ClassName AS admission_class,
        sec.SectionName AS section,
        s.Stream AS stream,
        s.ModeOfAdmission AS mode_of_admission,
        CONVERT(VARCHAR(10), s.AdmissionDate, 120) AS admission_date,
        
        -- School Info
        sch.SchoolName AS school_name,
        sch.SchoolLogo AS school_logo,
        
        -- Location Info
        dist.Geog_Name AS district_name,
        st.Geog_Name AS state_name,
        cnt.Geog_Name AS country_name,
        
        -- School Contact
        sch.Phone AS school_phone,
        sch.Email AS school_email,
        sch.Address AS school_address,
        sch.Website AS school_website,
        
        -- Payment Info (latest admission payment)
        p.ReceiptNumber AS receipt_number,
        CONVERT(VARCHAR(20), p.PaymentDate, 120) AS payment_date,
        p.PaymentMode AS payment_mode,
        p.PaidAmount AS amount_paid,
        p.TransactionRef AS transaction_ref,
        
        -- Student Portal Access
        s.StudentCode AS login_username,
        sch.Website AS portal_url,
        
        -- Current Date
        CONVERT(VARCHAR(10), GETDATE(), 120) AS current_date,
        FORMAT(GETDATE(), 'yyyy') + '-' + FORMAT(DATEADD(YEAR, 1, GETDATE()), 'yy') AS academic_year
        
    FROM Student s
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN SchoolMaster sch ON s.SchoolID = sch.SchoolID
    LEFT JOIN Geographical_Master dist ON s.District = dist.Geog_Id
    LEFT JOIN Geographical_Master st ON s.State = st.Geog_Id
    LEFT JOIN Geographical_Master cnt ON s.Country = cnt.Geog_Id
    LEFT JOIN (
        SELECT TOP 1 ReceiptNumber, PaymentDate, PaymentMode, PaidAmount, TransactionRef, EntityID
        FROM Payment
        WHERE PaymentFor = 'Admission' AND EntityType = 'Student' AND ISNULL(IsDeleted, 0) = 0
        ORDER BY PaymentDate DESC
    ) p ON p.EntityID = s.StudentID
    WHERE s.StudentCode = @StudentCode
      AND ISNULL(s.IsDeleted, 0) = 0;
    
    -- Get admission instructions
    SELECT InstructionTitle, InstructionText, DisplayOrder
    FROM AdmissionInstructions
    WHERE SchoolID = (SELECT SchoolID FROM Student WHERE StudentCode = @StudentCode)
      AND IsActive = 1 AND ISNULL(IsDeleted, 0) = 0
    ORDER BY DisplayOrder;
    
    -- Get uploaded documents
    SELECT DocumentType, DocumentName
    FROM StudentDocuments
    WHERE StudentID = (SELECT StudentID FROM Student WHERE StudentCode = @StudentCode)
      AND ISNULL(IsDeleted, 0) = 0
    ORDER BY UploadDate;
    
    -- Get fee structure with total
    SELECT ft.FeeTypeName, sfa.FeeAmount, sfa.DiscountPercentage, sfa.FinalAmount
    FROM Student_Fee_Assignment sfa
    JOIN FeeType_Master ft ON sfa.FeeTypeId = ft.FeeTypeId
    WHERE sfa.StudentID = (SELECT StudentID FROM Student WHERE StudentCode = @StudentCode)
      AND ISNULL(sfa.IsDeleted, 0) = 0
    ORDER BY ft.FeeTypeName;
    
    -- Get total fee amount
    SELECT SUM(sfa.FinalAmount) AS total_amount
    FROM Student_Fee_Assignment sfa
    WHERE sfa.StudentID = (SELECT StudentID FROM Student WHERE StudentCode = @StudentCode)
      AND ISNULL(sfa.IsDeleted, 0) = 0;
END
GO
