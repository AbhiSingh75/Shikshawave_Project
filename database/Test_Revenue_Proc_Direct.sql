-- Test the stored procedure directly with your SchoolID
-- Replace @SchoolID value with your actual SchoolID

DECLARE @SchoolID INT = 1; -- Change this to your actual SchoolID

-- Test 1: No date filters (should use current month for class breakdown)
PRINT '=== TEST 1: No Date Filters (Current Month Default) ===';
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = @SchoolID,
    @FromDate = NULL,
    @ToDate = NULL,
    @ClassID = NULL,
    @PaymentMode = NULL,
    @PaymentFor = NULL;

PRINT '';
PRINT '=== TEST 2: Last 6 Months Explicit ===';
-- Test 2: Explicit last 6 months
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = @SchoolID,
    @FromDate = '2024-05-01',
    @ToDate = '2025-11-30',
    @ClassID = NULL,
    @PaymentMode = NULL,
    @PaymentFor = NULL;
