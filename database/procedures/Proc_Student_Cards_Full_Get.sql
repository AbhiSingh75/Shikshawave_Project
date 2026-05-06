CREATE OR ALTER PROCEDURE Proc_Student_Cards_Full_Get
    @SchoolID INT,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @Search NVARCHAR(255) = NULL,
    @PageNumber INT = 1,
    @PageSize INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Offset INT = (@PageNumber - 1) * @PageSize;
    
    SELECT 
        s.StudentID,
        s.StudentCode,
        s.FullName,
        s.Gender,
        s.DateOfBirth,
        s.Age,
        s.BloodGroup,
        s.Category,
        s.Religion,
        s.Nationality,
        s.MotherTongue,
        s.StudentAadhaar,
        s.PresentAddress,
        s.ParentMobile,
        s.AlternateNumber,
        s.Email,
        s.FatherName,
        s.FatherMobile,
        s.MotherName,
        s.MotherMobile,
        s.GuardianName,
        s.GuardianMobile,
        s.AdmissionClass,
        s.Section,
        s.Stream,
        s.AdmissionDate,
        s.Photo,
        cm.ClassName,
        sm.SectionName,
        sch.SchoolName,
        sch.SchoolLogo,
        s.IsDeleted,
        COUNT(*) OVER() AS TotalCount
    FROM Student s
    LEFT JOIN ClassMaster cm ON s.AdmissionClass = cm.ClassID
    LEFT JOIN SectionMaster sm ON s.Section = sm.SectionID
    LEFT JOIN SchoolMaster sch ON s.SchoolID = sch.SchoolID
    WHERE s.SchoolID = @SchoolID
        AND ISNULL(s.IsDeleted, 0) = 0
        AND (@ClassID IS NULL OR s.AdmissionClass = @ClassID)
        AND (@SectionID IS NULL OR s.Section = @SectionID)
        AND (@Search IS NULL OR s.FullName LIKE '%' + @Search + '%' OR s.StudentCode LIKE '%' + @Search + '%')
    ORDER BY s.StudentCode
    OFFSET @Offset ROWS
    FETCH NEXT @PageSize ROWS ONLY;
END
