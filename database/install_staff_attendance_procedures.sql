-- =============================================
-- Install All Staff Attendance Procedures
-- Execute this file to create all procedures at once
-- =============================================

-- Procedure 1: Get Staff List for Attendance Marking
CREATE OR ALTER PROCEDURE Proc_StaffList_Get
    @SchoolID INT,
    @AttendanceDate DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        um.UserID AS EmployeeID,
        um.UserName AS EmployeeName,
        um.UserCode AS EmployeeCode,
        pm.ProfileName AS Role,
        sa.Status,
        sa.Remarks,
        sa.AttendanceID
    FROM UserMaster um
    INNER JOIN ProfileMaster pm ON um.ProfileID = pm.ProfileID
    LEFT JOIN StaffAttendance sa ON um.UserID = sa.EmployeeID 
        AND sa.AttendanceDate = @AttendanceDate 
        AND sa.IsDeleted = 0
    WHERE um.SchoolID = @SchoolID
    AND um.ProfileID IN (3, 5, 6, 7) -- Teacher, Accountant, Driver, Librarian
    AND um.IsDeleted = 0
    AND um.IsActive = 1
    ORDER BY pm.ProfileID, um.UserName;
END
GO

-- Procedure 2: Mark/Update Staff Attendance
CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Mark
    @SchoolID INT,
    @EmployeeID INT,
    @AttendanceDate DATE,
    @Status VARCHAR(20),
    @Remarks VARCHAR(500) = NULL,
    @CreatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    IF EXISTS (SELECT 1 FROM StaffAttendance 
               WHERE SchoolID = @SchoolID 
               AND EmployeeID = @EmployeeID 
               AND AttendanceDate = @AttendanceDate 
               AND IsDeleted = 0)
    BEGIN
        UPDATE StaffAttendance
        SET Status = @Status,
            Remarks = @Remarks,
            UpdatedBy = @CreatedBy,
            UpdatedAt = GETDATE()
        WHERE SchoolID = @SchoolID 
        AND EmployeeID = @EmployeeID 
        AND AttendanceDate = @AttendanceDate 
        AND IsDeleted = 0;
        
        SELECT 'Updated' AS Result;
    END
    ELSE
    BEGIN
        INSERT INTO StaffAttendance (SchoolID, EmployeeID, AttendanceDate, Status, Remarks, AttendanceState, CreatedBy, CreatedAt, IsDeleted)
        VALUES (@SchoolID, @EmployeeID, @AttendanceDate, @Status, @Remarks, 'Pending', @CreatedBy, GETDATE(), 0);
        
        SELECT 'Inserted' AS Result;
    END
END
GO

-- Procedure 3: Get Staff Attendance Records with Filters
CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Get
    @SchoolID INT,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @EmployeeID INT = NULL,
    @Status VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        sa.AttendanceID,
        sa.AttendanceDate,
        sa.Status,
        sa.Remarks,
        sa.AttendanceState,
        sa.ApprovalRemarks,
        sa.ApprovedAt,
        um.UserID AS EmployeeID,
        um.UserName AS EmployeeName,
        um.UserCode AS EmployeeCode,
        pm.ProfileName AS Role,
        approver.UserName AS ApprovedByName
    FROM StaffAttendance sa
    INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
    INNER JOIN ProfileMaster pm ON um.ProfileID = pm.ProfileID
    LEFT JOIN UserMaster approver ON sa.ApprovedBy = approver.UserID
    WHERE sa.SchoolID = @SchoolID
    AND sa.IsDeleted = 0
    AND (@StartDate IS NULL OR sa.AttendanceDate >= @StartDate)
    AND (@EndDate IS NULL OR sa.AttendanceDate <= @EndDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status)
    ORDER BY sa.AttendanceDate DESC, um.UserName;
END
GO

PRINT '============================================='
PRINT 'Staff Attendance Procedures Created Successfully!'
PRINT '============================================='
PRINT 'Procedures Created:'
PRINT '1. Proc_StaffList_Get'
PRINT '2. Proc_StaffAttendance_Mark'
PRINT '3. Proc_StaffAttendance_Get'
PRINT '============================================='
