-- =============================================
-- Proc_Ticket_Insert
-- Create a new ticket with role validation
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Ticket_Insert
    @UserID INT,
    @RoleID INT,
    @SchoolID INT = NULL,
    @CategoryID INT,
    @Priority INT,
    @Subject NVARCHAR(255),
    @Description NVARCHAR(MAX),
    @AttachmentPath NVARCHAR(500) = NULL,
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
        -- Role 1 = Super Admin, Role 2 = School Admin, Role 4 = Support Executive
        IF @RoleID = 2 -- School Admin
        BEGIN
            -- School Admin: auto-bind school from user's profile
            SELECT @SchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
            IF @SchoolID IS NULL
            BEGIN
                SET @ErrorMessage = 'School Admin must be associated with a school';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
        END
        ELSE IF @RoleID = 1 -- Super Admin
        BEGIN
            -- Super Admin: must provide school
            IF @SchoolID IS NULL
            BEGIN
                SET @ErrorMessage = 'Super Admin must select a school';
                ROLLBACK TRANSACTION;
                RETURN 400;
            END
        END
        ELSE IF @RoleID = 4 -- Support Executive
        BEGIN
            -- Support Executive: cannot create tickets
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
            Subject, Description, CurrentStatus, AttachmentPath,
            CreatedAt, UpdatedAt, IsDeleted
        )
        VALUES (
            @SchoolID, @UserID, @CategoryID, @Priority,
            @Subject, @Description, 'Open', @AttachmentPath,
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
