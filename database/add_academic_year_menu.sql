-- Add Academic Year Menu for School Admin and Super Admin
-- This script adds the Academic Year menu item under Master Data section

-- First, check if the menu already exists
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Academic Year' AND MenuURL = '/master-data/academic-year/')
BEGIN
    -- Get the Master Data parent menu ID
    DECLARE @ParentMenuId INT;
    SELECT @ParentMenuId = MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND ParentMenuID IS NULL;

    -- If Master Data menu doesn't exist, create it
    IF @ParentMenuId IS NULL
    BEGIN
        INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuOrder, IconClass, IsActive, CreatedAt, UpdatedAt)
        VALUES ('Master Data', '#', NULL, 90, 'fas fa-database', 1, GETDATE(), GETDATE());
        
        SET @ParentMenuId = SCOPE_IDENTITY();
    END

    -- Insert Academic Year menu
    INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuOrder, IconClass, IsActive, CreatedAt, UpdatedAt)
    VALUES ('Academic Year', '/master-data/academic-year/', @ParentMenuId, 4, 'fas fa-calendar-alt', 1, GETDATE(), GETDATE());

    DECLARE @AcademicYearMenuId INT = SCOPE_IDENTITY();

    -- Assign to Super Admin (ProfileID = 1)
    IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 1 AND MenuID = @AcademicYearMenuId)
    BEGIN
        INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsActive, CreatedAt, UpdatedAt)
        VALUES (1, @AcademicYearMenuId, 1, 1, 1, 1, 1, GETDATE(), GETDATE());
    END

    -- Assign to School Admin (ProfileID = 2)
    IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @AcademicYearMenuId)
    BEGIN
        INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsActive, CreatedAt, UpdatedAt)
        VALUES (2, @AcademicYearMenuId, 1, 1, 1, 1, 1, GETDATE(), GETDATE());
    END

    PRINT 'Academic Year menu added successfully for Super Admin and School Admin';
END
ELSE
BEGIN
    PRINT 'Academic Year menu already exists';
END
