-- Procedure to get payment receipt with complete information
CREATE OR ALTER PROCEDURE Proc_Payment_Receipt_Get
    @ReceiptNumber NVARCHAR(50) = NULL,
    @StudentCode NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get payment details
    SELECT 
        p.PaymentID,
        p.ReceiptNumber AS receipt_number,
        p.TotalAmount AS total_amount,
        p.PaidAmount AS amount_paid,
        p.PaymentMode AS payment_mode,
        CONVERT(VARCHAR(20), p.PaymentDate, 120) AS payment_date,
        p.TransactionRef AS transaction_ref,
        p.FeeBreakdown AS fee_breakdown,
        
        -- Student Info
        s.StudentID,
        s.StudentCode AS student_code,
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
        
        -- Parent Info
        s.FatherName AS father_name,
        s.FatherOccupation AS father_occupation,
        s.FatherMobile AS father_mobile,
        s.MotherName AS mother_name,
        s.MotherOccupation AS mother_occupation,
        s.MotherMobile AS mother_mobile,
        s.GuardianName AS guardian_name,
        s.GuardianRelation AS guardian_relation,
        s.GuardianMobile AS guardian_mobile,
        
        -- Previous School
        s.LastSchool AS last_school,
        s.LastClass AS last_class,
        
        -- Admission Info
        c.ClassName AS admission_class,
        sec.SectionName AS section,
        s.Stream AS stream,
        s.ModeOfAdmission AS mode_of_admission,
        CONVERT(VARCHAR(10), s.AdmissionDate, 120) AS admission_date,
        
        -- School Info
        sch.SchoolName AS school_name,
        sch.SchoolLogo AS school_logo
        
    FROM Payment p
    INNER JOIN Student s ON p.EntityID = s.StudentID AND p.EntityType = 'Student'
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN SchoolMaster sch ON p.SchoolID = sch.SchoolID
    WHERE (@ReceiptNumber IS NOT NULL AND p.ReceiptNumber = @ReceiptNumber)
       OR (@StudentCode IS NOT NULL AND s.StudentCode = @StudentCode)
    ORDER BY p.PaymentDate DESC;
END
GO
