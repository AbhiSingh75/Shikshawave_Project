CREATE OR ALTER PROCEDURE Proc_StaffList_Get
    @SchoolID INT = NULL,
    @AttendanceDate DATE = NULL,
    @LoginUserID INT = NULL,
    @LoginProfileName VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        um.UserID AS EmployeeID,
        CONCAT(um.UserCode, ' - ', um.UserName) AS EmployeeName,
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
    WHERE um.IsDeleted = 0
    AND um.IsActive = 1
    AND (
        -- Super Admin: Get users with no school assigned
        (@LoginProfileName = 'Super Admin' AND um.SchoolID IS NULL)
        OR
        -- School Admin: Get all school staff
        (@LoginProfileName = 'School Admin' AND um.SchoolID = @SchoolID AND um.ProfileID IN (3, 5, 6, 7))
        OR
        -- Support Executive with no school: Get own attendance only
        (@LoginProfileName = 'Support Executive' AND @SchoolID IS NULL AND um.UserID = @LoginUserID)
        OR
        -- Teacher/Driver/Librarian/Accountant: Get own attendance only
        (@LoginProfileName IN ('Teacher', 'Driver', 'Librarian', 'Accountant') AND um.UserID = @LoginUserID)
    )
    ORDER BY pm.ProfileID, um.UserName;
END
