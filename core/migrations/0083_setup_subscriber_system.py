from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0082_setup_subscription_postgres'),
    ]

    operations = [
        # 1. Create Subscriber Table
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS "Subscriber" (
                "SubscriberID" SERIAL PRIMARY KEY,
                "SubscriptionNo" VARCHAR(50) UNIQUE,
                "SubscriberType" VARCHAR(50) DEFAULT 'School',
                "SchoolID" INT REFERENCES "SchoolMaster"("SchoolID"),
                "PlanID" INT REFERENCES "SubscriptionPlan"("PlanID"),
                "SubscriptionStartDate" DATE,
                "SubscriptionEndDate" DATE,
                "DurationMonths" INT,
                "PaymentMode" VARCHAR(50),
                "PaymentStatus" VARCHAR(50) DEFAULT 'Pending',
                "PaymentReference" VARCHAR(100),
                "PaymentDate" TIMESTAMP,
                "AmountPaid" NUMERIC(15, 2),
                "DiscountPercent" NUMERIC(5, 2) DEFAULT 0,
                "FinalAmount" NUMERIC(15, 2),
                "ReferredByUserID" INT,
                "ReferralIncentive" NUMERIC(15, 2) DEFAULT 0,
                "IsActive" BOOLEAN DEFAULT FALSE,
                "IsRenewed" BOOLEAN DEFAULT FALSE,
                "RenewalParentID" INT,
                "CreatedBy" INT,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedBy" INT,
                "UpdatedAt" TIMESTAMP,
                "DeletedBy" INT,
                "DeletedAt" TIMESTAMP,
                "IsDeleted" BOOLEAN DEFAULT FALSE
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS \"Subscriber\" CASCADE;"
        ),
        
        # 2. Setup fn_subscriber_get_list
        migrations.RunSQL(
            sql="""
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
                AmountPaid NUMERIC,
                DiscountPercent NUMERIC,
                FinalAmount NUMERIC,
                ReferredByUserID INT,
                ReferredByName VARCHAR,
                ReferralIncentive NUMERIC,
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
                    s."SubscriberID",
                    s."SubscriptionNo"::VARCHAR,
                    COALESCE(sm."SchoolName", 'N/A')::VARCHAR,
                    sp."PlanName"::VARCHAR,
                    sp."PlanType"::VARCHAR,
                    s."PlanID",
                    s."SubscriptionStartDate",
                    s."SubscriptionEndDate",
                    s."DurationMonths",
                    COALESCE(s."PaymentMode", '')::VARCHAR,
                    COALESCE(s."PaymentStatus", 'Pending')::VARCHAR,
                    COALESCE(s."PaymentReference", '')::VARCHAR,
                    s."PaymentDate",
                    s."AmountPaid",
                    s."DiscountPercent",
                    s."FinalAmount",
                    s."ReferredByUserID",
                    COALESCE(um."UserName", 'N/A')::VARCHAR,
                    s."ReferralIncentive",
                    s."IsActive",
                    s."IsRenewed",
                    s."RenewalParentID",
                    s."CreatedBy",
                    s."CreatedAt",
                    s."UpdatedBy",
                    s."UpdatedAt",
                    s."IsDeleted",
                    s."SchoolID"
                FROM "Subscriber" s
                INNER JOIN "SubscriptionPlan" sp ON s."PlanID" = sp."PlanID"
                LEFT JOIN "SchoolMaster" sm ON s."SchoolID" = sm."SchoolID"
                LEFT JOIN "UserMaster" um ON s."ReferredByUserID" = um."UserID"
                WHERE (p_SubscriberID IS NULL OR s."SubscriberID" = p_SubscriberID)
                    AND (p_PlanID IS NULL OR s."PlanID" = p_PlanID)
                    AND (p_PaymentStatus IS NULL OR s."PaymentStatus" ILIKE p_PaymentStatus)
                    AND (COALESCE(s."IsDeleted", FALSE) = p_IncludeDeleted)
                    AND (p_Search IS NULL OR 
                         s."SubscriptionNo" ILIKE '%' || p_Search || '%' OR 
                         sm."SchoolName" ILIKE '%' || p_Search || '%' OR
                         sp."PlanName" ILIKE '%' || p_Search || '%')
                ORDER BY s."CreatedAt" DESC;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS fn_subscriber_get_list;"
        ),

        # 3. Setup fn_subscriber_iud
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION fn_subscriber_iud(
                p_Action VARCHAR,
                p_SubscriberID INT DEFAULT NULL,
                p_SubscriptionNo VARCHAR DEFAULT NULL,
                p_SubscriberType VARCHAR DEFAULT NULL,
                p_SchoolID INT DEFAULT NULL,
                p_PlanID INT DEFAULT NULL,
                p_SubscriptionStartDate DATE DEFAULT NULL,
                p_DurationMonths INT DEFAULT NULL,
                p_PaymentMode VARCHAR DEFAULT NULL,
                p_PaymentStatus VARCHAR DEFAULT NULL,
                p_PaymentReference VARCHAR DEFAULT NULL,
                p_PaymentDate TIMESTAMP DEFAULT NULL,
                p_AmountPaid NUMERIC DEFAULT NULL,
                p_DiscountPercent NUMERIC DEFAULT NULL,
                p_ReferredByUserID INT DEFAULT NULL,
                p_ReferralIncentive NUMERIC DEFAULT NULL,
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
                v_FinalAmount NUMERIC;
                v_NewID INT;
            BEGIN
                IF p_SubscriptionStartDate IS NOT NULL AND p_DurationMonths IS NOT NULL THEN
                    v_SubscriptionEndDate := (p_SubscriptionStartDate + (p_DurationMonths || ' months')::interval)::date;
                END IF;

                v_FinalAmount := p_AmountPaid;

                IF p_Action = 'INSERT' THEN
                    IF p_RenewalParentID IS NOT NULL THEN
                        UPDATE "Subscriber" SET "IsRenewed" = TRUE WHERE "SubscriberID" = p_RenewalParentID;
                    END IF;

                    INSERT INTO "Subscriber" (
                        "SubscriptionNo", "SubscriberType", "SchoolID", "PlanID", 
                        "SubscriptionStartDate", "SubscriptionEndDate", "DurationMonths",
                        "PaymentMode", "PaymentStatus", "PaymentReference", "PaymentDate",
                        "AmountPaid", "DiscountPercent", "FinalAmount", "ReferredByUserID", "ReferralIncentive",
                        "IsActive", "IsRenewed", "RenewalParentID", "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES (
                        p_SubscriptionNo, p_SubscriberType, p_SchoolID, p_PlanID,
                        COALESCE(p_SubscriptionStartDate, CURRENT_DATE), v_SubscriptionEndDate, p_DurationMonths,
                        p_PaymentMode, COALESCE(p_PaymentStatus, 'Pending'), p_PaymentReference, p_PaymentDate,
                        p_AmountPaid, p_DiscountPercent, v_FinalAmount, p_ReferredByUserID, p_ReferralIncentive,
                        (COALESCE(p_PaymentStatus, 'Pending') = 'Paid'), p_IsRenewed, p_RenewalParentID,
                        p_UserID, CURRENT_TIMESTAMP, FALSE
                    ) RETURNING "SubscriberID" INTO v_NewID;
                    
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber added successfully'::VARCHAR, v_NewID;

                ELSIF p_Action = 'UPDATE' THEN
                    UPDATE "Subscriber" SET
                        "SubscriberType" = COALESCE(p_SubscriberType, "SubscriberType"),
                        "SchoolID" = COALESCE(p_SchoolID, "SchoolID"),
                        "PlanID" = COALESCE(p_PlanID, "PlanID"),
                        "SubscriptionStartDate" = COALESCE(p_SubscriptionStartDate, "SubscriptionStartDate"),
                        "SubscriptionEndDate" = COALESCE(v_SubscriptionEndDate, "SubscriptionEndDate"),
                        "DurationMonths" = COALESCE(p_DurationMonths, "DurationMonths"),
                        "PaymentMode" = COALESCE(p_PaymentMode, "PaymentMode"),
                        "PaymentStatus" = COALESCE(p_PaymentStatus, "PaymentStatus"),
                        "PaymentReference" = COALESCE(p_PaymentReference, "PaymentReference"),
                        "PaymentDate" = COALESCE(p_PaymentDate, "PaymentDate"),
                        "AmountPaid" = COALESCE(p_AmountPaid, "AmountPaid"),
                        "DiscountPercent" = COALESCE(p_DiscountPercent, "DiscountPercent"),
                        "FinalAmount" = COALESCE(v_FinalAmount, "FinalAmount"),
                        "ReferredByUserID" = COALESCE(p_ReferredByUserID, "ReferredByUserID"),
                        "ReferralIncentive" = COALESCE(p_ReferralIncentive, "ReferralIncentive"),
                        "IsActive" = CASE WHEN COALESCE(p_PaymentStatus, "PaymentStatus") = 'Paid' THEN TRUE ELSE "IsActive" END,
                        "IsRenewed" = COALESCE(p_IsRenewed, "IsRenewed"),
                        "RenewalParentID" = COALESCE(p_RenewalParentID, "RenewalParentID"),
                        "UpdatedBy" = p_UserID,
                        "UpdatedAt" = CURRENT_TIMESTAMP
                    WHERE "SubscriberID" = p_SubscriberID;
                    
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber updated successfully'::VARCHAR, p_SubscriberID;

                ELSIF p_Action = 'DELETE' THEN
                    UPDATE "Subscriber" SET
                        "IsDeleted" = TRUE, "DeletedBy" = p_UserID, "DeletedAt" = CURRENT_TIMESTAMP, "IsActive" = FALSE
                    WHERE "SubscriberID" = p_SubscriberID;
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber deleted successfully'::VARCHAR, p_SubscriberID;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS fn_subscriber_iud;"
        ),

        # 4. Setup fn_my_subscription_get
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION fn_my_subscription_get(p_SchoolID INT) 
            RETURNS TABLE (TotalSubscriptions BIGINT, ActiveSubscriptions BIGINT, TotalAmountPaid NUMERIC) AS $$
            BEGIN
                RETURN QUERY SELECT 
                    COUNT(*)::BIGINT,
                    COUNT(CASE WHEN "IsActive" = TRUE AND "PaymentStatus" = 'Paid' THEN 1 END)::BIGINT,
                    COALESCE(SUM("FinalAmount"), 0)::NUMERIC
                FROM "Subscriber" WHERE "SchoolID" = p_SchoolID AND "IsDeleted" = FALSE;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS fn_my_subscription_get;"
        ),
    ]
