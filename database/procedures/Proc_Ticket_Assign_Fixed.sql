-- =============================================
-- Proc_Ticket_Assign - Fixed Version
-- Assign ticket to Support Executive (Super Admin only) with notification
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Ticket_Assign
    @UserID INT,
    @RoleName NVARCHAR(50),
    @TicketID BIGINT,
    @AssignToUserID INT,
    @Comment NVARCHAR(MAX) = NULL,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Only Super Admin can assign tickets
        IF @RoleName != 'Super Admin'
        BEGIN
            SET @ErrorMessage = 'Only Super Admin can assign tickets';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        
        -- Validate ticket exists
        DECLARE @CurrentStatus VARCHAR(20), @OldAssignee INT, @SchoolID INT, @TicketNumber NVARCHAR(50), @Subject NVARCHAR(255);
        SELECT @CurrentStatus = CurrentStatus, 
               @OldAssignee = AssignedToUserID,
               @SchoolID = SchoolID,
               @TicketNumber = TicketNumber,
               @Subject = Subject
        FROM TicketMaster
        WHERE TicketID = @TicketID AND ISNULL(IsDeleted, 0) = 0;
        
        IF @CurrentStatus IS NULL
        BEGIN
            SET @ErrorMessage = 'Ticket not found';
            ROLLBACK TRANSACTION;
            RETURN 404;
        END
        
        -- Can only assign Open or Reopened tickets
        IF @CurrentStatus NOT IN ('Open', 'Reopened')
        BEGIN
            SET @ErrorMessage = 'Can only assign Open or Reopened tickets';
            ROLLBACK TRANSACTION;
            RETURN 422;
        END
        
        -- Validate assignee is Support Executive
        DECLARE @AssigneeProfileName NVARCHAR(50);
        SELECT @AssigneeProfileName = p.ProfileName
        FROM UserMaster u
        INNER JOIN ProfileMaster p ON u.ProfileID = p.ProfileID
        WHERE u.UserID = @AssignToUserID AND u.IsActive = 1 AND ISNULL(u.IsDeleted, 0) = 0;
        
        IF @AssigneeProfileName IS NULL
        BEGIN
            SET @ErrorMessage = 'Assignee user not found or inactive';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        IF @AssigneeProfileName != 'Support Executive'
        BEGIN
            SET @ErrorMessage = 'Can only assign to Support Executive';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        -- Update ticket
        UPDATE TicketMaster
        SET AssignedToUserID = @AssignToUserID,
            UpdatedAt = SYSDATETIMEOFFSET()
        WHERE TicketID = @TicketID;
        
        -- Log activity
        INSERT INTO TicketActivityLog (
            TicketID, ActionByUserID, ActionType,
            OldAssignee, NewAssignee, Comment, Timestamp
        )
        VALUES (
            @TicketID, @UserID, 'Assigned',
            @OldAssignee, @AssignToUserID,
            ISNULL(@Comment, 'Ticket assigned to support executive'),
            SYSDATETIMEOFFSET()
        );
        
        -- Send notification to assigned user
        DECLARE @NotificationID BIGINT;
        DECLARE @TypeID INT;
        
        SELECT @TypeID = TypeID FROM NotificationTypeMaster WHERE TypeName = 'TicketAssigned' AND IsActive = 1;
        
        IF @TypeID IS NOT NULL
        BEGIN
            INSERT INTO NotificationMaster (SchoolID, TypeID, Title, Message, TargetURL, TargetModule, TargetRecordID, CreatedByUserID)
            VALUES (
                @SchoolID, 
                @TypeID, 
                'Ticket Assigned: ' + @TicketNumber,
                'Ticket "' + @Subject + '" has been assigned to you.',
                '/tickets/view/' + CAST(@TicketID AS NVARCHAR(20)) + '/',
                'tickets',
                @TicketID,
                @UserID
            );
            
            SET @NotificationID = SCOPE_IDENTITY();
            
            -- Add recipient
            INSERT INTO NotificationRecipients (NotificationID, UserID)
            VALUES (@NotificationID, @AssignToUserID);
        END
        
        COMMIT TRANSACTION;
        SET @ErrorMessage = NULL;
        RETURN 0;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SET @ErrorMessage = ERROR_MESSAGE();
        RETURN 500;
    END CATCH
END
GO
