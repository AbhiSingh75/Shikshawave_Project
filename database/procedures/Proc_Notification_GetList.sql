-- =============================================
-- Get Notifications for User
-- =============================================
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
        n.NotificationID,
        n.Title,
        n.Message,
        n.TargetURL,
        n.TargetModule,
        n.TargetRecordID,
        nt.TypeName,
        nt.TypeCategory,
        nt.IconClass,
        nt.ColorCode,
        nr.IsRead,
        nr.ReadAt,
        n.CreatedAt,
        u.UserName AS CreatedByUserName,
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
