-- Update Data Import Menu URLs
USE ShikshaWaveDB;
GO

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/'
WHERE MenuURL = '/import/dashboard/';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Students'
WHERE MenuURL = '/import/dashboard/?type=Students';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Teachers'
WHERE MenuURL = '/import/dashboard/?type=Teachers';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Salary'
WHERE MenuURL = '/import/dashboard/?type=Salary';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Fee'
WHERE MenuURL = '/import/dashboard/?type=Fee';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Attendance'
WHERE MenuURL = '/import/dashboard/?type=Attendance';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=Exam'
WHERE MenuURL = '/import/dashboard/?type=Exam';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=ExamResult'
WHERE MenuURL = '/import/dashboard/?type=ExamResult';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=ClassMaster'
WHERE MenuURL = '/import/dashboard/?type=ClassMaster';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=SectionMaster'
WHERE MenuURL = '/import/dashboard/?type=SectionMaster';

UPDATE MenuMaster 
SET MenuURL = '/data-import/dashboard/?type=SubjectMaster'
WHERE MenuURL = '/import/dashboard/?type=SubjectMaster';

PRINT 'Menu URLs updated successfully!';
GO
