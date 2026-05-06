from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0086_drop_legacy_subscriber_func'),
    ]

    operations = [
        migrations.RunSQL("""
            DROP FUNCTION IF EXISTS fn_referral_get_list(INT, INT, INT, VARCHAR, VARCHAR, INT);
            
            CREATE OR REPLACE FUNCTION fn_referral_get_list(
                p_ReferredByUserID INT DEFAULT NULL,
                p_SchoolID INT DEFAULT NULL,
                p_PageNumber INT DEFAULT 1,
                p_PageSize INT DEFAULT 10,
                p_SortColumn VARCHAR DEFAULT 'createdat',
                p_SortOrder VARCHAR DEFAULT 'DESC',
                p_Search VARCHAR DEFAULT NULL
            ) RETURNS TABLE (
                subscriberid INT,
                subscriptionno VARCHAR,
                subscribername VARCHAR,
                planname VARCHAR,
                referredbyname VARCHAR,
                referralincentive NUMERIC,
                createdat TIMESTAMP,
                totalcount INT
            ) AS $$
            BEGIN
                RETURN QUERY
                WITH FilteredData AS (
                    SELECT 
                        s."SubscriberID" AS subscriberid,
                        s."SubscriptionNo"::VARCHAR AS subscriptionno,
                        COALESCE(sm."SchoolName", 'N/A')::VARCHAR AS subscribername,
                        sp.planname::VARCHAR AS planname,
                        COALESCE(um."UserName", 'N/A')::VARCHAR AS referredbyname,
                        s."ReferralIncentive" AS referralincentive,
                        s."CreatedAt" AS createdat,
                        COUNT(*) OVER()::INT AS totalcount
                    FROM "Subscriber" s
                    INNER JOIN subscriptionplan sp ON s."PlanID" = sp.planid
                    INNER JOIN "UserMaster" um ON s."ReferredByUserID" = um."UserID"
                    LEFT JOIN "SchoolMaster" sm ON s."SchoolId" = sm."SchoolID"
                    WHERE (p_ReferredByUserID IS NULL OR s."ReferredByUserID" = p_ReferredByUserID)
                        AND (p_SchoolID IS NULL OR s."SchoolId" = p_SchoolID)
                        AND (p_Search IS NULL OR 
                             s."SubscriptionNo" ILIKE '%' || p_Search || '%' OR 
                             sm."SchoolName" ILIKE '%' || p_Search || '%' OR 
                             um."UserName" ILIKE '%' || p_Search || '%')
                        AND s."ReferredByUserID" IS NOT NULL
                )
                SELECT * FROM FilteredData fd
                ORDER BY 
                    CASE WHEN p_SortOrder = 'ASC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('subscriptionno') THEN fd.subscriptionno
                            WHEN p_SortColumn IN ('subscribername') THEN fd.subscribername
                            WHEN p_SortColumn IN ('referredbyname') THEN fd.referredbyname
                            ELSE NULL
                        END
                    END ASC,
                    CASE WHEN p_SortOrder = 'DESC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('subscriptionno') THEN fd.subscriptionno
                            WHEN p_SortColumn IN ('subscribername') THEN fd.subscribername
                            WHEN p_SortColumn IN ('referredbyname') THEN fd.referredbyname
                            ELSE NULL
                        END
                    END DESC,
                    CASE WHEN p_SortOrder = 'ASC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('createdat') THEN fd.createdat::text
                            WHEN p_SortColumn IN ('referralincentive') THEN LPAD(fd.referralincentive::text, 20, '0')
                            ELSE NULL
                        END
                    END ASC,
                    CASE WHEN p_SortOrder = 'DESC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('createdat') THEN fd.createdat::text
                            WHEN p_SortColumn IN ('referralincentive') THEN LPAD(fd.referralincentive::text, 20, '0')
                            ELSE NULL
                        END
                    END DESC
                LIMIT p_PageSize
                OFFSET (p_PageNumber - 1) * p_PageSize;
            END;
            $$ LANGUAGE plpgsql;
        """)
    ]
