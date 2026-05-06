# Employment Type Field Implementation

## Overview
Added Employment Type field to the Employee Add page with three options: Permanent, Contract, and Guest.

## Changes Made

### 1. Frontend Changes (add_employee.html)
- Added Employment Type dropdown field after Date of Joining field
- Field is marked as required with validation
- Options: Permanent, Contract, Guest

**Location:** `core/templates/add_employee.html`

### 2. Backend Changes (views.py)
- Updated `add_employee_submit` function to capture `employmentType` from form
- Added validation for Employment Type field
- Passed `employment_type` parameter to stored procedure

**Location:** `core/views.py` (lines ~7540-7720)

### 3. Database Changes (Stored Procedure)
- Updated `Proc_Executive_set` stored procedure to accept `@EmploymentType` parameter
- Added EmploymentType column to INSERT statement for EmployeeMaster table
- Parameter is optional (NVARCHAR(50) = NULL)

**Location:** `database/procedures/Proc_Executive_set_Update_EmploymentType.sql`

## Database Prerequisites

### Required Column in EmployeeMaster Table
Ensure the `EmployeeMaster` table has the `EmploymentType` column:

```sql
-- Check if column exists
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'EmployeeMaster' 
AND COLUMN_NAME = 'EmploymentType';

-- If column doesn't exist, add it:
ALTER TABLE EmployeeMaster
ADD EmploymentType NVARCHAR(50) NULL;
```

## Installation Steps

1. **Update Database Column** (if not already done):
   ```sql
   ALTER TABLE EmployeeMaster
   ADD EmploymentType NVARCHAR(50) NULL;
   ```

2. **Update Stored Procedure**:
   - Run the SQL script: `database/procedures/Proc_Executive_set_Update_EmploymentType.sql`
   - This will drop and recreate the `Proc_Executive_set` procedure with the new parameter

3. **Frontend and Backend Changes**:
   - The changes to `add_employee.html` and `views.py` are already applied
   - No additional steps needed

## Testing

1. Navigate to: `http://127.0.0.1:8000/employees/add/`
2. Fill in the employee form
3. Select an Employment Type (Permanent, Contract, or Guest)
4. Submit the form
5. Verify the employee is created with the correct Employment Type in the database

## Validation

The Employment Type field is:
- **Required**: User must select a value
- **Options**: Permanent, Contract, Guest
- **Stored in**: EmployeeMaster.EmploymentType column

## Files Modified

1. `core/templates/add_employee.html` - Added Employment Type dropdown
2. `core/views.py` - Updated add_employee_submit function
3. `database/procedures/Proc_Executive_set_Update_EmploymentType.sql` - New procedure with EmploymentType parameter

## Notes

- The EmploymentType field is placed after Date of Joining for logical flow
- The field uses the same styling as other form fields for consistency
- The stored procedure handles NULL values gracefully if the field is not provided
- All existing functionality remains unchanged
