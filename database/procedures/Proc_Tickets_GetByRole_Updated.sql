-- =============================================
-- Proc_Tickets_GetByRole
-- Get tickets based on user role with filtering and pagination
-- Updated to use RoleName instead of RoleID
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Tickets_GetByRole
    @UserID INT,
    @RoleName NVARCHAR(50),
    @SchoolIDFilter INT = NULL,
    @AssignedToFilter INT = NULL,
    @StatusFilter VARCHAR(20) = NULL,
    @CategoryFilter INT = NULL,
    @PriorityFilter INT = NULL,
    @SearchTerm NVARCHAR(255) = NULL,
    @PageNumber INT = 1,
    @PageSize INT = 10,
    @SortColumn VARCHAR(50) = 'CreatedAt',
    @SortDirection VARCHAR(4) = 'DESC'
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    -- Build dynamic WHERE clause based on role
    DECLARE @WhereClause NVARCHAR(MAX) = 'WHERE t.IsDeleted = 0';
    
    -- Role-based filtering
    IF @RoleName = 'Super Admin' -- Super Admin: see all tickets
    BEGIN
        IF @SchoolIDFilter IS NOT NULL
            SET @WhereClause = @WhereClause + ' AND t.SchoolID = ' + CAST(@SchoolIDFilter AS VARCHAR);
    END
    ELSE IF @RoleName = 'School Admin' -- School Admin: only their school
    BEGIN
        SET @WhereClause = @WhereClause + ' AND t.SchoolID = ' + CAST(@UserSchoolID AS VARCHAR);
    END
    ELSE IF @RoleName = 'Support Executive' -- Support Executive: only assigned to them
    BEGIN
        SET @WhereClause = @WhereClause + ' AND t.AssignedToUserID = ' + CAST(@UserID AS VARCHAR);
    END
    ELSE
    BEGIN
        -- Invalid role
        SELECT 0 AS TotalCount;
        RETURN;
    END
    
    -- Additional filters
    IF @AssignedToFilter IS NOT NULL
        SET @WhereClause = @WhereClause + ' AND t.AssignedToUserID = ' + CAST(@AssignedToFilter AS VARCHAR);
    
    IF @StatusFilter IS NOT NULL
        SET @WhereClause = @WhereClause + ' AND t.CurrentStatus = ''' + @StatusFilter + '''';
    
    IF @CategoryFilter IS NOT NULL
        SET @WhereClause = @WhereClause + ' AND t.CategoryID = ' + CAST(@CategoryFilter AS VARCHAR);
    
    IF @PriorityFilter IS NOT NULL
        SET @WhereClause = @WhereClause + ' AND t.Priority = ' + CAST(@PriorityFilter AS VARCHAR);
    
    IF @SearchTerm IS NOT NULL AND LEN(@SearchTerm) > 0
        SET @WhereClause = @WhereClause + ' AND (t.Subject LIKE ''%' + @SearchTerm + '%'' OR t.Description LIKE ''%' + @SearchTerm + '%'' OR t.TicketNumber LIKE ''%' + @SearchTerm + '%'')';
    
    -- Calculate offset
    DECLARE @Offset INT = (@PageNumber - 1) * @PageSize;
    
    -- Build ORDER BY clause
    DECLARE @OrderByClause NVARCHAR(100) = 'ORDER BY t.' + @SortColumn + ' ' + @SortDirection;
    
    -- Build and execute query
    DECLARE @SQL NVARCHAR(MAX) = '
    WITH TicketCTE AS (
        SELECT 
            t.TicketID,
            t.TicketNumber,
            t.SchoolID,
            s.SchoolName,
            t.CreatedByUserID,
            creator.UserName AS CreatedByName,
            t.AssignedToUserID,
            assignee.UserName AS AssignedToName,
            t.CategoryID,
            c.CategoryName,
            t.Priority,
            CASE t.Priority
                WHEN 1 THEN ''Low''
                WHEN 2 THEN ''Medium''
                WHEN 3 THEN ''High''
                WHEN 4 THEN ''Critical''
            END AS PriorityName,
            t.Subject,
            t.Description,
            t.CurrentStatus,
            t.ReopenedCount,
            t.CreatedAt,
            t.UpdatedAt,
            t.ResolvedAt,
            t.ClosedAt,
            COUNT(*) OVER() AS TotalCount,
            ROW_NUMBER() OVER(' + @OrderByClause + ') AS RowNum
        FROM TicketMaster t
        INNER JOIN SchoolMaster s ON t.SchoolID = s.SchoolID
        INNER JOIN UserMaster creator ON t.CreatedByUserID = creator.UserID
        LEFT JOIN UserMaster assignee ON t.AssignedToUserID = assignee.UserID
        INNER JOIN TicketCategory c ON t.CategoryID = c.CategoryID
        ' + @WhereClause + '
    )
    SELECT *
    FROM TicketCTE
    WHERE RowNum BETWEEN ' + CAST(@Offset + 1 AS VARCHAR) + ' AND ' + CAST(@Offset + @PageSize AS VARCHAR);
    
    EXEC sp_executesql @SQL;
END
GO
