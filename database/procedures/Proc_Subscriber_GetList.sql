CREATE OR ALTER PROCEDURE [dbo].[Proc_Subscriber_GetList]
    @SubscriberID INT = NULL,
    @PlanID INT = NULL,
    @PaymentStatus NVARCHAR(20) = NULL,
    @IncludeDeleted BIT = 0,
    @Search NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        s.SubscriberID,
        s.SubscriptionNo,
        ISNULL(sm.SchoolName, 'N/A') as SubscriberName,
        sp.PlanName,
        sp.PlanType,
        s.PlanID,
        s.SubscriptionStartDate,
        s.SubscriptionEndDate,
        s.DurationMonths,
        s.PaymentMode,
        s.PaymentStatus,
        s.PaymentReference,
        s.PaymentDate,
        s.AmountPaid,
        s.DiscountPercent,
        s.FinalAmount,
        s.ReferredByUserID,
        ISNULL(um.UserName, 'N/A') as ReferredByName,
        s.ReferralIncentive,
        s.IsActive,
        s.IsRenewed,
        s.RenewalParentID,
        s.CreatedBy,
        s.CreatedAt,
        s.UpdatedBy,
        s.UpdatedAt,
        s.IsDeleted
    FROM dbo.Subscriber s
    INNER JOIN dbo.SubscriptionPlan sp ON s.PlanID = sp.PlanID
    LEFT JOIN dbo.SchoolMaster sm ON s.SchoolId = sm.SchoolID
    LEFT JOIN dbo.UserMaster um ON s.ReferredByUserID = um.UserID
    WHERE (@SubscriberID IS NULL OR s.SubscriberID = @SubscriberID)
        AND (@PlanID IS NULL OR s.PlanID = @PlanID)
        AND (@PaymentStatus IS NULL OR s.PaymentStatus = @PaymentStatus)
        AND (s.IsDeleted = @IncludeDeleted)
        AND (@Search IS NULL OR 
             s.SubscriptionNo LIKE '%' + @Search + '%' OR 
             sm.SchoolName LIKE '%' + @Search + '%' OR
             sp.PlanName LIKE '%' + @Search + '%')
    ORDER BY s.CreatedAt DESC;
END
GO
