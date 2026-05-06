-- Fix old template names in TemplateSettings table
UPDATE TemplateSettings 
SET TemplateFile = 'admission_acknowledgment.html'
WHERE TemplateType = 'AdmissionAcknowledgment' 
  AND TemplateFile IN ('admission_acknowledgment_classic.html', 'admission_acknowledgment_minimal.html');

-- Show current settings
SELECT SchoolID, TemplateType, TemplateFile, IsActive 
FROM TemplateSettings 
WHERE TemplateType = 'AdmissionAcknowledgment';
