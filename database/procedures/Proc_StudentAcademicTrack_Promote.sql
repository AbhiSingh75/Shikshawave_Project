-- Promote Students to Next Class/Section
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_Promote
    @SchoolID INT,
    @CurrentAcademicYearID INT,
    @NewAcademicYearID INT,
    @StudentIDs NVARCHAR(MAX), -- Comma-separated student IDs
    @PromotedToClassID INT,
    @PromotedToSectionID INT,
    @PromotionDate DATE,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Create temp table for student IDs
        CREATE TABLE #Students (StudentID INT);
        
        INSERT INTO #Students (StudentID)
        SELECT CAST(value AS INT)
        FROM STRING_SPLIT(@StudentIDs, ',')
        WHERE RTRIM(value) <> '';

        -- Mark current tracks as promoted and not current
        UPDATE sat
        SET 
            Status = 'Promoted',
            PromotedToClassID = @PromotedToClassID,
            PromotedToSectionID = @PromotedToSectionID,
            PromotionDate = @PromotionDate,
            IsCurrent = 0,
            EndDate = @PromotionDate,
            UpdatedBy = @UserID,
            UpdatedAt = GETDATE()
        FROM StudentAcademicTrack sat
        INNER JOIN #Students s ON sat.StudentID = s.StudentID
        WHERE sat.SchoolID = @SchoolID
            AND sat.AcademicYearID = @CurrentAcademicYearID
            AND sat.IsCurrent = 1
            AND sat.IsDeleted = 0;

        -- Create new tracks for promoted students
        INSERT INTO StudentAcademicTrack (
            SchoolID, StudentID, AcademicYearID, ClassID, SectionID,
            Status, IsCurrent, StartDate, CreatedBy, CreatedAt, IsDeleted
        )
        SELECT 
            @SchoolID,
            s.StudentID,
            @NewAcademicYearID,
            @PromotedToClassID,
            @PromotedToSectionID,
            'Active',
            1,
            @PromotionDate,
            @UserID,
            GETDATE(),
            0
        FROM #Students s;

        DROP TABLE #Students;

        SELECT 'SUCCESS' AS Status, 'Students promoted successfully' AS Message;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO
