-- Test script for Proc_Dashboard_Revenue_Get
-- Replace @SchoolID with your actual SchoolID

DECLARE @SchoolID INT = 1; -- Change this to your SchoolID

-- Test 1: Run without any filters (should default to current month for class breakdown)
PRINT '========== Test 1: No Filters (Current Month Default) ==========';
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = @SchoolID,
    @ClassID = NULL,
    @FromDate = NULL,
    @ToDate = NULL,
    @PaymentMode = NULL,
    @PaymentFor = NULL;

PRINT '';
PRINT '========== Test 2: Check Payment Table Data ==========';
-- Check if Payment table has data
SELECT 
    COUNT(*) AS TotalPayments,
    MIN(PaymentDate) AS EarliestPayment,
    MAX(PaymentDate) AS LatestPayment,
    COUNT(DISTINCT EntityID) AS UniqueStudents
FROM Payment 
WHERE IsDeleted = 0 AND SchoolID = @SchoolID;

PRINT '';
PRINT '========== Test 3: Check Student-Class Mapping ==========';
-- Check if students are mapped to classes
SELECT 
    c.ClassID,
    c.ClassName,
    COUNT(s.StudentID) AS StudentCount
FROM ClassMaster c
LEFT JOIN Student s ON c.ClassID = s.AdmissionClass AND s.IsDeleted = 0
WHERE c.SchoolID = @SchoolID
GROUP BY c.ClassID, c.ClassName
ORDER BY c.ClassID;

PRINT '';
PRINT '========== Test 4: Check Payment-Student Join ==========';
-- Check if payments are joining with students correctly
SELECT 
    c.ClassID,
    c.ClassName,
    COUNT(DISTINCT s.StudentID) AS TotalStudents,
    COUNT(DISTINCT p.EntityID) AS StudentsWithPayments,
    COUNT(p.PaymentID) AS TotalPayments,
    SUM(p.PaidAmount) AS TotalPaid
FROM ClassMaster c
INNER JOIN Student s ON c.ClassID = s.AdmissionClass AND s.IsDeleted = 0
LEFT JOIN Payment p ON s.StudentID = p.EntityID AND p.IsDeleted = 0
WHERE c.SchoolID = @SchoolID
GROUP BY c.ClassID, c.ClassName
ORDER BY c.ClassID;

PRINT '';
PRINT '========== Test 5: Check Date Range for Current Month ==========';
DECLARE @StartDate DATE = DATEADD(DAY, 1, EOMONTH(GETDATE(), -1));
DECLARE @EndDate DATE = EOMONTH(GETDATE());

SELECT 
    @StartDate AS CurrentMonthStart,
    @EndDate AS CurrentMonthEnd,
    COUNT(*) AS PaymentsInCurrentMonth
FROM Payment
WHERE IsDeleted = 0 
    AND SchoolID = @SchoolID
    AND PaymentDate >= @StartDate
    AND PaymentDate <= @EndDate;

PRINT '';
PRINT '========== Test 6: Check Last 6 Months Data ==========';
SELECT 
    FORMAT(PaymentDate, 'MMM yyyy') AS MonthYear,
    COUNT(*) AS PaymentCount,
    SUM(PaidAmount) AS TotalRevenue
FROM Payment
WHERE IsDeleted = 0 
    AND SchoolID = @SchoolID
    AND PaymentDate >= DATEADD(MONTH, -6, GETDATE())
GROUP BY FORMAT(PaymentDate, 'MMM yyyy'), MONTH(PaymentDate), YEAR(PaymentDate)
ORDER BY YEAR(PaymentDate), MONTH(PaymentDate);
