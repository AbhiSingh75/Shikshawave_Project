-- =============================================
-- Student Academic Track System Installation
-- =============================================
-- This script installs the complete Student Academic Track system
-- to maintain academic history, class/section tracking, and performance

PRINT '========================================';
PRINT 'Installing Student Academic Track System';
PRINT '========================================';

-- Step 1: Create Table
PRINT 'Step 1: Creating StudentAcademicTrack table...';

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[StudentAcademicTrack]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[StudentAcademicTrack] (
        [TrackID] INT IDENTITY(1,1) PRIMARY KEY,
        [SchoolID] INT NOT NULL,
        [StudentID] INT NOT NULL,
        [AcademicYearID] INT NOT NULL,
        [ClassID] INT NOT NULL,
        [SectionID] INT NOT NULL,
        [RollNumber] NVARCHAR(20) NULL,
        [Status] NVARCHAR(20) NOT NULL DEFAULT 'Active',
        [AttendancePercentage] DECIMAL(5,2) NULL,
        [OverallGrade] NVARCHAR(5) NULL,
        [OverallPercentage] DECIMAL(5,2) NULL,
        [Rank] INT NULL,
        [Remarks] NVARCHAR(500) NULL,
        [PromotedToClassID] INT NULL,
        [PromotedToSectionID] INT NULL,
        [PromotionDate] DATE NULL,
        [IsCurrent] BIT NOT NULL DEFAULT 1,
        [StartDate] DATE NOT NULL,
        [EndDate] DATE NULL,
        [CreatedBy] INT NULL,
        [CreatedAt] DATETIME DEFAULT GETDATE(),
        [UpdatedBy] INT NULL,
        [UpdatedAt] DATETIME NULL,
        [IsDeleted] BIT DEFAULT 0,
        
        CONSTRAINT FK_StudentAcademicTrack_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_StudentAcademicTrack_Student FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
        CONSTRAINT FK_StudentAcademicTrack_AcademicYear FOREIGN KEY (AcademicYearID) REFERENCES AcademicYear(AcademicYearID),
        CONSTRAINT FK_StudentAcademicTrack_Class FOREIGN KEY (ClassID) REFERENCES ClassMaster(ClassID),
        CONSTRAINT FK_StudentAcademicTrack_Section FOREIGN KEY (SectionID) REFERENCES SectionMaster(SectionID),
        CONSTRAINT FK_StudentAcademicTrack_PromotedClass FOREIGN KEY (PromotedToClassID) REFERENCES ClassMaster(ClassID),
        CONSTRAINT FK_StudentAcademicTrack_PromotedSection FOREIGN KEY (PromotedToSectionID) REFERENCES SectionMaster(SectionID),
        CONSTRAINT FK_StudentAcademicTrack_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_StudentAcademicTrack_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID)
    );

    CREATE INDEX IX_StudentAcademicTrack_Student ON StudentAcademicTrack(StudentID, IsCurrent);
    CREATE INDEX IX_StudentAcademicTrack_School_Year ON StudentAcademicTrack(SchoolID, AcademicYearID);
    CREATE INDEX IX_StudentAcademicTrack_Class_Section ON StudentAcademicTrack(ClassID, SectionID, IsCurrent);
    CREATE INDEX IX_StudentAcademicTrack_Status ON StudentAcademicTrack(Status, IsCurrent);

    PRINT '  ✓ StudentAcademicTrack table created';
END
ELSE
BEGIN
    PRINT '  - StudentAcademicTrack table already exists';
END
GO

-- Step 2: Create Stored Procedures
PRINT 'Step 2: Creating stored procedures...';

