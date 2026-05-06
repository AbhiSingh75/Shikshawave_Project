from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0087_referral_management_support'),
    ]

    operations = [
        migrations.RunSQL("""
            CREATE OR REPLACE FUNCTION fn_subscription_report_summary(
                p_StartDate DATE DEFAULT NULL,
                p_EndDate DATE DEFAULT NULL
            ) RETURNS TABLE (
                total_subscribers INT,
                active_subscribers INT,
                total_revenue NUMERIC,
                pending_amount NUMERIC,
                total_referral NUMERIC,
                total_before_discount NUMERIC,
                total_discount NUMERIC
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    COUNT(*)::INT,
                    COUNT(*) FILTER (WHERE "IsActive" = TRUE)::INT,
                    COALESCE(SUM("FinalAmount") FILTER (WHERE "PaymentStatus" = 'Paid'), 0)::NUMERIC,
                    COALESCE(SUM("FinalAmount") FILTER (WHERE "PaymentStatus" = 'Pending'), 0)::NUMERIC,
                    COALESCE(SUM("ReferralIncentive"), 0)::NUMERIC,
                    COALESCE(SUM("AmountPaid"), 0)::NUMERIC,
                    COALESCE(SUM("AmountPaid" - "FinalAmount"), 0)::NUMERIC
                FROM "Subscriber"
                WHERE "IsDeleted" = FALSE
                    AND (p_StartDate IS NULL OR "CreatedAt" >= p_StartDate)
                    AND (p_EndDate IS NULL OR "CreatedAt" <= p_EndDate);
            END;
            $$ LANGUAGE plpgsql;
        """)
    ]
