-- Add Payment Receipt Templates to TemplateSettings
-- This script adds 5 payment receipt templates for all schools

-- Insert payment receipt templates for all existing schools
INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateName, TemplateFile, IsActive, CreatedAt, IsDeleted)
SELECT 
    SchoolID, 
    'PaymentReceipt', 
    'Modern Success (Default)', 
    'payment_success.html', 
    1, 
    GETDATE(), 
    0
FROM SchoolMaster 
WHERE IsDeleted = 0
AND NOT EXISTS (
    SELECT 1 FROM TemplateSettings 
    WHERE SchoolID = SchoolMaster.SchoolID 
    AND TemplateType = 'PaymentReceipt' 
    AND IsDeleted = 0
);

-- Note: Additional templates are available for selection:
-- Template 2: 'payment_receipt_template2.html' - Professional Corporate
-- Template 3: 'payment_receipt_template3.html' - Modern Gradient
-- Template 4: 'payment_receipt_template4.html' - Classic Elegant
-- Template 5: 'payment_receipt_template5.html' - Fresh Green Receipt

-- Schools can change their preferred template using the Template Management interface
-- or by calling Proc_Template_Preference_Save stored procedure

GO

-- Verify the templates were added
SELECT 
    s.SchoolName,
    ts.TemplateType,
    ts.TemplateName,
    ts.TemplateFile,
    ts.IsActive
FROM TemplateSettings ts
INNER JOIN SchoolMaster s ON ts.SchoolID = s.SchoolID
WHERE ts.TemplateType = 'PaymentReceipt'
AND ts.IsDeleted = 0
ORDER BY s.SchoolName;

GO
