from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0098_harden_referral_procedure'),
    ]

    operations = [
        # Expanding ReferralIncentive Table
        migrations.RunSQL("""
            ALTER TABLE "ReferralIncentive" 
            ADD COLUMN IF NOT EXISTS "IncentivePercentage" NUMERIC(5,2),
            ADD COLUMN IF NOT EXISTS "InvoiceID" VARCHAR(100);
        """),
    ]
