from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0096_subscriber_list_payment_proof'),
    ]

    operations = [
        # 1. Create ReferralIncentive table
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "ReferralIncentive" (
                "IncentiveID" SERIAL PRIMARY KEY,
                "SubscriberID" INT REFERENCES "Subscriber"("SubscriberID"),
                "PartnerID" INT REFERENCES "UserMaster"("UserID"),
                "Amount" NUMERIC(15,2),
                "Status" VARCHAR(20) DEFAULT 'Pending',
                "Remarks" TEXT,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "CreatedBy" INT,
                "IsDeleted" BOOLEAN DEFAULT FALSE
            );
        """),

        # 2. Create Procedure to get Referral Partner list (Using user provided logic)
        migrations.RunSQL("""
            CREATE OR REPLACE FUNCTION fn_referral_partner_get_list()
            RETURNS TABLE (
                "UserID" INT, 
                "UserCode" VARCHAR, 
                "UserName" VARCHAR, 
                "Email" VARCHAR,
                "ProfileName" VARCHAR
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT u."UserID", u."UserCode", u."UserName", u."Email", p."ProfileName"
                FROM "UserMaster" AS u
                INNER JOIN "ProfileMaster" AS p ON u."ProfileID" = p."ProfileID"
                WHERE p."ProfileName" = 'Referral Partner'
                AND u."IsDeleted" = FALSE;
            END;
            $$ LANGUAGE plpgsql;
        """),
    ]
