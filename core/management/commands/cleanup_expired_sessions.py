from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update LogoutTime for expired sessions'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE "user_sessions" 
                SET "LogoutTime" = CURRENT_TIMESTAMP 
                WHERE "expires_at" < CURRENT_TIMESTAMP 
                AND "LogoutTime" IS NULL
            """)
            rows = cursor.rowcount
            connection.commit()
            logger.info(f"Updated LogoutTime for {rows} expired sessions")
            self.stdout.write(self.style.SUCCESS(f'Updated {rows} expired sessions'))
