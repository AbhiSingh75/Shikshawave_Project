from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Setup Master Data menu and Menu Data sub-menu'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                # Check if Master Data menu already exists
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Master Data' AND ISNULL(IsDeleted, 0) = 0
                """)
                master_data_menu = cursor.fetchone()
                
                if master_data_menu:
                    master_data_id = master_data_menu[0]
                    self.stdout.write(
                        self.style.WARNING('Master Data menu already exists with ID: ' + str(master_data_id))
                    )
                else:
                    # Get the next display order for root menus
                    cursor.execute("""
                        SELECT ISNULL(MAX(DisplayOrder), 0) + 1 
                        FROM MenuMaster 
                        WHERE ParentMenuID IS NULL AND ISNULL(IsDeleted, 0) = 0
                    """)
                    next_order = cursor.fetchone()[0]

                    # Insert Master Data parent menu
                    cursor.execute("""
                        INSERT INTO MenuMaster (
                            MenuName, MenuURL, Icon, DisplayOrder, ParentMenuID, 
                            IsActive, CreatedBy, CreatedAt
                        ) VALUES (
                            'Master Data', '/master-data/', 'fas fa-database', %s, NULL, 
                            1, 1, GETDATE()
                        )
                    """, [next_order])

                    # Get the Master Data menu ID
                    cursor.execute("""
                        SELECT MenuID FROM MenuMaster 
                        WHERE MenuName = 'Master Data' AND ISNULL(IsDeleted, 0) = 0
                    """)
                    master_data_id = cursor.fetchone()[0]
                    
                    self.stdout.write(
                        self.style.SUCCESS('Successfully created Master Data menu with ID: ' + str(master_data_id))
                    )

                # Check if Menu Data sub-menu already exists
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = 'Menu Data' AND ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                """, [master_data_id])
                
                menu_data_menu = cursor.fetchone()
                
                if menu_data_menu:
                    self.stdout.write(
                        self.style.WARNING('Menu Data sub-menu already exists with ID: ' + str(menu_data_menu[0]))
                    )
                else:
                    # Get the next display order for sub-menus under Master Data
                    cursor.execute("""
                        SELECT ISNULL(MAX(DisplayOrder), 0) + 1 
                        FROM MenuMaster 
                        WHERE ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                    """, [master_data_id])
                    next_sub_order = cursor.fetchone()[0]

                    # Insert Menu Data sub-menu
                    cursor.execute("""
                        INSERT INTO MenuMaster (
                            MenuName, MenuURL, Icon, DisplayOrder, ParentMenuID, 
                            IsActive, CreatedBy, CreatedAt
                        ) VALUES (
                            'Menu Data', '/master-data/menu-data/', 'fas fa-list', %s, %s, 
                            1, 1, GETDATE()
                        )
                    """, [next_sub_order, master_data_id])
                    
                    # Get the Menu Data menu ID
                    cursor.execute("""
                        SELECT MenuID FROM MenuMaster 
                        WHERE MenuName = 'Menu Data' AND ParentMenuID = %s AND ISNULL(IsDeleted, 0) = 0
                    """, [master_data_id])
                    menu_data_id = cursor.fetchone()[0]
                    
                    self.stdout.write(
                        self.style.SUCCESS('Successfully created Menu Data sub-menu with ID: ' + str(menu_data_id))
                    )

                # Verify the setup
                cursor.execute("""
                    SELECT 
                        m.MenuID,
                        m.MenuName,
                        m.MenuURL,
                        m.Icon,
                        m.DisplayOrder,
                        pm.MenuName as ParentMenuName
                    FROM MenuMaster m
                    LEFT JOIN MenuMaster pm ON m.ParentMenuID = pm.MenuID
                    WHERE m.MenuName IN ('Master Data', 'Menu Data') 
                    AND ISNULL(m.IsDeleted, 0) = 0
                    ORDER BY ISNULL(m.ParentMenuID, 0), m.DisplayOrder
                """)
                
                menus = cursor.fetchall()
                self.stdout.write(
                    self.style.SUCCESS('\nMenu structure created successfully:')
                )
                for menu in menus:
                    menu_id, name, url, icon, order, parent = menu
                    if parent:
                        self.stdout.write(f"  └── {name} (ID: {menu_id}) - {url}")
                    else:
                        self.stdout.write(f"  {name} (ID: {menu_id}) - {url}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up menu structure: {str(e)}')
            )
