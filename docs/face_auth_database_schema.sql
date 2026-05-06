-- Face Authentication Database Schema for ShikshaWave
-- This file contains the SQL Server schema for face authentication features

-- Face Authentication Logs Table
-- Tracks all face authentication attempts for security auditing
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceAuthLogs' AND xtype='U')
BEGIN
    CREATE TABLE FaceAuthLogs (
        LogID BIGINT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        TemplateID INT NULL,
        Similarity DECIMAL(5,2) NOT NULL, -- Similarity percentage (0.00-100.00)
        Success BIT NOT NULL DEFAULT 0,
        IPAddress NVARCHAR(45) NULL, -- Supports IPv6
        DeviceInfo NVARCHAR(500) NULL,
        AttemptTime DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_FaceAuthLogs_UserID FOREIGN KEY (UserID) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_FaceAuthLogs_TemplateID FOREIGN KEY (TemplateID) REFERENCES FaceTemplates(FaceTemplateID)
    );
    
    -- Indexes for performance
    CREATE INDEX IX_FaceAuthLogs_UserID_AttemptTime ON FaceAuthLogs(UserID, AttemptTime DESC);
    CREATE INDEX IX_FaceAuthLogs_Success_AttemptTime ON FaceAuthLogs(Success, AttemptTime DESC);
    CREATE INDEX IX_FaceAuthLogs_IPAddress ON FaceAuthLogs(IPAddress);
    
    PRINT 'FaceAuthLogs table created successfully';
END
ELSE
BEGIN
    PRINT 'FaceAuthLogs table already exists';
END
GO

-- Face Authentication Settings Table
-- Stores system-wide face authentication configuration
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceAuthSettings' AND xtype='U')
BEGIN
    CREATE TABLE FaceAuthSettings (
        SettingID INT IDENTITY(1,1) PRIMARY KEY,
        SettingKey NVARCHAR(100) NOT NULL UNIQUE,
        SettingValue NVARCHAR(500) NOT NULL,
        Description NVARCHAR(1000) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETDATE(),
        CreatedBy INT NULL,
        UpdatedBy INT NULL,
        
        CONSTRAINT FK_FaceAuthSettings_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_FaceAuthSettings_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID)
    );
    
    -- Insert default settings
    INSERT INTO FaceAuthSettings (SettingKey, SettingValue, Description) VALUES
    ('SIMILARITY_THRESHOLD', '85.0', 'Minimum similarity percentage required for face authentication'),
    ('MAX_TEMPLATES_PER_USER', '3', 'Maximum number of face templates allowed per user'),
    ('LIVENESS_DETECTION_ENABLED', 'true', 'Enable liveness detection for anti-spoofing'),
    ('MAX_AUTH_ATTEMPTS_PER_HOUR', '10', 'Maximum face authentication attempts per hour per user'),
    ('TEMPLATE_ENCRYPTION_ENABLED', 'true', 'Enable encryption for stored face templates'),
    ('AUDIT_LOG_RETENTION_DAYS', '90', 'Number of days to retain face authentication logs');
    
    PRINT 'FaceAuthSettings table created with default settings';
END
ELSE
BEGIN
    PRINT 'FaceAuthSettings table already exists';
END
GO

-- Face Authentication Rate Limiting Table
-- Tracks authentication attempts for rate limiting
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FaceAuthRateLimit' AND xtype='U')
BEGIN
    CREATE TABLE FaceAuthRateLimit (
        RateLimitID BIGINT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NULL,
        IPAddress NVARCHAR(45) NOT NULL,
        AttemptCount INT NOT NULL DEFAULT 1,
        WindowStart DATETIME2 NOT NULL DEFAULT GETDATE(),
        WindowEnd DATETIME2 NOT NULL,
        IsBlocked BIT NOT NULL DEFAULT 0,
        
        CONSTRAINT FK_FaceAuthRateLimit_UserID FOREIGN KEY (UserID) REFERENCES UserMaster(UserID)
    );
    
    -- Indexes for performance
    CREATE INDEX IX_FaceAuthRateLimit_UserID_WindowEnd ON FaceAuthRateLimit(UserID, WindowEnd DESC);
    CREATE INDEX IX_FaceAuthRateLimit_IPAddress_WindowEnd ON FaceAuthRateLimit(IPAddress, WindowEnd DESC);
    CREATE INDEX IX_FaceAuthRateLimit_IsBlocked ON FaceAuthRateLimit(IsBlocked);
    
    PRINT 'FaceAuthRateLimit table created successfully';
END
ELSE
BEGIN
    PRINT 'FaceAuthRateLimit table already exists';
END
GO

-- Update existing FaceTemplates table if needed
-- Add audit fields if they don't exist
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaceTemplates' AND COLUMN_NAME = 'LastUsedAt')
BEGIN
    ALTER TABLE FaceTemplates ADD LastUsedAt DATETIME2 NULL;
    PRINT 'Added LastUsedAt column to FaceTemplates table';
END

IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FaceTemplates' AND COLUMN_NAME = 'UsageCount')
BEGIN
    ALTER TABLE FaceTemplates ADD UsageCount INT NOT NULL DEFAULT 0;
    PRINT 'Added UsageCount column to FaceTemplates table';
END

-- Stored Procedures for Face Authentication

-- Procedure to log face authentication attempts
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_LogFaceAuthAttempt')
    DROP PROCEDURE sp_LogFaceAuthAttempt;
GO

CREATE PROCEDURE sp_LogFaceAuthAttempt
    @UserID INT,
    @TemplateID INT = NULL,
    @Similarity DECIMAL(5,2),
    @Success BIT,
    @IPAddress NVARCHAR(45) = NULL,
    @DeviceInfo NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Insert log entry
        INSERT INTO FaceAuthLogs (UserID, TemplateID, Similarity, Success, IPAddress, DeviceInfo)
        VALUES (@UserID, @TemplateID, @Similarity, @Success, @IPAddress, @DeviceInfo);
        
        -- Update template usage if successful
        IF @Success = 1 AND @TemplateID IS NOT NULL
        BEGIN
            UPDATE FaceTemplates 
            SET LastUsedAt = GETDATE(), 
                UsageCount = UsageCount + 1,
                UpdatedAt = GETDATE()
            WHERE FaceTemplateID = @TemplateID;
        END
        
        SELECT 1 as Success, 'Authentication attempt logged successfully' as Message;
    END TRY
    BEGIN CATCH
        SELECT 0 as Success, ERROR_MESSAGE() as Message;
    END CATCH
END
GO

-- Procedure to check rate limiting
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_CheckFaceAuthRateLimit')
    DROP PROCEDURE sp_CheckFaceAuthRateLimit;
GO

CREATE PROCEDURE sp_CheckFaceAuthRateLimit
    @UserID INT = NULL,
    @IPAddress NVARCHAR(45),
    @MaxAttemptsPerHour INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @WindowStart DATETIME2 = DATEADD(HOUR, -1, GETDATE());
    DECLARE @CurrentAttempts INT = 0;
    DECLARE @IsBlocked BIT = 0;
    
    BEGIN TRY
        -- Check current attempts in the last hour
        SELECT @CurrentAttempts = COUNT(*)
        FROM FaceAuthLogs
        WHERE (@UserID IS NULL OR UserID = @UserID)
          AND IPAddress = @IPAddress
          AND AttemptTime >= @WindowStart;
        
        -- Check if blocked
        IF @CurrentAttempts >= @MaxAttemptsPerHour
        BEGIN
            SET @IsBlocked = 1;
            
            -- Update or insert rate limit record
            MERGE FaceAuthRateLimit AS target
            USING (SELECT @UserID as UserID, @IPAddress as IPAddress) AS source
            ON target.UserID = source.UserID AND target.IPAddress = source.IPAddress
            WHEN MATCHED THEN
                UPDATE SET AttemptCount = @CurrentAttempts, 
                          WindowStart = @WindowStart,
                          WindowEnd = GETDATE(),
                          IsBlocked = @IsBlocked
            WHEN NOT MATCHED THEN
                INSERT (UserID, IPAddress, AttemptCount, WindowStart, WindowEnd, IsBlocked)
                VALUES (@UserID, @IPAddress, @CurrentAttempts, @WindowStart, GETDATE(), @IsBlocked);
        END
        
        SELECT 
            @IsBlocked as IsBlocked,
            @CurrentAttempts as CurrentAttempts,
            @MaxAttemptsPerHour as MaxAttempts,
            CASE WHEN @IsBlocked = 1 
                 THEN DATEDIFF(MINUTE, GETDATE(), DATEADD(HOUR, 1, @WindowStart))
                 ELSE 0 
            END as MinutesUntilReset;
            
    END TRY
    BEGIN CATCH
        SELECT 0 as IsBlocked, 0 as CurrentAttempts, @MaxAttemptsPerHour as MaxAttempts, 0 as MinutesUntilReset;
    END CATCH
END
GO

-- Procedure to cleanup old logs
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'sp_CleanupFaceAuthLogs')
    DROP PROCEDURE sp_CleanupFaceAuthLogs;
GO

CREATE PROCEDURE sp_CleanupFaceAuthLogs
    @RetentionDays INT = 90
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @CutoffDate DATETIME2 = DATEADD(DAY, -@RetentionDays, GETDATE());
    DECLARE @DeletedCount INT;
    
    BEGIN TRY
        -- Delete old authentication logs
        DELETE FROM FaceAuthLogs WHERE AttemptTime < @CutoffDate;
        SET @DeletedCount = @@ROWCOUNT;
        
        -- Delete old rate limit records
        DELETE FROM FaceAuthRateLimit WHERE WindowEnd < @CutoffDate;
        
        SELECT 1 as Success, 
               CONCAT('Cleanup completed. Deleted ', @DeletedCount, ' log entries older than ', @RetentionDays, ' days.') as Message;
    END TRY
    BEGIN CATCH
        SELECT 0 as Success, ERROR_MESSAGE() as Message;
    END CATCH
END
GO

PRINT 'Face Authentication database schema setup completed successfully';