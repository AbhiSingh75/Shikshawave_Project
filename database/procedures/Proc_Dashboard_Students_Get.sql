-- =============================================
-- Stored Procedure: Proc_Dashboard_Students_Get
-- Description: Get student count for dashboard with India standard school filters
-- Author: ShikshaWave Team
-- Created: 2024
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Students_Get
    @SchoolID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @AcademicYear NVARCHAR(20) = NULL,
    @Gender NVARCHAR(10) = NULL,
    @Category NVARCHAR(50) = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @ShowActiveOnly BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Get total student count with filters
        SELECT 
            COUNT(DISTINCT s.StudentID) AS TotalStudents,
            COUNT(DISTINCT CASE WHEN s.Gender = 'Male' THEN s.StudentID END) AS MaleStudents,
            COUNT(DISTINCT CASE WHEN s.Gender = 'Female' THEN s.StudentID END) AS FemaleStudents,
            COUNT(DISTINCT CASE WHEN s.Category = 'General' THEN s.StudentID END) AS GeneralCategory,
            COUNT(DISTINCT CASE WHEN s.Category = 'OBC' THEN s.StudentID END) AS OBCCategory,
            COUNT(DISTINCT CASE WHEN s.Category = 'SC' THEN s.StudentID END) AS SCCategory,
            COUNT(DISTINCT CASE WHEN s.Category = 'ST' THEN s.StudentID END) AS STCategory,
            COUNT(DISTINCT CASE WHEN s.IsDeleted = 0 THEN s.StudentID END) AS ActiveStudents,
            COUNT(DISTINCT CASE WHEN s.IsDeleted = 1 THEN s.StudentID END) AS InactiveStudents
        FROM Student s
        LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
        LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
        WHERE 
            ISNULL(s.IsDeleted, 0) = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (@ClassID IS NULL OR s.AdmissionClass = @ClassID)
            AND (@SectionID IS NULL OR s.Section = @SectionID)
            AND (@Gender IS NULL OR s.Gender = @Gender)
            AND (@Category IS NULL OR s.Category = @Category)
            AND (@FromDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @FromDate)
            AND (@ToDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @ToDate)
            AND (@ShowActiveOnly = 0 OR s.IsDeleted = 0);
            
        -- Get class-wise breakdown
        SELECT 
            c.ClassID,
            c.ClassName,
            COUNT(DISTINCT s.StudentID) AS StudentCount,
            COUNT(DISTINCT CASE WHEN s.Gender = 'Male' THEN s.StudentID END) AS MaleCount,
            COUNT(DISTINCT CASE WHEN s.Gender = 'Female' THEN s.StudentID END) AS FemaleCount
        FROM Student s
        INNER JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
        WHERE 
            ISNULL(s.IsDeleted, 0) = 0
            AND (@SchoolID IS NULL OR s.SchoolID = @SchoolID)
            AND (@FromDate IS NULL OR CAST(s.CreatedAt AS DATE) >= @FromDate)
            AND (@ToDate IS NULL OR CAST(s.CreatedAt AS DATE) <= @ToDate)
            AND (@ShowActiveOnly = 0 OR s.IsDeleted = 0)
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
