-- Manage Student Academic Track (INSERT/UPDATE/DELETE)
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_Manage
    @Action NVARCHAR(10),
    @TrackID INT = NULL,
    @SchoolID INT,
    @StudentID INT,
    @AcademicYearID INT,
    @ClassID INT,
    @SectionID INT,
    @RollNumber NVARCHAR(20) = NULL,
    @Status NVARCHAR(20) = 'Active',
    @AttendancePercentage DECIMAL(5,2) = NULL,
    @OverallGrade NVARCHAR(5) = NULL,
    @OverallPercentage DECIMAL(5,2) = NULL,
    @Rank INT = NULL,
    @Remarks NVARCHAR(500) = NULL,
    @PromotedToClassID INT = NULL,
    @PromotedToSectionID INT = NULL,
    @PromotionDate DATE = NULL,
    @IsCurrent BIT = 1,
    @StartDate DATE,
    @EndDate DATE = NULL,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF @Action = 'INSERT'
        BEGIN
            -- Check if student already has current track for same academic year
            IF EXISTS (
                SELECT 1 FROM StudentAcademicTrack 
                WHERE StudentID = @StudentID 
                    AND AcademicYearID = @AcademicYearID 
                    AND IsCurrent = 1 
                    AND IsDeleted = 0
            )
            BEGIN
                SELECT 'ERROR' AS Status, 'Student already has an active track for this academic year' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- Mark all previous tracks as not current if this is current
            IF @IsCurrent = 1
            BEGIN
                UPDATE StudentAcademicTrack 
                SET IsCurrent = 0, UpdatedBy = @UserID, UpdatedAt = GETDATE()
                WHERE StudentID = @StudentID AND IsCurrent = 1 AND IsDeleted = 0;
            END

            INSERT INTO StudentAcademicTrack (
                SchoolID, StudentID, AcademicYearID, ClassID, SectionID, RollNumber,
                Status, AttendancePercentage, OverallGrade, OverallPercentage, Rank,
                Remarks, PromotedToClassID, PromotedToSectionID, PromotionDate,
                IsCurrent, StartDate, EndDate, CreatedBy, CreatedAt, IsDeleted
            )
            VALUES (
                @SchoolID, @StudentID, @AcademicYearID, @ClassID, @SectionID, @RollNumber,
                @Status, @AttendancePercentage, @OverallGrade, @OverallPercentage, @Rank,
                @Remarks, @PromotedToClassID, @PromotedToSectionID, @PromotionDate,
                @IsCurrent, @StartDate, @EndDate, @UserID, GETDATE(), 0
            );

            SELECT 'SUCCESS' AS Status, 'Academic track created successfully' AS Message, SCOPE_IDENTITY() AS TrackID;
        END

        ELSE IF @Action = 'UPDATE'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM StudentAcademicTrack WHERE TrackID = @TrackID AND IsDeleted = 0)
            BEGIN
                SELECT 'ERROR' AS Status, 'Academic track not found' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- If setting as current, mark others as not current
            IF @IsCurrent = 1
            BEGIN
                UPDATE StudentAcademicTrack 
                SET IsCurrent = 0, UpdatedBy = @UserID, UpdatedAt = GETDATE()
                WHERE StudentID = @StudentID AND TrackID != @TrackID AND IsCurrent = 1 AND IsDeleted = 0;
            END

            UPDATE StudentAcademicTrack
            SET 
                AcademicYearID = @AcademicYearID,
                ClassID = @ClassID,
                SectionID = @SectionID,
                RollNumber = @RollNumber,
                Status = @Status,
                AttendancePercentage = @AttendancePercentage,
                OverallGrade = @OverallGrade,
                OverallPercentage = @OverallPercentage,
                Rank = @Rank,
                Remarks = @Remarks,
                PromotedToClassID = @PromotedToClassID,
                PromotedToSectionID = @PromotedToSectionID,
                PromotionDate = @PromotionDate,
                IsCurrent = @IsCurrent,
                StartDate = @StartDate,
                EndDate = @EndDate,
                UpdatedBy = @UserID,
                UpdatedAt = GETDATE()
            WHERE TrackID = @TrackID AND IsDeleted = 0;

            SELECT 'SUCCESS' AS Status, 'Academic track updated successfully' AS Message, @TrackID AS TrackID;
        END

        ELSE IF @Action = 'DELETE'
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM StudentAcademicTrack WHERE TrackID = @TrackID AND IsDeleted = 0)
            BEGIN
                SELECT 'ERROR' AS Status, 'Academic track not found' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            UPDATE StudentAcademicTrack
            SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
            WHERE TrackID = @TrackID;

            SELECT 'SUCCESS' AS Status, 'Academic track deleted successfully' AS Message;
        END

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 'ERROR' AS Status, ERROR_MESSAGE() AS Message;
    END CATCH
END
GO
