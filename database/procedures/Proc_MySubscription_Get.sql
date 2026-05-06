CREATE OR ALTER PROCEDURE dbo.Proc_MySubscription_Get
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;

    -- Summary Stats
    SELECT 
        COUNT(*) as TotalSubscriptions,
        SUM(CASE WHEN IsActive = 1 THEN 1 ELSE 0 END) as ActiveSubscriptions,
        SUM(ISNULL(AmountPaid, 0)) as TotalAmountPaid
    FROM dbo.Subscriber
    WHERE SchoolId = @SchoolID AND IsDeleted = 0;

    -- All Subscriptions
    SELECT
        s.SubscriptionNo,
        s.SubscriptionStartDate,
        s.SubscriptionEndDate,
        s.DurationMonths,
        s.AmountPaid,
        s.DiscountPercent,
        s.FinalAmount,
        s.PaymentStatus,
        s.IsActive,
        sp.PlanName,
        sp.PlanType,
        sp.MaxStudents,
        sp.MaxTeachers,
        sp.StorageLimitMB,
        sp.IncludeReports,
        s.CreatedAt
    FROM dbo.Subscriber s
    INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
    WHERE s.SchoolId = @SchoolID AND s.IsDeleted = 0
    ORDER BY s.IsActive DESC, s.CreatedAt DESC;

END
GO
