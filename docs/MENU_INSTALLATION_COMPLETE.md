# Data Import Menu Installation Guide

## 📋 Menu Structure

```
Data Import (Parent Menu)
├── Import Dashboard
├── Import Students
├── Import Teachers
├── Import Salary
├── Import Fee History
├── Import Attendance
├── Import Exams
├── Import Exam Results
├── Import Classes
├── Import Sections
└── Import Subjects
```

## 🚀 Quick Installation

### Step 1: Run SQL Script
```bash
sqlcmd -S localhost -d ShikshaWaveDB -i database/add_data_import_menu.sql
```

**OR** in SQL Server Management Studio:
```sql
:r C:\Users\AbhishekKumar\Desktop\ShikshaWave_Project\database\add_data_import_menu.sql
```

### Step 2: Verify Installation
```sql
-- Check parent menu
SELECT * FROM MenuMaster WHERE MenuName = 'Data Import';

-- Check submenus
SELECT m.MenuID, m.MenuName, m.MenuURL, m.Icon
FROM MenuMaster m
WHERE m.ParentMenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import')
ORDER BY m.DisplayOrder;

-- Check permissions
SELECT p.ProfileName, m.MenuName, pmm.CanView, pmm.CanAdd, pmm.CanEdit, pmm.CanDelete
FROM ProfileMenuMapping pmm
JOIN ProfileMaster p ON pmm.ProfileID = p.ProfileID
JOIN MenuMaster m ON pmm.MenuID = m.MenuID
WHERE m.MenuName LIKE '%Import%'
ORDER BY p.ProfileID, m.DisplayOrder;
```

### Step 3: Test Access
1. Refresh browser (Ctrl + F5)
2. Login as Super Admin or School Admin
3. Look for "Data Import" in navigation menu
4. Click to expand and see all submenus

## 📊 Menu Details

| Menu Name | URL | Icon | Access |
|-----------|-----|------|--------|
| Data Import | # | fa-upload | Super Admin, School Admin |
| Import Dashboard | /import/dashboard/ | fa-tachometer-alt | Super Admin, School Admin |
| Import Students | /import/dashboard/?type=Students | fa-user-graduate | Super Admin, School Admin |
| Import Teachers | /import/dashboard/?type=Teachers | fa-chalkboard-teacher | Super Admin, School Admin |
| Import Salary | /import/dashboard/?type=Salary | fa-money-bill-wave | Super Admin, School Admin |
| Import Fee History | /import/dashboard/?type=Fee | fa-receipt | Super Admin, School Admin |
| Import Attendance | /import/dashboard/?type=Attendance | fa-calendar-check | Super Admin, School Admin |
| Import Exams | /import/dashboard/?type=Exam | fa-file-alt | Super Admin, School Admin |
| Import Exam Results | /import/dashboard/?type=ExamResult | fa-chart-line | Super Admin, School Admin |
| Import Classes | /import/dashboard/?type=ClassMaster | fa-school | Super Admin, School Admin |
| Import Sections | /import/dashboard/?type=SectionMaster | fa-layer-group | Super Admin, School Admin |
| Import Subjects | /import/dashboard/?type=SubjectMaster | fa-book | Super Admin, School Admin |

## 🔐 Permissions

### Super Admin (ProfileID = 1)
- ✅ View all menus
- ✅ Add (upload files)
- ✅ Edit (re-upload)
- ✅ Delete (remove imports)
- ✅ Access all schools

### School Admin (ProfileID = 2)
- ✅ View all menus
- ✅ Add (upload files)
- ✅ Edit (re-upload)
- ✅ Delete (remove imports)
- ⚠️ Access only their school

### Teacher (ProfileID = 3)
- ❌ No access (not assigned)

### Student (ProfileID = 4)
- ❌ No access (not assigned)

## 🎯 Usage

### From Parent Menu
Click "Data Import" → Opens dropdown with all import types

### From Submenu
Click specific import type (e.g., "Import Students") → Opens dashboard with that type pre-selected

### Direct URL
Navigate to `/import/dashboard/?type=Students` → Opens dashboard with Students import ready

