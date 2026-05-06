from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0100_update_subscriber_get_perc'),
    ]

    operations = [
        # Adding missing audit columns to ReferralIncentive
        migrations.RunSQL("""
            ALTER TABLE "ReferralIncentive" 
            ADD COLUMN IF NOT EXISTS "UpdatedBy" INT,
            ADD COLUMN IF NOT EXISTS "UpdatedAt" TIMESTAMP;
        """),
    ]
