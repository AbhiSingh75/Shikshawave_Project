-- Add Subject Master menu under Master Data
DECLARE @ParentMenuID INT;
DECLARE @MenuID INT;

-- Get Master Data parent menu ID
SELECT @ParentMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0;

-- Check if menu already exists
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuURL = '/master-data/subject/' AND IsDeleted = 0)
BEGIN
    -- Insert Subject Master menu
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Subject Master', '/master-data/subject/', 'fas fa-book', @ParentMenuID, 25, 1, GETDATE(), 0);
    
    SET @MenuID = SCOPE_IDENTITY();
    
    -- Grant access to Super Admin (ProfileID = 1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @MenuID, 1, 1, 1, 1, GETDATE(), 0);
    
    -- Grant access to School Admin (ProfileID = 2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @MenuID, 1, 1, 1, 1, GETDATE(), 0);
    
    PRINT 'Subject Master menu added successfully';
END
ELSE
BEGIN
    PRINT 'Subject Master menu already exists';
END
GO
