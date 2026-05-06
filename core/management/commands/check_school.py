"""Check SchoolMaster columns"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check SchoolMaster columns'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'SchoolMaster'
                ORDER BY ordinal_position
            """)
            columns = [r[0] for r in cursor.fetchall()]
            self.stdout.write(f"SchoolMaster columns: {columns}")
            
            # Find logo-related columns
            logo_cols = [c for c in columns if 'logo' in c.lower()]
            self.stdout.write(f"Logo-related columns: {logo_cols}")
