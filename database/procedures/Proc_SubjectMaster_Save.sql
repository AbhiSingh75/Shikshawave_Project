CREATE PROCEDURE [dbo].[Proc_SubjectMaster_Save]
    @SubjectID INT = NULL,
    @SchoolID INT,
    @ClassId INT = NULL,
    @SubjectName NVARCHAR(150),
    @SubjectCode NVARCHAR(50) = NULL,
    @Description NVARCHAR(500) = NULL,
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Check if subject name already exists for this school (excluding current record)
        IF EXISTS (
            SELECT 1 FROM SubjectMaster 
            WHERE SchoolID = @SchoolID 
            AND SubjectName = @SubjectName 
            AND IsDeleted = 0
            AND (@SubjectID IS NULL OR SubjectID != @SubjectID)
        )
        BEGIN
            SELECT 'ERROR' AS Status, 'Subject name already exists' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        IF @SubjectID IS NULL OR @SubjectID = 0
        BEGIN
            -- Insert new subject
            INSERT INTO SubjectMaster (
                SchoolID, ClassId, SubjectName, SubjectCode, Description,
                CreatedBy, CreatedAt, IsDeleted
            )
            VALUES (
                @SchoolID, @ClassId, @SubjectName, @SubjectCode, @Description,
                @UserId, GETDATE(), 0
            );
            
            SELECT 'SUCCESS' AS Status, 'Subject created successfully' AS Message;
        END
        ELSE
        BEGIN
            -- Update existing subject
            UPDATE SubjectMaster
            SET ClassId = @ClassId,
                SubjectName = @SubjectName,
                SubjectCode = @SubjectCode,
                Description = @Description,
                UpdatedBy = @UserId,
                UpdatedAt = GETDATE()
            WHERE SubjectID = @SubjectID AND SchoolID = @SchoolID;
            
            SELECT 'SUCCESS' AS Status, 'Subject updated successfully' AS Message;
        END
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO
