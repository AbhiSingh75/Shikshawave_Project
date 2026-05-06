-- =============================================
-- Stored Procedure: Proc_Dashboard_Students_AdmissionTrend_Get
-- Description: Get monthly admission trend for last 6 months
-- Author: ShikshaWave Team
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Students_AdmissionTrend_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @Gender NVARCHAR(10) = NULL,
    @Category NVARCHAR(50) = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        DECLARE @StartDate DATE;
        DECLARE @EndDate DATE;
        
        -- If no dates provided, default to last 6 months
        IF @FromDate IS NULL
            SET @StartDate = DATEADD(MONTH, -5, DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1));
        ELSE
            SET @StartDate = DATEFROMPARTS(YEAR(@FromDate), MONTH(@FromDate), 1);
            
        IF @ToDate IS NULL
            SET @EndDate = EOMONTH(GETDATE());
        ELSE
            SET @EndDate = EOMONTH(@ToDate);
        
        -- Generate all months in range
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
            ISNULL(COUNT(DISTINCT s.StudentID), 0) AS NewAdmissions
        FROM MonthRange m
        LEFT JOIN Student s ON 
            YEAR(s.CreatedAt) = YEAR(m.MonthDate)
            AND MONTH(s.CreatedAt) = MONTH(m.MonthDate)
            AND ISNULL(s.IsDeleted, 0) = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR s.AdmissionClass = @ClassID)
            AND (@SectionID IS NULL OR s.Section = @SectionID)
            AND (@Gender IS NULL OR s.Gender = @Gender)
            AND (@Category IS NULL OR s.Category = @Category)
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
