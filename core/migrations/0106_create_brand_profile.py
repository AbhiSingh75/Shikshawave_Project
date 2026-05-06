from django.db import migrations, models
import os
import base64

def seed_brand_profile(apps, schema_editor):
    try:
        from django.conf import settings
        logo_path = os.path.join(settings.BASE_DIR, 'core', 'static', 'images', 'ShikshaWave_Logo.png')
        logo_binary = None
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_binary = f.read()
        
        # Use separate cursor for raw SQL seeding to ensure binary compatibility
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO "BrandProfile" 
                ("BrandName", "BrandLogo", "GSTIN", "Address", "Phone", "Email", "Website", "IsActive")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, [
                'ShikshaWave', 
                logo_binary, 
                '09AAAAA0000A1Z5', 
                'Plot No. 4, IT Park, Sector 62, Noida, UP - 201309', 
                '+91 99999 88888', 
                'billing@shikshawave.com', 
                'www.shikshawave.com', 
                True
            ])
    except Exception as e:
        print(f"Error seeding BrandProfile: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0105_create_tax_master'),
    ]

    operations = [
        migrations.RunSQL("""
            CREATE TABLE IF NOT EXISTS "BrandProfile" (
                "ProfileID" SERIAL PRIMARY KEY,
                "BrandName" VARCHAR(100) NOT NULL,
                "BrandLogo" BYTEA,
                "GSTIN" VARCHAR(15),
                "Address" TEXT,
                "Phone" VARCHAR(20),
                "Email" VARCHAR(100),
                "Website" VARCHAR(100),
                "IsActive" BOOLEAN DEFAULT TRUE,
                "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                "UpdatedAt" TIMESTAMP
            );
        """),
        migrations.RunPython(seed_brand_profile),
    ]
