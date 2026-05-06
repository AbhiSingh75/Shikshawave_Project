# Quick Installation Guide - Employment Type Feature

## Step-by-Step Installation

### Step 1: Add Database Column
Run this SQL script first:
```
database/add_employment_type_column.sql
```

This will:
- Add `EmploymentType` column to `EmployeeMaster` table
- Add a check constraint to ensure only valid values (Permanent, Contract, Guest)

### Step 2: Update Stored Procedure
Run this SQL script:
```
database/procedures/Proc_Executive_set_Update_EmploymentType.sql
```

This will:
- Drop the existing `Proc_Executive_set` procedure
- Create a new version with the `@EmploymentType` parameter

### Step 3: Verify Changes
The frontend and backend code changes are already applied:
- ✅ `core/templates/add_employee.html` - Employment Type dropdown added
- ✅ `core/views.py` - Backend processing updated

### Step 4: Test
1. Start your Django server
2. Navigate to: `http://127.0.0.1:8000/employees/add/`
3. Fill in the employee form
4. Select an Employment Type (required field)
5. Submit and verify

## Verification Queries

### Check if column exists:
```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'EmployeeMaster' 
AND COLUMN_NAME = 'EmploymentType';
```

### Check if procedure has the parameter:
```sql
SELECT 
    p.name AS ProcedureName,
    par.name AS ParameterName,
    t.name AS DataType
FROM sys.procedures p
INNER JOIN sys.parameters par ON p.object_id = par.object_id
INNER JOIN sys.types t ON par.user_type_id = t.user_type_id
WHERE p.name = 'Proc_Executive_set'
AND par.name = '@EmploymentType';
```

### Test data insertion:
```sql
-- View recent employees with Employment Type
SELECT TOP 10
    EmployeeID,
    EmployeeCode,
    EmployeeName,
    EmploymentType,
    DateOfJoining,
    CreatedAt
FROM EmployeeMaster
WHERE IsDeleted = 0
ORDER BY CreatedAt DESC;
```

## Rollback (if needed)

If you need to rollback the changes:

```sql
-- Remove check constraint
ALTER TABLE EmployeeMaster
DROP CONSTRAINT IF EXISTS CK_EmployeeMaster_EmploymentType;

-- Remove column
ALTER TABLE EmployeeMaster
DROP COLUMN IF EXISTS EmploymentType;
```

## Troubleshooting

### Issue: Column already exists error
**Solution**: The script checks for existence before adding. If you get this error, the column already exists.

### Issue: Procedure parameter mismatch
**Solution**: Make sure you run the procedure update script after adding the column.

### Issue: Form validation error
**Solution**: Clear browser cache and refresh the page. The Employment Type field is required.

## Support

For issues or questions, check:
- `EMPLOYMENT_TYPE_IMPLEMENTATION.md` for detailed documentation
- Database error logs for SQL-related issues
- Django console for backend errors
