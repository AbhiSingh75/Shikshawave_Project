from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0097_referral_tracking_system'),
    ]

    operations = [
        # Hardening the referral partner list procedure to be case-insensitive
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
                WHERE p."ProfileName" ILIKE 'Referral Partner'
                AND u."IsDeleted" = FALSE;
            END;
            $$ LANGUAGE plpgsql;
        """),
    ]
