CREATE OR ALTER PROCEDURE Proc_TermsConditions_Save
    @Id INT = NULL,
    @SchoolId INT,
    @Title NVARCHAR(200),
    @Description NVARCHAR(MAX),
    @Category NVARCHAR(100) = NULL,
    @IsActive BIT,
    @DisplayOrder INT,
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Id IS NULL OR @Id = 0
    BEGIN
        INSERT INTO TermsConditions (SchoolId, Title, Description, Category, IsActive, DisplayOrder, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
        VALUES (@SchoolId, @Title, @Description, @Category, @IsActive, @DisplayOrder, @UserId, GETDATE(), @UserId, GETDATE());
        
        SELECT 'SUCCESS' AS Status, 'Terms & Conditions added successfully' AS Message, SCOPE_IDENTITY() AS Id;
    END
    ELSE
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
END
GO
