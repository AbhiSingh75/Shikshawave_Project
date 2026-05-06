-- =============================================
-- Create Notification and Send to Recipients
-- =============================================
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
