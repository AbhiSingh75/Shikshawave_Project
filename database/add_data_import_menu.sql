-- Add Data Import Menu and Submenus to ShikshaWave ERP
-- Run this script in SQL Server Management Studio

USE ShikshaWaveDB;
GO

-- Variables
DECLARE @ParentMenuID INT;
DECLARE @DashboardMenuID INT;
DECLARE @StudentsMenuID INT;
DECLARE @TeachersMenuID INT;
DECLARE @SalaryMenuID INT;
DECLARE @FeeMenuID INT;
DECLARE @AttendanceMenuID INT;
DECLARE @ExamMenuID INT;
DECLARE @ExamResultMenuID INT;
DECLARE @ClassMenuID INT;
DECLARE @SectionMenuID INT;
DECLARE @SubjectMenuID INT;

-- 1. Create Parent Menu: Data Import
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Data Import', 100, NULL, '#', 'fas fa-upload', 1, 1, GETDATE(), 0);

SET @ParentMenuID = SCOPE_IDENTITY();
PRINT 'Parent Menu Created: Data Import (ID: ' + CAST(@ParentMenuID AS NVARCHAR) + ')';

-- 2. Create Submenu: Dashboard
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Dashboard', 1, @ParentMenuID, '/import/dashboard/', 'fas fa-tachometer-alt', 1, 1, GETDATE(), 0);

SET @DashboardMenuID = SCOPE_IDENTITY();
PRINT 'Submenu Created: Import Dashboard (ID: ' + CAST(@DashboardMenuID AS NVARCHAR) + ')';

-- 3. Create Submenu: Import Students
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Students', 2, @ParentMenuID, '/import/dashboard/?type=Students', 'fas fa-user-graduate', 1, 1, GETDATE(), 0);

SET @StudentsMenuID = SCOPE_IDENTITY();

-- 4. Create Submenu: Import Teachers
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Teachers', 3, @ParentMenuID, '/import/dashboard/?type=Teachers', 'fas fa-chalkboard-teacher', 1, 1, GETDATE(), 0);

SET @TeachersMenuID = SCOPE_IDENTITY();

-- 5. Create Submenu: Import Salary
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Salary', 4, @ParentMenuID, '/import/dashboard/?type=Salary', 'fas fa-money-bill-wave', 1, 1, GETDATE(), 0);

SET @SalaryMenuID = SCOPE_IDENTITY();

-- 6. Create Submenu: Import Fee History
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Fee History', 5, @ParentMenuID, '/import/dashboard/?type=Fee', 'fas fa-receipt', 1, 1, GETDATE(), 0);

SET @FeeMenuID = SCOPE_IDENTITY();

-- 7. Create Submenu: Import Attendance
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Attendance', 6, @ParentMenuID, '/import/dashboard/?type=Attendance', 'fas fa-calendar-check', 1, 1, GETDATE(), 0);

SET @AttendanceMenuID = SCOPE_IDENTITY();

-- 8. Create Submenu: Import Exams
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Exams', 7, @ParentMenuID, '/import/dashboard/?type=Exam', 'fas fa-file-alt', 1, 1, GETDATE(), 0);

SET @ExamMenuID = SCOPE_IDENTITY();

-- 9. Create Submenu: Import Exam Results
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Exam Results', 8, @ParentMenuID, '/import/dashboard/?type=ExamResult', 'fas fa-chart-line', 1, 1, GETDATE(), 0);

SET @ExamResultMenuID = SCOPE_IDENTITY();

-- 10. Create Submenu: Import Classes
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Classes', 9, @ParentMenuID, '/import/dashboard/?type=ClassMaster', 'fas fa-school', 1, 1, GETDATE(), 0);

SET @ClassMenuID = SCOPE_IDENTITY();

-- 11. Create Submenu: Import Sections
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Sections', 10, @ParentMenuID, '/import/dashboard/?type=SectionMaster', 'fas fa-layer-group', 1, 1, GETDATE(), 0);

SET @SectionMenuID = SCOPE_IDENTITY();

-- 12. Create Submenu: Import Subjects
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedBy, CreatedAt, IsDeleted)
VALUES ('Import Subjects', 11, @ParentMenuID, '/import/dashboard/?type=SubjectMaster', 'fas fa-book', 1, 1, GETDATE(), 0);

SET @SubjectMenuID = SCOPE_IDENTITY();

PRINT 'All submenus created successfully';

-- 13. Assign Parent Menu to Super Admin (ProfileID = 1)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
VALUES (1, @ParentMenuID, 1, 1, 1, 1, 1, GETDATE(), 0);

-- 14. Assign Parent Menu to School Admin (ProfileID = 2)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
VALUES (2, @ParentMenuID, 1, 1, 1, 1, 1, GETDATE(), 0);

PRINT 'Parent menu permissions assigned to Super Admin and School Admin';

-- 15. Assign all submenus to Super Admin
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
SELECT 1, MenuID, 1, 1, 1, 1, 1, GETDATE(), 0
FROM MenuMaster
WHERE ParentMenuID = @ParentMenuID;

-- 16. Assign all submenus to School Admin
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedBy, CreatedAt, IsDeleted)
SELECT 2, MenuID, 1, 1, 1, 1, 1, GETDATE(), 0
FROM MenuMaster
WHERE ParentMenuID = @ParentMenuID;

PRINT 'All submenu permissions assigned to Super Admin and School Admin';

-- 17. Verify menu structure
SELECT 
    m.MenuID,
    m.MenuName,
    m.DisplayOrder,
    ISNULL(pm.MenuName, 'ROOT') AS ParentMenu,
    m.MenuURL,
    m.Icon
FROM MenuMaster m
LEFT JOIN MenuMaster pm ON m.ParentMenuID = pm.MenuID
WHERE m.MenuID = @ParentMenuID OR m.ParentMenuID = @ParentMenuID
ORDER BY m.ParentMenuID, m.DisplayOrder;

PRINT '';
PRINT '✅ Data Import Menu Structure Created Successfully!';
PRINT '';
PRINT 'Menu Hierarchy:';
PRINT '├── Data Import (Parent)';
PRINT '    ├── Import Dashboard';
PRINT '    ├── Import Students';
PRINT '    ├── Import Teachers';
PRINT '    ├── Import Salary';
PRINT '    ├── Import Fee History';
PRINT '    ├── Import Attendance';
PRINT '    ├── Import Exams';
PRINT '    ├── Import Exam Results';
PRINT '    ├── Import Classes';
PRINT '    ├── Import Sections';
PRINT '    └── Import Subjects';
PRINT '';
PRINT 'Permissions assigned to:';
PRINT '- Super Admin (ProfileID = 1): Full Access';
PRINT '- School Admin (ProfileID = 2): Full Access';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Refresh your browser';
PRINT '2. Login as Super Admin or School Admin';
PRINT '3. Navigate to "Data Import" menu';
PRINT '4. Start importing data!';

GO
