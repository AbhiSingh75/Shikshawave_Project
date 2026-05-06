-- PostgreSQL Functions for Subscription Management

-- 1. Unified Subscription Plan IUD
CREATE OR REPLACE FUNCTION fn_subscription_plan_iud(
    p_Action VARCHAR,
    p_PlanID INT DEFAULT NULL,
    p_PlanName VARCHAR DEFAULT NULL,
    p_PlanCode VARCHAR DEFAULT NULL,
    p_PlanType VARCHAR DEFAULT NULL,
    p_DurationMonths INT DEFAULT NULL,
    p_Price DECIMAL DEFAULT NULL,
    p_DiscountPercent DECIMAL DEFAULT NULL,
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

-- 2. Unified Subscriber IUD
CREATE OR REPLACE FUNCTION fn_subscriber_iud(
    p_Action VARCHAR,
    p_SubscriberID INT DEFAULT NULL,
    p_SubscriptionNo VARCHAR DEFAULT NULL,
    p_SubscriberType VARCHAR DEFAULT NULL,
    p_SchoolId INT DEFAULT NULL,
    p_PlanID INT DEFAULT NULL,
    p_SubscriptionStartDate DATE DEFAULT NULL,
    p_DurationMonths INT DEFAULT NULL,
    p_PaymentMode VARCHAR DEFAULT NULL,
    p_PaymentStatus VARCHAR DEFAULT NULL,
    p_PaymentReference VARCHAR DEFAULT NULL,
    p_PaymentDate TIMESTAMP DEFAULT NULL,
    p_AmountPaid DECIMAL DEFAULT NULL,
    p_DiscountPercent DECIMAL DEFAULT NULL,
    p_ReferredByUserID INT DEFAULT NULL,
    p_ReferralIncentive DECIMAL DEFAULT NULL,
    p_IsRenewed BOOLEAN DEFAULT FALSE,
    p_RenewalParentID INT DEFAULT NULL,
    p_UserID INT DEFAULT NULL
) RETURNS TABLE (
    Status VARCHAR,
    Message VARCHAR,
    NewID INT
) AS $$
DECLARE
    v_SubscriptionEndDate DATE;
    v_FinalAmount DECIMAL;
    v_NewID INT;
BEGIN
    IF p_SubscriptionStartDate IS NOT NULL AND p_DurationMonths IS NOT NULL THEN
        v_SubscriptionEndDate := (p_SubscriptionStartDate + (p_DurationMonths || ' months')::interval)::date;
    END IF;

    v_FinalAmount := p_AmountPaid;

    IF p_Action = 'INSERT' THEN
        -- Handle Renewal
        IF p_RenewalParentID IS NOT NULL THEN
            UPDATE Subscriber 
            SET IsRenewed = TRUE, 
                UpdatedAt = CURRENT_TIMESTAMP, 
                UpdatedBy = p_UserID 
            WHERE SubscriberID = p_RenewalParentID;
        END IF;

        INSERT INTO Subscriber (
            SubscriptionNo, SubscriberType, SchoolId, PlanID, 
            SubscriptionStartDate, SubscriptionEndDate, DurationMonths,
            PaymentMode, PaymentStatus, PaymentReference, PaymentDate,
            AmountPaid, DiscountPercent, FinalAmount,
            ReferredByUserID, ReferralIncentive,
            IsActive, IsRenewed, RenewalParentID,
            CreatedBy, CreatedAt, IsDeleted
        ) VALUES (
            p_SubscriptionNo, p_SubscriberType, p_SchoolId, p_PlanID,
            COALESCE(p_SubscriptionStartDate, CURRENT_DATE), v_SubscriptionEndDate, p_DurationMonths,
            p_PaymentMode, COALESCE(p_PaymentStatus, 'Pending'), p_PaymentReference, p_PaymentDate,
            p_AmountPaid, p_DiscountPercent, v_FinalAmount,
            p_ReferredByUserID, p_ReferralIncentive,
            (COALESCE(p_PaymentStatus, 'Pending') = 'Paid'), p_IsRenewed, p_RenewalParentID,
            p_UserID, CURRENT_TIMESTAMP, FALSE
        ) RETURNING SubscriberID INTO v_NewID;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber added successfully'::VARCHAR, v_NewID;

    ELSIF p_Action = 'UPDATE' THEN
        UPDATE Subscriber SET
            SubscriberType = COALESCE(p_SubscriberType, SubscriberType),
            SchoolId = COALESCE(p_SchoolId, SchoolId),
            PlanID = COALESCE(p_PlanID, PlanID),
            SubscriptionStartDate = COALESCE(p_SubscriptionStartDate, SubscriptionStartDate),
            SubscriptionEndDate = COALESCE(v_SubscriptionEndDate, SubscriptionEndDate),
            DurationMonths = COALESCE(p_DurationMonths, DurationMonths),
            PaymentMode = COALESCE(p_PaymentMode, PaymentMode),
            PaymentStatus = COALESCE(p_PaymentStatus, PaymentStatus),
            PaymentReference = COALESCE(p_PaymentReference, PaymentReference),
            PaymentDate = COALESCE(p_PaymentDate, PaymentDate),
            AmountPaid = COALESCE(p_AmountPaid, AmountPaid),
            DiscountPercent = COALESCE(p_DiscountPercent, DiscountPercent),
            FinalAmount = COALESCE(v_FinalAmount, FinalAmount),
            ReferredByUserID = COALESCE(p_ReferredByUserID, ReferredByUserID),
            ReferralIncentive = COALESCE(p_ReferralIncentive, ReferralIncentive),
            IsActive = CASE WHEN COALESCE(p_PaymentStatus, PaymentStatus) = 'Paid' THEN TRUE ELSE IsActive END,
            IsRenewed = COALESCE(p_IsRenewed, IsRenewed),
            RenewalParentID = COALESCE(p_RenewalParentID, RenewalParentID),
            UpdatedBy = p_UserID,
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE SubscriberID = p_SubscriberID;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber updated successfully'::VARCHAR, p_SubscriberID;

    ELSIF p_Action = 'DELETE' THEN
        UPDATE Subscriber SET
            IsDeleted = TRUE,
            DeletedBy = p_UserID,
            DeletedAt = CURRENT_TIMESTAMP,
            IsActive = FALSE
        WHERE SubscriberID = p_SubscriberID;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber deleted successfully'::VARCHAR, p_SubscriberID;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 3. Subscriber GetList
CREATE OR REPLACE FUNCTION fn_subscriber_get_list(
    p_SubscriberID INT DEFAULT NULL,
    p_PlanID INT DEFAULT NULL,
    p_PaymentStatus VARCHAR DEFAULT NULL,
    p_IncludeDeleted BOOLEAN DEFAULT FALSE,
    p_Search VARCHAR DEFAULT NULL
) RETURNS TABLE (
    SubscriberID INT,
    SubscriptionNo VARCHAR,
    SubscriberName VARCHAR,
    PlanName VARCHAR,
    PlanType VARCHAR,
    PlanID INT,
    SubscriptionStartDate DATE,
    SubscriptionEndDate DATE,
    DurationMonths INT,
    PaymentMode VARCHAR,
    PaymentStatus VARCHAR,
    PaymentReference VARCHAR,
    PaymentDate TIMESTAMP,
    AmountPaid DECIMAL,
    DiscountPercent DECIMAL,
    FinalAmount DECIMAL,
    ReferredByUserID INT,
    ReferredByName VARCHAR,
    ReferralIncentive DECIMAL,
    IsActive BOOLEAN,
    IsRenewed BOOLEAN,
    RenewalParentID INT,
    CreatedBy INT,
    CreatedAt TIMESTAMP,
    UpdatedBy INT,
    UpdatedAt TIMESTAMP,
    IsDeleted BOOLEAN,
    SchoolID INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.SubscriberID,
        s.SubscriptionNo,
        COALESCE(sm.SchoolName, 'N/A')::VARCHAR,
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
        COALESCE(um.UserName, 'N/A')::VARCHAR,
        s.ReferralIncentive,
        s.IsActive,
        s.IsRenewed,
        s.RenewalParentID,
        s.CreatedBy,
        s.CreatedAt,
        s.UpdatedBy,
        s.UpdatedAt,
        s.IsDeleted,
        s.SchoolID
    FROM Subscriber s
    INNER JOIN SubscriptionPlan sp ON s.PlanID = sp.PlanID
    LEFT JOIN SchoolMaster sm ON s.SchoolId = sm.SchoolID
    LEFT JOIN UserMaster um ON s.ReferredByUserID = um.UserID
    WHERE (p_SubscriberID IS NULL OR s.SubscriberID = p_SubscriberID)
        AND (p_PlanID IS NULL OR s.PlanID = p_PlanID)
        AND (p_PaymentStatus IS NULL OR s.PaymentStatus = p_PaymentStatus)
        AND (s.IsDeleted = p_IncludeDeleted)
        AND (p_Search IS NULL OR 
             s.SubscriptionNo ILIKE '%' || p_Search || '%' OR 
             sm.SchoolName ILIKE '%' || p_Search || '%' OR
             sp.PlanName ILIKE '%' || p_Search || '%')
    ORDER BY s.CreatedAt DESC;
END;
$$ LANGUAGE plpgsql;

-- 4. My Subscription Get
CREATE OR REPLACE FUNCTION fn_my_subscription_get(
    p_SchoolID INT
) RETURNS TABLE (
    TotalSubscriptions BIGINT,
    ActiveSubscriptions BIGINT,
    TotalAmountPaid DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN IsActive = TRUE AND PaymentStatus = 'Paid' THEN 1 END)::BIGINT,
        COALESCE(SUM(FinalAmount), 0)::DECIMAL
    FROM Subscriber
    WHERE SchoolId = p_SchoolID AND IsDeleted = FALSE;
END;
$$ LANGUAGE plpgsql;

-- 5. Subscription Plan Details (for stats)
-- Reusing existing Proc_SubscriptionPlan_Get logic if needed, but lets add report functions.

CREATE OR REPLACE FUNCTION fn_subscription_report(
    p_StartDate DATE DEFAULT NULL,
    p_EndDate DATE DEFAULT NULL
) RETURNS TABLE (
    TotalSubscribers BIGINT,
    ActiveSubscribers BIGINT,
    TotalRevenue DECIMAL,
    PendingAmount DECIMAL,
    TotalReferral DECIMAL,
    TotalBeforeDiscount DECIMAL,
    TotalDiscount DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        COUNT(CASE WHEN IsActive = TRUE THEN 1 END)::BIGINT,
        COALESCE(SUM(CASE WHEN PaymentStatus = 'Paid' THEN FinalAmount ELSE 0 END), 0)::DECIMAL,
        COALESCE(SUM(CASE WHEN PaymentStatus = 'Pending' THEN FinalAmount ELSE 0 END), 0)::DECIMAL,
        COALESCE(SUM(ReferralIncentive), 0)::DECIMAL,
        COALESCE(SUM(AmountPaid), 0)::DECIMAL,
        COALESCE(SUM(AmountPaid - FinalAmount), 0)::DECIMAL
    FROM Subscriber
    WHERE IsDeleted = FALSE
      AND (p_StartDate IS NULL OR CreatedAt >= p_StartDate)
      AND (p_EndDate IS NULL OR CreatedAt <= p_EndDate + INTERVAL '1 day');
END;
$$ LANGUAGE plpgsql;
