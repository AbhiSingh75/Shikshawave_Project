# Generated migration for fee management tables

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_delete_geographicalmaster'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Create FeeStructure table
            CREATE TABLE IF NOT EXISTS "FeeStructure" (
                "FeeID" SERIAL PRIMARY KEY,
                "SchoolID" int NOT NULL,
                "ClassID" int NOT NULL,
                "FeeType" varchar(50) NOT NULL,
                "FeeName" varchar(100) NOT NULL,
                "Amount" decimal(10,2) NOT NULL,
                "IsMandatory" boolean DEFAULT TRUE,
                "IsActive" boolean DEFAULT TRUE,
                "CreatedBy" int NULL,
                "CreatedAt" timestamp DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ("SchoolID") REFERENCES "SchoolMaster"("SchoolID"),
                FOREIGN KEY ("CreatedBy") REFERENCES "UserMaster"("UserID")
            );
            """,
            reverse_sql='DROP TABLE IF EXISTS "FeeStructure";'
        ),
        
        migrations.RunSQL(
            """
            -- Create StudentFeeAssignment table
            CREATE TABLE IF NOT EXISTS "StudentFeeAssignment" (
                "AssignmentID" SERIAL PRIMARY KEY,
                "StudentID" int NOT NULL,
                "FeeID" int NOT NULL,
                "AssignedAmount" decimal(10,2) NOT NULL,
                "PaidAmount" decimal(10,2) DEFAULT 0,
                "DueAmount" decimal(10,2) NOT NULL,
                "Status" varchar(20) DEFAULT 'Pending',
                "AssignedDate" timestamp DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ("FeeID") REFERENCES "FeeStructure"("FeeID")
            );
            """,
            reverse_sql='DROP TABLE IF EXISTS "StudentFeeAssignment";'
        ),
        
        migrations.RunSQL(
            """
            -- Create FeePayment table
            CREATE TABLE IF NOT EXISTS "FeePayment" (
                "PaymentID" SERIAL PRIMARY KEY,
                "StudentID" int NOT NULL,
                "TotalAmount" decimal(10,2) NOT NULL,
                "PaymentMode" varchar(50) NOT NULL,
                "TransactionRef" varchar(100) NULL,
                "PaymentDate" timestamp DEFAULT CURRENT_TIMESTAMP,
                "ReceiptNumber" varchar(50) UNIQUE NOT NULL,
                "CreatedBy" int NULL,
                FOREIGN KEY ("CreatedBy") REFERENCES "UserMaster"("UserID")
            );
            """,
            reverse_sql='DROP TABLE IF EXISTS "FeePayment";'
        ),
        
        migrations.RunSQL(
            """
            -- Create PaymentReceipt table
            CREATE TABLE IF NOT EXISTS "PaymentReceipt" (
                "ReceiptID" SERIAL PRIMARY KEY,
                "PaymentID" int NOT NULL,
                "ReceiptType" varchar(20) NOT NULL,
                "ReceiptData" text NOT NULL,
                "GeneratedAt" timestamp DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ("PaymentID") REFERENCES "FeePayment"("PaymentID")
            );
            """,
            reverse_sql='DROP TABLE IF EXISTS "PaymentReceipt";'
        ),
        
        migrations.RunSQL(
            """
            -- Insert sample fee structure data
            INSERT INTO "FeeStructure" ("SchoolID", "ClassID", "FeeType", "FeeName", "Amount", "IsMandatory", "IsActive", "CreatedBy")
            SELECT 
                s."SchoolID", 
                1 as "ClassID", 
                'Admission' as "FeeType", 
                'Admission Fee' as "FeeName", 
                5000.00 as "Amount", 
                true as "IsMandatory", 
                true as "IsActive", 
                1 as "CreatedBy"
            FROM "SchoolMaster" s 
            WHERE s."IsDeleted" = false
            AND NOT EXISTS (SELECT 1 FROM "FeeStructure" WHERE "FeeName" = 'Admission Fee');
            
            INSERT INTO "FeeStructure" ("SchoolID", "ClassID", "FeeType", "FeeName", "Amount", "IsMandatory", "IsActive", "CreatedBy")
            SELECT 
                s."SchoolID", 
                1 as "ClassID", 
                'Tuition' as "FeeType", 
                'Tuition Fee' as "FeeName", 
                3000.00 as "Amount", 
                true as "IsMandatory", 
                true as "IsActive", 
                1 as "CreatedBy"
            FROM "SchoolMaster" s 
            WHERE s."IsDeleted" = false
            AND NOT EXISTS (SELECT 1 FROM "FeeStructure" WHERE "FeeName" = 'Tuition Fee');
            """,
            reverse_sql="DELETE FROM \"FeeStructure\" WHERE \"FeeName\" IN ('Admission Fee', 'Tuition Fee');"
        ),
    ]