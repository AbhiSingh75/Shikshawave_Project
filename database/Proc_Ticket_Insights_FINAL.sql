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
    SET NOCOUNT OFF;
    
    IF @StartDate IS NULL SET @StartDate = DATEADD(DAY, -30, GETDATE());
    IF @EndDate IS NULL SET @EndDate = GETDATE();
    
    DECLARE @UserSchoolID INT;
    SELECT @UserSchoolID = SchoolID FROM UserMaster WHERE UserID = @UserID;
    
    -- 1. Stats
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
        AND (@RoleName != 'Support Executive' OR AssignedToUserID = @UserID);
    
    -- 2. Trends
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
    ORDER BY CAST(CreatedAt AS DATE);
    
    -- 3. Categories
    SELECT 
        c.CategoryName,
        COUNT(t.TicketID) AS TicketCount,
        SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedCount,
        CAST(CASE WHEN COUNT(t.TicketID) > 0 THEN SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) * 100.0 / COUNT(t.TicketID) ELSE 0 END AS DECIMAL(5,2)) AS ResolutionRate
    FROM TicketMaster t
    INNER JOIN TicketCategory c ON t.CategoryID = c.CategoryID
    WHERE t.IsDeleted = 0
        AND CAST(t.CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
        AND (@RoleName = 'Super Admin' OR t.SchoolID = @UserSchoolID)
        AND (@RoleName != 'Support Executive' OR t.AssignedToUserID = @UserID)
    GROUP BY c.CategoryName
    ORDER BY TicketCount DESC;
    
    -- 4. Priorities
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
    ORDER BY Priority DESC;
    
    -- 5. Performers
    IF @RoleName IN ('Super Admin', 'School Admin')
    BEGIN
        SELECT TOP 5
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
            AND (@RoleName = 'Super Admin' OR t.SchoolID = @UserSchoolID)
        GROUP BY u.UserName
        ORDER BY ResolvedTickets DESC;
    END
    ELSE
    BEGIN
        SELECT NULL AS UserName, 0 AS AssignedTickets, 0 AS ResolvedTickets, 0.0 AS ResolutionRate, 0.0 AS AvgResolutionTimeHours WHERE 1 = 0;
    END
    
    -- 6. Schools
    IF @RoleName = 'Super Admin'
    BEGIN
        SELECT TOP 10
            s.SchoolName,
            COUNT(*) AS TicketCount,
            SUM(CASE WHEN t.CurrentStatus = 'Open' THEN 1 ELSE 0 END) AS OpenTickets,
            SUM(CASE WHEN t.CurrentStatus IN ('Resolved', 'Closed') THEN 1 ELSE 0 END) AS ResolvedTickets
        FROM TicketMaster t
        INNER JOIN SchoolMaster s ON t.SchoolID = s.SchoolID
        WHERE t.IsDeleted = 0
            AND CAST(t.CreatedAt AS DATE) BETWEEN @StartDate AND @EndDate
        GROUP BY s.SchoolName
        ORDER BY TicketCount DESC;
    END
    ELSE
    BEGIN
        SELECT NULL AS SchoolName, 0 AS TicketCount, 0 AS OpenTickets, 0 AS ResolvedTickets WHERE 1 = 0;
    END
END
GO

PRINT 'Procedure created successfully - NO dynamic SQL!';
