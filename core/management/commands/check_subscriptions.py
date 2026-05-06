from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for expiring subscriptions and generates notifications for school admins'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting subscription expiry check...'))
        
        try:
            with connection.cursor() as cursor:
                # Execute the authoritative processing procedure
                cursor.execute('SELECT * FROM "Proc_Subscription_ProcessExpiries"()')
                result = cursor.fetchone()
                
                if result:
                    count = result[0]
                    status = result[1]
                    self.stdout.write(self.style.SUCCESS(f'Processed {count} expiries. Status: {status}'))
                else:
                    self.stdout.write(self.style.WARNING('No data returned from Proc_Subscription_ProcessExpiries'))
                    
        except Exception as e:
            logger.error(f'Error during check_subscriptions: {e}')
            self.stdout.write(self.style.ERROR(f'Failed to process expiries: {e}'))
