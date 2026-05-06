CREATE PROCEDURE [dbo].[Proc_SubjectMaster_GetByClass]
    @SchoolID INT,
    @ClassId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        s.SubjectID,
        s.SchoolID,
        s.ClassId,
        c.ClassName,
        s.SubjectName,
        s.SubjectCode,
        s.Description,
        s.CreatedBy,
        s.CreatedAt,
        s.UpdatedBy,
        s.UpdatedAt
    FROM SubjectMaster s
    LEFT JOIN ClassMaster c ON s.ClassId = c.ClassID AND c.IsDeleted = 0
    WHERE s.SchoolID = @SchoolID 
    AND s.IsDeleted = 0
    AND (@ClassId IS NULL OR s.ClassId = @ClassId OR s.ClassId IS NULL)
    ORDER BY s.SubjectName;
END
GO
