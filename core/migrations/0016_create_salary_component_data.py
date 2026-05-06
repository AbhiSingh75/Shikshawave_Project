# Generated migration for SalaryComponentMaster table creation and sample data

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_add_salary_component_master'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Create SalaryComponentMaster table if it doesn't exist
            CREATE TABLE IF NOT EXISTS "SalaryComponentMaster" (
                "ComponentID" SERIAL PRIMARY KEY,
                "SchoolID" int NOT NULL,
                "ComponentName" varchar(100) NOT NULL,
                "ComponentType" varchar(20) NOT NULL CHECK ("ComponentType" IN ('Earning', 'Deduction')),
                "CreatedBy" int NULL,
                "CreatedAt" timestamp DEFAULT CURRENT_TIMESTAMP,
                "IsDeleted" boolean DEFAULT FALSE,
                FOREIGN KEY ("SchoolID") REFERENCES "SchoolMaster"("SchoolID"),
                FOREIGN KEY ("CreatedBy") REFERENCES "UserMaster"("UserID")
            );
            """,
            reverse_sql='DROP TABLE IF EXISTS "SalaryComponentMaster";'
        ),
        
        migrations.RunSQL(
            """
            -- Insert sample salary components for SchoolID 3
            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Basic Salary', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Basic Salary');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'House Rent Allowance (HRA)', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'House Rent Allowance (HRA)');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Dearness Allowance (DA)', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Dearness Allowance (DA)');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Transport Allowance', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Transport Allowance');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Medical Allowance', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Medical Allowance');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Special Allowance', 'Earning', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Special Allowance');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Provident Fund (PF)', 'Deduction', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Provident Fund (PF)');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Professional Tax (PT)', 'Deduction', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Professional Tax (PT)');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Income Tax (TDS)', 'Deduction', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Income Tax (TDS)');

            INSERT INTO "SalaryComponentMaster" 
            ("SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted")
            SELECT 3, 'Other Deductions', 'Deduction', 2, CURRENT_TIMESTAMP, false
            WHERE NOT EXISTS (SELECT 1 FROM "SalaryComponentMaster" WHERE "SchoolID" = 3 AND "ComponentName" = 'Other Deductions');
            """,
            reverse_sql="DELETE FROM \"SalaryComponentMaster\" WHERE \"SchoolID\" = 3;"
        ),
    ]
