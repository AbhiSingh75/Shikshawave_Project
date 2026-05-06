"""Show exact fee breakdown format"""
from django.core.management.base import BaseCommand
from django.db import connection
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM proc_payment_receipt_get(NULL, 'STU0000003'::VARCHAR)")
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                data = dict(zip(columns, row))
                fb = data.get('fee_breakdown')
                if fb:
                    parsed = json.loads(fb)
                    self.stdout.write(f"fee_breakdown has {len(parsed)} items")
                    if parsed:
                        self.stdout.write(f"Keys in first item: {list(parsed[0].keys())}")
                        self.stdout.write(f"First item data: {parsed[0]}")
