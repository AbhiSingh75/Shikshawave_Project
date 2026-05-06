-- Test Revenue Procedure with Date Filters

-- Test 1: No date filter (should show last 6 months for trend, current month for class breakdown)
PRINT '=== TEST 1: No Date Filter ===';
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = 3,
    @ClassID = NULL,
    @FromDate = NULL,
    @ToDate = NULL,
    @PaymentMode = NULL,
    @PaymentFor = NULL;

PRINT '';
PRINT '=== TEST 2: With Date Filter (Oct 2025 to Nov 2025) ===';
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = 3,
    @ClassID = NULL,
    @FromDate = '2025-10-01',
    @ToDate = '2025-11-30',
    @PaymentMode = NULL,
    @PaymentFor = NULL;

PRINT '';
PRINT '=== TEST 3: Single Month Filter (Nov 2025 only) ===';
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = 3,
    @ClassID = NULL,
    @FromDate = '2025-11-01',
    @ToDate = '2025-11-30',
    @PaymentMode = NULL,
    @PaymentFor = NULL;
