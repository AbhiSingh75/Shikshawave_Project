CREATE OR ALTER PROCEDURE dbo.Proc_SubscriptionReport_Get
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- Overall Stats
    SELECT 
        COUNT(*) as TotalSubscribers,
        SUM(CASE WHEN s.IsActive = 1 THEN 1 ELSE 0 END) as ActiveSubscribers,
        SUM(CASE WHEN s.PaymentStatus = 'Paid' THEN ISNULL(s.AmountPaid, 0) ELSE 0 END) as TotalRevenue,
        SUM(CASE WHEN s.PaymentStatus = 'Pending' THEN ISNULL(s.FinalAmount, 0) ELSE 0 END) as PendingAmount,
        SUM(ISNULL(s.ReferralIncentive, 0)) as TotalReferral,
        SUM(ISNULL(sp.Price, 0)) as TotalBeforeDiscount,
        SUM(ISNULL(sp.Price, 0) * ISNULL(s.DiscountPercent, 0) / 100) as TotalDiscount
    FROM dbo.Subscriber s
    INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
    WHERE s.IsDeleted = 0
        AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
        AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate);

    -- Plan-wise Stats
    SELECT 
        sp.PlanName,
        COUNT(*) as SubscriberCount,
        SUM(CASE WHEN s.PaymentStatus = 'Paid' THEN ISNULL(s.AmountPaid, 0) ELSE 0 END) as TotalRevenue
    FROM dbo.Subscriber s
    INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
    WHERE s.IsDeleted = 0
        AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
        AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
    GROUP BY sp.PlanName
    ORDER BY SubscriberCount DESC;

    -- Year-wise Stats
    SELECT 
        YEAR(s.CreatedAt) as [Year],
        COUNT(*) as Subscribers,
        SUM(CASE WHEN s.PaymentStatus = 'Paid' THEN ISNULL(s.AmountPaid, 0) ELSE 0 END) as Revenue
    FROM dbo.Subscriber s
    WHERE s.IsDeleted = 0
        AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
        AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
    GROUP BY YEAR(s.CreatedAt)
    ORDER BY [Year];

END
GO
