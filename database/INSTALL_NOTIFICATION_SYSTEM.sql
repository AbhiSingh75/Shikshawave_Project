-- =============================================
-- ShikshaWave Notification System - Quick Install
-- Execute this script to install the complete notification system
-- =============================================

USE ShikshaWaveDB;
GO

PRINT '========================================';
PRINT 'Installing ShikshaWave Notification System';
PRINT '========================================';
PRINT '';

-- =============================================
-- STEP 1: Create Tables
-- =============================================
PRINT 'Step 1: Creating Tables...';

-- Notification Type Master
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationTypeMaster')
BEGIN
    CREATE TABLE NotificationTypeMaster (
        TypeID INT PRIMARY KEY IDENTITY(1,1),
        TypeName NVARCHAR(50) NOT NULL UNIQUE,
        TypeCategory NVARCHAR(50) NOT NULL,
        IconClass NVARCHAR(50) NULL,
        ColorCode NVARCHAR(20) NULL,
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
    PRINT '  ✓ NotificationTypeMaster created';
END
ELSE
    PRINT '  - NotificationTypeMaster already exists';

-- Notification Master
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationMaster')
BEGIN
    CREATE TABLE NotificationMaster (
        NotificationID BIGINT PRIMARY KEY IDENTITY(1,1),
        SchoolID INT NOT NULL,
        TypeID INT NOT NULL,
        Title NVARCHAR(255) NOT NULL,
        Message NVARCHAR(MAX) NOT NULL,
        TargetURL NVARCHAR(500) NULL,
        TargetModule NVARCHAR(50) NULL,
        TargetRecordID BIGINT NULL,
        CreatedByUserID INT NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        ExpiresAt DATETIME NULL,
        IsDeleted BIT DEFAULT 0,
        CONSTRAINT FK_Notification_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_Notification_Type FOREIGN KEY (TypeID) REFERENCES NotificationTypeMaster(TypeID),
        CONSTRAINT FK_Notification_CreatedBy FOREIGN KEY (CreatedByUserID) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_Notification_School ON NotificationMaster(SchoolID);
    CREATE INDEX IX_Notification_Type ON NotificationMaster(TypeID);
    CREATE INDEX IX_Notification_CreatedAt ON NotificationMaster(CreatedAt DESC);
    
    PRINT '  ✓ NotificationMaster created with indexes';
END
ELSE
    PRINT '  - NotificationMaster already exists';

-- Notification Recipients
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationRecipients')
BEGIN
    CREATE TABLE NotificationRecipients (
        RecipientID BIGINT PRIMARY KEY IDENTITY(1,1),
        NotificationID BIGINT NOT NULL,
        UserID INT NOT NULL,
        IsRead BIT DEFAULT 0,
        ReadAt DATETIME NULL,
        IsDeleted BIT DEFAULT 0,
        CreatedAt DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_Recipient_Notification FOREIGN KEY (NotificationID) REFERENCES NotificationMaster(NotificationID),
        CONSTRAINT FK_Recipient_User FOREIGN KEY (UserID) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_Recipient_User ON NotificationRecipients(UserID, IsRead);
    CREATE INDEX IX_Recipient_Notification ON NotificationRecipients(NotificationID);
    CREATE UNIQUE INDEX UX_Recipient_User_Notification ON NotificationRecipients(NotificationID, UserID);
    
    PRINT '  ✓ NotificationRecipients created with indexes';
END
ELSE
    PRINT '  - NotificationRecipients already exists';

PRINT '';

-- =============================================
-- STEP 2: Insert Default Notification Types
-- =============================================
PRINT 'Step 2: Inserting Default Notification Types...';

IF NOT EXISTS (SELECT * FROM NotificationTypeMaster WHERE TypeName = 'TicketCreated')
BEGIN
    INSERT INTO NotificationTypeMaster (TypeName, TypeCategory, IconClass, ColorCode) VALUES
    ('TicketCreated', 'Ticket', 'fa-ticket', '#3b82f6'),
    ('TicketUpdated', 'Ticket', 'fa-ticket', '#f59e0b'),
    ('TicketAssigned', 'Ticket', 'fa-user-check', '#8b5cf6'),
    ('TicketChatMessage', 'Ticket', 'fa-comment', '#10b981'),
    ('TicketStatusChanged', 'Ticket', 'fa-exchange-alt', '#6366f1'),
    ('FeeReminder', 'Fee', 'fa-money-bill-wave', '#ef4444'),
    ('FeePaymentConfirmed', 'Fee', 'fa-check-circle', '#10b981'),
    ('FeeDueDate', 'Fee', 'fa-calendar-exclamation', '#f59e0b'),
    ('TimetableReleased', 'Timetable', 'fa-calendar-alt', '#3b82f6'),
    ('TimetableUpdated', 'Timetable', 'fa-calendar-edit', '#f59e0b'),
    ('AttendanceSummary', 'Attendance', 'fa-clipboard-check', '#10b981'),
    ('AttendanceLow', 'Attendance', 'fa-exclamation-triangle', '#ef4444'),
    ('ExamScheduled', 'Exam', 'fa-file-alt', '#8b5cf6'),
    ('ExamResultPublished', 'Exam', 'fa-trophy', '#10b981'),
    ('GeneralAnnouncement', 'General', 'fa-bullhorn', '#6366f1'),
    ('SystemAlert', 'General', 'fa-bell', '#ef4444');
    
    PRINT '  ✓ 16 notification types inserted';
END
ELSE
    PRINT '  - Notification types already exist';

PRINT '';

-- =============================================
-- STEP 3: Create Stored Procedures
-- =============================================
PRINT 'Step 3: Creating Stored Procedures...';

-- Proc_Notification_Create
IF OBJECT_ID('Proc_Notification_Create', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_Create;
GO

CREATE PROCEDURE Proc_Notification_Create
    @SchoolID INT,
    @TypeName NVARCHAR(50),
    @Title NVARCHAR(255),
    @Message NVARCHAR(MAX),
    @TargetURL NVARCHAR(500) = NULL,
    @TargetModule NVARCHAR(50) = NULL,
    @TargetRecordID BIGINT = NULL,
    @CreatedByUserID INT,
    @RecipientUserIDs NVARCHAR(MAX),
    @ExpiresAt DATETIME = NULL
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @NotificationID BIGINT, @TypeID INT;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        SELECT @TypeID = TypeID FROM NotificationTypeMaster WHERE TypeName = @TypeName AND IsActive = 1;
        IF @TypeID IS NULL
        BEGIN
            RAISERROR('Invalid notification type', 16, 1);
            RETURN;
        END
        
        INSERT INTO NotificationMaster (SchoolID, TypeID, Title, Message, TargetURL, TargetModule, TargetRecordID, CreatedByUserID, ExpiresAt)
        VALUES (@SchoolID, @TypeID, @Title, @Message, @TargetURL, @TargetModule, @TargetRecordID, @CreatedByUserID, @ExpiresAt);
        SET @NotificationID = SCOPE_IDENTITY();
        
        INSERT INTO NotificationRecipients (NotificationID, UserID)
        SELECT @NotificationID, CAST(value AS INT)
        FROM STRING_SPLIT(@RecipientUserIDs, ',')
        WHERE ISNUMERIC(value) = 1;
        
        COMMIT TRANSACTION;
        SELECT @NotificationID AS NotificationID, 'Success' AS Status;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS NotificationID, ERROR_MESSAGE() AS Status;
    END CATCH
END
GO
PRINT '  ✓ Proc_Notification_Create created';

-- Proc_Notification_GetList
IF OBJECT_ID('Proc_Notification_GetList', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_GetList;
GO

CREATE PROCEDURE Proc_Notification_GetList
    @UserID INT,
    @SchoolID INT,
    @PageNumber INT = 1,
    @PageSize INT = 20,
    @UnreadOnly BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Offset INT = (@PageNumber - 1) * @PageSize;
    
    SELECT 
        n.NotificationID, n.Title, n.Message, n.TargetURL, n.TargetModule, n.TargetRecordID,
        nt.TypeName, nt.TypeCategory, nt.IconClass, nt.ColorCode,
        nr.IsRead, nr.ReadAt, n.CreatedAt, u.UserName AS CreatedByUserName,
        COUNT(*) OVER() AS TotalCount
    FROM NotificationRecipients nr
    INNER JOIN NotificationMaster n ON nr.NotificationID = n.NotificationID
    INNER JOIN NotificationTypeMaster nt ON n.TypeID = nt.TypeID
    LEFT JOIN UserMaster u ON n.CreatedByUserID = u.UserID
    WHERE nr.UserID = @UserID AND n.SchoolID = @SchoolID
        AND n.IsDeleted = 0 AND nr.IsDeleted = 0
        AND (n.ExpiresAt IS NULL OR n.ExpiresAt > GETDATE())
        AND (@UnreadOnly = 0 OR nr.IsRead = 0)
    ORDER BY n.CreatedAt DESC
    OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY;
END
GO
PRINT '  ✓ Proc_Notification_GetList created';

-- Proc_Notification_MarkRead
IF OBJECT_ID('Proc_Notification_MarkRead', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_MarkRead;
GO

CREATE PROCEDURE Proc_Notification_MarkRead
    @NotificationID BIGINT,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE NotificationRecipients
    SET IsRead = 1, ReadAt = GETDATE()
    WHERE NotificationID = @NotificationID AND UserID = @UserID;
    SELECT @@ROWCOUNT AS RowsAffected;
END
GO
PRINT '  ✓ Proc_Notification_MarkRead created';

-- Proc_Notification_MarkAllRead
IF OBJECT_ID('Proc_Notification_MarkAllRead', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_MarkAllRead;
GO

CREATE PROCEDURE Proc_Notification_MarkAllRead
    @UserID INT,
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE nr SET IsRead = 1, ReadAt = GETDATE()
    FROM NotificationRecipients nr
    INNER JOIN NotificationMaster n ON nr.NotificationID = n.NotificationID
    WHERE nr.UserID = @UserID AND n.SchoolID = @SchoolID
        AND nr.IsRead = 0 AND n.IsDeleted = 0 AND nr.IsDeleted = 0;
    SELECT @@ROWCOUNT AS RowsAffected;
END
GO
PRINT '  ✓ Proc_Notification_MarkAllRead created';

-- Proc_Notification_GetUnreadCount
IF OBJECT_ID('Proc_Notification_GetUnreadCount', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_GetUnreadCount;
GO

CREATE PROCEDURE Proc_Notification_GetUnreadCount
    @UserID INT,
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT COUNT(*) AS UnreadCount
    FROM NotificationRecipients nr
    INNER JOIN NotificationMaster n ON nr.NotificationID = n.NotificationID
    WHERE nr.UserID = @UserID AND n.SchoolID = @SchoolID
        AND nr.IsRead = 0 AND n.IsDeleted = 0 AND nr.IsDeleted = 0
        AND (n.ExpiresAt IS NULL OR n.ExpiresAt > GETDATE());
END
GO
PRINT '  ✓ Proc_Notification_GetUnreadCount created';

PRINT '';

-- =============================================
-- STEP 4: Verification
-- =============================================
PRINT 'Step 4: Verification...';

DECLARE @TableCount INT = 0;
DECLARE @ProcCount INT = 0;
DECLARE @TypeCount INT = 0;

SELECT @TableCount = COUNT(*) FROM sys.tables 
WHERE name IN ('NotificationTypeMaster', 'NotificationMaster', 'NotificationRecipients');

SELECT @ProcCount = COUNT(*) FROM sys.procedures 
WHERE name LIKE 'Proc_Notification_%';

SELECT @TypeCount = COUNT(*) FROM NotificationTypeMaster;

PRINT '  Tables created: ' + CAST(@TableCount AS NVARCHAR(10)) + '/3';
PRINT '  Procedures created: ' + CAST(@ProcCount AS NVARCHAR(10)) + '/5';
PRINT '  Notification types: ' + CAST(@TypeCount AS NVARCHAR(10)) + '/16';

PRINT '';
PRINT '========================================';
IF @TableCount = 3 AND @ProcCount = 5 AND @TypeCount = 16
    PRINT '✓ Installation Complete - All components installed successfully!';
ELSE
    PRINT '⚠ Installation Incomplete - Please review errors above';
PRINT '========================================';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Add "notifications" to INSTALLED_APPS in settings.py';
PRINT '2. Add path("notifications/", include("notifications.urls")) to urls.py';
PRINT '3. Verify static files (notifications.js, notifications.css) are in place';
PRINT '4. Test the system by creating a test notification';
PRINT '';
PRINT 'Documentation: docs/NOTIFICATION_SYSTEM_COMPLETE_GUIDE.md';
GO
