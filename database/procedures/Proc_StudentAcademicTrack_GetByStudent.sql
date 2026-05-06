-- Get Academic Track History for a Student
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_GetByStudent
    @StudentID INT,
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        sat.TrackID,
        sat.StudentID,
        s.StudentCode,
        s.FullName,
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
        sat.Rank,
        sat.Remarks,
        sat.PromotedToClassID,
        pc.ClassName AS PromotedToClassName,
        sat.PromotedToSectionID,
        ps.SectionName AS PromotedToSectionName,
        sat.PromotionDate,
        sat.IsCurrent,
        sat.StartDate,
        sat.EndDate,
        sat.CreatedAt
    FROM StudentAcademicTrack sat
    INNER JOIN Student s ON sat.StudentID = s.StudentID
    INNER JOIN AcademicYear ay ON sat.AcademicYearID = ay.AcademicYearID
    INNER JOIN ClassMaster c ON sat.ClassID = c.ClassID
    INNER JOIN SectionMaster sec ON sat.SectionID = sec.SectionID
    LEFT JOIN ClassMaster pc ON sat.PromotedToClassID = pc.ClassID
    LEFT JOIN SectionMaster ps ON sat.PromotedToSectionID = ps.SectionID
    WHERE sat.StudentID = @StudentID 
        AND sat.SchoolID = @SchoolID
        AND sat.IsDeleted = 0
    ORDER BY ay.StartDate DESC, sat.CreatedAt DESC;
END
GO
