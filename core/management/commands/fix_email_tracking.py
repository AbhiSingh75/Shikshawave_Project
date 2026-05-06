"""Check and fix EmailTracking table"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check and fix EmailTracking table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if EmailTracking table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name ILIKE 'emailtracking'
            """)
            tables = cursor.fetchall()
            self.stdout.write(f"EmailTracking table: {tables}")
            
            if not tables:
                self.stdout.write(self.style.WARNING("EmailTracking table not found!"))
                return
            
            # Get column names
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name ILIKE 'emailtracking'
            """)
            columns = [r[0] for r in cursor.fetchall()]
            self.stdout.write(f"Columns: {columns}")
            
            # Add SchoolCode if missing
            if 'SchoolCode' not in columns and 'school_code' not in columns:
                self.stdout.write(self.style.WARNING("SchoolCode column not found, adding it..."))
                try:
                    cursor.execute('ALTER TABLE "EmailTracking" ADD COLUMN "SchoolCode" VARCHAR(50)')
                    self.stdout.write(self.style.SUCCESS("Added SchoolCode column"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Done!"))
