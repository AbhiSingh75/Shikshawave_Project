-- Test query to check if records exist
SELECT 
    sa.AttendanceID,
    sa.AttendanceDate,
    sa.Status,
    sa.SchoolID,
    um.UserName AS EmployeeName,
    um.UserCode AS EmployeeCode
FROM StaffAttendance sa
INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
WHERE sa.SchoolID IS NULL
AND sa.IsDeleted = 0
ORDER BY sa.AttendanceDate DESC;

-- Test the stored procedure
EXEC Proc_StaffAttendance_Get 
    @SchoolID=NULL, 
    @StartDate=NULL, 
    @EndDate=NULL, 
    @EmployeeID=NULL, 
    @Status=NULL, 
    @PageNumber=1, 
    @PageSize=50;
