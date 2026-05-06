# Attendance Menu Update - Quick Installation Guide

## What's Changed?

### Renamed Menus
- ✅ "Mark Attendance" → "Mark Student Attendance"
- ✅ "View Attendance" → "View Student Attendance"

### New Menus
- ✅ Mark Employee/Staff Attendance
- ✅ View Employee/Staff Attendance

### New Profiles
- ✅ Accountant (ProfileID: 5)
- ✅ Driver (ProfileID: 6)
- ✅ Librarian (ProfileID: 7)

## Installation (Choose One Method)

### Method 1: Django Migration (Recommended)
```bash
cd c:\Users\AbhishekKumar\Desktop\ShikshaWave_Project
python manage.py migrate
```

### Method 2: SQL Script
Execute this file in your SQL Server:
```
database/update_attendance_menu.sql
```

## Verify Installation

Run this SQL query to verify:
```sql
SELECT m.MenuName, m.MenuURL, m.DisplayOrder
FROM MenuMaster m
WHERE m.MenuName LIKE '%Attendance%' AND m.IsDeleted = 0
ORDER BY m.DisplayOrder;
```

Expected Output:
```
MenuName                          MenuURL                      DisplayOrder
--------------------------------  ---------------------------  ------------
Mark Student Attendance           /attendance/mark/            1
View Student Attendance           /attendance/view/            2
Mark Employee/Staff Attendance    /attendance/mark-employee/   3
View Employee/Staff Attendance    /attendance/view-employee/   4
```

## Access Permissions

| Profile      | Student Attendance | Employee Attendance |
|--------------|-------------------|---------------------|
| School Admin | ✓ Mark & View     | ✓ Mark & View       |
| Teacher      | ✓ Mark & View     | ✓ Mark & View       |
| Accountant   | ✗                 | ✓ Mark & View       |
| Driver       | ✗                 | ✓ Mark & View       |
| Librarian    | ✗                 | ✓ Mark & View       |

## Files Created
1. ✅ `database/update_attendance_menu.sql`
2. ✅ `core/migrations/0050_update_attendance_menu.py`
3. ✅ `docs/ATTENDANCE_MENU_UPDATE.md`
4. ✅ `core/models.py` (updated)

## Done! 🎉

The menu structure is now updated. You can now proceed to implement the backend views and templates for employee attendance functionality.

For detailed documentation, see: `docs/ATTENDANCE_MENU_UPDATE.md`
