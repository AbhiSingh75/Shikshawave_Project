# 📅 Academic Year - Quick Start Guide

## 🎯 What You Get

A complete CRUD system for managing Academic Years with:
- ✅ Add, Edit, Delete, View operations
- ✅ Super Admin can manage any school
- ✅ School Admin manages their school
- ✅ Modern UI matching your existing design
- ✅ Menu integration with proper permissions

---

## ⚡ Installation (Choose One)

### Option A: Django Migrations (Recommended)
```bash
cd c:\Users\AbhishekKumar\Desktop\ShikshaWave_Project
env\Scripts\activate
python manage.py migrate
```

### Option B: SQL Script (If migrations fail)
```sql
-- Open SQL Server Management Studio
-- Run this file: database/INSTALL_ACADEMIC_YEAR.sql
```

---

## 🔍 Verify Installation

```sql
-- Run this file: database/VERIFY_ACADEMIC_YEAR.sql
-- It will check everything and show status
```

---

## 🚀 How to Use

### For Super Admin:
1. Login to application
2. Go to **Master Data** → **Academic Year**
3. **Select a school** from dropdown
4. Click **"Add Academic Year"**
5. Fill in details:
   - Academic Year (e.g., "2024-2025")
   - Start Date
   - End Date
   - Check "Current Year" if applicable
   - Check "Active"
6. Click **Save**

### For School Admin:
1. Login to application
2. Go to **Master Data** → **Academic Year**
3. Click **"Add Academic Year"** (no school selection needed)
4. Fill in details and save

---

## 📋 Features Explained

### Current Year Logic
- Only **ONE** year can be "Current" per school
- When you mark a year as current, others automatically become non-current
- This is handled automatically by the system

### Card Display
Each academic year shows:
- 📅 Year name (e.g., "2024-2025")
- 🏆 "Current" badge (if it's the active year)
- 📆 Date range (Start - End)
- ✅ Active/Inactive status
- ✏️ Edit button
- 🗑️ Delete button

---

## 🎨 UI Preview

```
┌─────────────────────────────────────────────────────┐
│  📅 Academic Year (3)          [+ Add Academic Year] │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 2024-2025 [Current]                           │  │
│  │ Duration: 01 Apr 2024 - 31 Mar 2025          │  │
│  │ [Active]                          [✏️] [🗑️]   │  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
│  ┌───────────────────────────────────────────────┐  │
│  │ 2023-2024                                     │  │
│  │ Duration: 01 Apr 2023 - 31 Mar 2024          │  │
│  │ [Active]                          [✏️] [🗑️]   │  │
│  └───────────────────────────────────────────────┘  │
│                                                       │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/master-data/academic-year/` | View page |
| POST | `/master-data/academic-year/save/` | Add/Update |
| POST | `/master-data/academic-year/delete/` | Delete |
| POST | `/master-data/academic-year/load/` | Load by school |

---

## 📊 Database Operations

### List All Years
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'LIST',
    @SchoolId = 3
```

### Add New Year
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'ADD',
    @SchoolId = 3,
    @AcademicYear = '2024-2025',
    @StartDate = '2024-04-01',
    @EndDate = '2025-03-31',
    @IsCurrent = 1,
    @IsActive = 1,
    @UserId = 1
```

### Update Year
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'UPDATE',
    @SchoolId = 3,
    @AcademicYearID = 1,
    @AcademicYear = '2024-2025',
    @StartDate = '2024-04-01',
    @EndDate = '2025-03-31',
    @IsCurrent = 1,
    @IsActive = 1,
    @UserId = 1
```

### Delete Year
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'DELETE',
    @SchoolId = 3,
    @AcademicYearID = 1
```

---

## ❓ Troubleshooting

### Problem: Menu not showing
**Solution:**
```sql
-- Run this query to check
SELECT * FROM MenuMaster WHERE MenuName = 'Academic Year';

-- If not found, run:
-- database/add_academic_year_menu.sql
```

### Problem: Page shows error
**Solution:**
1. Check if you're logged in
2. Verify you have menu access
3. Check browser console for errors
4. Verify stored procedure exists:
```sql
SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD';
```

### Problem: Cannot add academic year
**Solution:**
1. Super Admin: Make sure you selected a school
2. Check all required fields are filled
3. Verify dates are valid
4. Check browser console for errors

---

## 📁 Files Reference

### Created Files (9 files)
```
database/
├── procedures/
│   └── Proc_AcademicYear_CRUD.sql          ← Stored procedure
├── add_academic_year_menu.sql              ← Menu script
├── INSTALL_ACADEMIC_YEAR.sql               ← Complete installer
└── VERIFY_ACADEMIC_YEAR.sql                ← Verification script

core/
├── academic_year_views.py                  ← Django views
├── templates/
│   └── academic_year.html                  ← UI template
├── migrations/
│   ├── 0052_add_academic_year_menu.py      ← Menu migration
│   └── 0053_create_academic_year_procedure.py  ← Proc migration
└── urls.py                                 ← Updated with routes

docs/
└── ACADEMIC_YEAR_IMPLEMENTATION.md         ← Full documentation
```

---

## ✅ Testing Checklist

### Super Admin
- [ ] Login as Super Admin
- [ ] Navigate to Master Data → Academic Year
- [ ] See school selector dropdown
- [ ] Select a school
- [ ] See academic years for that school
- [ ] Click "Add Academic Year"
- [ ] Fill form and save
- [ ] Edit an existing year
- [ ] Delete a year
- [ ] Switch to different school
- [ ] Verify data loads correctly

### School Admin
- [ ] Login as School Admin
- [ ] Navigate to Master Data → Academic Year
- [ ] No school selector visible
- [ ] See your school's academic years
- [ ] Add new academic year
- [ ] Edit existing year
- [ ] Delete a year
- [ ] Mark year as current
- [ ] Verify only one year is current

---

## 🎓 Example Data

```sql
-- Add sample academic years for testing
EXEC Proc_AcademicYear_CRUD 
    @Action = 'ADD', @SchoolId = 3,
    @AcademicYear = '2024-2025',
    @StartDate = '2024-04-01', @EndDate = '2025-03-31',
    @IsCurrent = 1, @IsActive = 1, @UserId = 1;

EXEC Proc_AcademicYear_CRUD 
    @Action = 'ADD', @SchoolId = 3,
    @AcademicYear = '2023-2024',
    @StartDate = '2023-04-01', @EndDate = '2024-03-31',
    @IsCurrent = 0, @IsActive = 1, @UserId = 1;

EXEC Proc_AcademicYear_CRUD 
    @Action = 'ADD', @SchoolId = 3,
    @AcademicYear = '2025-2026',
    @StartDate = '2025-04-01', @EndDate = '2026-03-31',
    @IsCurrent = 0, @IsActive = 0, @UserId = 1;
```

---

## 📞 Need More Help?

- **Full Documentation**: `docs/ACADEMIC_YEAR_IMPLEMENTATION.md`
- **Installation Script**: `database/INSTALL_ACADEMIC_YEAR.sql`
- **Verification Script**: `database/VERIFY_ACADEMIC_YEAR.sql`
- **Summary**: `ACADEMIC_YEAR_SUMMARY.md`

---

## 🎉 You're All Set!

The Academic Year master data management is ready to use. Just run the installation and start managing your academic years!

**Happy Managing! 📅**
