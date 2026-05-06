CREATE OR ALTER PROCEDURE Proc_AdmissionInstructions_List
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        InstructionID,
        SchoolID,
        InstructionTitle,
        InstructionText,
        DisplayOrder,
        IsActive,
        CreatedAt,
        IsDeleted
    FROM AdmissionInstructions
    WHERE SchoolID = @SchoolID AND IsDeleted = 0
    ORDER BY DisplayOrder, InstructionID;
END
GO
