-- Add LogoutTime column to user_sessions table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'user_sessions') AND name = 'LogoutTime')
BEGIN
    ALTER TABLE user_sessions ADD LogoutTime DATETIME NULL;
    PRINT 'LogoutTime column added to user_sessions table';
END
ELSE
BEGIN
    PRINT 'LogoutTime column already exists in user_sessions table';
END
GO
