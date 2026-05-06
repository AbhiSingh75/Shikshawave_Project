from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Initialize default themes in ThemeMaster'

    def handle(self, *args, **options):
        themes = [
            ('Default Blue', 'default_blue', '#004aad', '#003a8a', 1),
            ('Emerald Green', 'emerald_green', '#10b981', '#059669', 2),
            ('Royal Purple', 'royal_purple', '#8b5cf6', '#7c3aed', 3),
            ('Sunset Orange', 'sunset_orange', '#f59e0b', '#d97706', 4),
            ('Crimson Red', 'crimson_red', '#ef4444', '#dc2626', 5),
            ('Midnight Slate', 'midnight_slate', '#475569', '#334155', 6),
        ]

        with connection.cursor() as cursor:
            # Create table if it doesn't exist (safety)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "ThemeMaster" (
                    "ThemeID" SERIAL PRIMARY KEY,
                    "ThemeName" VARCHAR(100) NOT NULL,
                    "ThemeKey" VARCHAR(50) UNIQUE NOT NULL,
                    "PrimaryColor" VARCHAR(20) NOT NULL,
                    "PrimaryHover" VARCHAR(20) NOT NULL,
                    "DisplayOrder" INT DEFAULT 0,
                    "IsActive" BOOLEAN DEFAULT TRUE,
                    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert themes
            for name, key, color, hover, order in themes:
                cursor.execute("""
                    INSERT INTO "ThemeMaster" ("ThemeName", "ThemeKey", "PrimaryColor", "PrimaryHover", "DisplayOrder")
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT ("ThemeKey") DO UPDATE SET
                        "ThemeName" = EXCLUDED."ThemeName",
                        "PrimaryColor" = EXCLUDED."PrimaryColor",
                        "PrimaryHover" = EXCLUDED."PrimaryHover",
                        "DisplayOrder" = EXCLUDED."DisplayOrder"
                """, [name, key, color, hover, order])

            # Ensure ThemeID exists in UserMaster
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='UserMaster' AND column_name='ThemeID') THEN
                        ALTER TABLE "UserMaster" ADD COLUMN "ThemeID" INTEGER REFERENCES "ThemeMaster"("ThemeID");
                    END IF;
                END $$;
            """)

            # Ensure ThemeID exists in SchoolMaster
            cursor.execute("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='SchoolMaster' AND column_name='ThemeID') THEN
                        ALTER TABLE "SchoolMaster" ADD COLUMN "ThemeID" INTEGER REFERENCES "ThemeMaster"("ThemeID");
                    END IF;
                END $$;
            """)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully initialized {len(themes)} themes and verified table columns.'))
