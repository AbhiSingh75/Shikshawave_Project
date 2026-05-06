-- Add Documents menu for School Admin and Students
DECLARE @MenuID INT;

-- Insert main Documents menu
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Documents')
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuIcon, DisplayOrder, IsActive)
    VALUES ('Documents', '#', NULL, 'fas fa-file-alt', 8, 1);
    
    SET @MenuID = SCOPE_IDENTITY();
    
    -- Insert submenus
    INSERT INTO MenuMaster (MenuName, MenuURL, ParentMenuID, MenuIcon, DisplayOrder, IsActive)
    VALUES 
    ('Generate Document', '/documents/generate/', @MenuID, 'fas fa-plus-circle', 1, 1),
    ('View Documents', '/documents/view/', @MenuID, 'fas fa-list', 2, 1);
    
    -- Assign to School Admin (ProfileID = 2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID)
    SELECT 2, MenuID FROM MenuMaster WHERE MenuName IN ('Documents', 'Generate Document', 'View Documents');
    
    -- Assign View Documents to Students (ProfileID = 4)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID)
    SELECT 4, MenuID FROM MenuMaster WHERE MenuName IN ('Documents', 'View Documents');
    
    PRINT 'Documents menu added successfully';
END
ELSE
BEGIN
    PRINT 'Documents menu already exists';
END
GO
