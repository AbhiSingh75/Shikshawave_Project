-- Add Terms & Conditions menu item under Master Data

DECLARE @MasterDataMenuId INT;
DECLARE @MaxDisplayOrder INT;

-- Get Master Data parent menu ID
SELECT @MasterDataMenuId = MenuID 
FROM MenuMaster 
WHERE MenuName = 'Master Data' AND IsDeleted = 0;

-- Get max display order under Master Data
SELECT @MaxDisplayOrder = ISNULL(MAX(DisplayOrder), 0) + 1
FROM MenuMaster
WHERE ParentMenuID = @MasterDataMenuId AND IsDeleted = 0;

-- Insert Terms & Conditions menu
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuURL = '/master-data/terms-conditions/' AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedAt, IsDeleted)
    VALUES ('Terms & Conditions', @MaxDisplayOrder, @MasterDataMenuId, '/master-data/terms-conditions/', 'fas fa-file-contract', 1, GETDATE(), 0);
    
    PRINT 'Terms & Conditions menu added successfully';
END
ELSE
BEGIN
    PRINT 'Terms & Conditions menu already exists';
END

-- Grant access to Super Admin and School Admin
DECLARE @TermsMenuId INT;
SELECT @TermsMenuId = MenuID FROM MenuMaster WHERE MenuURL = '/master-data/terms-conditions/' AND IsDeleted = 0;

-- Super Admin (ProfileID = 1)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 1 AND MenuID = @TermsMenuId AND IsDeleted = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @TermsMenuId, 1, 1, 1, 1, GETDATE(), 0);
END

-- School Admin (ProfileID = 2)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @TermsMenuId AND IsDeleted = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @TermsMenuId, 1, 1, 1, 1, GETDATE(), 0);
END

PRINT 'Menu permissions granted to Super Admin and School Admin';
GO
