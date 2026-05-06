from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add Holiday Management menu item to Master Data section'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Get Master Data menu ID
                cursor.execute("""
                    SELECT "MenuID" FROM "MenuMaster" 
                    WHERE "MenuName" = 'Master Data' AND "IsDeleted" = FALSE
                """)
                
                master_data_result = cursor.fetchone()
                if not master_data_result:
                    self.stdout.write(
                        self.style.ERROR('Master Data menu not found.')
                    )
                    return
                
                master_data_id = master_data_result[0]
                
                # Check if Holiday menu already exists
                cursor.execute("""
                    SELECT "MenuID" FROM "MenuMaster" 
                    WHERE "MenuName" = 'Holiday Management' AND "ParentMenuID" = %s AND "IsDeleted" = FALSE
                """, [master_data_id])
                
                if cursor.fetchone():
                    self.stdout.write(
                        self.style.WARNING('Holiday Management menu already exists.')
                    )
                    return
                
                # Get the next display order
                cursor.execute("""
                    SELECT COALESCE(MAX("DisplayOrder"), 0) + 1 
                    FROM "MenuMaster" 
                    WHERE "ParentMenuID" = %s AND "IsDeleted" = FALSE
                """, [master_data_id])
                next_order = cursor.fetchone()[0]
                
                # Insert Holiday Management menu
                cursor.execute("""
                    INSERT INTO "MenuMaster" (
                        "MenuName", "MenuURL", "Icon", "DisplayOrder", "ParentMenuID", 
                        "IsActive", "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES (
                        'Holiday Management', '/master-data/holidays/', 'fas fa-calendar-check', %s, %s, 
                        TRUE, 1, CURRENT_TIMESTAMP, FALSE
                    )
                """, [next_order, master_data_id])
                
                # Get the inserted menu ID
                cursor.execute("""
                    SELECT "MenuID" FROM "MenuMaster" 
                    WHERE "MenuName" = 'Holiday Management' AND "ParentMenuID" = %s AND "IsDeleted" = FALSE
                """, [master_data_id])
                
                holiday_menu_id = cursor.fetchone()[0]
                
                # Add menu permissions for Super Admin (1) and School Admin (2)
                cursor.execute("""
                    INSERT INTO "ProfileMenuMapping" (
                        "ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete", 
                        "CreatedBy", "CreatedAt", "IsDeleted"
                    ) VALUES 
                    (1, %s, TRUE, TRUE, TRUE, TRUE, 1, CURRENT_TIMESTAMP, FALSE),
                    (2, %s, TRUE, TRUE, TRUE, TRUE, 1, CURRENT_TIMESTAMP, FALSE)
                """, [holiday_menu_id, holiday_menu_id])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully added Holiday Management menu with ID: {holiday_menu_id}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding Holiday menu: {str(e)}')
            )
