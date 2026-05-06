-- Fix the exam menu URL to match the Django URL pattern
UPDATE MenuMaster 
SET MenuURL = '/exam/management/'
WHERE MenuURL = '/exams/manage/' OR MenuName LIKE '%Manage%Exam%';

-- Verify
SELECT MenuID, MenuName, MenuURL FROM MenuMaster WHERE MenuName LIKE '%Exam%';
