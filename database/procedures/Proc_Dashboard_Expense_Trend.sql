CREATE OR ALTER PROCEDURE Proc_Dashboard_Expense_Trend
    @SchoolID INT,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @EmploymentType VARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @FromYear INT, @FromMonth INT, @ToYear INT, @ToMonth INT;
    
    IF @FromDate IS NULL
    BEGIN
        SET @FromDate = DATEADD(MONTH, -5, GETDATE());
    END
    
    IF @ToDate IS NULL
    BEGIN
        SET @ToDate = GETDATE();
    END
    
    SET @FromYear = YEAR(@FromDate);
    SET @FromMonth = MONTH(@FromDate);
    SET @ToYear = YEAR(@ToDate);
    SET @ToMonth = MONTH(@ToDate);
    
    SELECT 
        FORMAT(DATEFROMPARTS(esp.PaymentYear, esp.PaymentMonth, 1), 'MMM yyyy') AS MonthYear,
        esp.PaymentMonth AS Month,
        esp.PaymentYear AS Year,
        SUM(esp.GrossSalary) AS TotalExpense,
        SUM(CASE WHEN esp.PaymentStatus = 'Paid' THEN esp.NetSalary ELSE 0 END) AS PaidAmount,
        SUM(CASE WHEN esp.PaymentStatus != 'Paid' THEN esp.NetSalary ELSE 0 END) AS PendingAmount
    FROM EmployeeSalaryPayment esp
    INNER JOIN UserMaster um ON esp.EmployeeID = um.UserID
    WHERE esp.SchoolID = @SchoolID
    AND esp.IsDeleted = 0
    AND (esp.PaymentYear > @FromYear OR (esp.PaymentYear = @FromYear AND esp.PaymentMonth >= @FromMonth))
    AND (esp.PaymentYear < @ToYear OR (esp.PaymentYear = @ToYear AND esp.PaymentMonth <= @ToMonth))
    AND (@EmploymentType IS NULL OR um.EmploymentType = @EmploymentType)
    GROUP BY esp.PaymentYear, esp.PaymentMonth
    ORDER BY esp.PaymentYear, esp.PaymentMonth;
END
