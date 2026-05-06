-- =====================================================
-- COMPLETE CLASS TIMETABLE SYSTEM INSTALLATION
-- Indian School Standards
-- =====================================================

PRINT '========================================';
PRINT 'Starting Installation...';
PRINT '========================================';

-- =====================================================
-- STEP 1: CREATE TABLES
-- =====================================================
PRINT 'Step 1: Creating tables...';

IF OBJECT_ID('TimetableSlot', 'U') IS NOT NULL DROP TABLE TimetableSlot;
IF OBJECT_ID('TimetableMaster', 'U') IS NOT NULL DROP TABLE TimetableMaster;
IF OBJECT_ID('PeriodMaster', 'U') IS NOT NULL DROP TABLE PeriodMaster;

CREATE TABLE PeriodMaster (
    PeriodID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL FOREIGN KEY REFERENCES SchoolMaster(SchoolID),
    PeriodName NVARCHAR(50) NOT NULL,
    PeriodType NVARCHAR(20) NOT NULL DEFAULT 'Class',
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    DisplayOrder INT NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

CREATE TABLE TimetableMaster (
    TimetableID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL FOREIGN KEY REFERENCES SchoolMaster(SchoolID),
    ClassID INT NOT NULL FOREIGN KEY REFERENCES ClassMaster(ClassID),
    SectionID INT FOREIGN KEY REFERENCES SectionMaster(SectionID),
    AcademicYear NVARCHAR(20) NOT NULL,
    EffectiveFrom DATE NOT NULL,
    EffectiveTo DATE,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

CREATE TABLE TimetableSlot (
    SlotID INT IDENTITY(1,1) PRIMARY KEY,
    TimetableID INT NOT NULL FOREIGN KEY REFERENCES TimetableMaster(TimetableID),
    DayOfWeek INT NOT NULL,
    PeriodID INT NOT NULL FOREIGN KEY REFERENCES PeriodMaster(PeriodID),
    SubjectID INT FOREIGN KEY REFERENCES SubjectMaster(SubjectID),
    TeacherID INT FOREIGN KEY REFERENCES UserMaster(UserID),
    RoomNumber NVARCHAR(20),
    Notes NVARCHAR(255),
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

CREATE INDEX IX_PeriodMaster_School ON PeriodMaster(SchoolID, IsDeleted, IsActive);
CREATE INDEX IX_TimetableMaster_Class ON TimetableMaster(ClassID, SectionID, IsActive, IsDeleted);
CREATE INDEX IX_TimetableSlot_Timetable ON TimetableSlot(TimetableID, DayOfWeek, IsDeleted);
CREATE INDEX IX_TimetableSlot_Teacher ON TimetableSlot(TeacherID, DayOfWeek, IsDeleted);

PRINT '✓ Tables created successfully';
GO

-- =====================================================
-- STEP 2: CREATE STORED PROCEDURES
-- =====================================================
PRINT 'Step 2: Creating stored procedures...';

IF OBJECT_ID('Proc_PeriodMaster_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_PeriodMaster_Manage;
GO
CREATE PROCEDURE Proc_PeriodMaster_Manage
    @Action NVARCHAR(10), @PeriodID INT = NULL, @SchoolID INT, @PeriodName NVARCHAR(50) = NULL,
    @PeriodType NVARCHAR(20) = 'Class', @StartTime TIME = NULL, @EndTime TIME = NULL,
    @DisplayOrder INT = NULL, @IsActive BIT = 1, @UserID INT
AS BEGIN SET NOCOUNT ON;
    IF @Action = 'INSERT' BEGIN
        INSERT INTO PeriodMaster (SchoolID, PeriodName, PeriodType, StartTime, EndTime, DisplayOrder, IsActive, CreatedBy)
        VALUES (@SchoolID, @PeriodName, @PeriodType, @StartTime, @EndTime, @DisplayOrder, @IsActive, @UserID);
        SELECT SCOPE_IDENTITY() AS PeriodID, 'Period created' AS Message;
    END ELSE IF @Action = 'UPDATE' BEGIN
        UPDATE PeriodMaster SET PeriodName=@PeriodName, PeriodType=@PeriodType, StartTime=@StartTime, 
            EndTime=@EndTime, DisplayOrder=@DisplayOrder, IsActive=@IsActive, UpdatedBy=@UserID, UpdatedAt=GETDATE()
        WHERE PeriodID=@PeriodID AND SchoolID=@SchoolID AND IsDeleted=0;
        SELECT @PeriodID AS PeriodID, 'Period updated' AS Message;
    END ELSE IF @Action = 'DELETE' BEGIN
        UPDATE PeriodMaster SET IsDeleted=1, UpdatedBy=@UserID, UpdatedAt=GETDATE()
        WHERE PeriodID=@PeriodID AND SchoolID=@SchoolID;
        SELECT 'Period deleted' AS Message;
    END ELSE IF @Action = 'GET'
        SELECT * FROM PeriodMaster WHERE PeriodID=@PeriodID AND SchoolID=@SchoolID AND IsDeleted=0;
    ELSE IF @Action = 'LIST'
        SELECT * FROM PeriodMaster WHERE SchoolID=@SchoolID AND IsDeleted=0 ORDER BY DisplayOrder, StartTime;
END
GO

IF OBJECT_ID('Proc_Timetable_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_Timetable_Manage;
GO
CREATE PROCEDURE Proc_Timetable_Manage
    @Action NVARCHAR(10), @TimetableID INT = NULL, @SchoolID INT, @ClassID INT = NULL,
    @SectionID INT = NULL, @AcademicYear NVARCHAR(20) = NULL, @EffectiveFrom DATE = NULL,
    @EffectiveTo DATE = NULL, @IsActive BIT = 1, @UserID INT
AS BEGIN SET NOCOUNT ON;
    IF @Action = 'CREATE' BEGIN
        IF EXISTS (SELECT 1 FROM TimetableMaster WHERE SchoolID=@SchoolID AND ClassID=@ClassID 
            AND (@SectionID IS NULL OR SectionID=@SectionID) AND IsActive=1 AND IsDeleted=0) BEGIN
            SELECT -1 AS TimetableID, 'Active timetable exists' AS Message; RETURN;
        END
        INSERT INTO TimetableMaster (SchoolID, ClassID, SectionID, AcademicYear, EffectiveFrom, EffectiveTo, IsActive, CreatedBy)
        VALUES (@SchoolID, @ClassID, @SectionID, @AcademicYear, @EffectiveFrom, @EffectiveTo, @IsActive, @UserID);
        SELECT SCOPE_IDENTITY() AS TimetableID, 'Timetable created' AS Message;
    END ELSE IF @Action = 'UPDATE' BEGIN
        UPDATE TimetableMaster SET AcademicYear=@AcademicYear, EffectiveFrom=@EffectiveFrom, 
            EffectiveTo=@EffectiveTo, IsActive=@IsActive, UpdatedBy=@UserID, UpdatedAt=GETDATE()
        WHERE TimetableID=@TimetableID AND SchoolID=@SchoolID AND IsDeleted=0;
        SELECT @TimetableID AS TimetableID, 'Timetable updated' AS Message;
    END ELSE IF @Action = 'DELETE' BEGIN
        UPDATE TimetableMaster SET IsDeleted=1, UpdatedBy=@UserID, UpdatedAt=GETDATE()
        WHERE TimetableID=@TimetableID AND SchoolID=@SchoolID;
        UPDATE TimetableSlot SET IsDeleted=1, UpdatedBy=@UserID, UpdatedAt=GETDATE() WHERE TimetableID=@TimetableID;
        SELECT 'Timetable deleted' AS Message;
    END ELSE IF @Action = 'GET'
        SELECT t.*, c.ClassName, s.SectionName FROM TimetableMaster t
        INNER JOIN ClassMaster c ON t.ClassID=c.ClassID LEFT JOIN SectionMaster s ON t.SectionID=s.SectionID
        WHERE t.TimetableID=@TimetableID AND t.SchoolID=@SchoolID AND t.IsDeleted=0;
    ELSE IF @Action = 'LIST'
        SELECT t.*, c.ClassName, s.SectionName FROM TimetableMaster t
        INNER JOIN ClassMaster c ON t.ClassID=c.ClassID LEFT JOIN SectionMaster s ON t.SectionID=s.SectionID
        WHERE t.SchoolID=@SchoolID AND t.IsDeleted=0 ORDER BY c.ClassName, s.SectionName;
END
GO

IF OBJECT_ID('Proc_TimetableSlot_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_TimetableSlot_Manage;
GO
CREATE PROCEDURE Proc_TimetableSlot_Manage
    @Action NVARCHAR(10), @SlotID INT = NULL, @TimetableID INT, @DayOfWeek INT = NULL,
    @PeriodID INT = NULL, @SubjectID INT = NULL, @TeacherID INT = NULL,
    @RoomNumber NVARCHAR(20) = NULL, @Notes NVARCHAR(255) = NULL, @UserID INT
AS BEGIN SET NOCOUNT ON;
    IF @Action = 'SAVE' BEGIN
        IF EXISTS (SELECT 1 FROM TimetableSlot WHERE SlotID=@SlotID AND IsDeleted=0) BEGIN
            UPDATE TimetableSlot SET SubjectID=@SubjectID, TeacherID=@TeacherID, RoomNumber=@RoomNumber,
                Notes=@Notes, UpdatedBy=@UserID, UpdatedAt=GETDATE() WHERE SlotID=@SlotID;
            SELECT @SlotID AS SlotID, 'Slot updated' AS Message;
        END ELSE BEGIN
            INSERT INTO TimetableSlot (TimetableID, DayOfWeek, PeriodID, SubjectID, TeacherID, RoomNumber, Notes, CreatedBy)
            VALUES (@TimetableID, @DayOfWeek, @PeriodID, @SubjectID, @TeacherID, @RoomNumber, @Notes, @UserID);
            SELECT SCOPE_IDENTITY() AS SlotID, 'Slot created' AS Message;
        END
    END ELSE IF @Action = 'DELETE' BEGIN
        UPDATE TimetableSlot SET IsDeleted=1, UpdatedBy=@UserID, UpdatedAt=GETDATE() WHERE SlotID=@SlotID;
        SELECT 'Slot deleted' AS Message;
    END ELSE IF @Action = 'GET'
        SELECT ts.*, p.PeriodName, p.StartTime, p.EndTime, p.PeriodType, sm.SubjectName, u.UserName AS TeacherName
        FROM TimetableSlot ts INNER JOIN PeriodMaster p ON ts.PeriodID=p.PeriodID
        LEFT JOIN SubjectMaster sm ON ts.SubjectID=sm.SubjectID LEFT JOIN UserMaster u ON ts.TeacherID=u.UserID
        WHERE ts.TimetableID=@TimetableID AND ts.IsDeleted=0 ORDER BY ts.DayOfWeek, p.DisplayOrder;
END
GO

IF OBJECT_ID('Proc_Timetable_GetView', 'P') IS NOT NULL DROP PROCEDURE Proc_Timetable_GetView;
GO
CREATE PROCEDURE Proc_Timetable_GetView
    @TimetableID INT = NULL, @SchoolID INT, @ClassID INT = NULL, @SectionID INT = NULL
AS BEGIN SET NOCOUNT ON;
    IF @TimetableID IS NULL
        SELECT @TimetableID=TimetableID FROM TimetableMaster
        WHERE SchoolID=@SchoolID AND ClassID=@ClassID AND (@SectionID IS NULL OR SectionID=@SectionID)
        AND IsActive=1 AND IsDeleted=0;
    
    SELECT t.TimetableID, t.AcademicYear, t.EffectiveFrom, t.EffectiveTo, c.ClassName, s.SectionName, t.ClassID
    FROM TimetableMaster t INNER JOIN ClassMaster c ON t.ClassID=c.ClassID
    LEFT JOIN SectionMaster s ON t.SectionID=s.SectionID WHERE t.TimetableID=@TimetableID;
    
    SELECT * FROM PeriodMaster WHERE SchoolID=@SchoolID AND IsDeleted=0 ORDER BY DisplayOrder, StartTime;
    
    SELECT ts.SlotID, ts.DayOfWeek, ts.PeriodID, ts.RoomNumber, ts.Notes,
        p.PeriodName, p.StartTime, p.EndTime, p.PeriodType,
        sm.SubjectID, sm.SubjectName, sm.SubjectCode, u.UserID AS TeacherID, u.UserName AS TeacherName
    FROM TimetableSlot ts INNER JOIN PeriodMaster p ON ts.PeriodID=p.PeriodID
    LEFT JOIN SubjectMaster sm ON ts.SubjectID=sm.SubjectID LEFT JOIN UserMaster u ON ts.TeacherID=u.UserID
    WHERE ts.TimetableID=@TimetableID AND ts.IsDeleted=0 ORDER BY ts.DayOfWeek, p.DisplayOrder;
END
GO

PRINT '✓ Stored procedures created';
GO

-- =====================================================
-- STEP 3: UPDATE MENU ITEMS
-- =====================================================
PRINT 'Step 3: Updating menu items...';

UPDATE MenuMaster SET MenuURL='/timetable/management/?tab=create', Icon='fa fa-plus', UpdatedAt=GETDATE() WHERE MenuID=29;
UPDATE MenuMaster SET MenuURL='/timetable/management/?tab=view', Icon='fa fa-eye', UpdatedAt=GETDATE() WHERE MenuID=30;

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID=29 AND ProfileID=1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (1, 29, 1, 1, 1, 1, GETDATE());
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID=29 AND ProfileID=2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (2, 29, 1, 1, 1, 1, GETDATE());
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID=30 AND ProfileID=1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (1, 30, 1, 1, 1, 1, GETDATE());
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID=30 AND ProfileID=2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (2, 30, 1, 1, 1, 1, GETDATE());
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID=30 AND ProfileID=3)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (3, 30, 1, 0, 0, 0, GETDATE());

PRINT '✓ Menu items updated';
GO

PRINT '========================================';
PRINT '✓ INSTALLATION COMPLETED SUCCESSFULLY!';
PRINT '========================================';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Restart Django server';
PRINT '2. Navigate to: Timetable → Create Timetable';
PRINT '3. Setup periods first (Period Setup tab)';
PRINT '4. Create timetables (Timetables tab)';
PRINT '5. Fill slots (View Timetable tab)';
PRINT '';
PRINT 'Menu URLs:';
PRINT '- Create: /timetable/management/?tab=create';
PRINT '- View: /timetable/management/?tab=view';
PRINT '========================================';
GO
