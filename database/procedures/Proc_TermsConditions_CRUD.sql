CREATE OR ALTER PROCEDURE Proc_TermsConditions_CRUD
    @Action NVARCHAR(10),
    @SchoolId INT,
    @Id INT = NULL,
    @Title NVARCHAR(200) = NULL,
    @Description NVARCHAR(MAX) = NULL,
    @Category NVARCHAR(100) = NULL,
    @IsActive BIT = NULL,
    @DisplayOrder INT = NULL,
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'LIST'
    BEGIN
        SELECT Id, SchoolId, Title, Description, Category, IsActive, DisplayOrder, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
        FROM TermsConditions
        WHERE SchoolId = @SchoolId
        ORDER BY DisplayOrder, Id;
    END
    
    ELSE IF @Action = 'ADD'
    BEGIN
        INSERT INTO TermsConditions (SchoolId, Title, Description, Category, IsActive, DisplayOrder, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
        VALUES (@SchoolId, @Title, @Description, @Category, @IsActive, @DisplayOrder, @UserId, GETDATE(), @UserId, GETDATE());
        
        SELECT 'SUCCESS' AS Status, 'Terms & Conditions added successfully' AS Message, SCOPE_IDENTITY() AS Id;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE TermsConditions
        SET Title = @Title,
            Description = @Description,
            Category = @Category,
            IsActive = @IsActive,
            DisplayOrder = @DisplayOrder,
            UpdatedBy = @UserId,
            UpdatedAt = GETDATE()
        WHERE Id = @Id AND SchoolId = @SchoolId;
        
        SELECT 'SUCCESS' AS Status, 'Terms & Conditions updated successfully' AS Message, @Id AS Id;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        DELETE FROM TermsConditions
        WHERE Id = @Id AND SchoolId = @SchoolId;
        
        SELECT 'SUCCESS' AS Status, 'Terms & Conditions deleted successfully' AS Message;
    END
END
GO
