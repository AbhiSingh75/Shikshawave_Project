import os
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Applies Fee Type stored procedures for PostgreSQL compatibility'

    def handle(self, *args, **options):
        sql_path = os.path.join(settings.BASE_DIR, 'core', 'sql', 'fee_type_procedures.sql')
        self.stdout.write(f"Reading SQL file: {sql_path}")
        
        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f"File not found: {sql_path}"))
            return

        try:
            with open(sql_path, 'r') as f:
                sql_content = f.read()
            
            with connection.cursor() as cursor:
                self.stdout.write("Executing SQL...")
                cursor.execute(sql_content)
                self.stdout.write(self.style.SUCCESS('Successfully applied Fee Type procedures.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error applying procedures: {e}'))
