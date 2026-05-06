-- =============================================
-- Mark Notification as Read
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Notification_MarkRead
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

-- =============================================
-- Mark All Notifications as Read
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Notification_MarkAllRead
    @UserID INT,
    @SchoolID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE nr
    SET IsRead = 1, ReadAt = GETDATE()
    FROM NotificationRecipients nr
    INNER JOIN NotificationMaster n ON nr.NotificationID = n.NotificationID
    WHERE nr.UserID = @UserID 
        AND (@SchoolID IS NULL OR n.SchoolID = @SchoolID)
        AND nr.IsRead = 0
        AND n.IsDeleted = 0
        AND nr.IsDeleted = 0;
    
    SELECT @@ROWCOUNT AS RowsAffected;
END
GO

-- =============================================
-- Get Unread Count
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Notification_GetUnreadCount
    @UserID INT,
    @SchoolID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT COUNT(*) AS UnreadCount
    FROM NotificationRecipients nr
    INNER JOIN NotificationMaster n ON nr.NotificationID = n.NotificationID
    WHERE nr.UserID = @UserID 
        AND (@SchoolID IS NULL OR n.SchoolID = @SchoolID)
        AND nr.IsRead = 0
        AND n.IsDeleted = 0
        AND nr.IsDeleted = 0
        AND (n.ExpiresAt IS NULL OR n.ExpiresAt > GETDATE());
END
GO
