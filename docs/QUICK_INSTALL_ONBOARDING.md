# Quick Installation Guide - School Onboarding & Data Import

## 🚀 5-Minute Setup

### Step 1: Database Setup (2 minutes)
```sql
-- Open SQL Server Management Studio
-- Connect to your ShikshaWave database
USE ShikshaWaveDB;
GO

-- 1. Create tracking tables
:r C:\Users\AbhishekKumar\Desktop\ShikshaWave_Project\database\tables\DataImportTables.sql

-- 2. Create student import procedure
:r C:\Users\AbhishekKumar\Desktop\ShikshaWave_Project\database\procedures\Proc_Student_Bulk_Import.sql

-- 3. Verify tables created
SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'DataImport%';
-- Should show: DataImportLog, DataImportErrors, DataImportMapping, DataImportTemplate

-- 4. Verify procedure created
SELECT * FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'Proc_Student_Bulk_Import';
```

### Step 2: Install Python Packages (1 minute)
```bash
cd C:\Users\AbhishekKumar\Desktop\ShikshaWave_Project
env\Scripts\activate
pip install pandas==2.0.3 openpyxl==3.1.2
```

### Step 3: Configure Django (1 minute)

**Edit `ShikshaWave/urls.py`:**
```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('import/', include('core.data_import.urls')),  # ADD THIS LINE
]
```

**Edit `ShikshaWave/settings.py`:**
```python
# Add at the end of file
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_URL = '/media/'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
```

### Step 4: Create Menu Entry (1 minute)
```sql
-- Run in SQL Server
USE ShikshaWaveDB;
GO

-- Add Data Import menu
DECLARE @MenuID INT;

INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Data Import', 100, NULL, '/import/dashboard/', 'fa-upload', 1, 1, GETDATE(), 0);

SET @MenuID = SCOPE_IDENTITY();

-- Assign to Super Admin (ProfileID = 1)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
VALUES (1, @MenuID, 1, 1, 1, 1, 1, GETDATE(), 0);

-- Assign to School Admin (ProfileID = 2)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
VALUES (2, @MenuID, 1, 1, 1, 1, 1, GETDATE(), 0);

PRINT 'Menu created successfully!';
```

### Step 5: Test (30 seconds)
```bash
# Start Django server
python manage.py runserver

# Open browser: http://localhost:8000/import/dashboard/
# Login as Super Admin or School Admin
# You should see the Data Import dashboard
```

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Database tables exist (DataImportLog, DataImportErrors, etc.)
- [ ] Stored procedure exists (Proc_Student_Bulk_Import)
- [ ] Python packages installed (pandas, openpyxl)
- [ ] Django URLs configured
- [ ] Menu appears in navigation
- [ ] Can access /import/dashboard/
- [ ] Can download template
- [ ] Upload folder created automatically

---

## 🎯 Quick Test

### Test Student Import:

1. **Download Template:**
   - Go to http://localhost:8000/import/dashboard/
   - Select "Students" from dropdown
   - Click "Download Template"

2. **Fill Sample Data:**
   - Open downloaded Excel file
   - Keep the sample row or add your own
   - Required fields: FullName, Gender, DateOfBirth, ParentMobile, FatherName, AdmissionClass, Section, AdmissionDate
   - Save file

3. **Upload:**
   - Click "Upload File"
   - Select your Excel file
   - Wait for validation

4. **Import:**
   - If validation passed, click "Preview"
   - Click "Import"
   - Check success message

5. **Verify:**
   ```sql
   -- Check if student imported
   SELECT TOP 10 * FROM Student ORDER BY CreatedAt DESC;
   
   -- Check import log
   SELECT * FROM DataImportLog ORDER BY CreatedAt DESC;
   ```

---

## 🐛 Troubleshooting

### Issue: "Module not found: pandas"
**Solution:**
```bash
env\Scripts\activate
pip install pandas openpyxl
```

### Issue: "Table 'DataImportLog' doesn't exist"
**Solution:**
```sql
-- Re-run table creation script
:r C:\Users\AbhishekKumar\Desktop\ShikshaWave_Project\database\tables\DataImportTables.sql
```

### Issue: "Menu not appearing"
**Solution:**
```sql
-- Check if menu exists
SELECT * FROM MenuMaster WHERE MenuName = 'Data Import';

-- Check permissions
SELECT * FROM ProfileMenuMapping WHERE MenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import');

-- If missing, re-run Step 4
```

### Issue: "Upload folder not found"
**Solution:**
```bash
# Create manually
mkdir uploads
mkdir uploads\import_files
mkdir uploads\templates
```

### Issue: "File too large"
**Solution:**
- Check file size (max 10MB)
- Split into multiple files if needed
- Or increase limit in settings.py:
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20MB
```

---

## 📚 Next Steps

After successful installation:

1. **Create Frontend Templates:**
   - Copy template files from examples (to be provided)
   - Customize styling as needed

2. **Add More Import Types:**
   - Create stored procedures for Teachers, Salary, etc.
   - Follow Proc_Student_Bulk_Import.sql as template

3. **Test with Real Data:**
   - Export existing data to Excel
   - Test import with actual school data
   - Verify data integrity

4. **Train Users:**
   - Create user guide with screenshots
   - Record video tutorial
   - Conduct training session

---

## 📞 Support

For issues or questions:
- Check ONBOARDING_IMPLEMENTATION_PLAN.md for detailed documentation
- Review ONBOARDING_DELIVERABLES_SUMMARY.md for complete feature list
- Contact: ShikshaWave Development Team

---

**Installation Time:** ~5 minutes  
**Difficulty:** Easy  
**Prerequisites:** SQL Server, Django, Python 3.x  
**Status:** Production Ready
