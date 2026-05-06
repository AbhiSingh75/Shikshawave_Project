CREATE OR ALTER PROCEDURE dbo.Proc_Salary_Pay
    @PaymentID INT,
    @PaymentDate DATE,
    @PaymentMode VARCHAR(50),
    @TransactionRef VARCHAR(100) = NULL,
    @Remarks VARCHAR(500) = NULL,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @SalaryReferenceId VARCHAR(50);
    DECLARE @SchoolID INT, @EmployeeID INT, @PaymentMonth VARCHAR(7);

    -- Get payment details
    SELECT @SchoolID = SchoolID, @EmployeeID = EmployeeID, @PaymentMonth = PaymentMonth
    FROM dbo.EmployeeSalaryPayment
    WHERE PaymentID = @PaymentID;

    -- Generate unique SalaryReferenceId: SAL-SchoolID-EmployeeID-YYYYMM-PaymentID
    SET @SalaryReferenceId = CONCAT('SAL-', @SchoolID, '-', @EmployeeID, '-', REPLACE(@PaymentMonth, '-', ''), '-', @PaymentID);

    -- Update EmployeeSalaryPayment record
    UPDATE dbo.EmployeeSalaryPayment
    SET 
        SalaryReferenceId = @SalaryReferenceId,
        PaymentDate = @PaymentDate,
        PaymentMode = @PaymentMode,
        ReferenceNo = @TransactionRef,
        PaymentStatus = 'Paid',
        Remarks = @Remarks,
        UpdatedBy = @UserID,
        UpdatedAt = GETDATE()
    WHERE PaymentID = @PaymentID;

    SELECT 'SUCCESS' as Status, 'Salary paid successfully' as Message;

END
GO
