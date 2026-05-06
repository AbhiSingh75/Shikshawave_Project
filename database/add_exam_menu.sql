-- Add Exam Management menu to MenuMaster
-- First, check if "Manage Exams" menu already exists
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Manage Exams' AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, MenuIcon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Manage Exams', '/exam/management/', 'fas fa-clipboard-list', NULL, 50, 1, GETDATE(), 0);
    
    PRINT 'Exam Management menu added successfully';
END
ELSE
BEGIN
    -- Update the URL if menu exists
    UPDATE MenuMaster 
    SET MenuURL = '/exam/management/', MenuIcon = 'fas fa-clipboard-list'
    WHERE MenuName = 'Manage Exams' AND IsDeleted = 0;
    
    PRINT 'Exam Management menu updated';
END

-- Grant access to all profiles (you can modify this as needed)
DECLARE @MenuID INT;
SELECT @MenuID = MenuID FROM MenuMaster WHERE MenuName = 'Manage Exams' AND IsDeleted = 0;

IF @MenuID IS NOT NULL
BEGIN
    -- Add to ProfileMenuMapping for all active profiles
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
    SELECT p.ProfileID, @MenuID, 1, 1, 1, 1, 0, GETDATE()
    FROM ProfileMaster p
    WHERE p.IsDeleted = 0 
    AND NOT EXISTS (
        SELECT 1 FROM ProfileMenuMapping 
        WHERE ProfileID = p.ProfileID AND MenuID = @MenuID
    );
    
    PRINT 'Exam Management menu permissions added for all profiles';
END
