CREATE OR ALTER PROCEDURE Proc_Template_Preference_Get
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TemplateType, TemplateFile
    FROM TemplateSettings
    WHERE SchoolID = @SchoolID 
      AND IsActive = 1 
      AND IsDeleted = 0;
END
GO
