"""Apply PDF fix SQL - Django management command script"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Apply PDF email fixes'

    def handle(self, *args, **options):
        # Get project root from settings.BASE_DIR
        sql_file = os.path.join(settings.BASE_DIR, 'fix_pdf_issues.sql')
        
        self.stdout.write("Reading SQL file...")
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        self.stdout.write("Executing SQL fixes...")
        with connection.cursor() as cursor:
            # Execute the SQL in chunks (PostgreSQL handles this better)
            statements = sql_content.split(';')
            for stmt in statements:
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--') and not stmt.startswith('SELECT'):
                    try:
                        cursor.execute(stmt + ';')
                        self.stdout.write(f"OK: {stmt[:60]}...")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Skip: {str(e)[:80]}"))
            
            # Verification
            try:
                cursor.execute('SELECT COUNT(*) FROM "TemplateSettings"')
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"TemplateSettings has {count} rows"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"TemplateSettings check failed: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Done!"))
