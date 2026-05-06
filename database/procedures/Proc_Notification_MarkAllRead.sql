-- =============================================
-- Mark All Notifications as Read for User
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Notification_MarkAllRead
    @UserID INT,
    @SchoolID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        UPDATE nr
        SET IsRead = 1,
            ReadAt = GETDATE()
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
