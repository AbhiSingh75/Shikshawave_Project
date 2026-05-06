-- =============================================
-- FINAL FIX: Notification System for NULL SchoolID
-- =============================================

USE ShikshaWaveDB;
GO

PRINT '========================================='
PRINT 'STEP 1: Alter NotificationMaster Table'
PRINT '========================================='

IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Notification_School')
BEGIN
    ALTER TABLE NotificationMaster DROP CONSTRAINT FK_Notification_School;
    PRINT '✓ Dropped FK_Notification_School'
END

ALTER TABLE NotificationMaster ALTER COLUMN SchoolID INT NULL;
PRINT '✓ SchoolID is now nullable'

ALTER TABLE NotificationMaster ADD CONSTRAINT FK_Notification_School 
FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID);
PRINT '✓ Re-created FK_Notification_School'
GO

PRINT ''
PRINT '========================================='
PRINT 'STEP 2: Update Stored Procedures'
PRINT '========================================='

-- Proc_Notification_Create
CREATE OR ALTER PROCEDURE Proc_Notification_Create
    @SchoolID INT = NULL,
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
    DECLARE @NotificationID BIGINT;
    DECLARE @TypeID INT;
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
PRINT '✓ Proc_Notification_Create updated'

-- Proc_Notification_GetList
CREATE OR ALTER PROCEDURE Proc_Notification_GetList
    @UserID INT,
    @SchoolID INT = NULL,
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
    WHERE nr.UserID = @UserID
        AND (@SchoolID IS NULL OR n.SchoolID = @SchoolID OR n.SchoolID IS NULL)
        AND n.IsDeleted = 0
        AND nr.IsDeleted = 0
        AND (n.ExpiresAt IS NULL OR n.ExpiresAt > GETDATE())
        AND (@UnreadOnly = 0 OR nr.IsRead = 0)
    ORDER BY n.CreatedAt DESC
    OFFSET @Offset ROWS
    FETCH NEXT @PageSize ROWS ONLY;
END
GO
PRINT '✓ Proc_Notification_GetList updated'

-- Proc_Notification_GetUnreadCount
CREATE OR ALTER PROCEDURE Proc_Notification_GetUnreadCount
    @UserID INT,
    @SchoolID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SELECT COUNT(*) AS UnreadCount
        FROM NotificationRecipients nr
        INNER JOIN NotificationMaster nm ON nr.NotificationID = nm.NotificationID
        WHERE nr.UserID = @UserID
            AND nr.IsRead = 0
            AND nr.IsDeleted = 0
            AND nm.IsDeleted = 0
            AND (@SchoolID IS NULL OR nm.SchoolID = @SchoolID OR nm.SchoolID IS NULL)
            AND (nm.ExpiresAt IS NULL OR nm.ExpiresAt > GETDATE());
    END TRY
    BEGIN CATCH
        SELECT 0 AS UnreadCount;
    END CATCH
END
GO
PRINT '✓ Proc_Notification_GetUnreadCount updated'

-- Proc_Notification_MarkAllRead
CREATE OR ALTER PROCEDURE Proc_Notification_MarkAllRead
    @UserID INT,
    @SchoolID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        UPDATE nr
        SET IsRead = 1, ReadAt = GETDATE()
        FROM NotificationRecipients nr
        INNER JOIN NotificationMaster nm ON nr.NotificationID = nm.NotificationID
        WHERE nr.UserID = @UserID
            AND nr.IsRead = 0
            AND nr.IsDeleted = 0
            AND nm.IsDeleted = 0
            AND (@SchoolID IS NULL OR nm.SchoolID = @SchoolID OR nm.SchoolID IS NULL);
        COMMIT TRANSACTION;
        SELECT @@ROWCOUNT AS UpdatedCount;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS UpdatedCount;
    END CATCH
END
GO
PRINT '✓ Proc_Notification_MarkAllRead updated'

PRINT ''
PRINT '========================================='
PRINT '✓ ALL FIXES APPLIED SUCCESSFULLY!'
PRINT '========================================='
PRINT 'Notifications with NULL SchoolID will now work for all users'
GO
