# Quick Installation Guide - Dashboard Student Visualization

## Prerequisites
- ShikshaWave project already set up
- SQL Server database configured
- Django server running

## Installation Steps

### Step 1: Execute Stored Procedure
Open SQL Server Management Studio or use sqlcmd:

```sql
-- Option 1: Using SSMS
-- Open file: database/procedures/Proc_Dashboard_Students_Get.sql
-- Execute the script

-- Option 2: Using sqlcmd
sqlcmd -S your_server_name -d ShikshaWave_DB -i "database/procedures/Proc_Dashboard_Students_Get.sql"
```

### Step 2: Verify Installation
Check if the stored procedure was created:

```sql
-- Verify procedure exists
SELECT * FROM sys.procedures WHERE name = 'Proc_Dashboard_Students_Get';

-- Test the procedure
EXEC Proc_Dashboard_Students_Get @SchoolID = 3;
```

### Step 3: Restart Django Server
```bash
# Stop the server (Ctrl+C)
# Start again
python manage.py runserver
```

### Step 4: Test the Dashboard
1. Open browser and navigate to: `http://localhost:8000/login/`
2. Login with your credentials
3. You'll be redirected to the dashboard
4. You should see:
   - Filter section at the top
   - 5 cards showing student statistics
   - All filters should be populated

### Step 5: Test Filters
1. Select a class from the dropdown
2. Select a section (should populate after class selection)
3. Select gender and/or category
4. Click "Apply Filters"
5. Cards should update with filtered data

## Troubleshooting

### Issue: Stored procedure not found
**Solution:**
```sql
-- Check if procedure exists
SELECT * FROM sys.procedures WHERE name LIKE '%Dashboard%';

-- If not found, re-run the SQL script
```

### Issue: Filters showing no data
**Solution:**
```sql
-- Check if you have data in required tables
SELECT COUNT(*) FROM Student WHERE IsDeleted = 0;
SELECT COUNT(*) FROM ClassMaster WHERE IsDeleted = 0;
SELECT COUNT(*) FROM SectionMaster WHERE IsDeleted = 0;
```

### Issue: Section dropdown not populating
**Solution:**
- Make sure you select a class first
- Check browser console for JavaScript errors
- Verify `/api/sections/` endpoint is working:
  ```
  http://localhost:8000/api/sections/?class_id=1
  ```

### Issue: Cards showing 0 even with data
**Solution:**
```sql
-- Check if SchoolID matches your session
-- Run procedure with your SchoolID
EXEC Proc_Dashboard_Students_Get @SchoolID = YOUR_SCHOOL_ID;
```

## Verification Checklist

- [ ] Stored procedure created successfully
- [ ] Dashboard page loads without errors
- [ ] Filter dropdowns are populated
- [ ] Cards show correct initial data
- [ ] Section dropdown updates when class changes
- [ ] "Apply Filters" button works
- [ ] Cards update with filtered data
- [ ] No JavaScript errors in browser console

## Quick Test Commands

### Test API Endpoints
```bash
# Test classes API
curl http://localhost:8000/api/classes/

# Test sections API
curl http://localhost:8000/api/sections/?class_id=1

# Test dashboard students API (requires login)
curl -b cookies.txt http://localhost:8000/api/dashboard/students/
```

### Test Stored Procedure
```sql
-- Test with no filters (all students)
EXEC Proc_Dashboard_Students_Get @SchoolID = 3;

-- Test with class filter
EXEC Proc_Dashboard_Students_Get @SchoolID = 3, @ClassID = 5;

-- Test with gender filter
EXEC Proc_Dashboard_Students_Get @SchoolID = 3, @Gender = 'Male';

-- Test with category filter
EXEC Proc_Dashboard_Students_Get @SchoolID = 3, @Category = 'General';

-- Test with multiple filters
EXEC Proc_Dashboard_Students_Get 
    @SchoolID = 3, 
    @ClassID = 5, 
    @Gender = 'Male', 
    @Category = 'General';
```

## Expected Results

### Initial Dashboard Load
- Total Students: Shows count from database
- Male Students: Shows male count
- Female Students: Shows female count
- Active Students: Shows active count
- Category Breakdown: Shows "Gen: X | OBC: Y | SC: Z | ST: W"

### After Applying Filters
- All cards update with filtered counts
- Numbers should be less than or equal to initial counts
- Category breakdown updates accordingly

## Next Steps

After successful installation:
1. Review full documentation: `docs/DASHBOARD_STUDENT_VISUALIZATION.md`
2. Customize filters as needed
3. Add additional cards if required
4. Consider adding charts/graphs
5. Set up automated testing

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review browser console for JavaScript errors
3. Check Django server logs for backend errors
4. Verify database connectivity
5. Contact development team if issues persist

## Files Modified

This installation modified/created:
- `database/procedures/Proc_Dashboard_Students_Get.sql` (NEW)
- `core/views.py` (MODIFIED)
- `core/urls.py` (MODIFIED)
- `core/templates/core/dashboard.html` (MODIFIED)
- `docs/DASHBOARD_STUDENT_VISUALIZATION.md` (NEW)

## Rollback Instructions

If you need to rollback:

```sql
-- Drop the stored procedure
DROP PROCEDURE IF EXISTS Proc_Dashboard_Students_Get;
```

Then restore the original files from version control.

---

**Installation Complete!** 🎉

Your dashboard now has dynamic student data visualization with India standard school filters.
