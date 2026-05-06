CREATE OR ALTER PROCEDURE Proc_AdmissionInstructions_Delete
    @InstructionID INT,
    @SchoolID INT,
    @ModifiedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE AdmissionInstructions
    SET IsDeleted = 1,
        ModifiedBy = @ModifiedBy,
        ModifiedAt = GETDATE()
    WHERE InstructionID = @InstructionID AND SchoolID = @SchoolID;
    
    SELECT 'SUCCESS' AS Status, 'Instruction deleted successfully' AS Message;
END
GO
