DROP PROCEDURE IF EXISTS dbo.Proc_SalaryRelease_Generate;
GO

CREATE PROCEDURE dbo.Proc_SalaryRelease_Generate
    @SchoolID INT,
    @SalaryMonth VARCHAR(7),
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Check if already generated
    IF EXISTS (
        SELECT 1 FROM dbo.EmployeeSalaryPayment 
        WHERE SchoolID = @SchoolID AND PaymentMonth = @SalaryMonth AND IsDeleted = 0
    )
    BEGIN
        SELECT 'FAILED' as Status, 'Salary records already generated for this month' as Message;
        RETURN;
    END

    -- Generate salary payment records for all employees
    INSERT INTO dbo.EmployeeSalaryPayment (
        SchoolID,
        EmployeeID,
        PaymentMonth,
        GrossSalary,
        TotalDeductions,
        NetSalary,
        PaymentStatus,
        CreatedBy,
        CreatedAt,
        IsDeleted
    )
    SELECT 
        @SchoolID,
        u.EmployeeID,
        @SalaryMonth,
        ISNULL(SUM(CASE WHEN sc.ComponentType = 'Earning' THEN esb.Amount ELSE 0 END), 0),
        ISNULL(SUM(CASE WHEN sc.ComponentType = 'Deduction' THEN esb.Amount ELSE 0 END), 0),
        ISNULL(SUM(CASE WHEN sc.ComponentType = 'Earning' THEN esb.Amount ELSE 0 END), 0) - 
        ISNULL(SUM(CASE WHEN sc.ComponentType = 'Deduction' THEN esb.Amount ELSE 0 END), 0),
        'Pending',
        @UserID,
        GETDATE(),
        0
    FROM dbo.EmployeeMaster u
    LEFT JOIN dbo.EmployeeSalaryBreakup esb ON u.EmployeeID = esb.EmployeeID AND esb.IsDeleted = 0
    LEFT JOIN dbo.SalaryComponentMaster sc ON esb.ComponentID = sc.ComponentID
    WHERE u.SchoolID = @SchoolID 
        AND u.IsDeleted = 0
    GROUP BY u.EmployeeID;

    SELECT 'SUCCESS' as Status, 'Salary records generated successfully' as Message;

END
GO
