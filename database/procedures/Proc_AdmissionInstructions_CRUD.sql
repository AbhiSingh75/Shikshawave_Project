CREATE OR ALTER PROCEDURE Proc_AdmissionInstructions_CRUD
    @Action NVARCHAR(10), -- 'LIST', 'ADD', 'UPDATE', 'DELETE'
    @SchoolID INT,
    @InstructionID INT = NULL,
    @InstructionTitle NVARCHAR(200) = NULL,
    @InstructionText NVARCHAR(1000) = NULL,
    @DisplayOrder INT = 0,
    @IsActive BIT = 1,
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'LIST'
    BEGIN
        SELECT 
            InstructionID,
            InstructionTitle,
            InstructionText,
            DisplayOrder,
            IsActive,
            CreatedAt
        FROM AdmissionInstructions
        WHERE SchoolID = @SchoolID AND IsDeleted = 0
        ORDER BY DisplayOrder, InstructionID;
    END
    
    ELSE IF @Action = 'ADD'
    BEGIN
        INSERT INTO AdmissionInstructions (SchoolID, InstructionTitle, InstructionText, DisplayOrder, IsActive, CreatedBy, CreatedAt)
        VALUES (@SchoolID, @InstructionTitle, @InstructionText, @DisplayOrder, @IsActive, @UserId, GETDATE());
        
        SELECT 'SUCCESS' AS Status, 'Instruction added successfully' AS Message;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE AdmissionInstructions
        SET InstructionTitle = @InstructionTitle,
            InstructionText = @InstructionText,
            DisplayOrder = @DisplayOrder,
            IsActive = @IsActive,
            ModifiedBy = @UserId,
            ModifiedAt = GETDATE()
        WHERE InstructionID = @InstructionID AND SchoolID = @SchoolID AND IsDeleted = 0;
        
        SELECT 'SUCCESS' AS Status, 'Instruction updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE AdmissionInstructions
        SET IsDeleted = 1,
            ModifiedBy = @UserId,
            ModifiedAt = GETDATE()
        WHERE InstructionID = @InstructionID AND SchoolID = @SchoolID;
        
        SELECT 'SUCCESS' AS Status, 'Instruction deleted successfully' AS Message;
    END
END
GO
