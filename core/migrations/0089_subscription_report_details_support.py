from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0088_subscription_reporting_summaries'),
    ]

    operations = [
        migrations.RunSQL("""
            CREATE OR REPLACE FUNCTION fn_subscription_report_details(
                p_Type VARCHAR,
                p_StartDate DATE DEFAULT NULL,
                p_EndDate DATE DEFAULT NULL
            ) RETURNS TABLE (
                SubscriptionNo VARCHAR,
                SubscriberName VARCHAR,
                PlanName VARCHAR,
                SubscriptionStartDate DATE,
                SubscriptionEndDate DATE,
                Amount NUMERIC,
                Status VARCHAR
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    s."SubscriptionNo"::VARCHAR,
                    COALESCE(sm."SchoolName", 'N/A')::VARCHAR,
                    sp.planname::VARCHAR,
                    s."SubscriptionStartDate",
                    s."SubscriptionEndDate",
                    CASE 
                        WHEN p_Type = 'referral' THEN s."ReferralIncentive"
                        ELSE s."FinalAmount"
                    END,
                    s."PaymentStatus"::VARCHAR
                FROM "Subscriber" s
                INNER JOIN subscriptionplan sp ON s."PlanID" = sp.planid
                LEFT JOIN "SchoolMaster" sm ON s."SchoolId" = sm."SchoolID"
                WHERE s."IsDeleted" = FALSE
                    AND (p_StartDate IS NULL OR s."CreatedAt" >= p_StartDate)
                    AND (p_EndDate IS NULL OR s."CreatedAt" <= p_EndDate)
                    AND (
                        p_Type = 'total' OR
                        (p_Type = 'active' AND s."IsActive" = TRUE) OR
                        (p_Type = 'paid' AND s."PaymentStatus" = 'Paid') OR
                        (p_Type = 'pending' AND s."PaymentStatus" = 'Pending') OR
                        (p_Type = 'referral' AND s."ReferredByUserID" IS NOT NULL)
                    );
            END;
            $$ LANGUAGE plpgsql;
        """)
    ]
