CREATE OR ALTER PROCEDURE Proc_TermsConditions_List
    @SchoolId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        Id,
        SchoolId,
        Title,
        Description,
        Category,
        IsActive,
        DisplayOrder,
        CreatedBy,
        CreatedAt,
        UpdatedBy,
        UpdatedAt
    FROM TermsConditions
    WHERE SchoolId = @SchoolId
    ORDER BY DisplayOrder, Id;
END
GO
