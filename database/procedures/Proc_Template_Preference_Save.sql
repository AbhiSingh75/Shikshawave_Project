CREATE OR ALTER PROCEDURE Proc_Template_Preference_Save
    @SchoolID INT,
    @TemplateType NVARCHAR(50),
    @TemplateFile NVARCHAR(255),
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if preference exists
    IF EXISTS (SELECT 1 FROM TemplateSettings WHERE SchoolID = @SchoolID AND TemplateType = @TemplateType AND IsDeleted = 0)
    BEGIN
        -- Update existing
        UPDATE TemplateSettings 
        SET TemplateFile = @TemplateFile,
            ModifiedBy = @CreatedBy,
            ModifiedAt = GETDATE()
        WHERE SchoolID = @SchoolID 
          AND TemplateType = @TemplateType 
          AND IsDeleted = 0;
    END
    ELSE
    BEGIN
        -- Insert new
        INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateName, TemplateFile, IsActive, CreatedBy, CreatedAt, IsDeleted)
        VALUES (@SchoolID, @TemplateType, @TemplateType, @TemplateFile, 1, @CreatedBy, GETDATE(), 0);
    END
    
    SELECT 'SUCCESS' AS Status, 'Template preference saved successfully' AS Message;
END
GO
