USE ShikshaWaveDB;
GO

DROP PROCEDURE IF EXISTS Proc_Ticket_Insights_Dashboard;
GO

CREATE PROCEDURE Proc_Ticket_Insights_Dashboard
    @UserID INT,
    @RoleName NVARCHAR(50),
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @StartDate IS NULL SET @StartDate = DATEADD(DAY, -30, GETDATE());
    IF @EndDate IS NULL SET @EndDate = GETDATE();
    
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    DECLARE @StatsJSON NVARCHAR(MAX);
    DECLARE @TrendsJSON NVARCHAR(MAX);
    DECLARE @CategoriesJSON NVARCHAR(MAX);
    DECLARE @PrioritiesJSON NVARCHAR(MAX);
    
    -- 1. Stats JSON
    SELECT @StatsJSON = (
        SELECT 
            COUNT(*) AS TotalTickets,
            SUM(CASE WHEN CurrentStatus = 'Open' THEN 1 ELSE 0 END) AS OpenTickets,
            SUM(CASE WHEN CurrentStatus = 'In Progress' THEN 1 ELSE 0 END) AS InProgressTickets,
            SUM(CASE WHEN CurrentStatus = 'Resolved' THEN 1 ELSE 0 END) AS ResolvedTickets,
            SUM(CASE WHEN CurrentStatus = 'Closed' THEN 1 ELSE 0 END) AS ClosedTickets,
            SUM(CASE WHEN CurrentStatus = 'Reopened' THEN 1 ELSE 0 END) AS ReopenedTickets,
            AVG(CASE WHEN ResolvedAt IS NOT NULL THEN DATEDIFF(HOUR, CreatedAt, ResolvedAt) END) AS AvgResolutionTimeHours,
            SUM(CASE WHEN Priority = 4 THEN 1 ELSE 0 END) AS CriticalTickets,
            SUM(CASE WHEN Priority = 3 THEN 1 ELSE 0 END) AS HighTickets,
            SUM(CASE WHEN Sources = 'Email' THEN 1 ELSE 0 END) AS EmailTickets,
            SUM(CASE WHEN Sources = 'Call' THEN 1 ELSE 0 END) AS CallTickets,
            SUM(CASE WHEN Sources = 'Website' THEN 1 ELSE 0 END) AS WebsiteTickets
        FROM TicketMaster
        WHERE IsDeleted = 0
            AND CAST(CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName = 'Super Admin' OR SchoolID = @UserSchoolID)
            AND (@RoleName != 'Support Executive' OR AssignedToUserID = @UserID)
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    );
    
    -- 2. Trends JSON
    SELECT @TrendsJSON = (
        SELECT 
            CAST(CreatedAt AS DATE) AS Date,
            COUNT(*) AS TicketCount,
            SUM(CASE WHEN CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedCount
        FROM TicketMaster
        WHERE IsDeleted = 0
            AND CAST(CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName = 'Super Admin' OR SchoolID = @UserSchoolID)
            AND (@RoleName != 'Support Executive' OR AssignedToUserID = @UserID)
        GROUP BY CAST(CreatedAt AS DATE)
        ORDER BY CAST(CreatedAt AS DATE)
        FOR JSON PATH
    );
    
    -- 3. Categories JSON
    SELECT @CategoriesJSON = (
        SELECT 
            c.CategoryName,
            COUNT(t.TicketID) AS TicketCount,
            SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedCount
        FROM TicketMaster t
        INNER JOIN TicketCategory c ON t.CategoryID = c.CategoryID
        WHERE t.IsDeleted = 0
            AND CAST(t.CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName = 'Super Admin' OR t.SchoolID = @UserSchoolID)
            AND (@RoleName != 'Support Executive' OR t.AssignedToUserID = @UserID)
        GROUP BY c.CategoryName
        ORDER BY COUNT(t.TicketID) DESC
        FOR JSON PATH
    );
    
    -- 4. Priorities JSON
    SELECT @PrioritiesJSON = (
        SELECT 
            CASE Priority WHEN 1 THEN 'Low' WHEN 2 THEN 'Medium' WHEN 3 THEN 'High' WHEN 4 THEN 'Critical' END AS PriorityName,
            Priority,
            COUNT(*) AS TicketCount,
            CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS DECIMAL(5,2)) AS Percentage
        FROM TicketMaster
        WHERE IsDeleted = 0
            AND CAST(CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName = 'Super Admin' OR SchoolID = @UserSchoolID)
            AND (@RoleName != 'Support Executive' OR AssignedToUserID = @UserID)
        GROUP BY Priority
        ORDER BY Priority DESC
        FOR JSON PATH
    );
    
    -- Return combined JSON
    SELECT 
        ISNULL(@StatsJSON, '{}') AS stats,
        ISNULL(@TrendsJSON, '[]') AS trends,
        ISNULL(@CategoriesJSON, '[]') AS categories,
        ISNULL(@PrioritiesJSON, '[]') AS priorities;
END
GO

PRINT 'Procedure created - returns JSON!';
