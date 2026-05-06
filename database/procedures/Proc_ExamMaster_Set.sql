-- Stored Procedure: Proc_ExamMaster_Set
-- Purpose: Insert or Update Exam Master records
CREATE OR ALTER PROCEDURE Proc_ExamMaster_Set
    @ExamID INT = NULL,
    @SchoolID INT,
    @ClassID INT = NULL,
    @ExamName NVARCHAR(100),
    @ExamType NVARCHAR(50) = NULL,
    @StartDate DATE,
    @EndDate DATE,
    @AcademicYearId INT,
    @IsActive BIT = 1,
    @IsPublish BIT = 0,
    @UserId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        IF @ExamID IS NULL OR @ExamID = 0
        BEGIN
            -- Insert new exam
            INSERT INTO ExamMaster (
                SchoolID, ClassID, ExamName, ExamType, StartDate, EndDate, 
                AcademicYearId, IsActive, IsPublish, CreatedBy, CreatedOn
            )
            VALUES (
                @SchoolID, @ClassID, @ExamName, @ExamType, @StartDate, @EndDate,
                @AcademicYearId, @IsActive, @IsPublish, @UserId, GETDATE()
            );
            
            SELECT SCOPE_IDENTITY() AS ExamID, 'SUCCESS' AS Status, 'Exam created successfully' AS Message;
        END
        ELSE
        BEGIN
            -- Update existing exam
            UPDATE ExamMaster 
            SET 
                ClassID = @ClassID,
                ExamName = @ExamName,
                ExamType = @ExamType,
                StartDate = @StartDate,
                EndDate = @EndDate,
                AcademicYearId = @AcademicYearId,
                IsActive = @IsActive,
                IsPublish = @IsPublish,
                UpdatedBy = @UserId,
                UpdatedOn = GETDATE()
            WHERE ExamID = @ExamID;
            
            SELECT @ExamID AS ExamID, 'SUCCESS' AS Status, 'Exam updated successfully' AS Message;
        END
    END TRY
    BEGIN CATCH
        SELECT 0 AS ExamID, 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO
