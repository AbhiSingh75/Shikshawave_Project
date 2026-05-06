-- =============================================
-- Stored Procedure: Proc_Dashboard_Attendance_Trend_Get
-- Description: Get monthly attendance trend for last 6 months
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Attendance_Trend_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        DECLARE @StartDate DATE;
        DECLARE @EndDate DATE;
        
        IF @FromDate IS NULL
            SET @StartDate = DATEADD(MONTH, -5, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1));
        ELSE
            SET @StartDate = DATEFROMPARTS(YEAR(@FromDate), MONTH(@FromDate), 1);
            
        IF @ToDate IS NULL
            SET @EndDate = EOMONTH(GETDATE());
        ELSE
            SET @EndDate = EOMONTH(@ToDate);
        
        WITH MonthRange AS (
            SELECT @StartDate AS MonthDate
            UNION ALL
            SELECT DATEADD(MONTH, 1, MonthDate)
            FROM MonthRange
            WHERE DATEADD(MONTH, 1, MonthDate) <= @EndDate
        )
        SELECT 
            FORMAT(m.MonthDate, 'MMM yyyy') AS MonthYear,
            MONTH(m.MonthDate) AS Month,
            YEAR(m.MonthDate) AS Year,
            ISNULL(CAST(AVG(CASE WHEN a.AttendanceStatus = 'Present' THEN 100.0 ELSE 0 END) AS DECIMAL(5,2)), 0) AS PresentPercentage,
            ISNULL(CAST(AVG(CASE WHEN a.AttendanceStatus = 'Absent' THEN 100.0 ELSE 0 END) AS DECIMAL(5,2)), 0) AS AbsentPercentage,
            ISNULL(CAST(AVG(CASE WHEN a.AttendanceStatus = 'Late' THEN 100.0 ELSE 0 END) AS DECIMAL(5,2)), 0) AS LatePercentage,
            ISNULL(CAST(AVG(CASE WHEN a.AttendanceStatus = 'Holiday' THEN 100.0 ELSE 0 END) AS DECIMAL(5,2)), 0) AS HolidayPercentage
        FROM MonthRange m
        LEFT JOIN Attendance a ON 
            YEAR(a.AttendanceDate) = YEAR(m.MonthDate)
            AND MONTH(a.AttendanceDate) = MONTH(m.MonthDate)
            AND (@SchoolID IS NULL OR a.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR a.ClassID = @ClassID)
            AND (@SectionID IS NULL OR a.SectionID = @SectionID)
        GROUP BY m.MonthDate
        ORDER BY m.MonthDate
        OPTION (MAXRECURSION 0);
        
    END TRY
    BEGIN CATCH
        SELECT 
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_MESSAGE() AS ErrorMessage;
    END CATCH
END;
GO
