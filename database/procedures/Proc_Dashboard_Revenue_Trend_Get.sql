-- Separate procedure for monthly trend using PaymentMonth column
CREATE OR ALTER PROCEDURE Proc_Dashboard_Revenue_Trend_Get
    @SchoolID INT,
    @ClassID INT = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @PaymentMode NVARCHAR(50) = NULL,
    @PaymentFor NVARCHAR(50) = NULL
AS
BEGIN
    DECLARE @TrendStartDate DATE;
    DECLARE @TrendEndDate DATE;
    
    IF @FromDate IS NULL AND @ToDate IS NULL
    BEGIN
        SET @TrendStartDate = DATEADD(MONTH, -6, GETDATE());
        SET @TrendEndDate = GETDATE();
    END
    ELSE
    BEGIN
        SET @TrendStartDate = @FromDate;
        SET @TrendEndDate = @ToDate;
    END
    
    -- Generate all months in the date range
    ;WITH MonthSeries AS (
        SELECT DATEFROMPARTS(YEAR(@TrendStartDate), MONTH(@TrendStartDate), 1) AS MonthDate
        UNION ALL
        SELECT DATEADD(MONTH, 1, MonthDate)
        FROM MonthSeries
        WHERE DATEADD(MONTH, 1, MonthDate) <= DATEFROMPARTS(YEAR(@TrendEndDate), MONTH(@TrendEndDate), 1)
    )
    SELECT 
        FORMAT(m.MonthDate, 'MMM yyyy') AS MonthYear,
        MONTH(m.MonthDate) AS Month,
        YEAR(m.MonthDate) AS Year,
        ISNULL(SUM(p.PaidAmount + ISNULL(p.Discountvalue, 0)), 0) AS Revenue,
        ISNULL(SUM(CASE WHEN p.PaymentFor = 'Admission' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS AdmissionRevenue,
        ISNULL(SUM(CASE WHEN p.PaymentFor = 'Fee' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS FeeRevenue,
        ISNULL(SUM(p.Discountvalue), 0) AS Discount
    FROM MonthSeries m
    LEFT JOIN (
        SELECT p.*, s.AdmissionClass
        FROM Payment p
        INNER JOIN Student s ON p.EntityID = s.StudentID AND s.IsDeleted = 0
        WHERE p.IsDeleted = 0
            AND (@SchoolID IS NULL OR p.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR s.AdmissionClass = @ClassID)
            AND (@PaymentMode IS NULL OR p.PaymentMode = @PaymentMode)
            AND (@PaymentFor IS NULL OR p.PaymentFor = @PaymentFor)
    ) p ON FORMAT(CAST(Left(p.PaymentMonth,4)+'-'+Right(p.PaymentMonth,2)+'-01' AS DATE), 'yyyyMM') = FORMAT(m.MonthDate, 'yyyyMM')
    GROUP BY m.MonthDate
    ORDER BY m.MonthDate
    OPTION (MAXRECURSION 0);
END;
GO
