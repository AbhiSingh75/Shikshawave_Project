CREATE OR ALTER PROCEDURE Proc_AdmissionInstructions_Save
    @InstructionID INT = NULL,
    @SchoolID INT,
    @InstructionTitle NVARCHAR(200),
    @InstructionText NVARCHAR(1000),
    @DisplayOrder INT,
    @IsActive BIT,
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @InstructionID IS NULL OR @InstructionID = 0
    BEGIN
        -- Insert
        INSERT INTO AdmissionInstructions (SchoolID, InstructionTitle, InstructionText, DisplayOrder, IsActive, CreatedBy, CreatedAt)
        VALUES (@SchoolID, @InstructionTitle, @InstructionText, @DisplayOrder, @IsActive, @CreatedBy, GETDATE());
        
        SELECT 'SUCCESS' AS Status, 'Instruction added successfully' AS Message;
    END
    ELSE
    BEGIN
        -- Update
        UPDATE AdmissionInstructions
        SET InstructionTitle = @InstructionTitle,
            InstructionText = @InstructionText,
            DisplayOrder = @DisplayOrder,
            IsActive = @IsActive,
            ModifiedBy = @CreatedBy,
            ModifiedAt = GETDATE()
        WHERE InstructionID = @InstructionID AND SchoolID = @SchoolID AND IsDeleted = 0;
        
        SELECT 'SUCCESS' AS Status, 'Instruction updated successfully' AS Message;
    END
END
GO
