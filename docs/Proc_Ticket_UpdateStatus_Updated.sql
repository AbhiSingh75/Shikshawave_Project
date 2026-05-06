CREATE OR ALTER PROCEDURE Proc_Ticket_UpdateStatus
    @UserID INT,
    @RoleName NVARCHAR(50),
    @TicketID BIGINT,
    @NewStatus VARCHAR(20),
    @Comment NVARCHAR(MAX) = NULL,
    @ErrorMessage NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Get current ticket status
        DECLARE @CurrentStatus VARCHAR(20), @AssignedTo INT, @SchoolID INT, @CreatedBy INT;
        SELECT @CurrentStatus = CurrentStatus,
               @AssignedTo = AssignedToUserID,
               @SchoolID = SchoolID,
               @CreatedBy = CreatedByUserID
        FROM TicketMaster
        WHERE TicketID = @TicketID AND ISNULL(IsDeleted, 0) = 0;
        
        IF @CurrentStatus IS NULL
        BEGIN
            SET @ErrorMessage = 'Ticket not found';
            ROLLBACK TRANSACTION;
            RETURN 404;
        END
        
        -- Validate status transition based on role
        DECLARE @IsValidTransition BIT = 0;
        
        -- Support Executive: Open → In Progress, In Progress → Resolved
        IF @RoleName = 'Support Executive'
        BEGIN
            -- Must be assigned to this user
            IF @AssignedTo != @UserID
            BEGIN
                SET @ErrorMessage = 'You can only update tickets assigned to you';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
            
            IF (@CurrentStatus = 'Open' AND @NewStatus = 'In Progress')
                OR (@CurrentStatus = 'In Progress' AND @NewStatus = 'Resolved')
            BEGIN
                SET @IsValidTransition = 1;
            END
        END
        
        -- Super Admin: Resolved → Closed
        ELSE IF @RoleName = 'Super Admin'
        BEGIN
            IF @CurrentStatus = 'Resolved' AND @NewStatus = 'Closed'
            BEGIN
                SET @IsValidTransition = 1;
            END
        END
        
        -- School Admin: Resolved → Reopened
        ELSE IF @RoleName = 'School Admin'
        BEGIN
            -- Must be from same school
            DECLARE @UserSchoolID INT;
            SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
            
            IF @UserSchoolID != @SchoolID
            BEGIN
                SET @ErrorMessage = 'You can only update tickets from your school';
                ROLLBACK TRANSACTION;
                RETURN 403;
            END
            
            IF @CurrentStatus = 'Resolved' AND @NewStatus = 'Reopened'
            BEGIN
                SET @IsValidTransition = 1;
            END
        END
        
        IF @IsValidTransition = 0
        BEGIN
            SET @ErrorMessage = 'Invalid status transition: ' + @CurrentStatus + ' → ' + @NewStatus + ' for your role';
            ROLLBACK TRANSACTION;
            RETURN 422;
        END
        
        -- Update ticket status
        UPDATE TicketMaster
        SET CurrentStatus = @NewStatus,
            UpdatedAt = SYSDATETIMEOFFSET(),
            ReopenedCount = CASE WHEN @NewStatus = 'Reopened' THEN ReopenedCount + 1 ELSE ReopenedCount END,
            ResolvedAt = CASE WHEN @NewStatus = 'Resolved' THEN GETDATE() ELSE ResolvedAt END,
            ClosedAt = CASE WHEN @NewStatus = 'Closed' THEN GETDATE() ELSE ClosedAt END
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
