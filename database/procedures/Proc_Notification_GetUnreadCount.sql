-- =============================================
-- Get Unread Notification Count for User
-- =============================================
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
