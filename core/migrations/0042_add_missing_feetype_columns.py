# Generated manually to add missing columns to FeeType_Master table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_auto_20251006_2346'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Add missing columns to FeeType_Master table
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'UpdatedBy')
            ALTER TABLE FeeType_Master ADD UpdatedBy INT NULL;
            
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'UpdatedAt')
            ALTER TABLE FeeType_Master ADD UpdatedAt DATETIME NULL;
            
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'ClassId')
            ALTER TABLE FeeType_Master ADD ClassId INT NULL;
            
            -- Add foreign key constraints
            IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_FeeType_Master_UpdatedBy')
            ALTER TABLE FeeType_Master ADD CONSTRAINT FK_FeeType_Master_UpdatedBy 
            FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID);
            
            IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_FeeType_Master_ClassId')
            ALTER TABLE FeeType_Master ADD CONSTRAINT FK_FeeType_Master_ClassId 
            FOREIGN KEY (ClassId) REFERENCES ClassMaster(ClassID);
            """,
            reverse_sql="""
            -- Remove the added columns
            IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'UpdatedBy')
            ALTER TABLE FeeType_Master DROP COLUMN UpdatedBy;
            
            IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'UpdatedAt')
            ALTER TABLE FeeType_Master DROP COLUMN UpdatedAt;
            
            IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('FeeType_Master') AND name = 'ClassId')
            ALTER TABLE FeeType_Master DROP COLUMN ClassId;
            """
        ),
    ]
