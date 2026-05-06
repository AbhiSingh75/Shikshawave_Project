-- =============================================
-- FIX NOTIFICATION SYSTEM
-- This script fixes the notification system to work properly
-- =============================================

PRINT '========================================';
PRINT 'FIXING NOTIFICATION SYSTEM';
PRINT '========================================';

-- Step 1: Create missing stored procedures
PRINT 'Step 1: Creating missing notification procedures...';

-- Proc_Notification_GetUnreadCount
IF OBJECT_ID('Proc_Notification_GetUnreadCount', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_GetUnreadCount;
GO

CREATE PROCEDURE Proc_Notification_GetUnreadCount
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
            AND (@SchoolID IS NULL OR nm.SchoolID = @SchoolID)
            AND (nm.ExpiresAt IS NULL OR nm.ExpiresAt > GETDATE());
    END TRY
    BEGIN CATCH
        SELECT 0 AS UnreadCount;
    END CATCH
END
GO

PRINT '  - Proc_Notification_GetUnreadCount created';

-- Proc_Notification_MarkAllRead
IF OBJECT_ID('Proc_Notification_MarkAllRead', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Notification_MarkAllRead;
GO

CREATE PROCEDURE Proc_Notification_MarkAllRead
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
            AND (@SchoolID IS NULL OR nm.SchoolID = @SchoolID);
        
        COMMIT TRANSACTION;
        
        SELECT @@ROWCOUNT AS UpdatedCount;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS UpdatedCount;
    END CATCH
END
GO

PRINT '  - Proc_Notification_MarkAllRead created';

-- Step 2: Fix ticket procedures to accept RoleName and send notifications
PRINT 'Step 2: Fixing ticket procedures...';

-- Proc_Ticket_Insert
IF OBJECT_ID('Proc_Ticket_Insert', 'P') IS NOT NULL
    DROP PROCEDURE Proc_Ticket_Insert;
GO

CREATE PROCEDURE Proc_Ticket_Insert
    @UserID INT,
    @RoleName NVARCHAR(50),
    @SchoolID INT = NULL,
    @CategoryID INT,
    @Priority INT,
    @Subject NVARCHAR(255),
    @Description NVARCHAR(MAX),
    @AttachmentPath NVARCHAR(500) = NULL,
    @Sources NVARCHAR(50) = 'Website',
    @TicketID BIGINT OUTPUT,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Validate user exists and is active
        IF NOT EXISTS (SELECT 1 FROM UserMaster WHERE UserID = @UserID AND IsActive = 1 AND ISNULL(IsDeleted, 0) = 0)
        BEGIN
            SET @ErrorMessage = 'Invalid or inactive user';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        
        -- Role-based validation
        IF @RoleName = 'School Admin'
        BEGIN
            SELECT @SchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
            IF @SchoolID IS NULL
            BEGIN
                SET @ErrorMessage = 'School Admin must be associated with a school';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
        END
        ELSE IF @RoleName = 'Super Admin'
        BEGIN
            IF @SchoolID IS NULL
            BEGIN
                SET @ErrorMessage = 'Super Admin must select a school';
                ROLLBACK TRANSACTION;
                RETURN 400;
            END
        END
        ELSE IF @RoleName = 'Support Executive'
        BEGIN
            SET @ErrorMessage = 'Support Executives cannot create tickets';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        ELSE
        BEGIN
            SET @ErrorMessage = 'Invalid role for ticket creation';
            ROLLBACK TRANSACTION;
            RETURN 403;
        END
        
        -- Validate school exists
        IF NOT EXISTS (SELECT 1 FROM SchoolMaster WHERE SchoolID = @SchoolID AND ISNULL(IsDeleted, 0) = 0)
        BEGIN
            SET @ErrorMessage = 'Invalid school';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        -- Validate category
        IF NOT EXISTS (SELECT 1 FROM TicketCategory WHERE CategoryID = @CategoryID AND IsActive = 1 AND ISNULL(IsDeleted, 0) = 0)
        BEGIN
            SET @ErrorMessage = 'Invalid category';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        -- Validate priority
        IF @Priority NOT BETWEEN 1 AND 4
        BEGIN
            SET @ErrorMessage = 'Priority must be between 1 and 4';
            ROLLBACK TRANSACTION;
            RETURN 400;
        END
        
        -- Insert ticket
        INSERT INTO TicketMaster (
            SchoolID, CreatedByUserID, CategoryID, Priority,
            Subject, Description, CurrentStatus, AttachmentPath, Sources,
            CreatedAt, UpdatedAt, IsDeleted
        )
        VALUES (
            @SchoolID, @UserID, @CategoryID, @Priority,
            @Subject, @Description, 'Open', @AttachmentPath, @Sources,
            SYSDATETIMEOFFSET(), SYSDATETIMEOFFSET(), 0
        );
        
        SET @TicketID = SCOPE_IDENTITY();
        
        -- Log activity
        INSERT INTO TicketActivityLog (TicketID, ActionByUserID, ActionType, NewStatus, Comment, Timestamp)
        VALUES (@TicketID, @UserID, 'Created', 'Open', 'Ticket created', SYSDATETIMEOFFSET());
        
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

PRINT '  - Proc_Ticket_Insert fixed';

-- Proc_Ticket_Assign
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

PRINT '  - Proc_Ticket_Assign fixed';

-- Proc_Ticket_UpdateStatus
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

PRINT '  - Proc_Ticket_UpdateStatus fixed';

PRINT '';
PRINT '========================================';
PRINT 'NOTIFICATION SYSTEM FIX COMPLETED';
PRINT '========================================';
PRINT '';
PRINT 'Summary:';
PRINT '  - Created Proc_Notification_GetUnreadCount';
PRINT '  - Created Proc_Notification_MarkAllRead';
PRINT '  - Fixed Proc_Ticket_Insert to accept RoleName';
PRINT '  - Fixed Proc_Ticket_Assign to accept RoleName and send notifications';
PRINT '  - Fixed Proc_Ticket_UpdateStatus to accept RoleName and send notifications';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Restart your Django application';
PRINT '  2. Test ticket creation - Super Admins should receive notifications';
PRINT '  3. Test ticket assignment - Assigned user should receive notification';
PRINT '  4. Test ticket status changes - Relevant users should receive notifications';
PRINT '  5. Test ticket messages - Participants should receive notifications';
PRINT '';
