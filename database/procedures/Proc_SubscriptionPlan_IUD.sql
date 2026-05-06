-- Standardized SubscriptionPlan IUD Procedure
-- Aligned with official [dbo].[SubscriptionPlan] table structure

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