-- Proc_StudentAcademicTrack_GetByStudent
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_GetByStudent
    @StudentID INT,
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        sat.TrackID, sat.StudentID, s.StudentCode, s.FullName,
        sat.AcademicYearID, ay.AcademicYear,
        sat.ClassID, c.ClassName,
        sat.SectionID, sec.SectionName,
        sat.RollNumber, sat.Status, sat.AttendancePercentage,
        sat.OverallGrade, sat.OverallPercentage, sat.Rank, sat.Remarks,
        sat.PromotedToClassID, pc.ClassName AS PromotedToClassName,
        sat.PromotedToSectionID, ps.SectionName AS PromotedToSectionName,
        sat.PromotionDate, sat.IsCurrent, sat.StartDate, sat.EndDate, sat.CreatedAt
    FROM StudentAcademicTrack sat
    INNER JOIN Student s ON sat.StudentID = s.StudentID
    INNER JOIN AcademicYear ay ON sat.AcademicYearID = ay.AcademicYearID
    INNER JOIN ClassMaster c ON sat.ClassID = c.ClassID
    INNER JOIN SectionMaster sec ON sat.SectionID = sec.SectionID
    LEFT JOIN ClassMaster pc ON sat.PromotedToClassID = pc.ClassID
    LEFT JOIN SectionMaster ps ON sat.PromotedToSectionID = ps.SectionID
    WHERE sat.StudentID = @StudentID AND sat.SchoolID = @SchoolID AND sat.IsDeleted = 0
    ORDER BY ay.StartDate DESC, sat.CreatedAt DESC;
END
GO
PRINT '  ✓ Proc_StudentAcademicTrack_GetByStudent created';

-- Proc_StudentAcademicTrack_GetByClass
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_GetByClass
    @SchoolID INT,
    @AcademicYearID INT = NULL,
    @ClassID INT = NULL,
    @SectionID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;

    SELECT 
        sat.TrackID, sat.StudentID, s.StudentCode, s.FullName, s.Gender, s.DateOfBirth, s.ParentMobile,
        sat.AcademicYearID, ay.AcademicYear,
        sat.ClassID, c.ClassName,
        sat.SectionID, sec.SectionName,
        sat.RollNumber, sat.Status, sat.AttendancePercentage,
        sat.OverallGrade, sat.OverallPercentage, sat.Rank
    FROM StudentAcademicTrack sat
    INNER JOIN Student s ON sat.StudentID = s.StudentID
    INNER JOIN AcademicYear ay ON sat.AcademicYearID = ay.AcademicYearID
    INNER JOIN ClassMaster c ON sat.ClassID = c.ClassID
    INNER JOIN SectionMaster sec ON sat.SectionID = sec.SectionID
    WHERE sat.SchoolID = @SchoolID
        AND sat.IsCurrent = 1 AND sat.IsDeleted = 0 AND s.IsDeleted = 0
        AND (@AcademicYearID IS NULL OR sat.AcademicYearID = @AcademicYearID)
        AND (@ClassID IS NULL OR sat.ClassID = @ClassID)
        AND (@SectionID IS NULL OR sat.SectionID = @SectionID)
    ORDER BY c.ClassName, sec.SectionName, sat.RollNumber, s.FullName;
END
GO
PRINT '  ✓ Proc_StudentAcademicTrack_GetByClass created';

-- Proc_StudentAcademicTrack_Manage
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_Manage
    @Action NVARCHAR(10), @TrackID INT = NULL, @SchoolID INT, @StudentID INT,
    @AcademicYearID INT, @ClassID INT, @SectionID INT, @RollNumber NVARCHAR(20) = NULL,
    @Status NVARCHAR(20) = 'Active', @AttendancePercentage DECIMAL(5,2) = NULL,
    @OverallGrade NVARCHAR(5) = NULL, @OverallPercentage DECIMAL(5,2) = NULL,
    @Rank INT = NULL, @Remarks NVARCHAR(500) = NULL,
    @PromotedToClassID INT = NULL, @PromotedToSectionID INT = NULL,
    @PromotionDate DATE = NULL, @IsCurrent BIT = 1,
    @StartDate DATE, @EndDate DATE = NULL, @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF @Action = 'INSERT'
        BEGIN
            IF EXISTS (SELECT 1 FROM StudentAcademicTrack WHERE StudentID = @StudentID AND AcademicYearID = @AcademicYearID AND IsCurrent = 1 AND IsDeleted = 0)
            BEGIN
                SELECT 'ERROR' AS Status, 'Student already has an active track for this academic year' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            IF @IsCurrent = 1
                UPDATE StudentAcademicTrack SET IsCurrent = 0, UpdatedBy = @UserID, UpdatedAt = GETDATE()
                WHERE StudentID = @StudentID AND IsCurrent = 1 AND IsDeleted = 0;

            INSERT INTO StudentAcademicTrack (SchoolID, StudentID, AcademicYearID, ClassID, SectionID, RollNumber,
                Status, AttendancePercentage, OverallGrade, OverallPercentage, Rank, Remarks,
                PromotedToClassID, PromotedToSectionID, PromotionDate, IsCurrent, StartDate, EndDate, CreatedBy, CreatedAt, IsDeleted)
            VALUES (@SchoolID, @StudentID, @AcademicYearID, @ClassID, @SectionID, @RollNumber,
                @Status, @AttendancePercentage, @OverallGrade, @OverallPercentage, @Rank, @Remarks,
                @PromotedToClassID, @PromotedToSectionID, @PromotionDate, @IsCurrent, @StartDate, @EndDate, @UserID, GETDATE(), 0);

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

            IF @IsCurrent = 1
                UPDATE StudentAcademicTrack SET IsCurrent = 0, UpdatedBy = @UserID, UpdatedAt = GETDATE()
                WHERE StudentID = @StudentID AND TrackID != @TrackID AND IsCurrent = 1 AND IsDeleted = 0;

            UPDATE StudentAcademicTrack
            SET AcademicYearID = @AcademicYearID, ClassID = @ClassID, SectionID = @SectionID, RollNumber = @RollNumber,
                Status = @Status, AttendancePercentage = @AttendancePercentage, OverallGrade = @OverallGrade,
                OverallPercentage = @OverallPercentage, Rank = @Rank, Remarks = @Remarks,
                PromotedToClassID = @PromotedToClassID, PromotedToSectionID = @PromotedToSectionID,
                PromotionDate = @PromotionDate, IsCurrent = @IsCurrent, StartDate = @StartDate, EndDate = @EndDate,
                UpdatedBy = @UserID, UpdatedAt = GETDATE()
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

            UPDATE StudentAcademicTrack SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
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
PRINT '  ✓ Proc_StudentAcademicTrack_Manage created';

-- Proc_StudentAcademicTrack_Promote
CREATE OR ALTER PROCEDURE Proc_StudentAcademicTrack_Promote
    @SchoolID INT, @CurrentAcademicYearID INT, @NewAcademicYearID INT,
    @StudentIDs NVARCHAR(MAX), @PromotedToClassID INT, @PromotedToSectionID INT,
    @PromotionDate DATE, @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        CREATE TABLE #Students (StudentID INT);
        INSERT INTO #Students (StudentID)
        SELECT CAST(value AS INT) FROM STRING_SPLIT(@StudentIDs, ',') WHERE RTRIM(value) <> '';

        UPDATE sat SET Status = 'Promoted', PromotedToClassID = @PromotedToClassID,
            PromotedToSectionID = @PromotedToSectionID, PromotionDate = @PromotionDate,
            IsCurrent = 0, EndDate = @PromotionDate, UpdatedBy = @UserID, UpdatedAt = GETDATE()
        FROM StudentAcademicTrack sat
        INNER JOIN #Students s ON sat.StudentID = s.StudentID
        WHERE sat.SchoolID = @SchoolID AND sat.AcademicYearID = @CurrentAcademicYearID
            AND sat.IsCurrent = 1 AND sat.IsDeleted = 0;

        INSERT INTO StudentAcademicTrack (SchoolID, StudentID, AcademicYearID, ClassID, SectionID,
            Status, IsCurrent, StartDate, CreatedBy, CreatedAt, IsDeleted)
        SELECT @SchoolID, s.StudentID, @NewAcademicYearID, @PromotedToClassID, @PromotedToSectionID,
            'Active', 1, @PromotionDate, @UserID, GETDATE(), 0
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
PRINT '  ✓ Proc_StudentAcademicTrack_Promote created';

PRINT '';
PRINT '========================================';
PRINT '✓ Student Academic Track System Installed Successfully!';
PRINT '========================================';
PRINT '';
PRINT 'Created:';
PRINT '  - StudentAcademicTrack table';
PRINT '  - Proc_StudentAcademicTrack_GetByStudent';
PRINT '  - Proc_StudentAcademicTrack_GetByClass';
PRINT '  - Proc_StudentAcademicTrack_Manage';
PRINT '  - Proc_StudentAcademicTrack_Promote';
PRINT '';
GO
