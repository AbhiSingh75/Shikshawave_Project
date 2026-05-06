import os
import sys
import django

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ShikshaWave.settings')
django.setup()
from django.db import connection

def execute_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
    print("Executed SQL successfully.")

proc_assign = """
CREATE OR ALTER PROCEDURE [dbo].[Proc_Ticket_Assign]
    @TicketID INT,
    @AssignedToUserID INT,
    @AssignedByUserID INT,
    @AssignmentNotes NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @SchoolID INT, @CurrentStatusID INT;
        DECLARE @AssignerProfileID INT;
        
        -- Check Assigner Role (Super Admin Only)
        SELECT @AssignerProfileID = ProfileID FROM UserMaster WHERE UserID = @AssignedByUserID;
        
        IF @AssignerProfileID <> 1
        BEGIN
            SELECT 'ERROR' AS Status, 'Access denied. Only Super Admin can assign tickets.' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Get ticket details
        SELECT @SchoolID = SchoolID, @CurrentStatusID = StatusID
        FROM TicketMaster
        WHERE TicketID = @TicketID AND IsDeleted = 0;
        
        IF @SchoolID IS NULL
        BEGIN
            SELECT 'ERROR' AS Status, 'Ticket not found' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Deactivate previous assignments
        UPDATE TicketAssignment
        SET IsActive = 0, UnassignedAt = GETDATE(), UnassignedBy = @AssignedByUserID
        WHERE TicketID = @TicketID AND IsActive = 1;
        
        -- Create new assignment
        INSERT INTO TicketAssignment (
            TicketID, SchoolID, AssignedToUserID, AssignedByUserID, 
            AssignmentNotes, IsActive, AssignedAt
        )
        VALUES (
            @TicketID, @SchoolID, @AssignedToUserID, @AssignedByUserID,
            @AssignmentNotes, 1, GETDATE()
        );
        
        -- Update ticket status to Assigned (StatusID = 2)
        UPDATE TicketMaster
        SET StatusID = 2, AssignedToUserID = @AssignedToUserID, 
            UpdatedBy = @AssignedByUserID, UpdatedAt = GETDATE()
        WHERE TicketID = @TicketID;
        
        -- Log status change
        INSERT INTO TicketStatusHistory (
            TicketID, SchoolID, FromStatusID, ToStatusID, 
            ChangeReason, ChangedBy, ChangedAt
        )
        VALUES (
            @TicketID, @SchoolID, @CurrentStatusID, 2,
            'Ticket assigned to support executive', @AssignedByUserID, GETDATE()
        );
        
        COMMIT TRANSACTION;
        
        SELECT 'SUCCESS' AS Status, 'Ticket assigned successfully' AS Message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
"""

proc_status_change = """
CREATE OR ALTER PROCEDURE [dbo].[Proc_Ticket_StatusChange]
    @TicketID INT,
    @NewStatusID INT,
    @ChangedByUserID INT,
    @ChangeReason NVARCHAR(500) = NULL,
    @ResolutionNotes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @SchoolID INT, @CurrentStatusID INT;
        DECLARE @UserProfileID INT;
        
        -- Get ticket details
        SELECT @SchoolID = SchoolID, @CurrentStatusID = StatusID
        FROM TicketMaster
        WHERE TicketID = @TicketID AND IsDeleted = 0;
        
        IF @SchoolID IS NULL
        BEGIN
            SELECT 'ERROR' AS Status, 'Ticket not found' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Get User Profile
        SELECT @UserProfileID = ProfileID FROM UserMaster WHERE UserID = @ChangedByUserID;
        
        -- Workflow Enforcement
        DECLARE @IsAllowed BIT = 0;
        
        -- Open (1) -> In Progress (3)
        IF @CurrentStatusID = 1 AND @NewStatusID = 3
        BEGIN
            IF @UserProfileID IN (1, 5) SET @IsAllowed = 1; -- Super Admin, Support Exec
        END
        -- In Progress (3) -> Resolved (5)
        ELSE IF @CurrentStatusID = 3 AND @NewStatusID = 5
        BEGIN
            IF @UserProfileID IN (1, 5) SET @IsAllowed = 1;
        END
        -- Resolved (5) -> Closed (6)
        ELSE IF @CurrentStatusID = 5 AND @NewStatusID = 6
        BEGIN
            IF @UserProfileID = 1 SET @IsAllowed = 1; -- Super Admin Only
        END
        -- Resolved (5) -> Reopened (7)
        ELSE IF @CurrentStatusID = 5 AND @NewStatusID = 7
        BEGIN
            IF @UserProfileID IN (1, 2) SET @IsAllowed = 1; -- Super Admin, School Admin
        END
        -- Allow other transitions if Super Admin? Or strictly follow the graph?
        -- For now, let's allow Super Admin to do anything to prevent lockouts, 
        -- but strictly enforce for others.
        ELSE IF @UserProfileID = 1
        BEGIN
            SET @IsAllowed = 1;
        END
        
        IF @IsAllowed = 0
        BEGIN
            SELECT 'ERROR' AS Status, 'Invalid status transition or access denied.' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Update ticket status
        UPDATE TicketMaster
        SET 
            StatusID = @NewStatusID,
            ResolutionNotes = CASE WHEN @NewStatusID = 5 THEN @ResolutionNotes ELSE ResolutionNotes END,
            ResolvedAt = CASE WHEN @NewStatusID = 5 THEN GETDATE() ELSE ResolvedAt END,
            ClosedAt = CASE WHEN @NewStatusID = 6 THEN GETDATE() ELSE ClosedAt END,
            UpdatedBy = @ChangedByUserID,
            UpdatedAt = GETDATE()
        WHERE TicketID = @TicketID;
        
        -- Log status change
        INSERT INTO TicketStatusHistory (
            TicketID, SchoolID, FromStatusID, ToStatusID, 
            ChangeReason, ChangedBy, ChangedAt
        )
        VALUES (
            @TicketID, @SchoolID, @CurrentStatusID, @NewStatusID,
            @ChangeReason, @ChangedByUserID, GETDATE()
        );
        
        COMMIT TRANSACTION;
        
        SELECT 'SUCCESS' AS Status, 'Ticket status updated successfully' AS Message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
"""

proc_get_list = """
CREATE OR ALTER PROCEDURE [dbo].[Proc_Ticket_GetList]
    @UserID INT,
    @SchoolID INT = NULL,
    @StatusID INT = NULL,
    @PriorityID INT = NULL,
    @CategoryID INT = NULL,
    @AssignedToUserID INT = NULL,
    @SearchText NVARCHAR(200) = NULL,
    @PageNumber INT = 1,
    @PageSize INT = 20
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @UserProfileID INT, @Offset INT;
    
    -- Get user profile
    SELECT @UserProfileID = ProfileID
    FROM UserMaster
    WHERE UserID = @UserID;
    
    SET @Offset = (@PageNumber - 1) * @PageSize;
    
    -- Build dynamic query based on role
    ;WITH TicketCTE AS (
        SELECT 
            t.TicketID,
            t.TicketNumber,
            t.SchoolID,
            s.SchoolName,
            t.Title,
            t.Description,
            t.CategoryID,
            tc.CategoryName,
            t.PriorityID,
            tp.PriorityName,
            tp.ColorCode AS PriorityColor,
            t.StatusID,
            ts.StatusName,
            ts.ColorCode AS StatusColor,
            t.CreatedByUserID,
            cu.UserName AS CreatedByUserName,
            t.AssignedToUserID,
            au.UserName AS AssignedToUserName,
            t.ReopenedCount,
            t.LastReopenedAt,
            t.CreatedAt,
            t.UpdatedAt,
            t.ResolvedAt,
            t.ClosedAt,
            ROW_NUMBER() OVER (ORDER BY t.CreatedAt DESC) AS RowNum
        FROM TicketMaster t
        INNER JOIN SchoolMaster s ON t.SchoolID = s.SchoolID
        INNER JOIN TicketCategory tc ON t.CategoryID = tc.CategoryID
        INNER JOIN TicketPriority tp ON t.PriorityID = tp.PriorityID
        INNER JOIN TicketStatus ts ON t.StatusID = ts.StatusID
        INNER JOIN UserMaster cu ON t.CreatedByUserID = cu.UserID
        LEFT JOIN UserMaster au ON t.AssignedToUserID = au.UserID
        WHERE t.IsDeleted = 0
            -- Role-based filtering
            AND (
                @UserProfileID = 1 -- Super Admin: all tickets
                OR (@UserProfileID = 2 AND t.SchoolID = @SchoolID) -- School Admin: school tickets
                OR (@UserProfileID = 3 AND t.CreatedByUserID = @UserID) -- Teacher: own tickets
                OR (@UserProfileID = 4 AND t.CreatedByUserID = @UserID) -- Student: own tickets
                OR (@UserProfileID = 5 AND t.AssignedToUserID = @UserID) -- Support Executive: assigned tickets
            )
            -- Additional filters
            -- For Support Execs (Profile 5), ignore SchoolID filter if it matches their assignment
            AND (
                (@UserProfileID = 5 AND t.AssignedToUserID = @UserID)
                OR
                (@SchoolID IS NULL OR t.SchoolID = @SchoolID)
            )
            AND (@StatusID IS NULL OR t.StatusID = @StatusID)
            AND (@PriorityID IS NULL OR t.PriorityID = @PriorityID)
            AND (@CategoryID IS NULL OR t.CategoryID = @CategoryID)
            AND (@AssignedToUserID IS NULL OR t.AssignedToUserID = @AssignedToUserID)
            AND (
                @SearchText IS NULL 
                OR t.TicketNumber LIKE '%' + @SearchText + '%'
                OR t.Title LIKE '%' + @SearchText + '%'
                OR t.Description LIKE '%' + @SearchText + '%'
            )
    )
    SELECT 
        TicketID, TicketNumber, SchoolID, SchoolName, Title, Description,
        CategoryID, CategoryName, PriorityID, PriorityName, PriorityColor,
        StatusID, StatusName, StatusColor, CreatedByUserID, CreatedByUserName,
        AssignedToUserID, AssignedToUserName, ReopenedCount, LastReopenedAt,
        CreatedAt, UpdatedAt, ResolvedAt, ClosedAt,
        (SELECT COUNT(*) FROM TicketCTE) AS TotalRecords
    FROM TicketCTE
    WHERE RowNum > @Offset AND RowNum <= (@Offset + @PageSize)
    ORDER BY RowNum;
END
"""

print("Applying Proc_Ticket_Assign...")
execute_sql(proc_assign)
print("Applying Proc_Ticket_StatusChange...")
execute_sql(proc_status_change)
print("Applying Proc_Ticket_GetList...")
execute_sql(proc_get_list)
print("All procedures updated.")
