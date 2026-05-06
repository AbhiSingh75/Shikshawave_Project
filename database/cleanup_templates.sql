-- Delete all old template settings
DELETE FROM TemplateSettings WHERE TemplateType = 'AdmissionAcknowledgment';

-- Verify deletion
SELECT * FROM TemplateSettings WHERE TemplateType = 'AdmissionAcknowledgment';
