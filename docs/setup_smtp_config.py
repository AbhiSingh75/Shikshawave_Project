"""Insert default SMTP and add menu entry"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.db import connection
from django.conf import settings
from django.core.signing import Signer

signer = Signer()

print("=" * 60)
print("ShikshaWave SMTP Configuration Setup")
print("=" * 60)

# Get current settings
smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.hostinger.com')
smtp_port = getattr(settings, 'EMAIL_PORT', 587)
use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
username = getattr(settings, 'EMAIL_HOST_USER', '')
password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

print(f"\n1. Default SMTP from settings.py:")
print(f"   Host: {smtp_host}")
print(f"   Port: {smtp_port}")
print(f"   Username: {username}")
print(f"   From: {from_email}")

with connection.cursor() as cursor:
    # Check if default already exists
    cursor.execute('SELECT "ConfigID" FROM "SMTPConfiguration" WHERE "SchoolID" IS NULL AND "IsDeleted" = FALSE')
    existing = cursor.fetchone()
    
    if existing:
        print(f"\n   Default SMTP already exists (ConfigID: {existing[0]}). Skipping.")
    else:
        # Encrypt password
        encrypted_password = signer.sign(password)
        
        # Insert default configuration
        cursor.execute('''
            INSERT INTO "SMTPConfiguration" (
                "SchoolID", "ConfigName", "SMTPHost", "SMTPPort", 
                "UseTLS", "UseSSL", "Username", "Password", 
                "FromEmail", "FromName", "IsActive", "IsDefault",
                "CreatedBy", "CreatedAt", "IsDeleted"
            ) VALUES (
                NULL, 'ShikshaWave Default', %s, %s,
                %s, %s, %s, %s,
                %s, 'ShikshaWave', TRUE, TRUE,
                1, CURRENT_TIMESTAMP, FALSE
            ) RETURNING "ConfigID"
        ''', [smtp_host, smtp_port, use_tls, use_ssl, username, encrypted_password, from_email])
        
        result = cursor.fetchone()
        print(f"\n   Default SMTP inserted! ConfigID: {result[0]}")

print("\n2. Adding menu entry...")

with connection.cursor() as cursor:
    # Get Master Data menu ID
    cursor.execute('''
        SELECT "MenuID" FROM "MenuMaster" 
        WHERE "MenuName" = 'Master Data' AND COALESCE("IsDeleted", FALSE) = FALSE
    ''')
    master_data = cursor.fetchone()
    
    if not master_data:
        print("   Warning: Master Data menu not found!")
    else:
        master_data_id = master_data[0]
        print(f"   Master Data MenuID: {master_data_id}")
        
        # Check if SMTP menu already exists
        cursor.execute('''
            SELECT "MenuID" FROM "MenuMaster"
            WHERE "MenuURL" = '/master-data/smtp-configuration/'
            AND COALESCE("IsDeleted", FALSE) = FALSE
        ''')
        existing_menu = cursor.fetchone()
        
        if existing_menu:
            print(f"   SMTP Configuration menu already exists (MenuID: {existing_menu[0]})")
        else:
            # Insert menu
            cursor.execute('''
                INSERT INTO "MenuMaster" (
                    "MenuName", "MenuURL", "Icon", "ParentMenuID",
                    "DisplayOrder", "IsActive", "CreatedAt", "IsDeleted"
                ) VALUES (
                    'SMTP Configuration', '/master-data/smtp-configuration/',
                    'fas fa-envelope-open-text', %s,
                    55, TRUE, CURRENT_TIMESTAMP, FALSE
                ) RETURNING "MenuID"
            ''', [master_data_id])
            
            menu_id = cursor.fetchone()[0]
            print(f"   SMTP Configuration menu created! MenuID: {menu_id}")
            
            # Add Super Admin permissions
            cursor.execute('''
                INSERT INTO "ProfileMenuMapping" (
                    "ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete",
                    "CreatedAt", "IsDeleted"
                ) VALUES (1, %s, TRUE, TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, FALSE)
            ''', [menu_id])
            print("   Super Admin permissions added")
            
            # Add School Admin permissions
            cursor.execute('''
                INSERT INTO "ProfileMenuMapping" (
                    "ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete",
                    "CreatedAt", "IsDeleted"
                ) VALUES (2, %s, TRUE, TRUE, TRUE, TRUE, CURRENT_TIMESTAMP, FALSE)
            ''', [menu_id])
            print("   School Admin permissions added")

print("\n" + "=" * 60)
print("Setup completed successfully!")
print("=" * 60)
print("\nYou can now access SMTP Configuration at:")
print("  /master-data/smtp-configuration/")
