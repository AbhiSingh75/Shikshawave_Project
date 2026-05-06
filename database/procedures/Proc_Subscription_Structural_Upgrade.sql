-- ShikshaWave Subscription Structural Migration
-- This script adds the GracePeriodDays column and installs the standardized IUD procedures.

-- 1. Add GracePeriodDays to SubscriptionPlan if missing
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[SubscriptionPlan]') AND name = 'GracePeriodDays')
BEGIN
    ALTER TABLE [dbo].[SubscriptionPlan] ADD [GracePeriodDays] INT DEFAULT 0;
END
GO

-- 2. Standardized Subscriber IUD Procedure
CREATE OR ALTER PROCEDURE [dbo].[Proc_Subscriber_IUD]
    @Action NVARCHAR(10),
    @SubscriberID INT = NULL,
    @SubscriptionNo NVARCHAR(100) = NULL,
    @SubscriberType NVARCHAR(50) = NULL,
    @SchoolId INT = NULL,
    @PlanID INT = NULL,
    @SubscriptionStartDate DATE = NULL,
    @DurationMonths INT = NULL,
    @PaymentMode NVARCHAR(50) = NULL,
    @PaymentStatus NVARCHAR(20) = NULL,
    @PaymentReference NVARCHAR(100) = NULL,
    @PaymentDate DATETIME = NULL,
    @AmountPaid DECIMAL(10, 2) = NULL,
    @DiscountPercent DECIMAL(5, 2) = NULL,
    @ReferredByUserID INT = NULL,
    @ReferralIncentive DECIMAL(10, 2) = NULL,
    @IsRenewed BIT = 0,
    @RenewalParentID INT = NULL,
    @UserID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @SubscriptionEndDate DATE = NULL;
    IF @SubscriptionStartDate IS NOT NULL AND @DurationMonths IS NOT NULL
    BEGIN
        SET @SubscriptionEndDate = DATEADD(MONTH, @DurationMonths, @SubscriptionStartDate);
    END

    DECLARE @FinalAmount DECIMAL(10, 2) = @AmountPaid;

    IF @Action = 'INSERT'
    BEGIN
        IF @RenewalParentID IS NOT NULL
        BEGIN
            UPDATE Subscriber 
            SET IsRenewed = 1, 
                UpdatedAt = GETDATE(), 
                UpdatedBy = @UserID 
            WHERE SubscriberID = @RenewalParentID;
        END

        INSERT INTO Subscriber (
            SubscriptionNo, SubscriberType, SchoolId, PlanID, 
            SubscriptionStartDate, SubscriptionEndDate, DurationMonths,
            PaymentMode, PaymentStatus, PaymentReference, PaymentDate,
            AmountPaid, DiscountPercent, FinalAmount,
            ReferredByUserID, ReferralIncentive,
            IsActive, IsRenewed, RenewalParentID,
            CreatedBy, CreatedAt, IsDeleted
        )
        VALUES (
            @SubscriptionNo, @SubscriberType, @SchoolId, @PlanID,
            ISNULL(@SubscriptionStartDate, GETDATE()), @SubscriptionEndDate, @DurationMonths,
            @PaymentMode, ISNULL(@PaymentStatus, 'Pending'), @PaymentReference, @PaymentDate,
            @AmountPaid, @DiscountPercent, @FinalAmount,
            @ReferredByUserID, @ReferralIncentive,
            1, @IsRenewed, @RenewalParentID,
            @UserID, GETDATE(), 0
        );
        
        SELECT 'SUCCESS' AS Status, 'Subscriber added successfully' AS Message;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE Subscriber
        SET 
            SubscriberType = ISNULL(@SubscriberType, SubscriberType),
            SchoolId = ISNULL(@SchoolId, SchoolId),
            PlanID = ISNULL(@PlanID, PlanID),
            SubscriptionStartDate = ISNULL(@SubscriptionStartDate, SubscriptionStartDate),
            SubscriptionEndDate = ISNULL(@SubscriptionEndDate, SubscriptionEndDate),
            DurationMonths = ISNULL(@DurationMonths, DurationMonths),
            PaymentMode = ISNULL(@PaymentMode, PaymentMode),
            PaymentStatus = ISNULL(@PaymentStatus, PaymentStatus),
            PaymentReference = ISNULL(@PaymentReference, PaymentReference),
            PaymentDate = ISNULL(@PaymentDate, PaymentDate),
            AmountPaid = ISNULL(@AmountPaid, AmountPaid),
            DiscountPercent = ISNULL(@DiscountPercent, DiscountPercent),
            FinalAmount = ISNULL(@FinalAmount, FinalAmount),
            ReferredByUserID = ISNULL(@ReferredByUserID, ReferredByUserID),
            ReferralIncentive = ISNULL(@ReferralIncentive, ReferralIncentive),
            IsRenewed = ISNULL(@IsRenewed, IsRenewed),
            RenewalParentID = ISNULL(@RenewalParentID, RenewalParentID),
            UpdatedBy = @UserID,
            UpdatedAt = GETDATE()
        WHERE SubscriberID = @SubscriberID;
        
        SELECT 'SUCCESS' AS Status, 'Subscriber updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE Subscriber 
        SET IsDeleted = 1, 
            DeletedBy = @UserID, 
            DeletedAt = GETDATE(),
            IsActive = 0
        WHERE SubscriberID = @SubscriberID;
        
        SELECT 'SUCCESS' AS Status, 'Subscriber deleted successfully' AS Message;
    END
