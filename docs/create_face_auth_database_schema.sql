-- Face Authentication Database Schema for ShikshaWave
-- Run this script to create the required tables and stored procedures

-- 1. Create FaceTemplates table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceTemplates' AND xtype='U')
BEGIN
    CREATE TABLE FaceTemplates (
        FaceTemplateID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        FaceDescriptor NVARCHAR(MAX) NOT NULL, -- Encrypted face descriptor
        TemplateVersion VARCHAR(10) DEFAULT '2.0',
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        CreatedBy INT NULL,
        UpdatedBy INT NULL,
        
        CONSTRAINT FK_FaceTemplates_UserID FOREIGN KEY (UserID) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_FaceTemplates_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_FaceTemplates_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_FaceTemplates_UserID ON FaceTemplates(UserID);
    CREATE INDEX IX_FaceTemplates_IsActive ON FaceTemplates(IsActive);
    
    PRINT 'FaceTemplates table created successfully';
END
ELSE
BEGIN
    PRINT 'FaceTemplates table already exists';
END

-- 2. Create FaceAuthSettings table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceAuthSettings' AND xtype='U')
BEGIN
    CREATE TABLE FaceAuthSettings (
        SettingID INT IDENTITY(1,1) PRIMARY KEY,
        SettingKey VARCHAR(100) NOT NULL UNIQUE,
        SettingValue VARCHAR(500) NOT NULL,
        Description VARCHAR(1000) NULL,
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE()
    );
    
    -- Insert default settings
    INSERT INTO FaceAuthSettings (SettingKey, SettingValue, Description) VALUES
    ('SIMILARITY_THRESHOLD', '85.0', 'Minimum similarity percentage required for face authentication (0-100)'),
    ('LIVENESS_DETECTION_ENABLED', 'false', 'Enable or disable liveness detection during face authentication'),
    ('MAX_TEMPLATES_PER_USER', '3', 'Maximum number of face templates allowed per user'),
    ('MAX_AUTH_ATTEMPTS_PER_HOUR', '10', 'Maximum face authentication attempts per hour per user/IP'),
    ('TEMPLATE_ENCRYPTION_ENABLED', 'true', 'Enable encryption of face descriptors in database');
    
    PRINT 'FaceAuthSettings table created with default settings';
END
ELSE
BEGIN
    PRINT 'FaceAuthSettings table already exists';
END

-- 3. Create FaceAuthLogs table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceAuthLogs' AND xtype='U')
BEGIN
    CREATE TABLE FaceAuthLogs (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NULL,
        FaceTemplateID INT NULL,
        Similarity DECIMAL(5,2) NULL,
        IsSuccessful BIT NOT NULL,
        AttemptTime DATETIME DEFAULT GETDATE(),
        IPAddress VARCHAR(45) NULL,
        UserAgent VARCHAR(2000) NULL,
        ErrorMessage VARCHAR(1000) NULL,
        
        CONSTRAINT FK_FaceAuthLogs_UserID FOREIGN KEY (UserID) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_FaceAuthLogs_FaceTemplateID FOREIGN KEY (FaceTemplateID) REFERENCES FaceTemplates(FaceTemplateID)
    );
    
    CREATE INDEX IX_FaceAuthLogs_UserID ON FaceAuthLogs(UserID);
    CREATE INDEX IX_FaceAuthLogs_AttemptTime ON FaceAuthLogs(AttemptTime);
    CREATE INDEX IX_FaceAuthLogs_IsSuccessful ON FaceAuthLogs(IsSuccessful);
    
    PRINT 'FaceAuthLogs table created successfully';
END
ELSE
BEGIN
    PRINT 'FaceAuthLogs table already exists';
END

-- 4. Create stored procedure for rate limiting
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_CheckFaceAuthRateLimit' AND type='P')
BEGIN
    DROP PROCEDURE sp_CheckFaceAuthRateLimit;
END

CREATE PROCEDURE sp_CheckFaceAuthRateLimit
    @UserID INT = NULL,
    @IPAddress VARCHAR(45) = NULL,
    @MaxAttempts INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @CurrentAttempts INT = 0;
    DECLARE @IsBlocked BIT = 0;
    DECLARE @MinutesUntilReset INT = 0;
    
    -- Count attempts in the last hour
    SELECT @CurrentAttempts = COUNT(*)
    FROM FaceAuthLogs
    WHERE (@UserID IS NULL OR UserID = @UserID)
      AND (@IPAddress IS NULL OR IPAddress = @IPAddress)
      AND AttemptTime >= DATEADD(HOUR, -1, GETDATE());
    
    -- Check if blocked
    IF @CurrentAttempts >= @MaxAttempts
    BEGIN
        SET @IsBlocked = 1;
        
        -- Calculate minutes until reset
        SELECT @MinutesUntilReset = DATEDIFF(MINUTE, GETDATE(), DATEADD(HOUR, 1, MIN(AttemptTime)))
        FROM FaceAuthLogs
        WHERE (@UserID IS NULL OR UserID = @UserID)
          AND (@IPAddress IS NULL OR IPAddress = @IPAddress)
          AND AttemptTime >= DATEADD(HOUR, -1, GETDATE());
          
        SET @MinutesUntilReset = ISNULL(@MinutesUntilReset, 0);
    END
    
    -- Return results
    SELECT 
        @IsBlocked as IsBlocked,
        @CurrentAttempts as CurrentAttempts,
        @MaxAttempts as MaxAttempts,
        @MinutesUntilReset as MinutesUntilReset;
END

PRINT 'sp_CheckFaceAuthRateLimit stored procedure created successfully';

-- 5. Create stored procedure for logging face auth attempts
IF EXISTS (SELECT * FROM sysobjects WHERE name='sp_LogFaceAuthAttempt' AND type='P')
BEGIN
    DROP PROCEDURE sp_LogFaceAuthAttempt;
END

CREATE PROCEDURE sp_LogFaceAuthAttempt
    @UserID INT = NULL,
    @FaceTemplateID INT = NULL,
    @Similarity DECIMAL(5,2) = NULL,
    @IsSuccessful BIT,
    @IPAddress VARCHAR(45) = NULL,
    @UserAgent VARCHAR(2000) = NULL,
    @ErrorMessage VARCHAR(1000) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO FaceAuthLogs (
        UserID, 
        FaceTemplateID, 
        Similarity, 
        IsSuccessful, 
        IPAddress, 
        UserAgent, 
        ErrorMessage
    )
    VALUES (
        @UserID, 
        @FaceTemplateID, 
        @Similarity, 
        @IsSuccessful, 
        @IPAddress, 
        @UserAgent, 
        @ErrorMessage
    );
    
    SELECT SCOPE_IDENTITY() as LogID;
END

PRINT 'sp_LogFaceAuthAttempt stored procedure created successfully';

-- 6. Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE ON FaceTemplates TO [YourAppUser];
-- GRANT SELECT, INSERT ON FaceAuthLogs TO [YourAppUser];
-- GRANT SELECT ON FaceAuthSettings TO [YourAppUser];
-- GRANT EXECUTE ON sp_CheckFaceAuthRateLimit TO [YourAppUser];
-- GRANT EXECUTE ON sp_LogFaceAuthAttempt TO [YourAppUser];

PRINT '=== Face Authentication Database Schema Setup Complete ===';
PRINT 'Tables created: FaceTemplates, FaceAuthSettings, FaceAuthLogs';
PRINT 'Stored procedures created: sp_CheckFaceAuthRateLimit, sp_LogFaceAuthAttempt';
PRINT 'Default settings inserted into FaceAuthSettings';
PRINT '';
PRINT 'Next steps:';
PRINT '1. Verify all tables were created successfully';
PRINT '2. Test face authentication - it should now work';
PRINT '3. Check FaceAuthSettings table for configuration options';
PRINT '4. Monitor FaceAuthLogs table for authentication attempts';