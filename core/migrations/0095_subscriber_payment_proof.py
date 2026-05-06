# core/migrations/0095_subscriber_payment_proof.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0094_subscriber_include_school_code'),
    ]

    operations = [
        # 1. Add column to Subscriber table
        migrations.RunSQL("""
            ALTER TABLE "Subscriber" ADD COLUMN IF NOT EXISTS "PaymentProof" bytea;
        """),

        # 2. Update fn_subscriber_iud procedure to handle the new field
        migrations.RunSQL("""
            -- Drop existing to re-define with new parameter
            DROP FUNCTION IF EXISTS fn_subscriber_iud(
                VARCHAR, INT, VARCHAR, VARCHAR, INT, INT, DATE, INT, VARCHAR, VARCHAR, 
                VARCHAR, TIMESTAMP, NUMERIC, NUMERIC, INT, NUMERIC, BOOLEAN, INT, INT
            );

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
                p_PaymentProof bytea DEFAULT NULL, -- NEW FIELD
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
                v_ExistingEndDate DATE;
                v_CalculatedStartDate DATE;
            BEGIN
                -- 1. Identify Sequencing Logic
                IF p_Action = 'INSERT' AND p_SchoolID IS NOT NULL THEN
                    SELECT MAX("SubscriptionEndDate") INTO v_ExistingEndDate
                    FROM "Subscriber"
                    WHERE "SchoolID" = p_SchoolID AND "IsDeleted" = FALSE AND "IsActive" = TRUE;
                    
                    IF v_ExistingEndDate >= CURRENT_DATE THEN
                        v_CalculatedStartDate := v_ExistingEndDate + INTERVAL '1 day';
                    ELSE
                        v_CalculatedStartDate := COALESCE(p_SubscriptionStartDate, CURRENT_DATE);
                    END IF;
                ELSE
                    v_CalculatedStartDate := COALESCE(p_SubscriptionStartDate, CURRENT_DATE);
                END IF;

                -- 2. Calculate End Date
                IF v_CalculatedStartDate IS NOT NULL AND p_DurationMonths IS NOT NULL THEN
                    v_SubscriptionEndDate := (v_CalculatedStartDate + (p_DurationMonths || ' months')::interval)::date;
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
                        "IsActive", "IsRenewed", "RenewalParentID", "PaymentProof", "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES (
                        p_SubscriptionNo, p_SubscriberType, p_SchoolID, p_PlanID,
                        v_CalculatedStartDate, v_SubscriptionEndDate, p_DurationMonths,
                        p_PaymentMode, COALESCE(p_PaymentStatus, 'Pending'), p_PaymentReference, p_PaymentDate,
                        p_AmountPaid, p_DiscountPercent, v_FinalAmount, p_ReferredByUserID, p_ReferralIncentive,
                        (COALESCE(p_PaymentStatus, 'Pending') = 'Paid'), p_IsRenewed, p_RenewalParentID, p_PaymentProof,
                        p_UserID, CURRENT_TIMESTAMP, FALSE
                    ) RETURNING "SubscriberID" INTO v_NewID;
                    
                    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subscriber added successfully'::VARCHAR, v_NewID;

                ELSIF p_Action = 'UPDATE' THEN
                    UPDATE "Subscriber" SET
                        "SubscriberType" = COALESCE(p_SubscriberType, "SubscriberType"),
                        "SchoolID" = COALESCE(p_SchoolID, "SchoolID"),
                        "PlanID" = COALESCE(p_PlanID, "PlanID"),
                        "SubscriptionStartDate" = COALESCE(v_CalculatedStartDate, "SubscriptionStartDate"),
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
                        "PaymentProof" = COALESCE(p_PaymentProof, "PaymentProof"),
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
        """)
    ]
