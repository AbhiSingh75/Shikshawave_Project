-- Standardized Subscription Plan Management Function (v2)
-- Recreates the IUD function with explicit NUMERIC and BOOLEAN types for strict PostgreSQL compatibility.

DROP FUNCTION IF EXISTS fn_subscription_plan_iud(varchar, int, varchar, varchar, varchar, int, numeric, numeric, int, int, int, boolean, boolean, int, int);

CREATE OR REPLACE FUNCTION fn_subscription_plan_iud(
    p_Action VARCHAR,
    p_PlanID INT DEFAULT NULL,
    p_PlanName VARCHAR DEFAULT NULL,
    p_PlanCode VARCHAR DEFAULT NULL,
    p_PlanType VARCHAR DEFAULT NULL,
    p_DurationMonths INT DEFAULT NULL,
    p_Price NUMERIC DEFAULT NULL,
    p_DiscountPercent NUMERIC DEFAULT NULL,
    p_MaxStudents INT DEFAULT NULL,
    p_MaxTeachers INT DEFAULT NULL,
    p_StorageLimitMB INT DEFAULT NULL,
    p_IncludeReports BOOLEAN DEFAULT TRUE,
    p_IsTrialPlan BOOLEAN DEFAULT FALSE,
    p_GracePeriodDays INT DEFAULT 0,
    p_UserID INT DEFAULT NULL
) RETURNS TABLE (
    Status VARCHAR,
    Message VARCHAR
) AS $$
BEGIN
    IF p_Action = 'INSERT' THEN
        INSERT INTO SubscriptionPlan (
            PlanName, PlanCode, PlanType, DurationMonths, Price, DiscountPercent,
            MaxStudents, MaxTeachers, StorageLimitMB, IncludeReports, IsTrialPlan,
            GracePeriodDays, CreatedBy, CreatedAt, IsDeleted
        ) VALUES (
            p_PlanName, p_PlanCode, p_PlanType, p_DurationMonths, p_Price, p_DiscountPercent,
            p_MaxStudents, p_MaxTeachers, p_StorageLimitMB, p_IncludeReports, p_IsTrialPlan,
            p_GracePeriodDays, p_UserID, CURRENT_TIMESTAMP, FALSE
        );
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Plan created successfully'::VARCHAR;

    ELSIF p_Action = 'UPDATE' THEN
        UPDATE SubscriptionPlan SET
            PlanName = COALESCE(p_PlanName, PlanName),
            PlanCode = COALESCE(p_PlanCode, PlanCode),
            PlanType = COALESCE(p_PlanType, PlanType),
            DurationMonths = COALESCE(p_DurationMonths, DurationMonths),
            Price = COALESCE(p_Price, Price),
            DiscountPercent = COALESCE(p_DiscountPercent, DiscountPercent),
            MaxStudents = COALESCE(p_MaxStudents, MaxStudents),
            MaxTeachers = COALESCE(p_MaxTeachers, MaxTeachers),
            StorageLimitMB = COALESCE(p_StorageLimitMB, StorageLimitMB),
            IncludeReports = COALESCE(p_IncludeReports, IncludeReports),
            IsTrialPlan = COALESCE(p_IsTrialPlan, IsTrialPlan),
            GracePeriodDays = COALESCE(p_GracePeriodDays, GracePeriodDays),
            UpdatedBy = p_UserID,
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE PlanID = p_PlanID;
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Plan updated successfully'::VARCHAR;

    ELSIF p_Action = 'DELETE' THEN
        UPDATE SubscriptionPlan SET
            IsDeleted = TRUE,
            DeletedBy = p_UserID,
            DeletedAt = CURRENT_TIMESTAMP
        WHERE PlanID = p_PlanID;
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Plan deleted successfully'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;
