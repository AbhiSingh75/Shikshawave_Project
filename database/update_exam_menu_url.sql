-- Update the existing Manage Exams menu to point to the correct URL
UPDATE MenuMaster 
SET MenuURL = '/exam/management/'
WHERE MenuName = 'Manage Exams' OR MenuName LIKE '%Exam%Management%';

-- Verify the update
SELECT MenuID, MenuName, MenuURL, ParentMenuID 
FROM MenuMaster 
WHERE MenuName LIKE '%Exam%';
