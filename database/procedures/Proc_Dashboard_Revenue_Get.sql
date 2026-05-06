-- =============================================
-- Stored Procedure: Proc_Dashboard_Revenue_Get
-- Description: Get revenue/fee statistics using Payment table
-- Author: ShikshaWave Team
-- Created: 2024
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Revenue_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @PaymentMode NVARCHAR(50) = NULL,
    @PaymentFor NVARCHAR(50) = NULL
AS
BEGIN
    BEGIN TRY
        -- Get overall revenue statistics
        SELECT 
            ISNULL(SUM(p.PaidAmount + ISNULL(p.Discountvalue, 0)), 0) AS TotalRevenue,
            COUNT(DISTINCT p.PaymentID) AS TotalTransactions,
            COUNT(DISTINCT p.EntityID) AS TotalStudentsPaid,
            ISNULL(SUM(CASE WHEN p.PaymentMode = 'Cash' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS CashRevenue,
            ISNULL(SUM(CASE WHEN p.PaymentMode = 'Online' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS OnlineRevenue,
            ISNULL(SUM(CASE WHEN p.PaymentMode = 'Cheque' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS ChequeRevenue,
            ISNULL(SUM(CASE WHEN p.PaymentMode = 'Card' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS CardRevenue,
            ISNULL(SUM(p.TotalAmount - p.PaidAmount - ISNULL(p.Discountvalue, 0)), 0) AS TotalPending,
            ISNULL(SUM(CASE WHEN p.PaymentFor = 'Admission' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS AdmissionRevenue,
            ISNULL(SUM(CASE WHEN p.PaymentFor = 'Fee' THEN p.PaidAmount + ISNULL(p.Discountvalue, 0) ELSE 0 END), 0) AS FeeRevenue,
            ISNULL(SUM(p.Discountvalue), 0) AS TotalDiscount
        FROM Payment p
        WHERE 
            p.IsDeleted = 0
            AND (@SchoolID IS NULL OR p.SchoolID = @SchoolID)
            AND (@FromDate IS NULL OR p.PaymentDate >= @FromDate)
            AND (@ToDate IS NULL OR p.PaymentDate <= @ToDate)
            AND (@PaymentMode IS NULL OR p.PaymentMode = @PaymentMode)
            AND (@PaymentFor IS NULL OR p.PaymentFor = @PaymentFor);
            
        -- Get class-wise revenue breakdown (default current month if no date filter)
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
        INNER JOIN Student s ON c.ClassID = s.AdmissionClass AND s.IsDeleted = 0
        LEFT JOIN Payment p ON s.StudentID = p.EntityID AND p.IsDeleted = 0
            AND (@StartDate IS NULL OR p.PaymentDate >= @StartDate)
            AND (@EndDate IS NULL OR p.PaymentDate <= @EndDate)
            AND (@PaymentFor IS NULL OR p.PaymentFor = @PaymentFor)
        WHERE 
            c.SchoolID = @SchoolID
            AND (@ClassID IS NULL OR c.ClassID = @ClassID)
        GROUP BY c.ClassID, c.ClassName
        ORDER BY c.ClassID;
        
        -- Get monthly revenue trend (default last 6 months if no date filter)
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
        
        SELECT 
            FORMAT(p.PaymentDate, 'MMM yyyy') AS MonthYear,
            MONTH(p.PaymentDate) AS Month,
            YEAR(p.PaymentDate) AS Year,
            ISNULL(SUM(p.PaidAmount + ISNULL(p.Discountvalue, 0)), 0) AS Revenue,
            ISNULL(SUM(p.Discountvalue), 0) AS Discount
        FROM Payment p
        WHERE 
            p.IsDeleted = 0
            AND (@SchoolID IS NULL OR p.SchoolID = @SchoolID)
            AND (@TrendStartDate IS NULL OR p.PaymentDate >= @TrendStartDate)
            AND (@TrendEndDate IS NULL OR p.PaymentDate <= @TrendEndDate)
            AND (@PaymentFor IS NULL OR p.PaymentFor = @PaymentFor)
        GROUP BY FORMAT(p.PaymentDate, 'MMM yyyy'), MONTH(p.PaymentDate), YEAR(p.PaymentDate)
        ORDER BY YEAR(p.PaymentDate), MONTH(p.PaymentDate);
        
    END TRY
    BEGIN CATCH
        SELECT 
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_MESSAGE() AS ErrorMessage;
    END CATCH
END;
GO
