CREATE OR ALTER PROCEDURE Proc_Ticket_GetDetails
    @UserID INT,
    @RoleName NVARCHAR(50),
    @TicketID BIGINT,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get ticket details
    DECLARE @SchoolID INT, @AssignedTo INT;
    SELECT @SchoolID = SchoolID, @AssignedTo = AssignedToUserID
    FROM TicketMaster
    WHERE TicketID = @TicketID AND ISNULL(IsDeleted, 0) = 0;
    
    IF @SchoolID IS NULL
    BEGIN
        SET @ErrorMessage = 'Ticket not found';
        RETURN 404;
    END
    
    -- Validate access based on role
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    IF @RoleName = 'School Admin' AND @UserSchoolID != @SchoolID
    BEGIN
        SET @ErrorMessage = 'Access denied: ticket belongs to different school';
        RETURN 403;
    END
    ELSE IF @RoleName = 'Support Executive' AND @AssignedTo != @UserID
    BEGIN
        SET @ErrorMessage = 'Access denied: ticket not assigned to you';
        RETURN 403;
    END
    
    -- Return ticket details
    SELECT 
        t.TicketID,
        t.TicketNumber,
        t.SchoolID,
        s.SchoolName,
        t.CreatedByUserID,
        creator.UserName AS CreatedByName,
        creator.Email AS CreatedByEmail,
        creator.Phone AS CreatedByPhone,
        t.AssignedToUserID,
        assignee.UserName AS AssignedToName,
        assignee.Email AS AssignedToEmail,
        t.CategoryID,
        c.CategoryName,
        t.Priority,
        CASE t.Priority
            WHEN 1 THEN 'Low'
            WHEN 2 THEN 'Medium'
            WHEN 3 THEN 'High'
            WHEN 4 THEN 'Critical'
        END AS PriorityName,
        t.Subject,
        t.Description,
        t.CurrentStatus,
        t.AttachmentPath,
        t.ReopenedCount,
        t.CreatedAt,
        t.UpdatedAt,
        t.ResolvedAt,
        t.ClosedAt
    FROM TicketMaster t
    INNER JOIN SchoolMaster s ON t.SchoolID = s.SchoolID
    INNER JOIN UserMaster creator ON t.CreatedByUserID = creator.UserID
    LEFT JOIN UserMaster assignee ON t.AssignedToUserID = assignee.UserID
    INNER JOIN TicketCategory c ON t.CategoryID = c.CategoryID
    WHERE t.TicketID = @TicketID;
    
    -- Return activity log
    SELECT 
        a.ActivityID,
        a.ActionType,
        a.OldStatus,
        a.NewStatus,
        a.OldAssignee,
        oldUser.UserName AS OldAssigneeName,
        a.NewAssignee,
        newUser.UserName AS NewAssigneeName,
        a.Comment,
        a.Timestamp,
        u.UserName AS ActionByName,
        u.ProfileID AS ActionByRole
    FROM TicketActivityLog a
    INNER JOIN UserMaster u ON a.ActionByUserID = u.UserID
    LEFT JOIN UserMaster oldUser ON a.OldAssignee = oldUser.UserID
    LEFT JOIN UserMaster newUser ON a.NewAssignee = newUser.UserID
    WHERE a.TicketID = @TicketID
    ORDER BY a.Timestamp DESC;
    
    -- Return comments
    SELECT 
        c.CommentID,
        c.CommentText,
        c.IsInternal,
        c.CreatedAt,
        u.UserName AS CommentByName,
        u.ProfileID AS CommentByRole
    FROM TicketComments c
    INNER JOIN UserMaster u ON c.CommentByUserID = u.UserID
    WHERE c.TicketID = @TicketID AND c.IsDeleted = 0
    ORDER BY c.CreatedAt DESC;
    
    -- Return attachments
    SELECT 
        a.AttachmentID,
        a.FileName,
        a.FilePath,
        a.FileSize,
        a.ContentType,
        a.UploadedAt,
        u.UserName AS UploadedByName
    FROM TicketAttachments a
    INNER JOIN UserMaster u ON a.UploadedByUserID = u.UserID
    WHERE a.TicketID = @TicketID AND a.IsDeleted = 0
    ORDER BY a.UploadedAt DESC;
    
    SET @ErrorMessage = NULL;
    RETURN 0;
END
