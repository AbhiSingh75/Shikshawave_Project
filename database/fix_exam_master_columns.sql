-- Add missing columns to ExamMaster table
-- Run this SQL script in your SQL Server database

-- Check if CreatedAt column exists, if not add it
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'ExamMaster') AND name = 'CreatedAt')
BEGIN
    ALTER TABLE ExamMaster ADD CreatedAt DATETIME DEFAULT GETDATE();
    PRINT 'CreatedAt column added successfully';
END
ELSE
BEGIN
    PRINT 'CreatedAt column already exists';
END

-- Check if IsDeleted column exists, if not add it
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'ExamMaster') AND name = 'IsDeleted')
BEGIN
    ALTER TABLE ExamMaster ADD IsDeleted BIT DEFAULT 0;
    PRINT 'IsDeleted column added successfully';
END
ELSE
BEGIN
    PRINT 'IsDeleted column already exists';
END

-- Update existing records to have default values
UPDATE ExamMaster SET CreatedAt = ISNULL(CreatedOn, GETDATE()) WHERE CreatedAt IS NULL;
UPDATE ExamMaster SET IsDeleted = 0 WHERE IsDeleted IS NULL;

PRINT 'ExamMaster table updated successfully';
