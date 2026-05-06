from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Insert a single menu item into MenuMaster table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--menu-name',
            type=str,
            required=True,
            help='Name of the menu item'
        )
        parser.add_argument(
            '--menu-url',
            type=str,
            default='',
            help='URL for the menu item (optional)'
        )
        parser.add_argument(
            '--icon',
            type=str,
            default='fas fa-circle',
            help='Icon class for the menu item (default: fas fa-circle)'
        )
        parser.add_argument(
            '--display-order',
            type=int,
            default=1,
            help='Display order for the menu item (default: 1)'
        )
        parser.add_argument(
            '--parent-id',
            type=int,
            default=None,
            help='Parent menu ID (optional)'
        )

    def handle(self, *args, **options):
        menu_name = options['menu_name']
        menu_url = options['menu_url']
        icon = options['icon']
        display_order = options['display_order']
        parent_id = options['parent_id']

        try:
            with connection.cursor() as cursor:
                # Insert the menu item
                cursor.execute("""
                    INSERT INTO MenuMaster (
                        MenuName, MenuURL, Icon, DisplayOrder, ParentMenuID, 
                        IsActive, CreatedBy, CreatedAt
                    ) VALUES (
                        %s, %s, %s, %s, %s, 
                        1, 1, GETDATE()
                    )
                """, [menu_name, menu_url, icon, display_order, parent_id])

                # Get the inserted menu ID
                cursor.execute("""
                    SELECT MenuID FROM MenuMaster 
                    WHERE MenuName = %s AND ISNULL(IsDeleted, 0) = 0
                    ORDER BY CreatedAt DESC
                """, [menu_name])
                
                menu_id = cursor.fetchone()[0]

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully inserted menu "{menu_name}" with ID: {menu_id}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error inserting menu: {str(e)}')
            )
