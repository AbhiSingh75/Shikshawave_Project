CREATE PROCEDURE [dbo].[Proc_SubjectMaster_Delete]
    @SubjectID INT,
    @SchoolID INT,
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Check if subject is being used
        IF EXISTS (SELECT 1 FROM SubjectAllocation WHERE SubjectID = @SubjectID AND IsDeleted = 0)
        BEGIN
            SELECT 'ERROR' AS Status, 'Cannot delete subject as it is assigned to classes' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Soft delete
        UPDATE SubjectMaster
        SET IsDeleted = 1,
            DeletedBy = @UserId,
            DeletedAt = GETDATE()
        WHERE SubjectID = @SubjectID AND SchoolID = @SchoolID;
        
        SELECT 'SUCCESS' AS Status, 'Subject deleted successfully' AS Message;
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO
