-- Add OTP Template Management menu to MenuMaster and ProfileMenuMapping

-- Insert menu if not exists
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuURL = '/otp-template-management/')
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('OTP Template Management', '/otp-template-management/', 'fas fa-envelope-open-text', 
            (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0), 
            90, 1, GETDATE(), 0);
    
    DECLARE @MenuID INT = SCOPE_IDENTITY();
    
    -- Grant access to Super Admin (ProfileID = 1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @MenuID, 1, 1, 1, 1, GETDATE(), 0);
    
    -- Grant access to School Admin (ProfileID = 2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @MenuID, 1, 1, 1, 0, GETDATE(), 0);
    
    PRINT 'OTP Template Management menu added successfully';
END
ELSE
BEGIN
    PRINT 'OTP Template Management menu already exists';
END
GO
