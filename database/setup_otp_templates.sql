-- Setup OTP Template Management (No EmailTemplate table needed)
-- Uses TemplateSettings table like salary/timetable approach

-- Add OTP Template Management menu
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuURL = '/otp-template-management/')
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('OTP Templates', '/otp-template-management/', 'fas fa-envelope-open-text', 
            (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Master Data' AND IsDeleted = 0), 
            90, 1, GETDATE(), 0);
    
    DECLARE @MenuID INT = SCOPE_IDENTITY();
    
    -- Grant to Super Admin
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @MenuID, 1, 1, 1, 1, GETDATE(), 0);
    
    -- Grant to School Admin
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @MenuID, 1, 1, 1, 0, GETDATE(), 0);
    
    PRINT 'OTP Templates menu added';
END

-- Set default template for all schools
INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateFile, IsActive, CreatedBy, CreatedAt, IsDeleted)
SELECT SchoolID, 'OTP_EMAIL', 'modern_gradient', 1, 1, GETDATE(), 0
FROM SchoolMaster
WHERE IsDeleted = 0
AND NOT EXISTS (SELECT 1 FROM TemplateSettings WHERE SchoolID = SchoolMaster.SchoolID AND TemplateType = 'OTP_EMAIL');

PRINT 'OTP template setup complete';
PRINT 'Available templates: modern_gradient, minimal_clean, professional_blue';
GO
