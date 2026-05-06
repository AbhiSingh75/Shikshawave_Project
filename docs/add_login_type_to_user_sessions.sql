-- Add LoginType column to user_sessions table for tracking login methods
-- This script safely adds the column if it doesn't exist

-- Check if LoginType column exists, if not add it
IF NOT EXISTS (
    SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'user_sessions' 
    AND COLUMN_NAME = 'LoginType'
)
BEGIN
    ALTER TABLE user_sessions 
    ADD LoginType VARCHAR(50) DEFAULT 'By UserId and Password';
    
    PRINT 'LoginType column added to user_sessions table';
END
ELSE
BEGIN
    PRINT 'LoginType column already exists in user_sessions table';
    
    -- Update column size if it's too small
    ALTER TABLE user_sessions 
    ALTER COLUMN LoginType VARCHAR(50);
    
    PRINT 'LoginType column size updated to VARCHAR(50)';
END

-- Update existing records to have 'By UserId and Password' as default login type
UPDATE user_sessions 
SET LoginType = 'By UserId and Password' 
WHERE LoginType IS NULL OR LoginType = 'Password';

PRINT 'Updated existing records with default LoginType = By UserId and Password';

-- Verify the column was added
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    COLUMN_DEFAULT,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'user_sessions' 
AND COLUMN_NAME = 'LoginType';

PRINT 'LoginType column details displayed above';

-- Show sample of recent sessions with login types
SELECT TOP 10
    user_id,
    profile_name,
    LoginType,
    created_at,
    ip_address
FROM user_sessions 
ORDER BY created_at DESC;

PRINT 'Sample of recent sessions with LoginType displayed above';

-- Summary
PRINT '=== LOGIN TYPE TRACKING SETUP COMPLETE ===';
PRINT 'LoginType column added to user_sessions table';
PRINT 'Possible values: By UserId and Password, By OTP, By FaceId';
PRINT 'Default value: By UserId and Password';
PRINT 'All future logins will be tracked with their descriptive login method';