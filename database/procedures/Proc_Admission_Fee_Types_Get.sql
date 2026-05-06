-- Procedure to get admission fee types (not class-specific)
CREATE OR ALTER PROCEDURE Proc_Admission_Fee_Types_Get
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        FeeTypeId,
        SchoolId,
        FeeTypeName,
        DefaultAmount
    FROM FeeType_Master
    WHERE SchoolId = @SchoolID
      AND IsActive = 0
      AND ClassId IS NULL
      AND ISNULL(IsDeleted, 0) = 0
    ORDER BY FeeTypeName;
END
GO
