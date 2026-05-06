# Salary Component Master Data Management

## Overview
This module provides complete CRUD (Create, Read, Update, Delete, Restore) functionality for managing salary components in the ShikshaWave ERP system. The design follows the same pattern as the Fee Type Management module.

## Features
- ✅ List all salary components with filtering
- ✅ Add new salary components
- ✅ Edit existing salary components
- ✅ Soft delete salary components
- ✅ Restore deleted salary components
- ✅ School-based access control (Super Admin sees all, School Admin sees only their school)
- ✅ Component type validation (Earning/Deduction)
- ✅ Duplicate prevention per school

## Files Created

### 1. Database Stored Procedure
**File:** `database/procedures/Proc_SalaryComponentMaster_Manage.sql`
- Single unified procedure handling all CRUD operations
- Actions: INSERT, UPDATE, DELETE, RESTORE
- Validates component type (Earning/Deduction)
- Prevents duplicate component names per school
- Returns JSON response with status and message

### 2. Django Migration
**File:** `core/migrations/0044_create_salary_component_procedure.py`
- Creates the stored procedure in the database
- Run with: `python manage.py migrate`

### 3. HTML Templates
**Location:** `core/templates/core/`

#### a. salary_component_list.html
- Lists all salary components
- Shows component name, type (Earning/Deduction), school (for super admin), and status
- Action buttons: Edit, Delete, Restore
- Responsive design matching Fee Type Management

#### b. salary_component_add.html
- Form to add new salary component
- Fields:
  - School (for super admin only)
  - Component Name (required)
  - Component Type (Earning/Deduction) (required)
- Client-side validation
- Matches Fee Type Management design

#### c. salary_component_edit.html
- Form to edit existing salary component
- Shows current component information
- Fields:
  - Component Name (required)
  - Component Type (Earning/Deduction) (required)
- Client-side validation

### 4. View Functions
**File:** `core/salary_component_views.py`

Functions:
- `salary_component_list(request)` - List all components
- `salary_component_add(request)` - Add new component
- `salary_component_edit(request, component_id)` - Edit component
- `salary_component_delete(request, component_id)` - Soft delete component
- `salary_component_restore(request, component_id)` - Restore deleted component

### 5. URL Patterns
**File:** `core/urls.py`

Routes added:
```python
path('master-data/salary-component/', salary_component_views.salary_component_list, name='salary_component_list')
path('master-data/salary-component/add/', salary_component_views.salary_component_add, name='salary_component_add')
path('master-data/salary-component/<int:component_id>/edit/', salary_component_views.salary_component_edit, name='salary_component_edit')
path('master-data/salary-component/<int:component_id>/delete/', salary_component_views.salary_component_delete, name='salary_component_delete')
path('master-data/salary-component/<int:component_id>/restore/', salary_component_views.salary_component_restore, name='salary_component_restore')
```

## Database Table Structure
The module uses the existing `SalaryComponentMaster` table:

```sql
CREATE TABLE [dbo].[SalaryComponentMaster](
    [ComponentID] [int] IDENTITY(1,1) NOT NULL,
    [SchoolID] [int] NOT NULL,
    [ComponentName] [nvarchar](100) NOT NULL,
    [ComponentType] [nvarchar](20) NOT NULL,  -- 'Earning' or 'Deduction'
    [CreatedBy] [int] NULL,
    [CreatedAt] [datetime] NULL,
    [UpdatedBy] [int] NULL,
    [UpdatedAt] [datetime] NULL,
    [DeletedBy] [int] NULL,
    [DeletedAt] [datetime] NULL,
    [IsDeleted] [bit] NOT NULL
)
```

## Usage

### 1. Run Migration
```bash
python manage.py migrate
```

### 2. Add Menu Item

**Option A: Using Django Management Command (Recommended)**
```bash
python manage.py add_salary_component_menu
```

**Option B: Using SQL Script**
```bash
# Run the SQL script in SQL Server Management Studio or Azure Data Studio
# File: database/add_salary_component_menu.sql
```

**Option C: Manual SQL**
```sql
INSERT INTO MenuMaster (MenuName, MenuURL, MenuIcon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
VALUES ('Salary Components', '/master-data/salary-component/', 'fas fa-money-check-alt', 
        (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Master Data'), 
        50, 1, GETDATE(), 0);
```

### 3. Access URLs
- **List:** `/master-data/salary-component/`
- **Add:** `/master-data/salary-component/add/`
- **Edit:** `/master-data/salary-component/<id>/edit/`
- **Delete:** `/master-data/salary-component/<id>/delete/`
- **Restore:** `/master-data/salary-component/<id>/restore/`

## Access Control
- **Super Admin (ProfileID = 1):** Can view and manage salary components for all schools
- **School Admin (ProfileID = 2):** Can view and manage salary components only for their school
- **Other Profiles:** Access controlled via ProfileMenuMapping

## Component Types
- **Earning:** Components that add to salary (e.g., Basic Salary, HRA, DA, Allowances)
- **Deduction:** Components that subtract from salary (e.g., PF, ESI, Tax, Loan)

## Validation Rules
1. Component Name is required (max 100 characters)
2. Component Type must be either 'Earning' or 'Deduction'
3. School ID is required
4. Duplicate component names are not allowed per school
5. Soft delete preserves data (IsDeleted = 1)
6. Restore functionality available for deleted components

## Design Pattern
This module follows the exact same design pattern as Fee Type Management:
- Single stored procedure for all CRUD operations
- Consistent UI/UX with other master data modules
- Responsive design for mobile and desktop
- Action buttons (Edit/Delete/Restore) based on status
- Color-coded badges for component types and status
- Client-side and server-side validation

## Testing Checklist
- [ ] List page displays all components correctly
- [ ] Super admin can see all schools' components
- [ ] School admin can see only their school's components
- [ ] Add new component with valid data
- [ ] Prevent duplicate component names per school
- [ ] Edit existing component
- [ ] Delete component (soft delete)
- [ ] Restore deleted component
- [ ] Validate component type (Earning/Deduction)
- [ ] Responsive design on mobile devices
- [ ] Error messages display correctly
- [ ] Success messages display correctly

## Future Enhancements
- [ ] Search and filter functionality
- [ ] Pagination for large datasets
- [ ] Export to CSV/Excel
- [ ] Bulk operations (delete/restore multiple)
- [ ] Audit trail view
- [ ] Component usage tracking (which employees use which components)

## Support
For issues or questions, contact the development team.
