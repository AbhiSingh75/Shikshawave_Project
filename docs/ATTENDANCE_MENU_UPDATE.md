# Attendance Menu Update Documentation

## Overview
This document describes the updates made to the Attendance menu structure in the ShikshaWave application.

## Changes Made

### 1. Updated Existing Submenus
- **"Mark Attendance"** → **"Mark Student Attendance"**
- **"View Attendance"** → **"View Student Attendance"**

### 2. New Submenus Added
- **Mark Employee/Staff Attendance** (`/attendance/mark-employee/`)
  - Icon: `fas fa-user-tie`
  - Display Order: 3
  
- **View Employee/Staff Attendance** (`/attendance/view-employee/`)
  - Icon: `fas fa-users`
  - Display Order: 4

### 3. New Profile Types Added
Three new profile types have been added to the system:
- **Accountant** (ProfileID: 5)
- **Driver** (ProfileID: 6)
- **Librarian** (ProfileID: 7)

## Menu Structure

```
Attendance (Parent Menu)
├── Mark Student Attendance (Order: 1)
├── View Student Attendance (Order: 2)
├── Mark Employee/Staff Attendance (Order: 3)
└── View Employee/Staff Attendance (Order: 4)
```

## Profile Access Permissions

### Student Attendance Menus
| Menu | School Admin | Teacher | Accountant | Driver | Librarian |
|------|--------------|---------|------------|--------|-----------|
| Mark Student Attendance | ✓ (Add/Edit) | ✓ (Add/Edit) | ✗ | ✗ | ✗ |
| View Student Attendance | ✓ (View) | ✓ (View) | ✗ | ✗ | ✗ |

### Employee/Staff Attendance Menus
| Menu | School Admin | Teacher | Accountant | Driver | Librarian |
|------|--------------|---------|------------|--------|-----------|
| Mark Employee/Staff Attendance | ✓ (Add/Edit) | ✓ (Add/Edit) | ✓ (Add/Edit) | ✓ (Add/Edit) | ✓ (Add/Edit) |
| View Employee/Staff Attendance | ✓ (View) | ✓ (View) | ✓ (View) | ✓ (View) | ✓ (View) |

## Installation Instructions

### Option 1: Using Django Migration (Recommended)
```bash
# Navigate to project directory
cd c:\Users\AbhishekKumar\Desktop\ShikshaWave_Project

# Run the migration
python manage.py migrate core 0050_update_attendance_menu
```

### Option 2: Using SQL Script Directly
```sql
-- Execute the SQL script in SQL Server Management Studio or Azure Data Studio
-- File: database/update_attendance_menu.sql
```

## Files Modified/Created

### New Files
1. `database/update_attendance_menu.sql` - SQL script for menu updates
2. `core/migrations/0050_update_attendance_menu.py` - Django migration file
3. `docs/ATTENDANCE_MENU_UPDATE.md` - This documentation file

### Modified Files
1. `core/models.py` - Updated ProfileMaster.PROFILE_CHOICES to include new profiles

## Verification Steps

After running the migration, verify the changes:

1. **Check Profile Types:**
```sql
SELECT * FROM ProfileMaster WHERE ProfileID IN (5, 6, 7);
```

2. **Check Menu Structure:**
```sql
SELECT m.MenuID, m.MenuName, m.MenuURL, m.DisplayOrder, p.MenuName as ParentMenu
FROM MenuMaster m
LEFT JOIN MenuMaster p ON m.ParentMenuID = p.MenuID
WHERE m.MenuName LIKE '%Attendance%' AND m.IsDeleted = 0
ORDER BY m.DisplayOrder;
```

3. **Check Profile Menu Mappings:**
```sql
SELECT p.ProfileName, m.MenuName, pmm.CanView, pmm.CanAdd, pmm.CanEdit
FROM ProfileMenuMapping pmm
JOIN ProfileMaster p ON pmm.ProfileID = p.ProfileID
JOIN MenuMaster m ON pmm.MenuID = m.MenuID
WHERE m.MenuName LIKE '%Attendance%' AND pmm.IsDeleted = 0
ORDER BY p.ProfileID, m.DisplayOrder;
```

## Next Steps

### Backend Implementation Required
You will need to create views and templates for the new employee attendance functionality:

1. **Views to Create:**
   - `mark_employee_attendance_view` - Handle marking employee attendance
   - `view_employee_attendance_view` - Display employee attendance records

2. **Templates to Create:**
   - `core/templates/core/mark_employee_attendance.html`
   - `core/templates/core/view_employee_attendance.html`

3. **URL Configuration:**
   Add the following to `core/urls.py`:
   ```python
   path('attendance/mark-employee/', views.mark_employee_attendance_view, name='mark_employee_attendance'),
   path('attendance/view-employee/', views.view_employee_attendance_view, name='view_employee_attendance'),
   ```

4. **Database Tables:**
   Consider creating an `EmployeeAttendance` table similar to student attendance:
   ```sql
   CREATE TABLE EmployeeAttendance (
       AttendanceID INT PRIMARY KEY IDENTITY(1,1),
       EmployeeID INT NOT NULL,
       SchoolID INT NOT NULL,
       AttendanceDate DATE NOT NULL,
       Status VARCHAR(20) NOT NULL, -- Present, Absent, Leave, etc.
       CheckInTime TIME,
       CheckOutTime TIME,
       Remarks VARCHAR(500),
       CreatedBy INT,
       CreatedAt DATETIME DEFAULT GETDATE(),
       FOREIGN KEY (EmployeeID) REFERENCES UserMaster(UserID),
       FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID)
   );
   ```

## Rollback Instructions

If you need to rollback the changes:

### Using Django Migration
```bash
python manage.py migrate core 0049_dataimporterror_dataimportlog
```

### Using SQL
The migration includes reverse SQL that will:
- Restore original menu names
- Remove employee attendance menus
- Remove profile menu mappings for new menus

## Support

For issues or questions, please contact the development team.

## Version History
- **v1.0** (Current) - Initial attendance menu restructuring
  - Added employee/staff attendance menus
  - Renamed student attendance menus
  - Added new profile types (Accountant, Driver, Librarian)
