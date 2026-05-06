from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0104_subscriber_billing_prefill'),
    ]

    operations = [
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "TaxMaster" (
                "TaxID" SERIAL PRIMARY KEY,
                "TaxName" VARCHAR(100) NOT NULL,
                "TaxPercentage" NUMERIC(5, 2) NOT NULL,
                "TaxCode" VARCHAR(50) UNIQUE,
                "IsInclusive" BOOLEAN DEFAULT TRUE,
                "IsActive" BOOLEAN DEFAULT TRUE,
                "CreatedBy" INTEGER,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt" TIMESTAMP
            );

            -- Seed default GST
            INSERT INTO "TaxMaster" ("TaxName", "TaxPercentage", "TaxCode", "IsInclusive", "IsActive")
            VALUES ('GST', 18.00, 'GST-18', TRUE, TRUE)
            ON CONFLICT ("TaxCode") DO NOTHING;
        """),
    ]