## 🔧 Customization

### Add More Roles
```sql
-- Example: Add access for Accountant (ProfileID = 8)
DECLARE @ParentMenuID INT = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import');

-- Parent menu
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
VALUES (8, @ParentMenuID, 1, 1, 0, 0, 1, GETDATE(), 0);

-- All submenus
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
SELECT 8, MenuID, 1, 1, 0, 0, 1, GETDATE(), 0
FROM MenuMaster
WHERE ParentMenuID = @ParentMenuID;
```

### Change Display Order
```sql
-- Move Data Import menu to position 50
UPDATE MenuMaster
SET DisplayOrder = 50
WHERE MenuName = 'Data Import';
```

### Change Icon
```sql
-- Change parent menu icon
UPDATE MenuMaster
SET Icon = 'fa-database'
WHERE MenuName = 'Data Import';
```

### Disable Submenu
```sql
-- Disable Import Attendance
UPDATE MenuMaster
SET IsActive = 0
WHERE MenuName = 'Import Attendance';
```

## 🐛 Troubleshooting

### Menu Not Appearing
```sql
-- Check if menu exists
SELECT * FROM MenuMaster WHERE MenuName = 'Data Import';

-- Check if active
SELECT MenuName, IsActive, IsDeleted FROM MenuMaster WHERE MenuName LIKE '%Import%';

-- Check permissions
SELECT * FROM ProfileMenuMapping 
WHERE MenuID IN (SELECT MenuID FROM MenuMaster WHERE MenuName LIKE '%Import%')
AND ProfileID = 1; -- Your ProfileID
```

### Submenu Not Showing
```sql
-- Check parent-child relationship
SELECT 
    child.MenuName AS Submenu,
    parent.MenuName AS ParentMenu,
    child.IsActive,
    child.IsDeleted
FROM MenuMaster child
LEFT JOIN MenuMaster parent ON child.ParentMenuID = parent.MenuID
WHERE parent.MenuName = 'Data Import';
```

### Permission Denied
```sql
-- Check your permissions
SELECT 
    p.ProfileName,
    m.MenuName,
    pmm.CanView,
    pmm.CanAdd,
    pmm.CanEdit,
    pmm.CanDelete
FROM ProfileMenuMapping pmm
JOIN ProfileMaster p ON pmm.ProfileID = p.ProfileID
JOIN MenuMaster m ON pmm.MenuID = m.MenuID
WHERE p.ProfileID = 2 -- Your ProfileID
AND m.MenuName LIKE '%Import%';
```

## 🔄 Rollback (If Needed)

```sql
-- Remove all Data Import menus and permissions
DECLARE @ParentMenuID INT = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import');

-- Delete permissions
DELETE FROM ProfileMenuMapping 
WHERE MenuID = @ParentMenuID 
OR MenuID IN (SELECT MenuID FROM MenuMaster WHERE ParentMenuID = @ParentMenuID);

-- Delete submenus
DELETE FROM MenuMaster WHERE ParentMenuID = @ParentMenuID;

-- Delete parent menu
DELETE FROM MenuMaster WHERE MenuID = @ParentMenuID;

PRINT 'Data Import menu removed successfully';
```

## ✅ Verification Checklist

- [ ] SQL script executed without errors
- [ ] Parent menu "Data Import" exists in MenuMaster
- [ ] 11 submenus created under parent menu
- [ ] Permissions assigned to Super Admin (ProfileID = 1)
- [ ] Permissions assigned to School Admin (ProfileID = 2)
- [ ] Menu appears in navigation after browser refresh
- [ ] Clicking parent menu shows dropdown with submenus
- [ ] Clicking submenu opens correct import type
- [ ] Dashboard loads without errors

## 📞 Support

If menu installation fails:
1. Check SQL Server connection
2. Verify database name (ShikshaWaveDB)
3. Ensure MenuMaster and ProfileMenuMapping tables exist
4. Check for duplicate menu names
5. Review error messages in SQL output

---

**Installation Time:** 1 minute  
**Difficulty:** Easy  
**Status:** ✅ Ready to Use
