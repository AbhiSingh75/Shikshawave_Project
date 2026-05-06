-- =============================================
-- Update Attendance Menu Structure
-- =============================================
-- This script:
-- 1. Updates existing student attendance submenus
-- 2. Adds new employee/staff attendance submenus
-- 3. Adds new profile types (Accountant, Driver, Librarian)
-- 4. Maps menus to appropriate profiles
-- =============================================

-- Step 1: Add new profile types if they don't exist
IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 5)
BEGIN
    SET IDENTITY_INSERT ProfileMaster ON;
    INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
    VALUES (5, 'Accountant', 'School Accountant', 0);
    SET IDENTITY_INSERT ProfileMaster OFF;
    PRINT 'Accountant profile added';
END

IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 6)
BEGIN
    SET IDENTITY_INSERT ProfileMaster ON;
    INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
    VALUES (6, 'Driver', 'School Driver', 0);
    SET IDENTITY_INSERT ProfileMaster OFF;
    PRINT 'Driver profile added';
END

IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 7)
BEGIN
    SET IDENTITY_INSERT ProfileMaster ON;
    INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
    VALUES (7, 'Librarian', 'School Librarian', 0);
    SET IDENTITY_INSERT ProfileMaster OFF;
    PRINT 'Librarian profile added';
END

-- Step 2: Get or create Attendance parent menu
DECLARE @AttendanceMenuID INT;

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Attendance', NULL, 'fas fa-calendar-check', NULL, 30, 1, GETDATE(), 0);
    PRINT 'Attendance parent menu created';
END

SELECT @AttendanceMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0;

-- Step 3: Update existing student attendance submenus
DECLARE @MarkStudentAttendanceID INT, @ViewStudentAttendanceID INT;

-- Update "Mark Attendance" to "Mark Student Attendance"
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    UPDATE MenuMaster 
    SET MenuName = 'Mark Student Attendance'
    WHERE MenuName = 'Mark Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;
    PRINT 'Updated "Mark Attendance" to "Mark Student Attendance"';
END
ELSE IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Mark Student Attendance', '/attendance/mark/', 'fas fa-user-check', @AttendanceMenuID, 1, 1, GETDATE(), 0);
    PRINT 'Created "Mark Student Attendance" submenu';
END

SELECT @MarkStudentAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'Mark Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

-- Update "View Attendance" to "View Student Attendance"
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    UPDATE MenuMaster 
    SET MenuName = 'View Student Attendance'
    WHERE MenuName = 'View Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;
    PRINT 'Updated "View Attendance" to "View Student Attendance"';
END
ELSE IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('View Student Attendance', '/attendance/view/', 'fas fa-eye', @AttendanceMenuID, 2, 1, GETDATE(), 0);
    PRINT 'Created "View Student Attendance" submenu';
END

SELECT @ViewStudentAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'View Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

-- Step 4: Add new employee/staff attendance submenus
DECLARE @MarkEmployeeAttendanceID INT, @ViewEmployeeAttendanceID INT;

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Mark Employee/Staff Attendance', '/attendance/mark-employee/', 'fas fa-user-tie', @AttendanceMenuID, 3, 1, GETDATE(), 0);
    PRINT 'Created "Mark Employee/Staff Attendance" submenu';
END

SELECT @MarkEmployeeAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'Mark Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('View Employee/Staff Attendance', '/attendance/view-employee/', 'fas fa-users', @AttendanceMenuID, 4, 1, GETDATE(), 0);
    PRINT 'Created "View Employee/Staff Attendance" submenu';
END

SELECT @ViewEmployeeAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'View Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

-- Step 5: Map menus to profiles
-- Map Attendance parent menu to all profiles
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
SELECT p.ProfileID, @AttendanceMenuID, 1, 0, 0, 0, 0, GETDATE()
FROM ProfileMaster p
WHERE p.IsDeleted = 0 
AND NOT EXISTS (
    SELECT 1 FROM ProfileMenuMapping 
    WHERE ProfileID = p.ProfileID AND MenuID = @AttendanceMenuID
);

-- Map Mark Student Attendance (School Admin, Teacher)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
SELECT p.ProfileID, @MarkStudentAttendanceID, 1, 1, 1, 0, 0, GETDATE()
FROM ProfileMaster p
WHERE p.ProfileID IN (2, 3) -- School Admin, Teacher
AND p.IsDeleted = 0 
AND NOT EXISTS (
    SELECT 1 FROM ProfileMenuMapping 
    WHERE ProfileID = p.ProfileID AND MenuID = @MarkStudentAttendanceID
);

-- Map View Student Attendance (School Admin, Teacher)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
SELECT p.ProfileID, @ViewStudentAttendanceID, 1, 0, 0, 0, 0, GETDATE()
FROM ProfileMaster p
WHERE p.ProfileID IN (2, 3) -- School Admin, Teacher
AND p.IsDeleted = 0 
AND NOT EXISTS (
    SELECT 1 FROM ProfileMenuMapping 
    WHERE ProfileID = p.ProfileID AND MenuID = @ViewStudentAttendanceID
);

-- Map Mark Employee/Staff Attendance (School Admin, Teacher, Accountant, Driver, Librarian)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
SELECT p.ProfileID, @MarkEmployeeAttendanceID, 1, 1, 1, 0, 0, GETDATE()
FROM ProfileMaster p
WHERE p.ProfileID IN (2, 3, 5, 6, 7) -- School Admin, Teacher, Accountant, Driver, Librarian
AND p.IsDeleted = 0 
AND NOT EXISTS (
    SELECT 1 FROM ProfileMenuMapping 
    WHERE ProfileID = p.ProfileID AND MenuID = @MarkEmployeeAttendanceID
);

-- Map View Employee/Staff Attendance (School Admin, Teacher, Accountant, Driver, Librarian)
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
SELECT p.ProfileID, @ViewEmployeeAttendanceID, 1, 0, 0, 0, 0, GETDATE()
FROM ProfileMaster p
WHERE p.ProfileID IN (2, 3, 5, 6, 7) -- School Admin, Teacher, Accountant, Driver, Librarian
AND p.IsDeleted = 0 
AND NOT EXISTS (
    SELECT 1 FROM ProfileMenuMapping 
    WHERE ProfileID = p.ProfileID AND MenuID = @ViewEmployeeAttendanceID
);

PRINT '============================================='
PRINT 'Attendance menu update completed successfully!'
PRINT '============================================='
PRINT 'Summary:'
PRINT '- Added new profiles: Accountant, Driver, Librarian'
PRINT '- Updated: Mark Attendance -> Mark Student Attendance'
PRINT '- Updated: View Attendance -> View Student Attendance'
PRINT '- Added: Mark Employee/Staff Attendance'
PRINT '- Added: View Employee/Staff Attendance'
PRINT '- Mapped menus to appropriate profiles'
PRINT '============================================='
