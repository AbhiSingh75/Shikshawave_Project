from django.core.management.base import BaseCommand
from django.db import connection
import os

class Command(BaseCommand):
    help = 'Updates the Proc_UserList_Get stored procedure'

    def handle(self, *args, **kwargs):
        sql_path = os.path.join(os.getcwd(), 'core', 'sql', 'user_list_proc.sql')
        self.stdout.write(f"Reading SQL from {sql_path}")
        
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        with connection.cursor() as cursor:
            cursor.execute(sql)
            
        self.stdout.write(self.style.SUCCESS('Successfully updated Proc_UserList_Get'))
