CREATE OR ALTER PROCEDURE Proc_Employee_Document_Update
    @EmployeeCode NVARCHAR(50),
    @SchoolID INT,
    @DocumentType NVARCHAR(100),
    @FileName NVARCHAR(255),
    @FileExtension NVARCHAR(10),
    @FileContent VARBINARY(MAX),
    @UpdatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @EmployeeID INT;
    DECLARE @ExistingDocID INT;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Get EmployeeID
        SELECT @EmployeeID = EmployeeID 
        FROM EmployeeMaster 
        WHERE EmployeeCode = @EmployeeCode AND SchoolID = @SchoolID;
        
        IF @EmployeeID IS NULL
        BEGIN
            SELECT 'error' AS Status, 'Employee not found' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Check if document exists
        SELECT @ExistingDocID = DocumentID 
        FROM EmployeeDocument 
        WHERE EmployeeID = @EmployeeID AND DocumentType = @DocumentType;
        
        IF @ExistingDocID IS NOT NULL
        BEGIN
            -- Update existing document
            UPDATE EmployeeDocument
            SET FilesName = @FileName,
                FileExtension = @FileExtension,
                FileContent = @FileContent,
                UploadedBy = @UpdatedBy,
                UploadedAt = GETDATE(),
                IsActive = 1,
                IsDeleted = 0
            WHERE DocumentID = @ExistingDocID;
            
            SELECT 'success' AS Status, 'Document updated successfully' AS Message;
        END
        ELSE
        BEGIN
            -- Insert new document
            INSERT INTO EmployeeDocument (EmployeeID, DocumentType, FilesName, FileExtension, FileContent, UploadedBy, UploadedAt, IsActive, IsDeleted)
            VALUES (@EmployeeID, @DocumentType, @FileName, @FileExtension, @FileContent, @UpdatedBy, GETDATE(), 1, 0);
            
            SELECT 'success' AS Status, 'Document uploaded successfully' AS Message;
        END
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'error' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
