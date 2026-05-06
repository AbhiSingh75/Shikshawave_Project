"""Check TemplateSettings columns and fix if needed"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check and fix TemplateSettings table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check columns
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'TemplateSettings'
            """)
            columns = [r[0] for r in cursor.fetchall()]
            self.stdout.write(f"TemplateSettings columns: {columns}")
            
            # Check if IsDeleted exists
            if 'IsDeleted' not in columns:
                self.stdout.write(self.style.WARNING("IsDeleted column not found, adding it..."))
                cursor.execute('ALTER TABLE "TemplateSettings" ADD COLUMN "IsDeleted" BOOLEAN DEFAULT FALSE')
                self.stdout.write(self.style.SUCCESS("Added IsDeleted column"))
            
            # Check content
            cursor.execute('SELECT * FROM "TemplateSettings" LIMIT 5')
            rows = cursor.fetchall()
            self.stdout.write(f"\nTemplateSettings has {len(rows)} sample rows")
            for r in rows:
                self.stdout.write(f"  {r}")