END
GO

-- 3. Standardized SubscriptionPlan IUD Procedure
CREATE OR ALTER PROCEDURE [dbo].[Proc_SubscriptionPlan_IUD]
    @Action NVARCHAR(10),
    @PlanID INT = NULL,
    @PlanName NVARCHAR(100) = NULL,
    @PlanCode NVARCHAR(50) = NULL,
    @PlanType NVARCHAR(50) = NULL,
    @DurationMonths INT = NULL,
    @Price DECIMAL(10, 2) = NULL,
    @DiscountPercent DECIMAL(5, 2) = NULL,
    @MaxStudents INT = NULL,
    @MaxTeachers INT = NULL,
    @StorageLimitMB INT = NULL,
    @IncludeReports BIT = 1,
    @IsTrialPlan BIT = 0,
    @GracePeriodDays INT = 0,
    @UserID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    IF @Action = 'INSERT'
    BEGIN
        INSERT INTO SubscriptionPlan (
            PlanName, PlanCode, PlanType, DurationMonths, Price, DiscountPercent,
            MaxStudents, MaxTeachers, StorageLimitMB, IncludeReports, IsTrialPlan,
            GracePeriodDays, CreatedBy, CreatedAt, IsDeleted
        )
        VALUES (
            @PlanName, @PlanCode, @PlanType, @DurationMonths, @Price, @DiscountPercent,
            @MaxStudents, @MaxTeachers, @StorageLimitMB, @IncludeReports, @IsTrialPlan,
            @GracePeriodDays, @UserID, GETDATE(), 0
        );

        SELECT 'SUCCESS' AS Status, 'Plan created successfully' AS Message;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE SubscriptionPlan
        SET 
            PlanName = ISNULL(@PlanName, PlanName),
            PlanCode = ISNULL(@PlanCode, PlanCode),
            PlanType = ISNULL(@PlanType, PlanType),
            DurationMonths = ISNULL(@DurationMonths, DurationMonths),
            Price = ISNULL(@Price, Price),
            DiscountPercent = ISNULL(@DiscountPercent, DiscountPercent),
            MaxStudents = ISNULL(@MaxStudents, MaxStudents),
            MaxTeachers = ISNULL(@MaxTeachers, MaxTeachers),
            StorageLimitMB = ISNULL(@StorageLimitMB, StorageLimitMB),
            IncludeReports = ISNULL(@IncludeReports, IncludeReports),
            IsTrialPlan = ISNULL(@IsTrialPlan, IsTrialPlan),
            GracePeriodDays = ISNULL(@GracePeriodDays, GracePeriodDays),
            UpdatedBy = @UserID,
            UpdatedAt = GETDATE()
        WHERE PlanID = @PlanID;

        SELECT 'SUCCESS' AS Status, 'Plan updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE SubscriptionPlan 
        SET IsDeleted = 1, 
            DeletedBy = @UserID, 
            DeletedAt = GETDATE()
        WHERE PlanID = @PlanID;

        SELECT 'SUCCESS' AS Status, 'Plan deleted successfully' AS Message;
    END
END
GO

-- 4. Standardized Subscriber GetList Procedure
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
