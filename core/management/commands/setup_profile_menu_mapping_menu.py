from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup Profile Menu Mapping sub-menu under Master Data menu'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # First, ensure Master Data menu exists
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0)
                    BEGIN
                        INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
                        VALUES ('Master Data', 1, NULL, NULL, 'fas fa-database', 1, 1, GETDATE(), 0)
                    END
                """)
                
                # Get Master Data menu ID
                cursor.execute("SELECT MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0")
                master_data_menu = cursor.fetchone()
                
                if not master_data_menu:
                    self.stdout.write(self.style.ERROR('Master Data menu not found'))
                    return
                
                master_data_menu_id = master_data_menu[0]
                
                # Check if Profile Menu Mapping menu already exists
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Profile Menu Mapping' AND ParentMenuID = %s AND IsDeleted = 0
                """, [master_data_menu_id])
                
                existing_menu = cursor.fetchone()
                
                if existing_menu:
                    self.stdout.write(self.style.WARNING('Profile Menu Mapping menu already exists'))
                    return
                
                # Insert Profile Menu Mapping sub-menu
                cursor.execute("""
                    INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
                    VALUES ('Profile Menu Mapping', 2, %s, '/master-data/profile-menu-mapping/', 'fas fa-users-cog', 1, 1, GETDATE(), 0)
                """, [master_data_menu_id])
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully created Profile Menu Mapping sub-menu under Master Data')
                )
                
        except Exception as e:
            logger.error(f"Error setting up Profile Menu Mapping menu: {e}")
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
