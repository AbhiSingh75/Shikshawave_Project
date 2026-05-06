DROP PROCEDURE IF EXISTS dbo.Proc_Employee_Individual_Salary_Get;
GO

CREATE PROCEDURE dbo.Proc_Employee_Individual_Salary_Get
    @SchoolID INT,
    @EmployeeID INT,
    @Year INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        esp.PaymentID,
        u.EmployeeID as EmployeeID,
        u.EmployeeCode,
        u.EmployeeName as EmployeeName,
        u.Email,
        pf.ProfileName as Designation,
        DATENAME(MONTH, DATEFROMPARTS(esp.PaymentYear, esp.PaymentMonth, 1)) 
        + ' ' + CAST(esp.PaymentYear AS VARCHAR(4)) AS PaymentMonth,
        esp.GrossSalary,
        esp.TotalDeductions,
        esp.NetSalary,
        esp.PaymentStatus,
        esp.PaymentDate,
        esp.PaymentMode,
        esp.ReferenceNo AS TransactionReference,
        esp.SalaryReferenceId
    FROM dbo.EmployeeSalaryPayment esp
    INNER JOIN dbo.EmployeeMaster u ON esp.EmployeeID = u.EmployeeID AND esp.SchoolID = u.SchoolID
    LEFT JOIN ProfileMaster AS pf ON u.ProfileId = pf.ProfileID
    WHERE esp.SchoolID = @SchoolID 
        AND u.EmployeeID = @EmployeeID
        AND (@Year IS NULL OR esp.PaymentYear = @Year)
    ORDER BY esp.PaymentYear DESC, esp.PaymentMonth DESC;

END
GO
