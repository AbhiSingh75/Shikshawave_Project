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
        DECLARE @CurrentStatus VARCHAR(20), @OldAssignee INT;
        SELECT @CurrentStatus = CurrentStatus, @OldAssignee = AssignedToUserID
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
        DECLARE @AssigneeRole VARCHAR(20);

        SELECT @AssigneeRole = p.ProfileName 
        FROM UserMaster AS U WITH(NOLOCK)
        INNER JOIN ProfileMaster AS P ON U.ProfileID = P.ProfileID
        WHERE p.ProfileName = 'Support Executive'
        AND U.UserID = @AssignToUserID AND ISNULL(u.IsDeleted, 0) = 0;
        
        IF @AssigneeRole IS NULL
        BEGIN
            SET @ErrorMessage = 'Assignee user not found or inactive';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        IF @AssigneeRole != 'Support Executive'
        BEGIN
            SET @ErrorMessage = 'Can only assign to Support Executive';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        -- Update ticket
        UPDATE TicketMaster
        SET AssignedToUserID = @AssignToUserID,
            CurrentStatus = 'In Progress',
            UpdatedAt = GETDATE()
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
            GETDATE()
        );
        
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
