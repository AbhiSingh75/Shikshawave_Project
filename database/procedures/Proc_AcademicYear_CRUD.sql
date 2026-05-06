CREATE OR ALTER PROCEDURE Proc_AcademicYear_CRUD
    @Action NVARCHAR(10),
    @SchoolId INT,
    @AcademicYearID INT = NULL,
    @AcademicYear NVARCHAR(10) = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @IsCurrent BIT = NULL,
    @IsActive BIT = NULL,
    @UserId INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'LIST'
    BEGIN
        SELECT AcademicYearID, SchoolID, AcademicYear, StartDate, EndDate, IsCurrent, IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
        FROM AcademicYear
        WHERE SchoolID = @SchoolId
        ORDER BY StartDate DESC;
    END
    
    ELSE IF @Action = 'ADD'
    BEGIN
        -- If IsCurrent is set to 1, update all other records to 0
        IF @IsCurrent = 1
        BEGIN
            UPDATE AcademicYear SET IsCurrent = 0 WHERE SchoolID = @SchoolId;
        END
        
        INSERT INTO AcademicYear (SchoolID, AcademicYear, StartDate, EndDate, IsCurrent, IsActive, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
        VALUES (@SchoolId, @AcademicYear, @StartDate, @EndDate, @IsCurrent, @IsActive, @UserId, GETDATE(), @UserId, GETDATE());
        
        SELECT 'SUCCESS' AS Status, 'Academic Year added successfully' AS Message, SCOPE_IDENTITY() AS Id;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        -- If IsCurrent is set to 1, update all other records to 0
        IF @IsCurrent = 1
        BEGIN
            UPDATE AcademicYear SET IsCurrent = 0 WHERE SchoolID = @SchoolId AND AcademicYearID != @AcademicYearID;
        END
        
        UPDATE AcademicYear
        SET AcademicYear = @AcademicYear,
            StartDate = @StartDate,
            EndDate = @EndDate,
            IsCurrent = @IsCurrent,
            IsActive = @IsActive,
            UpdatedBy = @UserId,
            UpdatedAt = GETDATE()
        WHERE AcademicYearID = @AcademicYearID AND SchoolID = @SchoolId;
        
        SELECT 'SUCCESS' AS Status, 'Academic Year updated successfully' AS Message, @AcademicYearID AS Id;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        DELETE FROM AcademicYear
        WHERE AcademicYearID = @AcademicYearID AND SchoolID = @SchoolId;
        
        SELECT 'SUCCESS' AS Status, 'Academic Year deleted successfully' AS Message;
    END
END
