-- =============================================
-- Proc_Tickets_GetKPIs
-- Get ticket counts by status without pagination
-- =============================================
CREATE OR ALTER PROCEDURE Proc_Tickets_GetKPIs
    @UserID INT,
    @RoleName VARCHAR(50),
    @SchoolIDFilter INT = NULL,
    @AssignedToFilter INT = NULL,
    @StatusFilter VARCHAR(20) = NULL,
    @CategoryFilter INT = NULL,
    @PriorityFilter INT = NULL,
    @SearchTerm NVARCHAR(255) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    -- Base WHERE clause
    DECLARE @WhereClause NVARCHAR(MAX) = 'WHERE t.IsDeleted = 0';
    
    -- Role-based filtering
    IF @RoleName = 'Super Admin'
    BEGIN
        IF @SchoolIDFilter IS NOT NULL
            SET @WhereClause = @WhereClause + ' AND t.SchoolID = ' + CAST(@SchoolIDFilter AS VARCHAR);
    END
    ELSE IF @RoleName = 'School Admin'
    BEGIN
        SET @WhereClause = @WhereClause + ' AND t.SchoolID = ' + CAST(@UserSchoolID AS VARCHAR);
    END
    ELSE IF @RoleName = 'Support Executive'
    BEGIN
        SET @WhereClause = @WhereClause + ' AND t.AssignedToUserID = ' + CAST(@UserID AS VARCHAR);
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
    
    -- Get counts by status
    DECLARE @SQL NVARCHAR(MAX) = '
    SELECT 
        SUM(CASE WHEN t.CurrentStatus = ''Open'' THEN 1 ELSE 0 END) AS OpenCount,
        SUM(CASE WHEN t.CurrentStatus = ''In Progress'' THEN 1 ELSE 0 END) AS InProgressCount,
        SUM(CASE WHEN t.CurrentStatus = ''Resolved'' THEN 1 ELSE 0 END) AS ResolvedCount,
        SUM(CASE WHEN t.CurrentStatus = ''Closed'' THEN 1 ELSE 0 END) AS ClosedCount,
        SUM(CASE WHEN t.CurrentStatus = ''Reopened'' THEN 1 ELSE 0 END) AS ReopenedCount
    FROM TicketMaster t
    ' + @WhereClause;
    
    EXEC sp_executesql @SQL;
END
GO
