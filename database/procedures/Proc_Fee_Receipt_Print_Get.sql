-- Procedure to get fee receipt data for printing with last 10 payments
CREATE OR ALTER PROCEDURE Proc_Fee_Receipt_Print_Get
    @ReceiptNumber NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StudentID INT;
    DECLARE @SchoolID INT;
    
    -- Get StudentID and SchoolID from the receipt
    SELECT @StudentID = EntityID, @SchoolID = SchoolID
    FROM Payment
    WHERE ReceiptNumber = @ReceiptNumber AND EntityType = 'Student' AND IsDeleted = 0;
    
    -- Return receipt details with student and school info
    SELECT 
        -- Receipt Info
        p.ReceiptNumber AS receipt_no,
        CONVERT(VARCHAR(20), p.PaymentDate, 106) AS date_of_submission,
        p.PaymentMode AS payment_mode,
        p.TotalAmount AS total_amount,
        p.PaidAmount AS paid_amount,
        (p.TotalAmount - p.PaidAmount) AS remaining_amount,
        p.FeeBreakdown AS fee_breakdown,
        p.PaymentMonth AS fees_month,
        p.TransactionRef AS transaction_ref,
        
        -- Student Info
        s.StudentCode AS student_code,
        s.FullName AS full_name,
        s.FatherName AS father_name,
        s.MotherName AS mother_name,
        
        -- Class Info
        c.ClassName AS class_name,
        sec.SectionName AS section_name,
        
        -- School Info
        sch.SchoolName AS school_name,
        sch.SchoolAddress AS school_address,
        sch.Phone AS school_phone,
        sch.Email AS school_email,
        sch.SchoolLogo AS school_logo
        
    FROM Payment p
    INNER JOIN Student s ON p.EntityID = s.StudentID
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN SchoolMaster sch ON p.SchoolID = sch.SchoolID
    WHERE p.ReceiptNumber = @ReceiptNumber 
      AND p.EntityType = 'Student' 
      AND p.IsDeleted = 0;
    
    -- Return last 10 fee payments for this student
    SELECT TOP 10
        p.ReceiptNumber,
        CONVERT(VARCHAR(20), p.PaymentDate, 106) AS PaymentDate,
        p.PaymentMonth,
        p.PaymentMode,
        p.TotalAmount,
        ISNULL(p.DiscountValue, 0) AS DiscountValue,
        p.PaidAmount
    FROM Payment p
    WHERE p.EntityID = @StudentID 
      AND p.EntityType = 'Student' 
      AND p.SchoolID = @SchoolID
      AND p.IsDeleted = 0
    ORDER BY p.PaymentDate DESC, p.CreatedAt DESC;
END
GO
