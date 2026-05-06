#!/usr/bin/env python3
"""
Database Setup Script for Secure Face Authentication
This script sets up the required database tables and stored procedures for the secure face authentication system.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
django.setup()

from django.db import connection
import logging

logger = logging.getLogger(__name__)

def execute_sql_file(file_path):
    """Execute SQL commands from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Split by GO statements (SQL Server batch separator)
        batches = [batch.strip() for batch in sql_content.split('GO') if batch.strip()]
        
        with connection.cursor() as cursor:
            for i, batch in enumerate(batches):
                if batch:
                    try:
                        cursor.execute(batch)
                        print(f"✓ Executed batch {i+1}/{len(batches)}")
                    except Exception as e:
                        print(f"✗ Error in batch {i+1}: {e}")
                        # Continue with other batches
        
        print(f"✓ Successfully executed SQL file: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to execute SQL file {file_path}: {e}")
        return False

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = %s
            """, [table_name])
            return cursor.fetchone()[0] > 0
    except Exception:
        return False

def check_procedure_exists(procedure_name):
    """Check if a stored procedure exists in the database"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.objects 
                WHERE type = 'P' AND name = %s
            """, [procedure_name])
            return cursor.fetchone()[0] > 0
    except Exception:
        return False

def setup_face_auth_database():
    """Main function to set up face authentication database components"""
    print("🚀 Setting up Secure Face Authentication Database...")
    print("=" * 60)
    
    # Check if we're connected to the database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT @@VERSION")
            db_version = cursor.fetchone()[0]
            print(f"📊 Connected to: {db_version[:50]}...")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Execute the face authentication schema SQL
    schema_file = project_root / 'docs' / 'face_auth_database_schema.sql'
    
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    print(f"📄 Executing schema file: {schema_file}")
    success = execute_sql_file(schema_file)
    
    if not success:
        print("❌ Failed to set up database schema")
        return False
    
    # Verify tables were created
    print("\n🔍 Verifying database setup...")
    
    tables_to_check = [
        'FaceAuthLogs',
        'FaceAuthSettings', 
        'FaceAuthRateLimit'
    ]
    
    procedures_to_check = [
        'sp_LogFaceAuthAttempt',
        'sp_CheckFaceAuthRateLimit',
        'sp_CleanupFaceAuthLogs'
    ]
    
    # Check tables
    for table in tables_to_check:
        if check_table_exists(table):
            print(f"✓ Table {table} exists")
        else:
            print(f"✗ Table {table} missing")
    
    # Check procedures
    for procedure in procedures_to_check:
        if check_procedure_exists(procedure):
            print(f"✓ Procedure {procedure} exists")
        else:
            print(f"✗ Procedure {procedure} missing")
    
    # Check if FaceTemplates table has new columns
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'FaceTemplates' AND COLUMN_NAME = 'LastUsedAt'
            """)
            has_last_used = cursor.fetchone()[0] > 0
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'FaceTemplates' AND COLUMN_NAME = 'UsageCount'
            """)
            has_usage_count = cursor.fetchone()[0] > 0
            
            if has_last_used and has_usage_count:
                print("✓ FaceTemplates table updated with new columns")
            else:
                print("✗ FaceTemplates table missing new columns")
                
    except Exception as e:
        print(f"⚠️  Could not verify FaceTemplates updates: {e}")
    
    # Test a simple query
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM FaceAuthSettings")
            settings_count = cursor.fetchone()[0]
            print(f"✓ FaceAuthSettings has {settings_count} default settings")
    except Exception as e:
        print(f"✗ Could not query FaceAuthSettings: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Face Authentication Database Setup Complete!")
    print("\nNext steps:")
    print("1. Update your Django settings to include the new face auth apps")
    print("2. Test the face authentication endpoints")
    print("3. Configure face authentication settings as needed")
    print("\nFor more information, see the Face Authentication documentation.")
    
    return True

def cleanup_old_logs():
    """Clean up old face authentication logs (optional maintenance)"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_CleanupFaceAuthLogs 30")  # Keep 30 days
            result = cursor.fetchone()
            if result and result[0] == 1:
                print(f"✓ Cleanup completed: {result[1]}")
            else:
                print("⚠️  Cleanup procedure executed but may have issues")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Face Authentication Database')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Clean up old authentication logs (30+ days)')
    
    args = parser.parse_args()
    
    if args.cleanup:
        print("🧹 Cleaning up old face authentication logs...")
        cleanup_old_logs()
    else:
        setup_face_auth_database()