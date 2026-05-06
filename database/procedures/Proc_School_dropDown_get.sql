CREATE OR ALTER PROCEDURE dbo.Proc_School_dropDown_get
AS
BEGIN
    SET NOCOUNT ON;
    SELECT SchoolID, SchoolName, SchoolCode
    FROM dbo.SchoolMaster
    WHERE IsDeleted = 0 OR IsDeleted IS NULL
    ORDER BY SchoolName;
END;
GO
