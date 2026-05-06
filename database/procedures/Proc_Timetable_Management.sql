-- Stored Procedures for Class Timetable Management

-- 1. Manage Period Master
IF OBJECT_ID('Proc_PeriodMaster_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_PeriodMaster_Manage;
GO
CREATE PROCEDURE Proc_PeriodMaster_Manage
    @Action NVARCHAR(10), -- 'INSERT', 'UPDATE', 'DELETE', 'GET', 'LIST'
    @PeriodID INT = NULL,
    @SchoolID INT,
    @PeriodName NVARCHAR(50) = NULL,
    @PeriodType NVARCHAR(20) = 'Class',
    @StartTime TIME = NULL,
    @EndTime TIME = NULL,
    @DisplayOrder INT = NULL,
    @IsActive BIT = 1,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'INSERT'
    BEGIN
        INSERT INTO PeriodMaster (SchoolID, PeriodName, PeriodType, StartTime, EndTime, DisplayOrder, IsActive, CreatedBy)
        VALUES (@SchoolID, @PeriodName, @PeriodType, @StartTime, @EndTime, @DisplayOrder, @IsActive, @UserID);
        
        SELECT SCOPE_IDENTITY() AS PeriodID, 'Period created successfully' AS Message;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE PeriodMaster
        SET PeriodName = @PeriodName,
            PeriodType = @PeriodType,
            StartTime = @StartTime,
            EndTime = @EndTime,
            DisplayOrder = @DisplayOrder,
            IsActive = @IsActive,
            UpdatedBy = @UserID,
            UpdatedAt = GETDATE()
        WHERE PeriodID = @PeriodID AND SchoolID = @SchoolID AND IsDeleted = 0;
        
        SELECT @PeriodID AS PeriodID, 'Period updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE PeriodMaster
        SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
        WHERE PeriodID = @PeriodID AND SchoolID = @SchoolID;
        
        SELECT 'Period deleted successfully' AS Message;
    END
    
    ELSE IF @Action = 'GET'
    BEGIN
        SELECT * FROM PeriodMaster
        WHERE PeriodID = @PeriodID AND SchoolID = @SchoolID AND IsDeleted = 0;
    END
    
    ELSE IF @Action = 'LIST'
    BEGIN
        SELECT * FROM PeriodMaster
        WHERE SchoolID = @SchoolID AND IsDeleted = 0
        ORDER BY DisplayOrder, StartTime;
    END
END
GO

-- 2. Manage Timetable
IF OBJECT_ID('Proc_Timetable_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_Timetable_Manage;
GO
CREATE PROCEDURE Proc_Timetable_Manage
    @Action NVARCHAR(10), -- 'CREATE', 'UPDATE', 'DELETE', 'GET', 'LIST'
    @TimetableID INT = NULL,
    @SchoolID INT,
    @ClassID INT = NULL,
    @SectionID INT = NULL,
    @AcademicYear NVARCHAR(20) = NULL,
    @EffectiveFrom DATE = NULL,
    @EffectiveTo DATE = NULL,
    @IsActive BIT = 1,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'CREATE'
    BEGIN
        -- Check if active timetable exists for this class/section
        IF EXISTS (
            SELECT 1 FROM TimetableMaster
            WHERE SchoolID = @SchoolID AND ClassID = @ClassID 
            AND (@SectionID IS NULL OR SectionID = @SectionID)
            AND IsActive = 1 AND IsDeleted = 0
        )
        BEGIN
            SELECT -1 AS TimetableID, 'Active timetable already exists for this class/section' AS Message;
            RETURN;
        END
        
        INSERT INTO TimetableMaster (SchoolID, ClassID, SectionID, AcademicYear, EffectiveFrom, EffectiveTo, IsActive, CreatedBy)
        VALUES (@SchoolID, @ClassID, @SectionID, @AcademicYear, @EffectiveFrom, @EffectiveTo, @IsActive, @UserID);
        
        SELECT SCOPE_IDENTITY() AS TimetableID, 'Timetable created successfully' AS Message;
    END
    
    ELSE IF @Action = 'UPDATE'
    BEGIN
        UPDATE TimetableMaster
        SET AcademicYear = @AcademicYear,
            EffectiveFrom = @EffectiveFrom,
            EffectiveTo = @EffectiveTo,
            IsActive = @IsActive,
            UpdatedBy = @UserID,
            UpdatedAt = GETDATE()
        WHERE TimetableID = @TimetableID AND SchoolID = @SchoolID AND IsDeleted = 0;
        
        SELECT @TimetableID AS TimetableID, 'Timetable updated successfully' AS Message;
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE TimetableMaster
        SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
        WHERE TimetableID = @TimetableID AND SchoolID = @SchoolID;
        
        -- Also delete associated slots
        UPDATE TimetableSlot
        SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
        WHERE TimetableID = @TimetableID;
        
        SELECT 'Timetable deleted successfully' AS Message;
    END
    
    ELSE IF @Action = 'GET'
    BEGIN
        SELECT t.*, c.ClassName, s.SectionName
        FROM TimetableMaster t
        INNER JOIN ClassMaster c ON t.ClassID = c.ClassID
        LEFT JOIN SectionMaster s ON t.SectionID = s.SectionID
        WHERE t.TimetableID = @TimetableID AND t.SchoolID = @SchoolID AND t.IsDeleted = 0;
    END
    
    ELSE IF @Action = 'LIST'
    BEGIN
        SELECT t.*, c.ClassName, s.SectionName
        FROM TimetableMaster t
        INNER JOIN ClassMaster c ON t.ClassID = c.ClassID
        LEFT JOIN SectionMaster s ON t.SectionID = s.SectionID
        WHERE t.SchoolID = @SchoolID AND t.IsDeleted = 0
        ORDER BY c.ClassName, s.SectionName;
    END
END
GO

-- 3. Manage Timetable Slots
IF OBJECT_ID('Proc_TimetableSlot_Manage', 'P') IS NOT NULL DROP PROCEDURE Proc_TimetableSlot_Manage;
GO
CREATE PROCEDURE Proc_TimetableSlot_Manage
    @Action NVARCHAR(10), -- 'SAVE', 'DELETE', 'GET'
    @SlotID INT = NULL,
    @TimetableID INT,
    @DayOfWeek INT = NULL,
    @PeriodID INT = NULL,
    @SubjectID INT = NULL,
    @TeacherID INT = NULL,
    @RoomNumber NVARCHAR(20) = NULL,
    @Notes NVARCHAR(255) = NULL,
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @Action = 'SAVE'
    BEGIN
        -- Check if slot already exists for this day/period combination
        IF EXISTS (
            SELECT 1 FROM TimetableSlot 
            WHERE TimetableID = @TimetableID 
            AND DayOfWeek = @DayOfWeek 
            AND PeriodID = @PeriodID 
            AND IsDeleted = 0
            AND (@SlotID IS NULL OR SlotID != @SlotID)
        )
        BEGIN
            SELECT -1 AS SlotID, 'A slot already exists for this day and period' AS Message;
            RETURN;
        END
        
        -- Check if slot already exists
        IF EXISTS (SELECT 1 FROM TimetableSlot WHERE SlotID = @SlotID AND IsDeleted = 0)
        BEGIN
            -- Update existing slot
            UPDATE TimetableSlot
            SET SubjectID = @SubjectID,
                TeacherID = @TeacherID,
                RoomNumber = @RoomNumber,
                Notes = @Notes,
                UpdatedBy = @UserID,
                UpdatedAt = GETDATE()
            WHERE SlotID = @SlotID;
            
            SELECT @SlotID AS SlotID, 'Slot updated successfully' AS Message;
        END
        ELSE
        BEGIN
            -- Insert new slot
            INSERT INTO TimetableSlot (TimetableID, DayOfWeek, PeriodID, SubjectID, TeacherID, RoomNumber, Notes, CreatedBy)
            VALUES (@TimetableID, @DayOfWeek, @PeriodID, @SubjectID, @TeacherID, @RoomNumber, @Notes, @UserID);
            
            SELECT SCOPE_IDENTITY() AS SlotID, 'Slot created successfully' AS Message;
        END
    END
    
    ELSE IF @Action = 'DELETE'
    BEGIN
        UPDATE TimetableSlot
        SET IsDeleted = 1, UpdatedBy = @UserID, UpdatedAt = GETDATE()
        WHERE SlotID = @SlotID;
        
        SELECT 'Slot deleted successfully' AS Message;
    END
    
    ELSE IF @Action = 'GET'
    BEGIN
        SELECT 
            ts.*,
            p.PeriodName, p.StartTime, p.EndTime, p.PeriodType,
            sm.SubjectName,
            u.UserName AS TeacherName
        FROM TimetableSlot ts
        INNER JOIN PeriodMaster p ON ts.PeriodID = p.PeriodID
        LEFT JOIN SubjectMaster sm ON ts.SubjectID = sm.SubjectID
        LEFT JOIN UserMaster u ON ts.TeacherID = u.UserID
        WHERE ts.TimetableID = @TimetableID AND ts.IsDeleted = 0
        ORDER BY ts.DayOfWeek, p.DisplayOrder;
    END
END
GO

-- 4. Get Complete Timetable View
IF OBJECT_ID('Proc_Timetable_GetView', 'P') IS NOT NULL DROP PROCEDURE Proc_Timetable_GetView;
GO
CREATE PROCEDURE Proc_Timetable_GetView
    @TimetableID INT = NULL,
    @SchoolID INT,
    @ClassID INT = NULL,
    @SectionID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- If TimetableID not provided, get active timetable
    IF @TimetableID IS NULL
    BEGIN
        SELECT @TimetableID = TimetableID
        FROM TimetableMaster
        WHERE SchoolID = @SchoolID 
        AND ClassID = @ClassID
        AND (@SectionID IS NULL OR SectionID = @SectionID)
        AND IsActive = 1 AND IsDeleted = 0;
    END
    
    -- Get timetable details
    SELECT 
        t.TimetableID, t.AcademicYear, t.EffectiveFrom, t.EffectiveTo,
        c.ClassName, s.SectionName
    FROM TimetableMaster t
    INNER JOIN ClassMaster c ON t.ClassID = c.ClassID
    LEFT JOIN SectionMaster s ON t.SectionID = s.SectionID
    WHERE t.TimetableID = @TimetableID;
    
    -- Get all periods
    SELECT * FROM PeriodMaster
    WHERE SchoolID = @SchoolID AND IsDeleted = 0
    ORDER BY DisplayOrder, StartTime;
    
    -- Get all slots
    SELECT 
        ts.SlotID, ts.DayOfWeek, ts.PeriodID, ts.RoomNumber, ts.Notes,
        p.PeriodName, p.StartTime, p.EndTime, p.PeriodType,
        sm.SubjectID, sm.SubjectName, sm.SubjectCode,
        u.UserID AS TeacherID, u.UserName AS TeacherName
    FROM TimetableSlot ts
    INNER JOIN PeriodMaster p ON ts.PeriodID = p.PeriodID
    LEFT JOIN SubjectMaster sm ON ts.SubjectID = sm.SubjectID
    LEFT JOIN UserMaster u ON ts.TeacherID = u.UserID
    WHERE ts.TimetableID = @TimetableID AND ts.IsDeleted = 0
    ORDER BY ts.DayOfWeek, p.DisplayOrder;
END
GO

PRINT 'Timetable stored procedures created successfully';
