"""
Run this once to set up Leave Management:
  python core/sql/run_leave_setup.py

It will:
1. Create all tables and stored procedures
2. Aggressively move all leave-related sub-menus under the "Attendance" parent menu
3. Cleanup all duplicate menu entries
4. Map them to all staff profiles
"""

import os
import sys
import django

# ── Bootstrap Django ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
django.setup()

from django.db import connection

def run_sql_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read()
    with connection.cursor() as cur:
        cur.execute(sql)
    print(f"✅ SQL file executed: {path}")

def setup_menus():
    """Aggressively move all leave-related menus to Attendance and cleanup duplicates."""
    with connection.cursor() as cur:
        # ── 1. Find or Create the Attendance parent menu ─────────
        cur.execute("""
            SELECT "MenuID" FROM "MenuMaster"
            WHERE "MenuName" = 'Attendance' AND "ParentMenuID" = 0
            AND "IsDeleted" = FALSE
            LIMIT 1
        """)
        row = cur.fetchone()
        
        if not row:
            print("  ⚠️ Attendance parent menu not found. Creating it...")
            cur.execute("""
                INSERT INTO "MenuMaster" ("MenuName", "DisplayOrder", "ParentMenuID", "Icon", "IsActive", "IsDeleted", "CreatedBy", "CreatedAt")
                VALUES ('Attendance', 10, 0, 'fas fa-clipboard-check', TRUE, FALSE, 1, NOW())
                RETURNING "MenuID"
            """)
            parent_menu_id = cur.fetchone()[0]
            print(f"  ✅ Created Attendance parent menu (ID={parent_menu_id})")
        else:
            parent_menu_id = row[0]
            print(f"  ✅ Found Attendance parent menu (ID={parent_menu_id})")

        # Get all profile IDs for mapping
        cur.execute("SELECT \"ProfileID\" FROM \"ProfileMaster\" WHERE \"IsDeleted\" = FALSE")
        profile_ids = [r[0] for r in cur.fetchall()]

        # ── 2. Identify ALL menus that are leave-related ──────────
        # We look for anything that points to /leave/ or has 'leave' in name
        cur.execute("""
            SELECT "MenuID", "MenuName", "MenuURL" FROM "MenuMaster"
            WHERE ("MenuURL" LIKE '%%/leave/%%' OR "MenuName" ILIKE '%%leave%%')
              AND "ParentMenuID" != 0
        """)
        all_leave_submenus = cur.fetchall()
        print(f"Found {len(all_leave_submenus)} leave-related submenus to process.")

        # Targeted sub-menus we WANT to keep
        target_defs = {
            '/leave/':        ('Leave Dashboard', 'fas fa-calendar-check', 1),
            '/leave/apply/':  ('Apply Leave',     'fas fa-paper-plane',    2),
            '/leave/report/': ('Leave Report',    'fas fa-chart-bar',      3),
        }

        # First, mark EVERY existing leave submenu as deleted to start fresh
        if all_leave_submenus:
            ids = [m[0] for m in all_leave_submenus]
            cur.execute("UPDATE \"MenuMaster\" SET \"IsDeleted\" = TRUE WHERE \"MenuID\" = ANY(%s)", [ids])
            print(f"  🗑️ Temporarily disabled {len(ids)} menus for cleanup.")

        # Now, for each target, either find one to reactivate or create new
        for url, (name, icon, order) in target_defs.items():
            print(f"\n  Processing '{name}' ({url})...")
            cur.execute("""
                SELECT "MenuID" FROM "MenuMaster" 
                WHERE "MenuURL" = %s 
                ORDER BY "MenuID" ASC LIMIT 1
            """, [url])
            existing = cur.fetchone()
            
            if existing:
                menu_id = existing[0]
                cur.execute("""
                    UPDATE "MenuMaster"
                    SET "MenuName" = %s, "ParentMenuID" = %s, "DisplayOrder" = %s, 
                        "Icon" = %s, "IsActive" = TRUE, "IsDeleted" = FALSE
                    WHERE "MenuID" = %s
                """, [name, parent_menu_id, order, icon, menu_id])
                print(f"    ↺ Reactivated and moved (ID={menu_id}) → Attendance")
            else:
                cur.execute("""
                    INSERT INTO "MenuMaster"
                        ("MenuName","DisplayOrder","ParentMenuID","MenuURL","Icon","IsActive","IsDeleted","CreatedBy","CreatedAt")
                    VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, 1, NOW())
                    RETURNING "MenuID"
                """, [name, order, parent_menu_id, url, icon])
                menu_id = cur.fetchone()[0]
                print(f"    ✅ Created NEW (ID={menu_id}) → Attendance")

            # Profile Mapping
            for pid in profile_ids:
                cur.execute("""
                    INSERT INTO "ProfileMenuMapping" ("ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete", "IsDeleted", "CreatedAt")
                    VALUES (%s, %s, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
                    ON CONFLICT ("ProfileID", "MenuID") DO UPDATE SET "CanView" = TRUE, "IsDeleted" = FALSE
                """, [pid, menu_id])

        # Ensure Attendance parent is mapped too
        for pid in profile_ids:
            cur.execute("""
                INSERT INTO "ProfileMenuMapping" ("ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete", "IsDeleted", "CreatedAt")
                VALUES (%s, %s, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
                ON CONFLICT ("ProfileID", "MenuID") DO UPDATE SET "CanView" = TRUE, "IsDeleted" = FALSE
            """, [pid, parent_menu_id])

    print("\n🎉 Aggressive menu migration and deduplication complete!")

if __name__ == '__main__':
    print("=" * 60)
    print("ShikshaWave — Aggressive Leave Menu Cleanup")
    print("=" * 60)

    sql_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'leave_management_procedures.sql'
    )

    try:
        print("\n[1/2] Refreshing SQL procedures...")
        run_sql_file(sql_file)
    except Exception as e:
        print(f"❌ SQL error: {e}")

    try:
        print("\n[2/2] Cleaning up menus...")
        setup_menus()
    except Exception as e:
        print(f"❌ Menu setup error: {e}")
        import traceback; traceback.print_exc()
