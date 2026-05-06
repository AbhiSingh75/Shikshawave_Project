# Employment Type Feature - Installation Checklist

## Pre-Installation Checklist

- [ ] Backup your database before making changes
- [ ] Ensure you have database admin access
- [ ] Verify Django server is stopped (or restart after changes)
- [ ] Review all documentation files

## Installation Steps

### Step 1: Database Column Addition
- [ ] Open SQL Server Management Studio (or your SQL client)
- [ ] Connect to your database
- [ ] Open file: `database/add_employment_type_column.sql`
- [ ] Execute the script
- [ ] Verify output shows: "EmploymentType column added successfully"
- [ ] Run verification query:
  ```sql
  SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
  FROM INFORMATION_SCHEMA.COLUMNS 
  WHERE TABLE_NAME = 'EmployeeMaster' 
  AND COLUMN_NAME = 'EmploymentType';
  ```
- [ ] Confirm column exists with type NVARCHAR(50) and IS_NULLABLE = YES

### Step 2: Stored Procedure Update
- [ ] Open file: `database/procedures/Proc_Executive_set_Update_EmploymentType.sql`
- [ ] Execute the script
- [ ] Verify output shows procedure created successfully
- [ ] Run verification query:
  ```sql
  SELECT par.name AS ParameterName, t.name AS DataType
  FROM sys.procedures p
  INNER JOIN sys.parameters par ON p.object_id = par.object_id
  INNER JOIN sys.types t ON par.user_type_id = t.user_type_id
  WHERE p.name = 'Proc_Executive_set'
  AND par.name = '@EmploymentType';
  ```
- [ ] Confirm @EmploymentType parameter exists

### Step 3: Code Verification
- [ ] Verify file modified: `core/templates/add_employee.html`
  - [ ] Employment Type dropdown exists after Date of Joining
  - [ ] Field has id="employmentType" and name="employmentType"
  - [ ] Field is marked as required
  - [ ] Three options present: Permanent, Contract, Guest

- [ ] Verify file modified: `core/views.py`
  - [ ] Line ~7543: `employment_type = request.POST.get('employmentType', '').strip()`
  - [ ] Line ~7558: Validation for employment_type
  - [ ] Line ~7650: employment_type in procedure parameters

### Step 4: Server Restart
- [ ] Stop Django development server (Ctrl+C)
- [ ] Clear any cached files: `python manage.py clear_cache` (if applicable)
- [ ] Restart Django server: `python manage.py runserver`
- [ ] Verify server starts without errors

## Testing Checklist

### Test 1: Form Display
- [ ] Navigate to: `http://127.0.0.1:8000/employees/add/`
- [ ] Verify Employment Type field is visible
- [ ] Verify field is positioned after Date of Joining
- [ ] Verify field shows "Select Employment Type" as placeholder
- [ ] Verify dropdown shows three options: Permanent, Contract, Guest
- [ ] Verify field has red asterisk (*) indicating required

### Test 2: Form Validation
- [ ] Fill in all required fields EXCEPT Employment Type
- [ ] Click "Save Employee"
- [ ] Verify browser shows validation error
- [ ] Verify form does not submit

### Test 3: Successful Submission
- [ ] Fill in all required fields INCLUDING Employment Type
- [ ] Select "Permanent" from Employment Type dropdown
- [ ] Click "Save Employee"
- [ ] Verify success message appears
- [ ] Verify no errors in browser console
- [ ] Verify no errors in Django console

### Test 4: Database Verification
- [ ] Run query to check the newly created employee:
  ```sql
  SELECT TOP 1
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
- [ ] Verify EmploymentType column shows "Permanent"
- [ ] Verify all other fields are populated correctly

### Test 5: All Employment Types
- [ ] Create employee with Employment Type = "Contract"
- [ ] Verify successful creation
- [ ] Create employee with Employment Type = "Guest"
- [ ] Verify successful creation
- [ ] Run query to verify all three types:
  ```sql
  SELECT EmploymentType, COUNT(*) as Count
  FROM EmployeeMaster
  WHERE IsDeleted = 0
  GROUP BY EmploymentType;
  ```

### Test 6: Mobile Responsiveness
- [ ] Open browser developer tools (F12)
- [ ] Toggle device toolbar (mobile view)
- [ ] Navigate to employee add page
- [ ] Verify Employment Type field displays correctly
- [ ] Verify field is usable on mobile
- [ ] Test form submission on mobile view

### Test 7: Browser Compatibility
- [ ] Test in Chrome/Edge
- [ ] Test in Firefox
- [ ] Test in Safari (if available)
- [ ] Verify consistent behavior across browsers

## Post-Installation Verification

### Database Health Check
- [ ] Run query to check data integrity:
  ```sql
  -- Check for any invalid values
  SELECT EmployeeID, EmployeeName, EmploymentType
  FROM EmployeeMaster
  WHERE EmploymentType NOT IN ('Permanent', 'Contract', 'Guest')
  AND EmploymentType IS NOT NULL
  AND IsDeleted = 0;
  ```
- [ ] Verify no invalid values exist

### Application Health Check
- [ ] Check Django logs for any errors
- [ ] Verify no 500 errors on employee add page
- [ ] Verify no JavaScript console errors
- [ ] Test other employee-related pages still work

### Documentation Review
- [ ] Read `EMPLOYMENT_TYPE_IMPLEMENTATION.md`
- [ ] Read `QUICK_INSTALL_EMPLOYMENT_TYPE.md`
- [ ] Read `EMPLOYMENT_TYPE_SUMMARY.txt`
- [ ] Read `EMPLOYMENT_TYPE_VISUAL_GUIDE.txt`

## Rollback Plan (If Needed)

If something goes wrong, follow these steps to rollback:

### Rollback Step 1: Remove Database Changes
```sql
-- Remove check constraint
ALTER TABLE EmployeeMaster
DROP CONSTRAINT IF EXISTS CK_EmployeeMaster_EmploymentType;

-- Remove column
ALTER TABLE EmployeeMaster
DROP COLUMN IF EXISTS EmploymentType;
```

### Rollback Step 2: Restore Original Procedure
- [ ] Restore previous version of `Proc_Executive_set` from backup
- [ ] Or remove the @EmploymentType parameter manually

### Rollback Step 3: Revert Code Changes
- [ ] Use git to revert changes to `add_employee.html`
- [ ] Use git to revert changes to `views.py`
- [ ] Restart Django server

## Sign-Off

Installation completed by: _____________________ Date: _____________

Testing completed by: _____________________ Date: _____________

Approved by: _____________________ Date: _____________

## Notes

Use this space to document any issues encountered or deviations from the standard installation:

___________________________________________________________________

___________________________________________________________________

___________________________________________________________________

___________________________________________________________________

___________________________________________________________________
