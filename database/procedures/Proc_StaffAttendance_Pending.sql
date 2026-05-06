CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Pending
    @SchoolID INT = NULL,
    @LoginUserID INT = NULL,
    @LoginProfileName VARCHAR(100) = NULL
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
    WHERE sa.AttendanceState = 'Pending'
    AND sa.IsDeleted = 0
    AND (
        -- Super Admin: Get pending for users with no school
        (@LoginProfileName = 'Super Admin' AND um.SchoolID IS NULL)
        OR
        -- School Admin: Get all school pending attendance
        (@LoginProfileName = 'School Admin' AND sa.SchoolID = @SchoolID)
        OR
        -- Support Executive with no school: Get own pending only
        (@LoginProfileName = 'Support Executive' AND @SchoolID IS NULL AND um.UserID = @LoginUserID)
    )
    ORDER BY sa.AttendanceDate DESC, um.UserName;
END
