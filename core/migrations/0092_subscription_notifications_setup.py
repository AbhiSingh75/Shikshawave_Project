from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0091_polar_stabilization'),
    ]

    operations = [
        migrations.RunSQL("""
            -- 1. Setup Notification Type
            INSERT INTO "NotificationTypeMaster" ("TypeName", "TypeCategory", "IconClass", "ColorCode", "IsActive", "CreatedAt")
            SELECT 'SubscriptionExpiry', 'System', 'fas fa-clock', '#f59e0b', TRUE, CURRENT_TIMESTAMP
            WHERE NOT EXISTS (SELECT 1 FROM "NotificationTypeMaster" WHERE "TypeName" = 'SubscriptionExpiry');

            -- 2. Create the Expiry Processing Procedure
            CREATE OR REPLACE FUNCTION "Proc_Subscription_ProcessExpiries"()
            RETURNS TABLE (
                "ProcessedCount" INT,
                "NotificationStatus" VARCHAR
            ) AS $$
            DECLARE
                v_Subscriber RECORD;
                v_RecipientIDs TEXT;
                v_DaysLeft INT;
                v_Title VARCHAR;
                v_Message TEXT;
                v_TotalProcessed INT := 0;
            BEGIN
                -- Find all active subscriptions ending within 7 days
                FOR v_Subscriber IN 
                    SELECT s."SubscriberID" as sub_id, s."SchoolId" as school_id, s."SubscriptionEndDate" as end_date, sp.planname, sm."SchoolName" as school_name
                    FROM "Subscriber" s
                    JOIN subscriptionplan sp ON s."PlanID" = sp.planid
                    JOIN "SchoolMaster" sm ON s."SchoolId" = sm."SchoolID"
                    WHERE s."IsActive" = TRUE AND s."IsDeleted" = FALSE
                      AND s."SubscriptionEndDate" >= CURRENT_DATE
                      AND s."SubscriptionEndDate" <= CURRENT_DATE + INTERVAL '7 days'
                LOOP
                    v_DaysLeft := (v_Subscriber.end_date - CURRENT_DATE);
                    
                    -- Only notify on 7, 5, 3, 2, 1, 0 days
                    IF v_DaysLeft IN (7, 5, 3, 2, 1, 0) THEN
                        
                        -- Define Message
                        v_Title := 'Subscription Expiry Alert';
                        IF v_DaysLeft = 0 THEN
                            v_Message := 'CRITICAL: Your subscription for ' || v_Subscriber.planname || ' expires TODAY! Renew now to avoid service interruption.';
                        ELSE
                            v_Message := 'Important: Your subscription for ' || v_Subscriber.planname || ' will expire in ' || v_DaysLeft || ' days. Please renew.';
                        END IF;

                        -- Check if we already sent THIS specific reminder today for this school
                        IF NOT EXISTS (
                            SELECT 1 FROM "NotificationMaster" 
                            WHERE "SchoolID" = v_Subscriber.school_id 
                              AND "Title" = v_Title 
                              AND "Message" = v_Message
                              AND "CreatedAt" >= CURRENT_DATE
                        ) THEN
                            
                            -- Get all administrative users for this school
                            SELECT string_agg("UserID"::text, ',') INTO v_RecipientIDs
                            FROM "UserMaster"
                            WHERE "SchoolID" = v_Subscriber.school_id AND "IsDeleted" = FALSE;

                            IF v_RecipientIDs IS NOT NULL AND v_RecipientIDs != '' THEN
                                -- Create Notification via existing system procedure
                                PERFORM "Proc_Notification_Create"(
                                    v_Subscriber.school_id,
                                    'SubscriptionExpiry',
                                    v_Title,
                                    v_Message,
                                    '/subscription/my/', -- Target URL
                                    'Subscription',
                                    v_Subscriber.sub_id::BIGINT,
                                    NULL, -- CreatedByUserID (System)
                                    v_RecipientIDs,
                                    (v_Subscriber.end_date::timestamp + INTERVAL '1 day') -- ExpiresAt
                                );
                                v_TotalProcessed := v_TotalProcessed + 1;
                            END IF;
                        END IF;
                    END IF;
                END LOOP;

                RETURN QUERY SELECT v_TotalProcessed, 'Finished'::VARCHAR;
            END;
            $$ LANGUAGE plpgsql;
        """)
    ]
