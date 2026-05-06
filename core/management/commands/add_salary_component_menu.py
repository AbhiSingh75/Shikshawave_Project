from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add Salary Component menu under Master Data'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Get Master Data parent menu ID
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Master Data' AND ISNULL(IsDeleted, 0) = 0
                """)
                result = cursor.fetchone()
                
                if not result:
                    self.stdout.write(self.style.ERROR('Master Data menu not found'))
                    return
                
                master_data_menu_id = result[0]
                
                # Check if menu already exists
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuURL = '/master-data/salary-component/' 
                    AND ISNULL(IsDeleted, 0) = 0
                """)
                
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('Salary Component menu already exists'))
                    return
                
                # Insert menu
                cursor.execute("""
                    INSERT INTO MenuMaster (
                        MenuName, MenuURL, MenuIcon, ParentMenuID, 
                        DisplayOrder, IsActive, CreatedAt, IsDeleted
                    )
                    VALUES (
                        'Salary Components',
                        '/master-data/salary-component/',
                        'fas fa-money-check-alt',
                        %s,
                        50,
                        1,
                        GETDATE(),
                        0
                    );
                    SELECT SCOPE_IDENTITY();
                """, [master_data_menu_id])
                
                new_menu_id = cursor.fetchone()[0]
                
                # Add permissions for Super Admin (ProfileID = 1)
                cursor.execute("""
                    INSERT INTO ProfileMenuMapping (
                        ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, 
                        CreatedAt, IsDeleted
                    )
                    VALUES (1, %s, 1, 1, 1, 1, GETDATE(), 0)
                """, [new_menu_id])
                
                # Add permissions for School Admin (ProfileID = 2)
                cursor.execute("""
                    INSERT INTO ProfileMenuMapping (
                        ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, 
                        CreatedAt, IsDeleted
                    )
                    VALUES (2, %s, 1, 1, 1, 1, GETDATE(), 0)
                """, [new_menu_id])
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully added Salary Component menu (MenuID: {new_menu_id})'
                ))
                self.stdout.write(self.style.SUCCESS(
                    'Permissions added for Super Admin and School Admin'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
