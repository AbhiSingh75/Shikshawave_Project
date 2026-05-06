-- Update Proc_Timetable_GetView to include ClassID
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
        t.TimetableID, t.ClassID, t.AcademicYear, t.EffectiveFrom, t.EffectiveTo,
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
        ts.SlotID, ts.TimetableID, ts.DayOfWeek, ts.PeriodID, ts.RoomNumber, ts.Notes,
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

PRINT 'Stored procedure updated successfully';
