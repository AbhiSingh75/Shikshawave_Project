-- =============================================
-- Install Staff Attendance Approval System
-- =============================================

-- Step 1: Create Approval Procedures
CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Pending
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        sa.AttendanceID,
        sa.AttendanceDate,
        sa.Status,
        sa.Remarks,
        um.UserID AS EmployeeID,
        um.UserName AS EmployeeName,
        um.UserCode AS EmployeeCode,
        pm.ProfileName AS Role,
        creator.UserName AS CreatedByName,
        sa.CreatedAt
    FROM StaffAttendance sa
    INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
    INNER JOIN ProfileMaster pm ON um.ProfileID = pm.ProfileID
    LEFT JOIN UserMaster creator ON sa.CreatedBy = creator.UserID
    WHERE sa.SchoolID = @SchoolID
    AND sa.AttendanceState = 'Pending'
    AND sa.IsDeleted = 0
    ORDER BY sa.AttendanceDate DESC, um.UserName;
END
GO

CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Approve
    @AttendanceID INT,
    @ApprovedBy INT,
    @AttendanceState VARCHAR(20),
    @ApprovalRemarks VARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE StaffAttendance
    SET AttendanceState = @AttendanceState,
        ApprovedBy = @ApprovedBy,
        ApprovedAt = GETDATE(),
        ApprovalRemarks = @ApprovalRemarks,
        UpdatedBy = @ApprovedBy,
        UpdatedAt = GETDATE()
    WHERE AttendanceID = @AttendanceID
    AND IsDeleted = 0;
    
    SELECT 'Success' AS Result;
END
GO

-- Step 2: Add Approval Menu
DECLARE @AttendanceMenuID INT;

SELECT @AttendanceMenuID = MenuID FROM MenuMaster 
WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0;

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Approve Employee/Staff Attendance' AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Approve Employee/Staff Attendance', '/attendance/approve-employee/', 'fas fa-check-circle', @AttendanceMenuID, 5, 1, GETDATE(), 0);
END

-- Step 3: Map to School Admin
DECLARE @ApproveMenuID INT;
SELECT @ApproveMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Approve Employee/Staff Attendance' AND IsDeleted = 0;

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @ApproveMenuID)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
    VALUES (2, @ApproveMenuID, 1, 1, 1, 0, 0, GETDATE());
END

PRINT '============================================='
PRINT 'Approval System Installed Successfully!'
PRINT '============================================='
PRINT 'Created:'
PRINT '- Proc_StaffAttendance_Pending'
PRINT '- Proc_StaffAttendance_Approve'
PRINT '- Approve Employee/Staff Attendance menu'
PRINT '- Mapped to School Admin profile'
PRINT '============================================='
