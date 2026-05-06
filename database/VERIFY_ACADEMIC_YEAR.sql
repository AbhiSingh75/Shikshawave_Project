-- =============================================
-- Academic Year - Verification & Testing Script
-- =============================================
-- Run this script to verify installation and test functionality
-- =============================================

PRINT '========================================';
PRINT 'Academic Year - Verification Script';
PRINT '========================================';
PRINT '';

-- =============================================
-- 1. Check Stored Procedure
-- =============================================
PRINT '1. Checking Stored Procedure...';
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD')
BEGIN
    PRINT '   ✓ Proc_AcademicYear_CRUD exists';
    
    -- Show procedure details
    SELECT 
        name AS ProcedureName,
        create_date AS CreatedDate,
        modify_date AS ModifiedDate
    FROM sys.procedures 
    WHERE name = 'Proc_AcademicYear_CRUD';
END
ELSE
BEGIN
    PRINT '   ✗ Proc_AcademicYear_CRUD NOT FOUND!';
    PRINT '   → Run: database/procedures/Proc_AcademicYear_CRUD.sql';
END
PRINT '';

-- =============================================
-- 2. Check Menu Entry
-- =============================================
PRINT '2. Checking Menu Entry...';
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Academic Year')
BEGIN
    PRINT '   ✓ Academic Year menu exists';
    
    -- Show menu details
    SELECT 
        MenuID,
        MenuName,
        MenuURL,
        ParentMenuID,
        MenuOrder,
        IconClass,
        IsActive
    FROM MenuMaster 
    WHERE MenuName = 'Academic Year';
END
ELSE
BEGIN
    PRINT '   ✗ Academic Year menu NOT FOUND!';
    PRINT '   → Run: database/add_academic_year_menu.sql';
END
PRINT '';

-- =============================================
-- 3. Check Menu Permissions
-- =============================================
PRINT '3. Checking Menu Permissions...';
DECLARE @MenuId INT;
SELECT @MenuId = MenuID FROM MenuMaster WHERE MenuName = 'Academic Year';

IF @MenuId IS NOT NULL
BEGIN
    SELECT 
        p.ProfileName,
        pm.CanView,
        pm.CanAdd,
        pm.CanEdit,
        pm.CanDelete,
        pm.IsActive
    FROM ProfileMenuMapping pm
    JOIN Profile p ON pm.ProfileID = p.ProfileID
    WHERE pm.MenuID = @MenuId;
    
    DECLARE @PermCount INT;
    SELECT @PermCount = COUNT(*) FROM ProfileMenuMapping WHERE MenuID = @MenuId;
    PRINT '   ✓ Permissions assigned to ' + CAST(@PermCount AS NVARCHAR) + ' profile(s)';
END
ELSE
BEGIN
    PRINT '   ✗ Cannot check permissions - Menu not found';
END
PRINT '';

-- =============================================
-- 4. Check AcademicYear Table
-- =============================================
PRINT '4. Checking AcademicYear Table...';
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'AcademicYear')
BEGIN
    PRINT '   ✓ AcademicYear table exists';
    
    -- Show table structure
    SELECT 
        COLUMN_NAME,
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'AcademicYear'
    ORDER BY ORDINAL_POSITION;
    
    -- Show record count
    DECLARE @RecordCount INT;
    SELECT @RecordCount = COUNT(*) FROM AcademicYear;
    PRINT '   → Total records: ' + CAST(@RecordCount AS NVARCHAR);
END
ELSE
BEGIN
    PRINT '   ✗ AcademicYear table NOT FOUND!';
    PRINT '   → Create table using the schema provided';
END
PRINT '';

-- =============================================
-- 5. Test Stored Procedure - LIST
-- =============================================
PRINT '5. Testing Stored Procedure - LIST Action...';
BEGIN TRY
    -- Get first active school
    DECLARE @TestSchoolId INT;
    SELECT TOP 1 @TestSchoolId = SchoolID FROM School WHERE IsActive = 1;
    
    IF @TestSchoolId IS NOT NULL
    BEGIN
        PRINT '   Testing with SchoolID: ' + CAST(@TestSchoolId AS NVARCHAR);
        
        EXEC Proc_AcademicYear_CRUD 
            @Action = 'LIST',
            @SchoolId = @TestSchoolId;
        
        PRINT '   ✓ LIST action executed successfully';
    END
    ELSE
    BEGIN
        PRINT '   ⚠ No active schools found for testing';
    END
END TRY
BEGIN CATCH
    PRINT '   ✗ Error executing LIST action:';
    PRINT '   ' + ERROR_MESSAGE();
END CATCH
PRINT '';

-- =============================================
-- 6. Sample Data Check
-- =============================================
PRINT '6. Checking Sample Data...';
IF EXISTS (SELECT 1 FROM AcademicYear)
BEGIN
    PRINT '   Existing Academic Years:';
    SELECT 
        AcademicYearID,
        SchoolID,
        AcademicYear,
        StartDate,
        EndDate,
        IsCurrent,
        IsActive
    FROM AcademicYear
    ORDER BY SchoolID, StartDate DESC;
END
ELSE
BEGIN
    PRINT '   ⚠ No academic years found in database';
    PRINT '   → Add academic years through the UI';
END
PRINT '';

-- =============================================
-- 7. Test ADD Action (Optional - Commented)
-- =============================================
PRINT '7. Test ADD Action (Commented - Uncomment to test)...';
PRINT '   -- Uncomment below to test adding a record:';
PRINT '   /*';
PRINT '   EXEC Proc_AcademicYear_CRUD';
PRINT '       @Action = ''ADD'',';
PRINT '       @SchoolId = 3,';
PRINT '       @AcademicYear = ''2024-2025'',';
PRINT '       @StartDate = ''2024-04-01'',';
PRINT '       @EndDate = ''2025-03-31'',';
PRINT '       @IsCurrent = 1,';
PRINT '       @IsActive = 1,';
PRINT '       @UserId = 1';
PRINT '   */';
PRINT '';

-- =============================================
-- 8. URL Access Check
-- =============================================
PRINT '8. URL Access Information...';
PRINT '   Main URL: /master-data/academic-year/';
PRINT '   Save URL: /master-data/academic-year/save/';
PRINT '   Delete URL: /master-data/academic-year/delete/';
PRINT '   Load URL: /master-data/academic-year/load/';
PRINT '';

-- =============================================
-- 9. Summary
-- =============================================
PRINT '========================================';
PRINT 'Verification Summary';
PRINT '========================================';

DECLARE @AllGood BIT = 1;

IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'Proc_AcademicYear_CRUD')
BEGIN
    PRINT '✗ Stored Procedure Missing';
    SET @AllGood = 0;
END

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Academic Year')
BEGIN
    PRINT '✗ Menu Entry Missing';
    SET @AllGood = 0;
END

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AcademicYear')
BEGIN
    PRINT '✗ AcademicYear Table Missing';
    SET @AllGood = 0;
END

IF @AllGood = 1
BEGIN
    PRINT '✓ All components installed correctly!';
    PRINT '';
    PRINT 'Next Steps:';
    PRINT '1. Login to application';
    PRINT '2. Navigate to: Master Data → Academic Year';
    PRINT '3. Start managing academic years';
END
ELSE
BEGIN
    PRINT '';
    PRINT '⚠ Some components are missing!';
    PRINT 'Run: database/INSTALL_ACADEMIC_YEAR.sql';
END

PRINT '';
PRINT '========================================';
