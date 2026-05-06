-- =============================================
-- Academic Year Master Data - Complete Installation
-- =============================================
-- This script installs all components for Academic Year management
-- Run this script if migrations fail or for manual installation
-- =============================================

PRINT '========================================';
PRINT 'Installing Academic Year Master Data';
PRINT '========================================';
PRINT '';

-- =============================================
-- Step 1: Create Stored Procedure
-- =============================================
PRINT 'Step 1: Creating stored procedure...';

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD')
BEGIN
    DROP PROCEDURE Proc_AcademicYear_CRUD;
    PRINT '  - Dropped existing procedure';
END

EXEC('
CREATE PROCEDURE Proc_AcademicYear_CRUD
    @Action NVARCHAR(10),
    @SchoolId INT,
    @AcademicYearID INT = NULL,
    @AcademicYear NVARCHAR(10) = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @IsCurrent BIT = NULL,
    @IsActive BIT = NULL,
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = ''LIST''
    BEGIN
        SELECT AcademicYearID, SchoolID, AcademicYear, StartDate, EndDate, IsCurrent, IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
        FROM AcademicYear
        WHERE SchoolID = @SchoolId
        ORDER BY StartDate DESC;
    END
    
    ELSE IF @Action = ''ADD''
    BEGIN
        IF @IsCurrent = 1
        BEGIN
            UPDATE AcademicYear SET IsCurrent = 0 WHERE SchoolID = @SchoolId;
        END
        
        INSERT INTO AcademicYear (SchoolID, AcademicYear, StartDate, EndDate, IsCurrent, IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
        VALUES (@SchoolId, @AcademicYear, @StartDate, @EndDate, @IsCurrent, @IsActive, @UserId, GETDATE(), @UserId, GETDATE());
        
        SELECT ''SUCCESS'' AS Status, ''Academic Year added successfully'' AS Message, SCOPE_IDENTITY() AS Id;
    END
    
    ELSE IF @Action = ''UPDATE''
    BEGIN
        IF @IsCurrent = 1
        BEGIN
            UPDATE AcademicYear SET IsCurrent = 0 WHERE SchoolID = @SchoolId AND AcademicYearID != @AcademicYearID;
        END
        
        UPDATE AcademicYear
        SET AcademicYear = @AcademicYear,
            StartDate = @StartDate,
            EndDate = @EndDate,
            IsCurrent = @IsCurrent,
            IsActive = @IsActive,
            UpdatedBy = @UserId,
            UpdatedAt = GETDATE()
        WHERE AcademicYearID = @AcademicYearID AND SchoolID = @SchoolId;
        
        SELECT ''SUCCESS'' AS Status, ''Academic Year updated successfully'' AS Message, @AcademicYearID AS Id;
    END
    
    ELSE IF @Action = ''DELETE''
    BEGIN
        DELETE FROM AcademicYear
        WHERE AcademicYearID = @AcademicYearID AND SchoolID = @SchoolId;
        
        SELECT ''SUCCESS'' AS Status, ''Academic Year deleted successfully'' AS Message;
    END
END
');

PRINT '  ✓ Stored procedure created successfully';
PRINT '';

-- =============================================
-- Step 2: Add Menu Entry
-- =============================================
PRINT 'Step 2: Adding menu entry...';

DECLARE @ParentMenuId INT;
DECLARE @AcademicYearMenuId INT;

-- Get or create Master Data parent menu
SELECT @ParentMenuId = MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND ParentMenuID IS NULL;

IF @ParentMenuId IS NULL
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuOrder, IconClass, IsActive, CreatedAt, UpdatedAt)
    VALUES ('Master Data', '#', NULL, 90, 'fas fa-database', 1, GETDATE(), GETDATE());
    
    SET @ParentMenuId = SCOPE_IDENTITY();
    PRINT '  - Created Master Data parent menu';
END

-- Check if Academic Year menu already exists
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Academic Year' AND MenuURL = '/master-data/academic-year/')
BEGIN
    SELECT @AcademicYearMenuId = MenuID FROM MenuMaster WHERE MenuName = 'Academic Year' AND MenuURL = '/master-data/academic-year/';
    PRINT '  - Academic Year menu already exists';
END
ELSE
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuOrder, IconClass, IsActive, CreatedAt, UpdatedAt)
    VALUES ('Academic Year', '/master-data/academic-year/', @ParentMenuId, 4, 'fas fa-calendar-alt', 1, GETDATE(), GETDATE());
    
    SET @AcademicYearMenuId = SCOPE_IDENTITY();
    PRINT '  ✓ Academic Year menu created';
END

PRINT '';

-- =============================================
-- Step 3: Assign Menu Permissions
-- =============================================
PRINT 'Step 3: Assigning menu permissions...';

-- Super Admin (ProfileID = 1)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 1 AND MenuID = @AcademicYearMenuId)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsActive, CreatedAt, UpdatedAt)
    VALUES (1, @AcademicYearMenuId, 1, 1, 1, 1, 1, GETDATE(), GETDATE());
    PRINT '  ✓ Assigned to Super Admin';
END
ELSE
BEGIN
    PRINT '  - Super Admin already has access';
END

-- School Admin (ProfileID = 2)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @AcademicYearMenuId)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsActive, CreatedAt, UpdatedAt)
    VALUES (2, @AcademicYearMenuId, 1, 1, 1, 1, 1, GETDATE(), GETDATE());
    PRINT '  ✓ Assigned to School Admin';
END
ELSE
BEGIN
    PRINT '  - School Admin already has access';
END

PRINT '';

-- =============================================
-- Step 4: Verification
-- =============================================
PRINT 'Step 4: Verifying installation...';

-- Check procedure
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD')
    PRINT '  ✓ Stored procedure exists';
ELSE
    PRINT '  ✗ Stored procedure NOT found';

-- Check menu
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Academic Year')
    PRINT '  ✓ Menu entry exists';
ELSE
    PRINT '  ✗ Menu entry NOT found';

-- Check permissions
DECLARE @PermCount INT;
SELECT @PermCount = COUNT(*) FROM ProfileMenuMapping WHERE MenuID = @AcademicYearMenuId;
PRINT '  ✓ Menu permissions: ' + CAST(@PermCount AS NVARCHAR) + ' profiles';

PRINT '';
PRINT '========================================';
PRINT 'Installation Complete!';
PRINT '========================================';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Access URL: /master-data/academic-year/';
PRINT '2. Super Admin: Select school and manage years';
PRINT '3. School Admin: Manage their school years';
PRINT '';
PRINT 'Test Query:';
PRINT 'EXEC Proc_AcademicYear_CRUD @Action = ''LIST'', @SchoolId = 3';
PRINT '';
