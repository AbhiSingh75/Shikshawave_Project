# core/migrations/0094_subscriber_include_school_code.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0093_subscription_renewal_sequencing'),
    ]

    operations = [
        migrations.RunSQL("""
            -- NUCLEAR CLEANUP: Drop every overloaded version of fn_subscriber_get_list 
            DO $$ 
            DECLARE 
                func_record RECORD;
            BEGIN
                FOR func_record IN 
                    SELECT proname, oid::regprocedure as sig
                    FROM pg_proc 
                    WHERE proname = 'fn_subscriber_get_list'
                LOOP
                    EXECUTE 'DROP FUNCTION ' || func_record.sig;
                END LOOP;
            END $$;

            -- UPDATED: Authority 33-column structure including schoolcode
            CREATE OR REPLACE FUNCTION fn_subscriber_get_list(
                p_SubscriberID INT DEFAULT NULL,
                p_PlanID INT DEFAULT NULL,
                p_PaymentStatus VARCHAR DEFAULT NULL,
                p_IncludeDeleted BOOLEAN DEFAULT FALSE,
                p_Search VARCHAR DEFAULT NULL,
                p_PageNumber INT DEFAULT 1,
                p_PageSize INT DEFAULT 10,
                p_SortColumn VARCHAR DEFAULT 'CreatedAt',
                p_SortOrder VARCHAR DEFAULT 'DESC',
                p_SchoolID INT DEFAULT NULL
            ) RETURNS TABLE (
                subscriberid INT,
                subscriptionno VARCHAR,
                subscribername VARCHAR,
                planname VARCHAR,
                plantype VARCHAR,
                planid INT,
                subscriptionstartdate DATE,
                subscriptionenddate DATE,
                durationmonths INT,
                paymentmode VARCHAR,
                paymentstatus VARCHAR,
                paymentreference VARCHAR,
                paymentdate TIMESTAMP,
                amountpaid NUMERIC,
                discountpercent NUMERIC,
                finalamount NUMERIC,
                referredbyuserid INT,
                referredbyname VARCHAR,
                referralincentive NUMERIC,
                isactive BOOLEAN,
                isrenewed BOOLEAN,
                renewalparentid INT,
                createdby INT,
                createdat TIMESTAMP,
                updatedby INT,
                updatedat TIMESTAMP,
                isdeleted BOOLEAN,
                schoolid INT,
                maxstudents INT,
                maxteachers INT,
                storagelimitmb INT,
                schoolcode VARCHAR, -- NEW Column
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
                        sp.plantype::VARCHAR AS plantype,
                        s."PlanID" AS planid,
                        s."SubscriptionStartDate" AS subscriptionstartdate,
                        s."SubscriptionEndDate" AS subscriptionenddate,
                        s."DurationMonths" AS durationmonths,
                        COALESCE(s."PaymentMode", '')::VARCHAR AS paymentmode,
                        COALESCE(s."PaymentStatus", 'Pending')::VARCHAR AS paymentstatus,
                        COALESCE(s."PaymentReference", '')::VARCHAR AS paymentreference,
                        s."PaymentDate" AS paymentdate,
                        s."AmountPaid" AS amountpaid,
                        s."DiscountPercent" AS discountpercent,
                        s."FinalAmount" AS finalamount,
                        s."ReferredByUserID" AS referredbyuserid,
                        COALESCE(um."UserName", 'N/A')::VARCHAR AS referredbyname,
                        s."ReferralIncentive" AS referralincentive,
                        s."IsActive" AS isactive,
                        s."IsRenewed" AS isrenewed,
                        s."RenewalParentID" AS renewalparentid,
                        s."CreatedBy" AS createdby,
                        s."CreatedAt" AS createdat,
                        s."UpdatedBy" AS updatedby,
                        s."UpdatedAt" AS updatedat,
                        s."IsDeleted" AS isdeleted,
                        s."SchoolId" AS schoolid,
                        sp.maxstudents,
                        sp.maxteachers,
                        sp.storagelimitmb,
                        COALESCE(sm."SchoolCode", 'N/A')::VARCHAR AS schoolcode, -- Selected NEW Column
                        COUNT(*) OVER()::INT AS totalcount
                    FROM "Subscriber" s
                    INNER JOIN subscriptionplan sp ON s."PlanID" = sp.planid
                    LEFT JOIN "SchoolMaster" sm ON s."SchoolId" = sm."SchoolID"
                    LEFT JOIN "UserMaster" um ON s."ReferredByUserID" = um."UserID"
                    WHERE (p_SubscriberID IS NULL OR s."SubscriberID" = p_SubscriberID)
                        AND (p_PlanID IS NULL OR s."PlanID" = p_PlanID)
                        AND (p_PaymentStatus IS NULL OR s."PaymentStatus" ILIKE p_PaymentStatus)
                        AND (COALESCE(s."IsDeleted", FALSE) = p_IncludeDeleted)
                        AND (p_SchoolID IS NULL OR s."SchoolId" = p_SchoolID)
                        AND (p_Search IS NULL OR 
                             s."SubscriptionNo" ILIKE '%' || p_Search || '%' OR 
                             sm."SchoolName" ILIKE '%' || p_Search || '%' OR
                             sm."SchoolCode" ILIKE '%' || p_Search || '%' OR
                             sp.planname ILIKE '%' || p_Search || '%')
                )
                SELECT * FROM FilteredData fd
                ORDER BY 
                    CASE WHEN p_SortOrder = 'ASC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('SubscriptionNo', 'subscriptionno') THEN fd.subscriptionno
                            WHEN p_SortColumn IN ('PlanName', 'planname') THEN fd.planname
                            WHEN p_SortColumn IN ('PaymentStatus', 'paymentstatus') THEN fd.paymentstatus
                            ELSE NULL
                        END
                    END ASC,
                    CASE WHEN p_SortOrder = 'DESC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('SubscriptionNo', 'subscriptionno') THEN fd.subscriptionno
                            WHEN p_SortColumn IN ('PlanName', 'planname') THEN fd.planname
                            WHEN p_SortColumn IN ('PaymentStatus', 'paymentstatus') THEN fd.paymentstatus
                            ELSE NULL
                        END
                    END DESC,
                    CASE WHEN p_SortOrder = 'ASC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('CreatedAt', 'createdat') THEN fd.createdat::text
                            WHEN p_SortColumn IN ('SubscriptionStartDate', 'subscriptionstartdate') THEN fd.subscriptionstartdate::text
                            WHEN p_SortColumn IN ('FinalAmount', 'finalamount') THEN LPAD(fd.finalamount::text, 20, '0')
                            ELSE NULL
                        END
                    END ASC,
                    CASE WHEN p_SortOrder = 'DESC' THEN
                        CASE 
                            WHEN p_SortColumn IN ('CreatedAt', 'createdat') THEN fd.createdat::text
                            WHEN p_SortColumn IN ('SubscriptionStartDate', 'subscriptionstartdate') THEN fd.subscriptionstartdate::text
                            WHEN p_SortColumn IN ('FinalAmount', 'finalamount') THEN LPAD(fd.finalamount::text, 20, '0')
                            ELSE NULL
                        END
                    END DESC
                LIMIT p_PageSize
                OFFSET (p_PageNumber - 1) * p_PageSize;
            END;
            $$ LANGUAGE plpgsql;
        """)
    ]
