-- Procedure for Exam Master Operations (Add, Update, Delete)
CREATE OR ALTER PROCEDURE Proc_ExamMaster_Operations
    @Action NVARCHAR(10),
    @ExamID INT = NULL,
    @SchoolID INT,
    @ClassID INT = NULL,
    @ExamName NVARCHAR(100),
    @ExamType NVARCHAR(50) = NULL,
    @StartDate DATE,
    @EndDate DATE,
    @AcademicYearId INT,
    @IsActive BIT = 1,
    @UserId INT,
    @Status NVARCHAR(50) OUTPUT,
    @Message NVARCHAR(500) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF @Action = 'ADD'
        BEGIN
            IF EXISTS (SELECT 1 FROM ExamMaster WHERE SchoolID = @SchoolID AND (ClassID = @ClassID OR (ClassID IS NULL AND @ClassID IS NULL)) AND ExamName = @ExamName AND AcademicYearId = @AcademicYearId)
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Exam already exists.';
                RETURN;
            END
            IF @StartDate > @EndDate
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Start date cannot be after end date.';
                RETURN;
            END
            INSERT INTO ExamMaster (SchoolID, ClassID, ExamName, ExamType, StartDate, EndDate, AcademicYearId, IsActive, CreatedBy, CreatedOn)
            VALUES (@SchoolID, @ClassID, @ExamName, @ExamType, @StartDate, @EndDate, @AcademicYearId, @IsActive, @UserId, GETDATE());
            SET @Status = 'SUCCESS';
            SET @Message = 'Exam added successfully.';
        END
        ELSE IF @Action = 'UPDATE'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM ExamMaster WHERE ExamID = @ExamID)
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Exam not found.';
                RETURN;
            END
            IF EXISTS (SELECT 1 FROM ExamMaster WHERE SchoolID = @SchoolID AND (ClassID = @ClassID OR (ClassID IS NULL AND @ClassID IS NULL)) AND ExamName = @ExamName AND AcademicYearId = @AcademicYearId AND ExamID != @ExamID)
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Exam already exists.';
                RETURN;
            END
            IF @StartDate > @EndDate
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Start date cannot be after end date.';
                RETURN;
            END
            UPDATE ExamMaster SET ClassID = @ClassID, ExamName = @ExamName, ExamType = @ExamType, StartDate = @StartDate, EndDate = @EndDate, AcademicYearId = @AcademicYearId, IsActive = @IsActive, UpdatedBy = @UserId, UpdatedOn = GETDATE() WHERE ExamID = @ExamID;
            SET @Status = 'SUCCESS';
            SET @Message = 'Exam updated successfully.';
        END
        ELSE IF @Action = 'DELETE'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM ExamMaster WHERE ExamID = @ExamID)
            BEGIN
                SET @Status = 'ERROR';
                SET @Message = 'Exam not found.';
                RETURN;
            END
            DELETE FROM ExamMaster WHERE ExamID = @ExamID;
            SET @Status = 'SUCCESS';
            SET @Message = 'Exam deleted successfully.';
        END
        ELSE
        BEGIN
            SET @Status = 'ERROR';
            SET @Message = 'Invalid action.';
        END
    END TRY
    BEGIN CATCH
        SET @Status = 'ERROR';
        SET @Message = ERROR_MESSAGE();
    END CATCH
END
GO

CREATE OR ALTER PROCEDURE Proc_ExamMaster_Get
    @SchoolID INT,
    @ClassID INT = NULL,
    @AcademicYearId INT = NULL,
    @SearchTerm NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SELECT e.ExamID, e.SchoolID, e.ClassID, ISNULL(c.ClassName, 'All Classes') AS ClassName, e.ExamName, e.ExamType, e.StartDate, e.EndDate, e.AcademicYearId, ay.AcademicYear, e.IsActive, e.CreatedBy, e.CreatedOn, e.UpdatedBy, e.UpdatedOn
    FROM ExamMaster e
    LEFT JOIN ClassMaster c ON e.ClassID = c.ClassID
    LEFT JOIN AcademicYear ay ON e.AcademicYearId = ay.AcademicYearID
    WHERE e.SchoolID = @SchoolID
    AND (@ClassID IS NULL OR e.ClassID = @ClassID OR e.ClassID IS NULL)
    AND (@AcademicYearId IS NULL OR e.AcademicYearId = @AcademicYearId)
    AND (@SearchTerm IS NULL OR e.ExamName LIKE '%' + @SearchTerm + '%' OR e.ExamType LIKE '%' + @SearchTerm + '%')
    ORDER BY e.AcademicYearId DESC, e.StartDate DESC;
END
GO
