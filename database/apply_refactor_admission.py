
import os
import django
from django.db import connection

# Setup Django environment
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shikshawave.settings')
django.setup()

def apply_sql():
    sql_file_path = os.path.join(os.path.dirname(__file__), 'refactor_admission.sql')
    
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()
        
    try:
        with connection.cursor() as cursor:
            print(f"Applying SQL from {sql_file_path}...")
            cursor.execute(sql_content)
            print("Successfully applied refactor_admission.sql")
    except Exception as e:
        print(f"Error applying SQL: {e}")

if __name__ == "__main__":
    apply_sql()
