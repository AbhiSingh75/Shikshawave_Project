-- Add EmploymentType column to EmployeeMaster table
-- This script checks if the column exists before adding it

-- Check if column exists
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'EmployeeMaster' 
    AND COLUMN_NAME = 'EmploymentType'
)
BEGIN
    -- Add the column
    ALTER TABLE EmployeeMaster
    ADD EmploymentType NVARCHAR(50) NULL;
    
    PRINT 'EmploymentType column added successfully to EmployeeMaster table';
END
ELSE
BEGIN
    PRINT 'EmploymentType column already exists in EmployeeMaster table';
END
GO

-- Optional: Add a check constraint to ensure only valid values
IF NOT EXISTS (
    SELECT 1 
    FROM sys.check_constraints 
    WHERE name = 'CK_EmployeeMaster_EmploymentType'
)
BEGIN
    ALTER TABLE EmployeeMaster
    ADD CONSTRAINT CK_EmployeeMaster_EmploymentType 
    CHECK (EmploymentType IN ('Permanent', 'Contract', 'Guest') OR EmploymentType IS NULL);
    
    PRINT 'Check constraint added for EmploymentType column';
END
ELSE
BEGIN
    PRINT 'Check constraint already exists for EmploymentType column';
END
GO
