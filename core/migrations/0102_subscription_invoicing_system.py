from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0101_referral_incentive_audit'),
    ]

    operations = [
        # 1. Platform Configuration Table (ShikshaWave Identity)
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "PlatformConfig" (
                "ConfigID" SERIAL PRIMARY KEY,
                "KeyName" VARCHAR(50) UNIQUE NOT NULL,
                "KeyValue" TEXT NOT NULL,
                "Category" VARCHAR(20) DEFAULT 'GENERAL',
                "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Seed platforms legal identity
            INSERT INTO "PlatformConfig" ("KeyName", "KeyValue", "Category") 
            VALUES 
            ('PLATFORM_GSTIN', 'GST_PLACEHOLDER', 'BILLING'),
            ('PLATFORM_ADDRESS', 'ADDRESS_PLACEHOLDER', 'BILLING')
            ON CONFLICT ("KeyName") DO NOTHING;
        """),

        # 2. Subscription Billing Information (Institutional Details)
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "SubscriptionBillingInfo" (
                "SubscriberID" INT PRIMARY KEY REFERENCES "Subscriber"("SubscriberID"),
                "GSTIN" VARCHAR(15),
                "CompanyName" VARCHAR(255),
                "BillingAddress" TEXT,
                "StateCode" VARCHAR(10),
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """),

        # 3. Subscription Invoice Records
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "SubscriptionInvoice" (
                "InvoiceID" SERIAL PRIMARY KEY,
                "SubscriberID" INT NOT NULL REFERENCES "Subscriber"("SubscriberID"),
                "InvoiceNo" VARCHAR(50) UNIQUE NOT NULL,
                "InvoiceDate" DATE DEFAULT CURRENT_DATE,
                "BaseAmount" NUMERIC(10,2) NOT NULL,
                "TaxAmount" NUMERIC(10,2) NOT NULL,
                "TotalAmount" NUMERIC(10,2) NOT NULL,
                "Status" VARCHAR(20) DEFAULT 'Generated',
                "PDFProof" bytea,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """),
    ]
