# Academic Year Master Data - Implementation Guide

## Overview
Complete CRUD functionality for Academic Year master data table with menu integration for Super Admin and School Admin roles.

## Features
- ✅ Create, Read, Update, Delete operations
- ✅ Super Admin can select school and manage academic years
- ✅ School Admin can manage their school's academic years
- ✅ Set current academic year (only one can be current at a time)
- ✅ Active/Inactive status management
- ✅ Date range validation (Start Date to End Date)
- ✅ Modern UI matching Terms & Conditions page design
- ✅ Menu integration with proper permissions

## Files Created

### 1. Database Files
- **`database/procedures/Proc_AcademicYear_CRUD.sql`** - Stored procedure for CRUD operations
- **`database/add_academic_year_menu.sql`** - SQL script to add menu entries

### 2. Backend Files
- **`core/academic_year_views.py`** - Django views for Academic Year management
- **`core/migrations/0052_add_academic_year_menu.py`** - Migration to add menu
- **`core/migrations/0053_create_academic_year_procedure.py`** - Migration to create stored procedure

### 3. Frontend Files
- **`core/templates/academic_year.html`** - Academic Year management page

### 4. URL Configuration
- Updated **`core/urls.py`** with Academic Year routes

## Installation Steps

### Step 1: Run Migrations
```bash
# Activate virtual environment
cd c:\Users\AbhishekKumar\Desktop\ShikshaWave_Project
env\Scripts\activate

# Run migrations
python manage.py migrate
```

### Step 2: Verify Database
```sql
-- Check if stored procedure exists
SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD';

-- Check if menu exists
SELECT * FROM MenuMaster WHERE MenuName = 'Academic Year';

-- Check menu permissions
SELECT pm.*, m.MenuName, p.ProfileName 
FROM ProfileMenuMapping pm
JOIN MenuMaster m ON pm.MenuID = m.MenuID
JOIN Profile p ON pm.ProfileID = p.ProfileID
WHERE m.MenuName = 'Academic Year';
```

### Step 3: Access the Page
- **URL**: `/master-data/academic-year/`
- **Super Admin**: Can select school and manage academic years
- **School Admin**: Can manage their school's academic years

## Database Schema

### Table: AcademicYear
```sql
CREATE TABLE [dbo].[AcademicYear](
    [AcademicYearID] [int] IDENTITY(1,1) NOT NULL,
    [SchoolID] [int] NOT NULL,
    [AcademicYear] [nvarchar](10) NOT NULL,
    [StartDate] [date] NOT NULL,
    [EndDate] [date] NOT NULL,
    [IsCurrent] [bit] NOT NULL,
    [IsActive] [bit] NOT NULL,
    [CreatedBy] [int] NULL,
    [CreatedAt] [datetime] NOT NULL,
    [UpdatedBy] [int] NULL,
    [UpdatedAt] [datetime] NULL
)
```

## API Endpoints

### 1. View Academic Years
- **URL**: `/master-data/academic-year/`
- **Method**: GET
- **Access**: Super Admin, School Admin

### 2. Save Academic Year (Add/Update)
- **URL**: `/master-data/academic-year/save/`
- **Method**: POST
- **Parameters**:
  - `academic_year_id` (optional) - For update
  - `school_id` (Super Admin only)
  - `academic_year` - e.g., "2024-2025"
  - `start_date` - Start date
  - `end_date` - End date
  - `is_current` - Checkbox (0 or 1)
  - `is_active` - Checkbox (0 or 1)

### 3. Delete Academic Year
- **URL**: `/master-data/academic-year/delete/`
- **Method**: POST
- **Parameters**:
  - `academic_year_id` - ID to delete

### 4. Load Academic Years (Super Admin)
- **URL**: `/master-data/academic-year/load/`
- **Method**: POST
- **Parameters**:
  - `school_id` - School ID to load years for

## Stored Procedure Actions

### LIST
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'LIST',
    @SchoolId = 3
```

### ADD
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

### UPDATE
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

### DELETE
```sql
EXEC Proc_AcademicYear_CRUD 
    @Action = 'DELETE',
    @SchoolId = 3,
    @AcademicYearID = 1
```

## Business Logic

### Current Year Management
- Only one academic year can be marked as "Current" per school
- When setting a year as current, all other years for that school are automatically set to non-current
- This is handled in the stored procedure

### Validation
- Start Date and End Date are required
- Academic Year name is required (e.g., "2024-2025")
- School selection is required for Super Admin

## UI Features

### Page Design
- Matches Terms & Conditions page design
- Card-based layout with hover effects
- Modal for Add/Edit operations
- Responsive design for mobile devices
- Dark mode support

### Card Display
- Academic Year name with "Current" badge if applicable
- Date range display (Start Date - End Date)
- Active/Inactive status badge
- Edit and Delete action buttons

### Super Admin Features
- School selector dropdown at the top
- Dynamic loading of academic years based on selected school
- Can manage academic years for any school

### School Admin Features
- Automatically shows their school's academic years
- No school selector (uses session SchoolID)

## Menu Structure
```
Master Data
└── Academic Year
    ├── Super Admin (Full Access)
    └── School Admin (Full Access)
```

## Testing Checklist

### Super Admin Tests
- [ ] Can see school selector
- [ ] Can select a school
- [ ] Can view academic years for selected school
- [ ] Can add new academic year
- [ ] Can edit existing academic year
- [ ] Can delete academic year
- [ ] Can set current year (others become non-current)
- [ ] Can switch between schools

### School Admin Tests
- [ ] Cannot see school selector
- [ ] Can view their school's academic years
- [ ] Can add new academic year
- [ ] Can edit existing academic year
- [ ] Can delete academic year
- [ ] Can set current year (others become non-current)

### Validation Tests
- [ ] Cannot submit without academic year name
- [ ] Cannot submit without start date
- [ ] Cannot submit without end date
- [ ] Super Admin cannot add without selecting school
- [ ] Only one year can be current at a time

## Troubleshooting

### Menu Not Showing
```sql
-- Check menu exists
SELECT * FROM MenuMaster WHERE MenuName = 'Academic Year';

-- Check permissions
SELECT * FROM ProfileMenuMapping WHERE MenuID IN (
    SELECT MenuID FROM MenuMaster WHERE MenuName = 'Academic Year'
);

-- Re-run menu script if needed
-- Execute: database/add_academic_year_menu.sql
```

### Stored Procedure Not Found
```sql
-- Check if procedure exists
SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD';

-- Re-create if needed
-- Execute: database/procedures/Proc_AcademicYear_CRUD.sql
```

### Page Not Loading
1. Check URL configuration in `core/urls.py`
2. Verify view import: `from . import academic_year_views`
3. Check template exists: `core/templates/academic_year.html`
4. Verify user has menu access

## Future Enhancements
- [ ] Bulk import of academic years
- [ ] Academic year templates
- [ ] Automatic year generation
- [ ] Year-wise reports
- [ ] Academic calendar integration

## Support
For issues or questions, contact the development team.
