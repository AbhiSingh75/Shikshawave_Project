-- Get Current Students in a Class/Section
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_GetByClass
    @SchoolID INT,
    @AcademicYearID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        sat.TrackID,
        sat.StudentID,
        s.StudentCode,
        s.FullName,
        s.Gender,
        s.DateOfBirth,
        s.ParentMobile,
        sat.AcademicYearID,
        ay.AcademicYear,
        sat.ClassID,
        c.ClassName,
        sat.SectionID,
        sec.SectionName,
        sat.RollNumber,
        sat.Status,
        sat.AttendancePercentage,
        sat.OverallGrade,
        sat.OverallPercentage,
        sat.Rank
    FROM StudentAcademicTrack sat
    INNER JOIN Student s ON sat.StudentID = s.StudentID
    INNER JOIN AcademicYear ay ON sat.AcademicYearID = ay.AcademicYearID
    INNER JOIN ClassMaster c ON sat.ClassID = c.ClassID
    INNER JOIN SectionMaster sec ON sat.SectionID = sec.SectionID
    WHERE sat.SchoolID = @SchoolID
        AND sat.IsCurrent = 1
        AND sat.IsDeleted = 0
        AND s.IsDeleted = 0
        AND (@AcademicYearID IS NULL OR sat.AcademicYearID = @AcademicYearID)
        AND (@ClassID IS NULL OR sat.ClassID = @ClassID)
        AND (@SectionID IS NULL OR sat.SectionID = @SectionID)
    ORDER BY c.ClassName, sec.SectionName, sat.RollNumber, s.FullName;
END
GO
