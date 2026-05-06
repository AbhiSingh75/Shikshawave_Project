-- =============================================
-- FIX NOTIFICATION URLs - Add #chat anchor for messages
-- =============================================

-- Update Proc_Ticket_Assign to use encrypted URL
IF OBJECT_ID('Proc_Ticket_Assign', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Ticket_Assign;
GO

CREATE PROCEDURE Proc_Ticket_Assign
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
        
        IF @RoleName != 'Super Admin'
        BEGIN
            SET @ErrorMessage = 'Only Super Admin can assign tickets';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        
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
        
        IF @CurrentStatus NOT IN ('Open', 'Reopened')
        BEGIN
            SET @ErrorMessage = 'Can only assign Open or Reopened tickets';
            ROLLBACK TRANSACTION;
            RETURN 422;
        END
        
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
        
        UPDATE TicketMaster
        SET AssignedToUserID = @AssignToUserID,
            UpdatedAt = SYSDATETIMEOFFSET()
        WHERE TicketID = @TicketID;
        
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
        
        -- Send notification with proper URL (will be encrypted in Python)
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

-- Update Proc_Ticket_UpdateStatus to use encrypted URL
IF OBJECT_ID('Proc_Ticket_UpdateStatus', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Ticket_UpdateStatus;
GO

CREATE PROCEDURE Proc_Ticket_UpdateStatus
    @UserID INT,
    @RoleName NVARCHAR(50),
    @TicketID BIGINT,
    @NewStatus NVARCHAR(20),
    @Comment NVARCHAR(MAX) = NULL,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @CurrentStatus NVARCHAR(20), @AssignedTo INT, @CreatedBy INT, @SchoolID INT, @TicketNumber NVARCHAR(50), @Subject NVARCHAR(255);
        SELECT @CurrentStatus = CurrentStatus,
               @AssignedTo = AssignedToUserID,
               @CreatedBy = CreatedByUserID,
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
        
        IF @RoleName = 'Support Executive'
        BEGIN
            IF NOT ((@CurrentStatus = 'Open' AND @NewStatus = 'In Progress') OR
                    (@CurrentStatus = 'In Progress' AND @NewStatus = 'Resolved'))
            BEGIN
                SET @ErrorMessage = 'Invalid status transition for Support Executive';
                ROLLBACK TRANSACTION;
                RETURN 422;
            END
            
            IF @AssignedTo != @UserID
            BEGIN
                SET @ErrorMessage = 'You can only update tickets assigned to you';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
        END
        ELSE IF @RoleName = 'Super Admin'
        BEGIN
            IF NOT (@CurrentStatus = 'Resolved' AND @NewStatus = 'Closed')
            BEGIN
                SET @ErrorMessage = 'Super Admin can only close resolved tickets';
                ROLLBACK TRANSACTION;
                RETURN 422;
            END
        END
        ELSE IF @RoleName = 'School Admin'
        BEGIN
            IF NOT (@CurrentStatus = 'Resolved' AND @NewStatus = 'Reopened')
            BEGIN
                SET @ErrorMessage = 'School Admin can only reopen resolved tickets';
                ROLLBACK TRANSACTION;
                RETURN 422;
            END
        END
        ELSE
        BEGIN
            SET @ErrorMessage = 'Invalid role for status update';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        
        UPDATE TicketMaster
        SET CurrentStatus = @NewStatus,
            UpdatedAt = SYSDATETIMEOFFSET()
        WHERE TicketID = @TicketID;
        
        INSERT INTO TicketActivityLog (
            TicketID, ActionByUserID, ActionType,
            OldStatus, NewStatus, Comment, Timestamp
        )
        VALUES (
            @TicketID, @UserID, 'StatusChanged',
            @CurrentStatus, @NewStatus,
            ISNULL(@Comment, 'Status changed from ' + @CurrentStatus + ' to ' + @NewStatus),
            SYSDATETIMEOFFSET()
        );
        
        DECLARE @NotificationID BIGINT;
        DECLARE @TypeID INT;
        DECLARE @RecipientIDs NVARCHAR(MAX) = '';
        
        IF @CreatedBy IS NOT NULL AND @CreatedBy != @UserID
            SET @RecipientIDs = CAST(@CreatedBy AS NVARCHAR(10));
        
        IF @AssignedTo IS NOT NULL AND @AssignedTo != @UserID
        BEGIN
            IF LEN(@RecipientIDs) > 0
                SET @RecipientIDs = @RecipientIDs + ',' + CAST(@AssignedTo AS NVARCHAR(10));
            ELSE
                SET @RecipientIDs = CAST(@AssignedTo AS NVARCHAR(10));
        END
        
        IF LEN(@RecipientIDs) > 0
        BEGIN
            SELECT @TypeID = TypeID FROM NotificationTypeMaster WHERE TypeName = 'TicketStatusChanged' AND IsActive = 1;
            
            IF @TypeID IS NOT NULL
            BEGIN
                INSERT INTO NotificationMaster (SchoolID, TypeID, Title, Message, TargetURL, TargetModule, TargetRecordID, CreatedByUserID)
                VALUES (
                    @SchoolID, 
                    @TypeID, 
                    'Ticket Status Updated: ' + @TicketNumber,
                    'Ticket "' + @Subject + '" status changed to ' + @NewStatus + '.',
                    '/tickets/view/' + CAST(@TicketID AS NVARCHAR(20)) + '/',
                    'tickets',
                    @TicketID,
                    @UserID
                );
                
                SET @NotificationID = SCOPE_IDENTITY();
                
                INSERT INTO NotificationRecipients (NotificationID, UserID)
                SELECT @NotificationID, CAST(value AS INT)
                FROM STRING_SPLIT(@RecipientIDs, ',')
                WHERE ISNUMERIC(value) = 1;
            END
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

PRINT 'Notification URLs updated successfully';
