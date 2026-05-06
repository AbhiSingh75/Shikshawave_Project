-- =============================================
-- Proc_Ticket_UpdateStatus - Fixed Version
-- Update ticket status with role validation and notification
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Ticket_UpdateStatus
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
        
        -- Get current ticket info
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
        
        -- Role-based status transition validation
        IF @RoleName = 'Support Executive'
        BEGIN
            -- Can only move Open -> In Progress or In Progress -> Resolved
            IF NOT ((@CurrentStatus = 'Open' AND @NewStatus = 'In Progress') OR
                    (@CurrentStatus = 'In Progress' AND @NewStatus = 'Resolved'))
            BEGIN
                SET @ErrorMessage = 'Invalid status transition for Support Executive';
                ROLLBACK TRANSACTION;
                RETURN 422;
            END
            
            -- Must be assigned to this executive
            IF @AssignedTo != @UserID
            BEGIN
                SET @ErrorMessage = 'You can only update tickets assigned to you';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
        END
        ELSE IF @RoleName = 'Super Admin'
        BEGIN
            -- Can close resolved tickets
            IF NOT (@CurrentStatus = 'Resolved' AND @NewStatus = 'Closed')
            BEGIN
                SET @ErrorMessage = 'Super Admin can only close resolved tickets';
                ROLLBACK TRANSACTION;
                RETURN 422;
            END
        END
        ELSE IF @RoleName = 'School Admin'
        BEGIN
            -- Can reopen resolved tickets
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
        
        -- Update ticket status
        UPDATE TicketMaster
        SET CurrentStatus = @NewStatus,
            UpdatedAt = SYSDATETIMEOFFSET()
        WHERE TicketID = @TicketID;
        
        -- Log activity
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
        
        -- Send notification to relevant users
        DECLARE @NotificationID BIGINT;
        DECLARE @TypeID INT;
        DECLARE @RecipientIDs NVARCHAR(MAX) = '';
        
        -- Build recipient list (exclude current user)
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
                
                -- Add recipients
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
