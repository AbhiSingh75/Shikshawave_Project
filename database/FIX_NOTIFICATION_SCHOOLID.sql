-- =============================================
-- Fix Notification System to Support NULL SchoolID
-- Super Admin and Support Executive don't require SchoolID
-- =============================================

USE ShikshaWaveDB;
GO

-- Step 1: Make SchoolID column nullable in NotificationMaster table
PRINT 'Step 1: Altering NotificationMaster table...';
GO

-- Drop foreign key constraint
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Notification_School')
BEGIN
    ALTER TABLE NotificationMaster DROP CONSTRAINT FK_Notification_School;
    PRINT '  - Dropped FK_Notification_School constraint';
END
GO

-- Alter column to allow NULL
ALTER TABLE NotificationMaster
ALTER COLUMN SchoolID INT NULL;
PRINT '  - SchoolID column altered to allow NULL';
GO

-- Re-create foreign key constraint (allowing NULL)
ALTER TABLE NotificationMaster
ADD CONSTRAINT FK_Notification_School 
FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID);
PRINT '  - Re-created FK_Notification_School constraint';
GO

-- Step 2: Update stored procedure to accept NULL SchoolID
PRINT 'Step 2: Updating Proc_Notification_Create...';
GO

-- Make SchoolID nullable in Proc_Notification_Create
CREATE OR ALTER PROCEDURE Proc_Notification_Create
    @SchoolID INT = NULL,
    @TypeName NVARCHAR(50),
    @Title NVARCHAR(255),
    @Message NVARCHAR(MAX),
    @TargetURL NVARCHAR(500) = NULL,
    @TargetModule NVARCHAR(50) = NULL,
    @TargetRecordID BIGINT = NULL,
    @CreatedByUserID INT,
    @RecipientUserIDs NVARCHAR(MAX), -- Comma-separated UserIDs
    @ExpiresAt DATETIME = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @NotificationID BIGINT;
    DECLARE @TypeID INT;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Get TypeID
        SELECT @TypeID = TypeID FROM NotificationTypeMaster WHERE TypeName = @TypeName AND IsActive = 1;
        
        IF @TypeID IS NULL
        BEGIN
            RAISERROR('Invalid notification type', 16, 1);
            RETURN;
        END
        
        -- Insert Notification
        INSERT INTO NotificationMaster (SchoolID, TypeID, Title, Message, TargetURL, TargetModule, TargetRecordID, CreatedByUserID, ExpiresAt)
        VALUES (@SchoolID, @TypeID, @Title, @Message, @TargetURL, @TargetModule, @TargetRecordID, @CreatedByUserID, @ExpiresAt);
        
        SET @NotificationID = SCOPE_IDENTITY();
        
        -- Insert Recipients
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

PRINT '  - Proc_Notification_Create updated';
GO

PRINT '';
PRINT '=========================================';
PRINT 'Notification system updated successfully!';
PRINT 'Super Admin and Support Executive notifications no longer require SchoolID.';
PRINT '=========================================';
GO
