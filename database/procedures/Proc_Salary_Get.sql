DROP PROCEDURE IF EXISTS dbo.Proc_Salary_Get;
GO

CREATE PROCEDURE dbo.Proc_Salary_Get
    @SchoolID INT,
    @Month VARCHAR(7),
    @EmployeeID INT = NULL,
    @Search VARCHAR(100) = NULL
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
        esp.PaymentMonth,
        esp.GrossSalary,
        esp.TotalDeductions,
        esp.NetSalary,
        esp.PaymentStatus,
        esp.PaymentDate,
        esp.PaymentMode,
        esp.ReferenceNo AS TransactionReference,
        esp.SalaryReferenceId
    FROM dbo.EmployeeSalaryPayment esp
    INNER JOIN dbo.EmployeeMaster u ON esp.EmployeeID = u.EmployeeID
    INNER JOIN dbo.ProfileMaster pf ON u.ProfileID = pf.ProfileID
    WHERE esp.SchoolID = @SchoolID 
        AND esp.PaymentMonth = @Month
        AND esp.IsDeleted = 0
        AND (@EmployeeID IS NULL OR u.EmployeeID = @EmployeeID)
        AND (@Search IS NULL OR u.EmployeeName LIKE '%' + @Search + '%' OR u.EmployeeCode LIKE '%' + @Search + '%')
    ORDER BY u.EmployeeName;

END
GO
