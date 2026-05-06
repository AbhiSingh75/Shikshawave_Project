-- Procedure to get monthly fee types based on class selection
CREATE OR ALTER PROCEDURE Proc_Monthly_Fee_Types_Get
    @SchoolID INT,
    @ClassID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        FeeTypeId,
        SchoolId,
        FeeTypeName,
        DefaultAmount,
        ClassId
    FROM FeeType_Master
    WHERE SchoolId = @SchoolID
      AND IsActive = 0
      AND ClassId = @ClassID
      AND ISNULL(IsDeleted, 0) = 0
    ORDER BY FeeTypeName;
END
GO
