-- Add Admission Instructions menu under Master Data
DECLARE @ParentMenuID INT;

-- Get Master Data menu ID
SELECT @ParentMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0;

-- Insert Admission Instructions menu
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuURL = '/master-data/admission-instructions/' AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, MenuIcon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Admission Instructions', '/master-data/admission-instructions/', 'fas fa-clipboard-list', @ParentMenuID, 8, 1, GETDATE(), 0);
    
    PRINT 'Admission Instructions menu added successfully';
END
ELSE
BEGIN
    PRINT 'Admission Instructions menu already exists';
END
GO
