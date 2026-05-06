-- Standardized Subscriber IUD Procedure
-- Aligned with official [dbo].[Subscriber] table structure

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
    
    -- Automatic SubscriptionEndDate calculation if duration is provided
    DECLARE @SubscriptionEndDate DATE = NULL;
    IF @SubscriptionStartDate IS NOT NULL AND @DurationMonths IS NOT NULL
    BEGIN
        SET @SubscriptionEndDate = DATEADD(MONTH, @DurationMonths, @SubscriptionStartDate);
    END

    -- Final Amount calculation
    DECLARE @FinalAmount DECIMAL(10, 2) = @AmountPaid; -- Simplified for now, can be Price * (1 - Discount)

    IF @Action = 'INSERT'
    BEGIN
        -- Handle Renewal: If this is a renewal, mark the parent as renewed
        IF @RenewalParentID IS NOT NULL
        BEGIN
            UPDATE Subscriber 
            SET IsRenewed = 1, 
                UpdatedAt = GETDATE(), 
                UpdatedBy = @UserId 
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
            @UserId, GETDATE(), 0
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
            UpdatedBy = @UserId,
            UpdatedAt = GETDATE()
        WHERE SubscriberID = @SubscriberID;
        
        SELECT 'SUCCESS' AS Status, 'Subscriber updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE Subscriber 
        SET IsDeleted = 1, 
            DeletedBy = @UserId, 
            DeletedAt = GETDATE(),
            IsActive = 0
        WHERE SubscriberID = @SubscriberID;
        
        SELECT 'SUCCESS' AS Status, 'Subscriber deleted successfully' AS Message;
    END
END
GO
