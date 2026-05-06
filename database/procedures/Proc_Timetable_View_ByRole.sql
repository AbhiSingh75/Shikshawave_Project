CREATE OR ALTER PROCEDURE Proc_Timetable_View_ByRole
    @SchoolID INT,
    @UserID INT,
    @ProfileID INT,
    @ClassID INT = NULL,
    @TeacherID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
	DECLARE @profileName VARCHAR(100), @userCode VARCHAR(20), @studentid INT, @employeeId INT, @Student_classId INT
	
	SELECT @userCode = u.UserCode, @profileName = p.ProfileName 
	FROM UserMaster AS u
	INNER JOIN ProfileMaster AS p ON u.ProfileID = p.ProfileID
	WHERE u.UserID = @UserID

	SELECT @studentid = StudentID FROM Student WHERE StudentCode = @userCode
	SELECT @Student_classId = ClassID FROM StudentAcademicTrack WHERE StudentID = @studentid AND IsCurrent = 1
	SELECT @employeeId = EmployeeID FROM EmployeeMaster WHERE EmployeeCode = @userCode

    -- For School Admin: Get timetables with filters
    IF @profileName = 'School Admin'
    BEGIN
        IF @ClassID IS NOT NULL
        BEGIN
            SELECT 
                tm.TimetableID,
                tm.ClassID,
                cm.ClassName,
                tm.SectionID,
                sm.SectionName,
                tm.AcademicYear,
                tm.EffectiveFrom,
                tm.EffectiveTo,
                pm.PeriodID,
                pm.PeriodName,
                pm.PeriodType,
                pm.StartTime,
                pm.EndTime,
                pm.DisplayOrder,
                ts.SlotID,
                ts.DayOfWeek,
                ts.SubjectID,
                sub.SubjectName,
                ts.TeacherID,
                em.EmployeeName AS TeacherName,
                ts.RoomNumber,
                ts.Notes
            FROM TimetableSlot AS ts
            INNER JOIN TimetableMaster AS tm ON ts.TimetableID = tm.TimetableID
            INNER JOIN PeriodMaster AS pm ON pm.PeriodID = ts.PeriodID
            LEFT JOIN ClassMaster AS cm ON cm.ClassID = tm.ClassID
            LEFT JOIN SectionMaster AS sm ON sm.SectionID = tm.SectionID
            LEFT JOIN SubjectMaster AS sub ON sub.SubjectID = ts.SubjectID
            LEFT JOIN EmployeeMaster AS em ON em.EmployeeID = ts.TeacherID
            WHERE tm.SchoolID = @SchoolID AND tm.ClassID = @ClassID AND tm.IsDeleted = 0 AND ts.IsDeleted = 0
            ORDER BY tm.TimetableID, ts.DayOfWeek, pm.DisplayOrder;
        END
        ELSE IF @TeacherID IS NOT NULL
        BEGIN
            SELECT 
                tm.TimetableID,
                tm.ClassID,
                cm.ClassName,
                tm.SectionID,
                sm.SectionName,
                tm.AcademicYear,
                tm.EffectiveFrom,
                tm.EffectiveTo,
                pm.PeriodID,
                pm.PeriodName,
                pm.PeriodType,
                pm.StartTime,
                pm.EndTime,
                pm.DisplayOrder,
                ts.SlotID,
                ts.DayOfWeek,
                ts.SubjectID,
                sub.SubjectName,
                ts.TeacherID,
                em.EmployeeName AS TeacherName,
                ts.RoomNumber,
                ts.Notes
            FROM TimetableSlot AS ts
            INNER JOIN TimetableMaster AS tm ON ts.TimetableID = tm.TimetableID
            INNER JOIN PeriodMaster AS pm ON pm.PeriodID = ts.PeriodID
            LEFT JOIN ClassMaster AS cm ON cm.ClassID = tm.ClassID
            LEFT JOIN SectionMaster AS sm ON sm.SectionID = tm.SectionID
            LEFT JOIN SubjectMaster AS sub ON sub.SubjectID = ts.SubjectID
            LEFT JOIN EmployeeMaster AS em ON em.EmployeeID = ts.TeacherID
            WHERE tm.SchoolID = @SchoolID AND ts.TeacherID = @TeacherID AND tm.IsDeleted = 0 AND ts.IsDeleted = 0
            ORDER BY tm.TimetableID, ts.DayOfWeek, pm.DisplayOrder;
        END
        ELSE
        BEGIN
            SELECT NULL AS TimetableID, NULL AS ClassID, NULL AS ClassName, NULL AS SectionID, NULL AS SectionName,
                   NULL AS AcademicYear, NULL AS EffectiveFrom, NULL AS EffectiveTo, NULL AS PeriodID, NULL AS PeriodName,
                   NULL AS PeriodType, NULL AS StartTime, NULL AS EndTime, NULL AS DisplayOrder, NULL AS SlotID,
                   NULL AS DayOfWeek, NULL AS SubjectID, NULL AS SubjectName, NULL AS TeacherID, NULL AS TeacherName,
                   NULL AS RoomNumber, NULL AS Notes
            WHERE 1 = 0;
        END
    END
    ELSE IF @profileName = 'Teacher'
    BEGIN
        SELECT 
            tm.TimetableID,
            tm.ClassID,
            cm.ClassName,
            tm.SectionID,
            sm.SectionName,
            tm.AcademicYear,
            tm.EffectiveFrom,
            tm.EffectiveTo,
            pm.PeriodID,
            pm.PeriodName,
            pm.PeriodType,
            pm.StartTime,
            pm.EndTime,
            pm.DisplayOrder,
            ts.SlotID,
            ts.DayOfWeek,
            ts.SubjectID,
            sub.SubjectName,
            ts.TeacherID,
            em.EmployeeName AS TeacherName,
            ts.RoomNumber,
            ts.Notes
        FROM TimetableSlot AS ts
        INNER JOIN TimetableMaster AS tm ON ts.TimetableID = tm.TimetableID
        INNER JOIN PeriodMaster AS pm ON pm.PeriodID = ts.PeriodID
        LEFT JOIN ClassMaster AS cm ON cm.ClassID = tm.ClassID
        LEFT JOIN SectionMaster AS sm ON sm.SectionID = tm.SectionID
        LEFT JOIN SubjectMaster AS sub ON sub.SubjectID = ts.SubjectID
        LEFT JOIN EmployeeMaster AS em ON em.EmployeeID = ts.TeacherID
        WHERE tm.SchoolID = @SchoolID AND ts.TeacherID = @employeeId AND tm.IsDeleted = 0 AND ts.IsDeleted = 0
        ORDER BY tm.TimetableID, ts.DayOfWeek, pm.DisplayOrder;
    END
    ELSE IF @profileName = 'Student'
    BEGIN
        SELECT 
            tm.TimetableID,
            tm.ClassID,
            cm.ClassName,
            tm.SectionID,
            sm.SectionName,
            tm.AcademicYear,
            tm.EffectiveFrom,
            tm.EffectiveTo,
            pm.PeriodID,
            pm.PeriodName,
            pm.PeriodType,
            pm.StartTime,
            pm.EndTime,
            pm.DisplayOrder,
            ts.SlotID,
            ts.DayOfWeek,
            ts.SubjectID,
            sub.SubjectName,
            ts.TeacherID,
            em.EmployeeName AS TeacherName,
            ts.RoomNumber,
            ts.Notes
        FROM TimetableSlot AS ts
        INNER JOIN TimetableMaster AS tm ON ts.TimetableID = tm.TimetableID
        INNER JOIN PeriodMaster AS pm ON pm.PeriodID = ts.PeriodID
        LEFT JOIN ClassMaster AS cm ON cm.ClassID = tm.ClassID
        LEFT JOIN SectionMaster AS sm ON sm.SectionID = tm.SectionID
        LEFT JOIN SubjectMaster AS sub ON sub.SubjectID = ts.SubjectID
        LEFT JOIN EmployeeMaster AS em ON em.EmployeeID = ts.TeacherID
        WHERE tm.SchoolID = @SchoolID AND tm.ClassID = @Student_classId AND tm.IsDeleted = 0 AND ts.IsDeleted = 0
        ORDER BY tm.TimetableID, ts.DayOfWeek, pm.DisplayOrder;
    END
END
GO
