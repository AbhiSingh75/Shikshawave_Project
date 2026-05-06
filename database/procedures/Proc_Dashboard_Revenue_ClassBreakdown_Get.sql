-- Separate procedure for class breakdown only
CREATE OR ALTER PROCEDURE Proc_Dashboard_Revenue_ClassBreakdown_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @PaymentMode NVARCHAR(50) = NULL,
    @PaymentFor NVARCHAR(50) = NULL
AS
BEGIN
    DECLARE @StartDate DATE;
    DECLARE @EndDate DATE;
    
    IF @FromDate IS NULL AND @ToDate IS NULL
    BEGIN
        SET @StartDate = DATEADD(DAY, 1, EOMONTH(GETDATE(), -1));
        SET @EndDate = EOMONTH(GETDATE());
    END
    ELSE
    BEGIN
        SET @StartDate = @FromDate;
        SET @EndDate = @ToDate;
    END
    
    SELECT 
        c.ClassID,
        c.ClassName,
        COUNT(DISTINCT s.StudentID) AS TotalStudents,
        COUNT(DISTINCT CASE WHEN p.PaymentID IS NOT NULL THEN p.EntityID END) AS PaidStudents,
        COUNT(DISTINCT s.StudentID) - COUNT(DISTINCT CASE WHEN p.PaymentID IS NOT NULL THEN p.EntityID END) AS NotPaidStudents,
        ISNULL(SUM(p.PaidAmount + ISNULL(p.Discountvalue, 0)), 0) AS TotalCollected,
        ISNULL(SUM(p.TotalAmount - p.PaidAmount - ISNULL(p.Discountvalue, 0)), 0) AS TotalDue,
        ISNULL(SUM(p.Discountvalue), 0) AS TotalDiscount
    FROM ClassMaster c
    LEFT JOIN Student s ON c.ClassID = s.AdmissionClass AND s.IsDeleted = 0
    LEFT JOIN Payment p ON s.StudentID = p.EntityID AND p.IsDeleted = 0
        AND (@StartDate IS NULL OR p.PaymentDate >= @StartDate)
        AND (@EndDate IS NULL OR p.PaymentDate <= @EndDate)
        AND (@PaymentMode IS NULL OR p.PaymentMode = @PaymentMode)
        AND (@PaymentFor IS NULL OR p.PaymentFor = @PaymentFor)
    WHERE 
        c.SchoolID = @SchoolID
        AND (@ClassID IS NULL OR c.ClassID = @ClassID)
    GROUP BY c.ClassID, c.ClassName
    ORDER BY c.ClassID;
END;
GO
