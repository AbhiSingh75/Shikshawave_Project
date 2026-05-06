CREATE OR ALTER PROCEDURE Proc_Dashboard_Expense_Get
    @SchoolID INT,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @EmploymentType VARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @FromYear INT, @FromMonth INT, @ToYear INT, @ToMonth INT;
    
    IF @FromDate IS NOT NULL
    BEGIN
        SET @FromYear = YEAR(@FromDate);
        SET @FromMonth = MONTH(@FromDate);
    END
    
    IF @ToDate IS NOT NULL
    BEGIN
        SET @ToYear = YEAR(@ToDate);
        SET @ToMonth = MONTH(@ToDate);
    END
    
    SELECT 
        COUNT(DISTINCT esp.EmployeeID) AS TotalEmployees,
        SUM(esp.GrossSalary) AS TotalExpense,
        SUM(CASE WHEN esp.PaymentStatus = 'Paid' THEN esp.NetSalary ELSE 0 END) AS TotalPaid,
        SUM(CASE WHEN esp.PaymentStatus != 'Paid' THEN esp.NetSalary ELSE 0 END) AS TotalPending,
        SUM(CASE WHEN um.EmploymentType = 'Permanent' THEN esp.GrossSalary ELSE 0 END) AS PermanentExpense,
        SUM(CASE WHEN um.EmploymentType = 'Contract' THEN esp.GrossSalary ELSE 0 END) AS ContractExpense,
        SUM(CASE WHEN um.EmploymentType = 'Guest' THEN esp.GrossSalary ELSE 0 END) AS GuestExpense,
        COUNT(DISTINCT CASE WHEN esp.PaymentStatus = 'Paid' THEN esp.EmployeeID END) AS PaidEmployees,
        COUNT(DISTINCT CASE WHEN esp.PaymentStatus != 'Paid' THEN esp.EmployeeID END) AS UnpaidEmployees
    FROM EmployeeSalaryPayment esp
    INNER JOIN UserMaster um ON esp.EmployeeID = um.UserID
    WHERE esp.SchoolID = @SchoolID
    AND esp.IsDeleted = 0
    AND (@FromYear IS NULL OR (esp.PaymentYear > @FromYear OR (esp.PaymentYear = @FromYear AND esp.PaymentMonth >= @FromMonth)))
    AND (@ToYear IS NULL OR (esp.PaymentYear < @ToYear OR (esp.PaymentYear = @ToYear AND esp.PaymentMonth <= @ToMonth)))
    AND (@EmploymentType IS NULL OR um.EmploymentType = @EmploymentType);
END
