CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Get
    @SchoolID INT = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @EmployeeID INT = NULL,
    @Status VARCHAR(20) = NULL,
    @PageNumber INT = 1,
    @PageSize INT = 50
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Offset INT = (@PageNumber - 1) * @PageSize;
    
    SELECT 
        sa.AttendanceID,
        sa.AttendanceDate,
        sa.Status,
        sa.Remarks,
        sa.AttendanceState,
        um.UserID AS EmployeeID,
        um.UserName AS EmployeeName,
        um.UserCode AS EmployeeCode,
        pm.ProfileName AS Role,
        approver.UserName AS ApprovedByName,
        sa.ApprovedAt,
        COUNT(*) OVER() AS TotalRecords
    FROM StaffAttendance sa
    INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
    INNER JOIN ProfileMaster pm ON um.ProfileID = pm.ProfileID
    LEFT JOIN UserMaster approver ON sa.ApprovedBy = approver.UserID
    WHERE ((@SchoolID IS NULL AND sa.SchoolID IS NULL) OR (@SchoolID IS NOT NULL AND sa.SchoolID = @SchoolID))
    AND sa.IsDeleted = 0
    AND (@StartDate IS NULL OR sa.AttendanceDate >= @StartDate)
    AND (@EndDate IS NULL OR sa.AttendanceDate <= @EndDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status)
    ORDER BY sa.AttendanceDate DESC, um.UserName
    OFFSET @Offset ROWS FETCH NEXT @PageSize ROWS ONLY;
END
