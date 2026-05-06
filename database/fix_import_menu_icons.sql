-- Fix Data Import Menu Icons
-- Run this to update existing menu icons with proper Font Awesome classes

USE ShikshaWaveDB;
GO

UPDATE MenuMaster SET Icon = 'fas fa-upload' WHERE MenuName = 'Data Import';
UPDATE MenuMaster SET Icon = 'fas fa-tachometer-alt' WHERE MenuName = 'Import Dashboard';
UPDATE MenuMaster SET Icon = 'fas fa-user-graduate' WHERE MenuName = 'Import Students';
UPDATE MenuMaster SET Icon = 'fas fa-chalkboard-teacher' WHERE MenuName = 'Import Teachers';
UPDATE MenuMaster SET Icon = 'fas fa-money-bill-wave' WHERE MenuName = 'Import Salary';
UPDATE MenuMaster SET Icon = 'fas fa-receipt' WHERE MenuName = 'Import Fee History';
UPDATE MenuMaster SET Icon = 'fas fa-calendar-check' WHERE MenuName = 'Import Attendance';
UPDATE MenuMaster SET Icon = 'fas fa-file-alt' WHERE MenuName = 'Import Exams';
UPDATE MenuMaster SET Icon = 'fas fa-chart-line' WHERE MenuName = 'Import Exam Results';
UPDATE MenuMaster SET Icon = 'fas fa-school' WHERE MenuName = 'Import Classes';
UPDATE MenuMaster SET Icon = 'fas fa-layer-group' WHERE MenuName = 'Import Sections';
UPDATE MenuMaster SET Icon = 'fas fa-book' WHERE MenuName = 'Import Subjects';

PRINT 'Icons updated successfully! Refresh your browser (Ctrl+F5) to see changes.';
GO
