CREATE OR ALTER PROCEDURE Proc_Students_For_Documents_Get
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        s.StudentID,
        s.FullName AS StudentName,
        s.StudentCode AS RollNumber,
        cm.ClassName,
        sm.SectionName
    FROM Student s
    LEFT JOIN ClassMaster cm ON s.AdmissionClass = cm.ClassID
    LEFT JOIN SectionMaster sm ON s.Section = sm.SectionID
    WHERE s.SchoolID = @SchoolID
        AND ISNULL(s.IsDeleted, 0) = 0
    ORDER BY s.StudentCode;
END
GO
