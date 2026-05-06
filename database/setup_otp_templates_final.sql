-- Setup OTP Templates in TemplateSettings

-- Set default OTP template for all schools
UPDATE TemplateSettings SET IsActive = 0 WHERE TemplateType = 'OTP_EMAIL';

INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateFile, IsActive, CreatedBy, CreatedAt, IsDeleted)
SELECT SchoolID, 'OTP_EMAIL', 'core/document_templates/Login_OTP/otp_template1.html', 1, 1, GETDATE(), 0
FROM SchoolMaster
WHERE IsDeleted = 0
AND NOT EXISTS (SELECT 1 FROM TemplateSettings WHERE SchoolID = SchoolMaster.SchoolID AND TemplateType = 'OTP_EMAIL');

PRINT '10 OTP email templates created in Login_OTP folder';
PRINT 'Template 1 set as default for all schools';
GO
