CREATE PROCEDURE [dbo].[Proc_SubjectMaster_Manage]
    @Action NVARCHAR(20),
    @SubjectID INT = NULL,
    @SchoolID INT,
    @ClassId INT = NULL,
    @SubjectName NVARCHAR(150) = NULL,
    @SubjectCode NVARCHAR(50) = NULL,
    @Description NVARCHAR(500) = NULL,
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- INSERT
        IF @Action = 'INSERT'
        BEGIN
            IF EXISTS (
                SELECT 1 FROM SubjectMaster 
                WHERE SchoolID = @SchoolID 
                AND SubjectName = @SubjectName 
                AND IsDeleted = 0
            )
            BEGIN
                SELECT 'ERROR' AS Status, 'Subject name already exists' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END
            
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
        
        -- UPDATE
        IF @Action = 'UPDATE'
        BEGIN
            IF EXISTS (
                SELECT 1 FROM SubjectMaster 
                WHERE SchoolID = @SchoolID 
                AND SubjectName = @SubjectName 
                AND IsDeleted = 0
                AND SubjectID != @SubjectID
            )
            BEGIN
                SELECT 'ERROR' AS Status, 'Subject name already exists' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END
            
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
        
        -- DELETE
        IF @Action = 'DELETE'
        BEGIN
            IF EXISTS (SELECT 1 FROM SubjectAllocation WHERE SubjectID = @SubjectID AND IsDeleted = 0)
            BEGIN
                SELECT 'ERROR' AS Status, 'Cannot delete subject as it is assigned to classes' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END
            
            UPDATE SubjectMaster
            SET IsDeleted = 1,
                DeletedBy = @UserId,
                DeletedAt = GETDATE()
            WHERE SubjectID = @SubjectID AND SchoolID = @SchoolID;
            
            SELECT 'SUCCESS' AS Status, 'Subject deleted successfully' AS Message;
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
