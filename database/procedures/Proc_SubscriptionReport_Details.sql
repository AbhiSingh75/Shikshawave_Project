CREATE OR ALTER PROCEDURE dbo.Proc_SubscriptionReport_Details
    @Type VARCHAR(20),
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @Type = 'total'
    BEGIN
        SELECT 
            s.SubscriptionNo,
            ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
            sp.PlanName,
            s.SubscriptionStartDate,
            s.SubscriptionEndDate,
            s.FinalAmount,
            s.PaymentStatus
        FROM dbo.Subscriber s
        INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
        LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
        WHERE s.IsDeleted = 0
            AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
            AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
        ORDER BY s.CreatedAt DESC;
    END
    ELSE IF @Type = 'active'
    BEGIN
        SELECT 
            s.SubscriptionNo,
            ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
            sp.PlanName,
            s.SubscriptionStartDate,
            s.SubscriptionEndDate,
            s.FinalAmount,
            s.PaymentStatus
        FROM dbo.Subscriber s
        INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
        LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
        WHERE s.IsDeleted = 0 AND s.IsActive = 1
            AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
            AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
        ORDER BY s.CreatedAt DESC;
    END
    ELSE IF @Type = 'paid'
    BEGIN
        SELECT 
            s.SubscriptionNo,
            ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
            sp.PlanName,
            s.SubscriptionStartDate,
            s.SubscriptionEndDate,
            s.AmountPaid,
            s.PaymentStatus
        FROM dbo.Subscriber s
        INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
        LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
        WHERE s.IsDeleted = 0 AND s.PaymentStatus = 'Paid'
            AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
            AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
        ORDER BY s.CreatedAt DESC;
    END
    ELSE IF @Type = 'pending'
    BEGIN
        SELECT 
            s.SubscriptionNo,
            ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
            sp.PlanName,
            s.SubscriptionStartDate,
            s.SubscriptionEndDate,
            s.FinalAmount,
            s.PaymentStatus
        FROM dbo.Subscriber s
        INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
        LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
        WHERE s.IsDeleted = 0 AND s.PaymentStatus = 'Pending'
            AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
            AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
        ORDER BY s.CreatedAt DESC;
    END
    ELSE IF @Type = 'referral'
    BEGIN
        SELECT 
            s.SubscriptionNo,
            ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
            sp.PlanName,
            s.SubscriptionStartDate,
            s.SubscriptionEndDate,
            s.ReferralIncentive,
            ISNULL(um.UserName, 'N/A') as ReferredBy
        FROM dbo.Subscriber s
        INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
        LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
        LEFT JOIN dbo.UserMaster um ON s.ReferredByUserID = um.UserID
        WHERE s.IsDeleted = 0 AND s.ReferralIncentive > 0
            AND (@StartDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @StartDate)
            AND (@EndDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @EndDate)
        ORDER BY s.CreatedAt DESC;
    END

END
GO
