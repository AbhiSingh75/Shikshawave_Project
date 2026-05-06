-- =============================================
-- Stored Procedure: Proc_Dashboard_Attendance_Get
-- Description: Get attendance statistics for dashboard
-- Author: ShikshaWave Team
-- Created: 2024
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Attendance_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @AttendanceDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Get overall attendance statistics
        SELECT 
            COUNT(*) AS TotalMarked,
            SUM(CASE WHEN a.Status = 'Present' THEN 1 ELSE 0 END) AS PresentCount,
            SUM(CASE WHEN a.Status = 'Absent' THEN 1 ELSE 0 END) AS AbsentCount,
            SUM(CASE WHEN a.Status = 'Leave' THEN 1 ELSE 0 END) AS LeaveCount,
            SUM(CASE WHEN a.Status = 'Late' THEN 1 ELSE 0 END) AS LateCount,
            SUM(CASE WHEN a.Status = 'Holiday' THEN 1 ELSE 0 END) AS HolidayCount,
            CAST(CASE 
                WHEN COUNT(*) > 0 
                THEN (SUM(CASE WHEN a.Status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
                ELSE 0 
            END AS DECIMAL(5,2)) AS AttendancePercentage,
            CAST(CASE 
                WHEN COUNT(*) > 0 
                THEN (SUM(CASE WHEN a.Status = 'Absent' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
                ELSE 0 
            END AS DECIMAL(5,2)) AS AbsentPercentage,
            CAST(CASE 
                WHEN COUNT(*) > 0 
                THEN (SUM(CASE WHEN a.Status = 'Late' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
                ELSE 0 
            END AS DECIMAL(5,2)) AS LatePercentage,
            CAST(CASE 
                WHEN COUNT(*) > 0 
                THEN (SUM(CASE WHEN a.Status = 'Holiday' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
                ELSE 0 
            END AS DECIMAL(5,2)) AS HolidayPercentage
        FROM StudentAttendance a
        INNER JOIN Student s ON a.StudentID = s.StudentID AND s.IsDeleted = 0
        WHERE 
            a.IsDeleted = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR a.ClassID = @ClassID)
            AND (@SectionID IS NULL OR a.SectionID = @SectionID)
            AND (
                (@AttendanceDate IS NOT NULL AND a.AttendanceDate = @AttendanceDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NOT NULL AND @ToDate IS NOT NULL AND a.AttendanceDate BETWEEN @FromDate AND @ToDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NULL AND @ToDate IS NULL AND a.AttendanceDate = CAST(GETDATE() AS DATE))
            );
            
        -- Get gender-wise attendance statistics
        SELECT 
            s.Gender,
            COUNT(*) AS TotalMarked,
            SUM(CASE WHEN a.Status = 'Present' THEN 1 ELSE 0 END) AS PresentCount,
            SUM(CASE WHEN a.Status = 'Absent' THEN 1 ELSE 0 END) AS AbsentCount,
            SUM(CASE WHEN a.Status = 'Leave' THEN 1 ELSE 0 END) AS LeaveCount,
            SUM(CASE WHEN a.Status = 'Late' THEN 1 ELSE 0 END) AS LateCount,
            CAST(CASE 
                WHEN COUNT(*) > 0 
                THEN (SUM(CASE WHEN a.Status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*))
                ELSE 0 
            END AS DECIMAL(5,2)) AS AttendancePercentage
        FROM StudentAttendance a
        INNER JOIN Student s ON a.StudentID = s.StudentID AND s.IsDeleted = 0
        WHERE 
            a.IsDeleted = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR a.ClassID = @ClassID)
            AND (@SectionID IS NULL OR a.SectionID = @SectionID)
            AND (
                (@AttendanceDate IS NOT NULL AND a.AttendanceDate = @AttendanceDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NOT NULL AND @ToDate IS NOT NULL AND a.AttendanceDate BETWEEN @FromDate AND @ToDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NULL AND @ToDate IS NULL AND a.AttendanceDate = CAST(GETDATE() AS DATE))
            )
        GROUP BY s.Gender;
            
        -- Get class-wise attendance breakdown
        SELECT 
            c.ClassID,
            c.ClassName,
            COUNT(DISTINCT a.StudentID) AS TotalMarked,
            COUNT(DISTINCT CASE WHEN a.Status = 'Present' THEN a.StudentID END) AS PresentCount,
            COUNT(DISTINCT CASE WHEN a.Status = 'Absent' THEN a.StudentID END) AS AbsentCount,
            CAST(CASE 
                WHEN COUNT(DISTINCT a.StudentID) > 0 
                THEN (COUNT(DISTINCT CASE WHEN a.Status = 'Present' THEN a.StudentID END) * 100.0 / COUNT(DISTINCT a.StudentID))
                ELSE 0 
            END AS DECIMAL(5,2)) AS AttendancePercentage
        FROM StudentAttendance a
        INNER JOIN Student s ON a.StudentID = s.StudentID AND s.IsDeleted = 0
        INNER JOIN ClassMaster c ON a.ClassID = c.ClassID
        WHERE 
            a.IsDeleted = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (
                (@AttendanceDate IS NOT NULL AND a.AttendanceDate = @AttendanceDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NOT NULL AND @ToDate IS NOT NULL AND a.AttendanceDate BETWEEN @FromDate AND @ToDate)
                OR (@AttendanceDate IS NULL AND @FromDate IS NULL AND @ToDate IS NULL AND a.AttendanceDate = CAST(GETDATE() AS DATE))
            )
        GROUP BY c.ClassID, c.ClassName
        ORDER BY c.ClassID;
        
    END TRY
    BEGIN CATCH
        SELECT 
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_MESSAGE() AS ErrorMessage;
    END CATCH
END;
GO
