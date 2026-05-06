-- Add SessionTimeoutMinutes column to UserMaster table
-- Default is 60 minutes (1 hour), NULL means no auto-logout

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('UserMaster') AND name = 'SessionTimeoutMinutes')
BEGIN
    ALTER TABLE UserMaster ADD SessionTimeoutMinutes INT NULL;
    PRINT 'SessionTimeoutMinutes column added successfully';
    
    -- Set default 60 minutes for all existing users
    UPDATE UserMaster SET SessionTimeoutMinutes = 60 WHERE SessionTimeoutMinutes IS NULL;
    PRINT 'Default timeout of 60 minutes set for existing users';
END
ELSE
BEGIN
    PRINT 'SessionTimeoutMinutes column already exists';
    
    -- Set default 60 minutes for users who don't have a value
    UPDATE UserMaster SET SessionTimeoutMinutes = 60 WHERE SessionTimeoutMinutes IS NULL;
    PRINT 'Default timeout of 60 minutes set for users without a value';
END
GO
