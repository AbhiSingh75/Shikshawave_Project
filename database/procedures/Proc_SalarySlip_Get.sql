DROP PROCEDURE IF EXISTS dbo.Proc_SalarySlip_Get;
GO

CREATE PROCEDURE dbo.Proc_SalarySlip_Get
    @PaymentID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get basic salary slip info
    SELECT 
        esp.PaymentID,
        esp.EmployeeID,
        e.EmployeeCode,
        e.EmployeeName,
        e.Email AS EmployeeEmail,
        p.ProfileName AS Designation,
        esp.PaymentMonth AS SalaryMonth,
        esp.GrossSalary,
        esp.TotalDeductions,
        esp.NetSalary,
        esp.PaymentStatus,
        esp.PaymentDate,
        esp.PaymentMode,
        esp.ReferenceNo,
        esp.SalaryReferenceId,
        esp.Remarks,
        s.SchoolName,
        s.SchoolCode,
        s.Address AS SchoolAddress,
        s.Phone AS SchoolPhone,
        s.Email AS SchoolEmail,
        s.SchoolLogo,
        'XXXX-XXXX-' + RIGHT('0000' + CAST(e.EmployeeID AS VARCHAR), 4) AS BankAccount,
        e.EmployeeCode + '@upi' AS UpiId,
        '1234-5678-' + RIGHT('0000' + CAST(e.EmployeeID AS VARCHAR), 4) AS UanNumber
    FROM dbo.EmployeeSalaryPayment esp
    INNER JOIN dbo.EmployeeMaster e ON esp.EmployeeID = e.EmployeeID
    INNER JOIN dbo.ProfileMaster p ON e.ProfileID = p.ProfileID
    INNER JOIN dbo.SchoolMaster s ON e.SchoolID = s.SchoolID
    WHERE esp.PaymentID = @PaymentID;
    
    -- Get earnings breakdown
    SELECT 
        scm.ComponentName,
        scm.ComponentType,
        esb.Amount
    FROM dbo.EmployeeSalaryPayment esp
    INNER JOIN dbo.EmployeeSalaryBreakup esb ON esp.EmployeeID = esb.EmployeeID
    INNER JOIN dbo.SalaryComponentMaster scm ON esb.ComponentID = scm.ComponentID
    WHERE esp.PaymentID = @PaymentID
        AND scm.ComponentType = 'Earning'
        AND esb.IsActive = 1
    ORDER BY scm.DisplayOrder;
    
    -- Get deductions breakdown
    SELECT 
        scm.ComponentName,
        scm.ComponentType,
        esb.Amount
    FROM dbo.EmployeeSalaryPayment esp
    INNER JOIN dbo.EmployeeSalaryBreakup esb ON esp.EmployeeID = esb.EmployeeID
    INNER JOIN dbo.SalaryComponentMaster scm ON esb.ComponentID = scm.ComponentID
    WHERE esp.PaymentID = @PaymentID
        AND scm.ComponentType = 'Deduction'
        AND esb.IsActive = 1
    ORDER BY scm.DisplayOrder;
END;
GO
