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
    
    IF @StartDate IS NULL SET @StartDate = DATEADD(DAY, -10, GETDATE());
    IF @EndDate IS NULL SET @EndDate = GETDATE();
    
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    -- Return all data as JSON in single row
    SELECT 
        (SELECT 
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
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS stats,
        
        (SELECT TOP 10
            dr.Date,
            ISNULL(COUNT(t.TicketID), 0) AS TicketCount,
            ISNULL(SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END), 0) AS ResolvedCount
        FROM (
            SELECT DATEADD(DAY, -number, @EndDate) AS Date
            FROM master..spt_values
            WHERE type = 'P' AND number BETWEEN 0 AND DATEDIFF(DAY, @StartDate, @EndDate)
        ) dr
        LEFT JOIN TicketMaster t ON CAST(t.CreatedAt AS DATE) = dr.Date
            AND t.IsDeleted = 0
            AND (@RoleName = 'Super Admin' OR t.SchoolID = @UserSchoolID)
            AND (@RoleName != 'Support Executive' OR t.AssignedToUserID = @UserID)
        GROUP BY dr.Date
        ORDER BY dr.Date DESC
        FOR JSON PATH) AS trends,
        
        (SELECT 
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
        FOR JSON PATH) AS categories,
        
        (SELECT 
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
        FOR JSON PATH) AS priorities,
        
        (SELECT TOP 5
            u.UserName,
            COUNT(*) AS AssignedTickets,
            SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedTickets,
            CAST(SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ResolutionRate,
            AVG(CASE WHEN t.ResolvedAt IS NOT NULL THEN DATEDIFF(HOUR, t.CreatedAt, t.ResolvedAt) END) AS AvgResolutionTimeHours
        FROM TicketMaster t
        INNER JOIN UserMaster u ON t.AssignedToUserID = u.UserID
        WHERE t.IsDeleted = 0
            AND t.AssignedToUserID IS NOT NULL
            AND CAST(t.CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName IN ('Super Admin', 'School Admin'))
            AND (@RoleName = 'Super Admin' OR t.SchoolID = @UserSchoolID)
        GROUP BY u.UserName
        ORDER BY SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) DESC
        FOR JSON PATH) AS performers,
        
        (SELECT TOP 10
            s.SchoolName,
            COUNT(*) AS TicketCount,
            SUM(CASE WHEN t.CurrentStatus = 'Open' THEN 1 ELSE 0 END) AS OpenTickets,
            SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedTickets
        FROM TicketMaster t
        INNER JOIN SchoolMaster s ON t.SchoolID = s.SchoolID
        WHERE t.IsDeleted = 0
            AND CAST(t.CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
            AND (@RoleName = 'Super Admin')
        GROUP BY s.SchoolName
        ORDER BY COUNT(*) DESC
        FOR JSON PATH) AS schools;
END
GO

PRINT 'Procedure created - returns JSON with 10-day trend by default!';
GO
