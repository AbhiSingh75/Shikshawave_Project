import os
import sys
import django

# Bootstrap Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
django.setup()

from django.db import connection

def run_sql_file(path):
    print(f"Executing SQL file: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with connection.cursor() as cur:
        cur.execute(sql)
    print("✅ SQL file executed successfully.")

if __name__ == '__main__':
    sql_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exam_management_procedures.sql')
    if os.path.exists(sql_file):
        run_sql_file(sql_file)
    else:
        print(f"❌ SQL file not found: {sql_file}")
