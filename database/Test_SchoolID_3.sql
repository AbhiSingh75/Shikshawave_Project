-- Test with SchoolID = 3
EXEC Proc_Dashboard_Revenue_Get 
    @SchoolID = 3,
    @FromDate = NULL,
    @ToDate = NULL,
    @ClassID = NULL,
    @PaymentMode = NULL,
    @PaymentFor = NULL;
