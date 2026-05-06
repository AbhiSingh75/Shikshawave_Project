from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add FeeType Management menu item to Master Data section'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Get Master Data menu ID
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Master Data' AND ISNULL(IsDeleted, 0) = 0
                """)
                
                master_data_result = cursor.fetchone()
                if not master_data_result:
                    self.stdout.write(
                        self.style.ERROR('Master Data menu not found. Please run setup_master_data_menu first.')
                    )
                    return
                
                master_data_id = master_data_result[0]
                
                # Check if FeeType menu already exists
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Fee Type Management' AND ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                """, [master_data_id])
                
                if cursor.fetchone():
                    self.stdout.write(
                        self.style.WARNING('Fee Type Management menu already exists.')
                    )
                    return
                
                # Get the next display order for Master Data sub-menus
                cursor.execute("""
                    SELECT ISNULL(MAX(DisplayOrder), 0) + 1 
                    FROM MenuMaster 
                    WHERE ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                """, [master_data_id])
                next_order = cursor.fetchone()[0]
                
                # Insert FeeType Management menu
                cursor.execute("""
                    INSERT INTO MenuMaster (
                        MenuName, MenuURL, Icon, DisplayOrder, ParentMenuID, 
                        IsActive, CreatedBy, CreatedAt
                    ) VALUES (
                        'Fee Type Management', '/master-data/fee-type/', 'fas fa-money-bill-wave', %s, %s, 
                        1, 1, GETDATE()
                    )
                """, [next_order, master_data_id])
                
                # Get the inserted menu ID
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Fee Type Management' AND ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                """, [master_data_id])
                
                fee_type_menu_id = cursor.fetchone()[0]
                
                # Add menu permissions for Super Admin and School Admin
                cursor.execute("""
                    INSERT INTO ProfileMenuMapping (
                        ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, 
                        CreatedBy, CreatedAt, IsDeleted
                    ) VALUES 
                    (1, %s, 1, 1, 1, 1, 1, GETDATE(), 0),
                    (2, %s, 1, 1, 1, 1, 1, GETDATE(), 0)
                """, [fee_type_menu_id, fee_type_menu_id])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully added Fee Type Management menu with ID: {fee_type_menu_id}'
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        'Added permissions for Super Admin and School Admin profiles'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error adding FeeType menu: {str(e)}')
            )
