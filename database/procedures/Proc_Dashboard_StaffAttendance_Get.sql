CREATE OR ALTER PROCEDURE Proc_Dashboard_StaffAttendance_Get
    @SchoolID INT,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @EmployeeID INT = NULL,
    @Status VARCHAR(20) = NULL,
    @EmploymentType VARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @TotalRecords INT;
    
    SELECT @TotalRecords = COUNT(*)
    FROM StaffAttendance sa
    INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
    WHERE sa.SchoolID = @SchoolID
    AND sa.IsDeleted = 0
    AND (@FromDate IS NULL OR sa.AttendanceDate >= @FromDate)
    AND (@ToDate IS NULL OR sa.AttendanceDate <= @ToDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status)
    AND (@EmploymentType IS NULL OR um.EmploymentType = @EmploymentType);
    
    SELECT 
        @TotalRecords AS TotalMarked,
        SUM(CASE WHEN sa.Status = 'present' THEN 1 ELSE 0 END) AS PresentCount,
        SUM(CASE WHEN sa.Status = 'absent' THEN 1 ELSE 0 END) AS AbsentCount,
        SUM(CASE WHEN sa.Status = 'leave' THEN 1 ELSE 0 END) AS LeaveCount,
        SUM(CASE WHEN sa.Status = 'late' THEN 1 ELSE 0 END) AS LateCount,
        CAST(SUM(CASE WHEN sa.Status = 'present' THEN 1 ELSE 0 END) * 100.0 / NULLIF(@TotalRecords, 0) AS DECIMAL(5,2)) AS PresentPercentage,
        CAST(SUM(CASE WHEN sa.Status = 'absent' THEN 1 ELSE 0 END) * 100.0 / NULLIF(@TotalRecords, 0) AS DECIMAL(5,2)) AS AbsentPercentage,
        CAST(SUM(CASE WHEN sa.Status = 'late' THEN 1 ELSE 0 END) * 100.0 / NULLIF(@TotalRecords, 0) AS DECIMAL(5,2)) AS LatePercentage,
        CAST(SUM(CASE WHEN sa.Status = 'leave' THEN 1 ELSE 0 END) * 100.0 / NULLIF(@TotalRecords, 0) AS DECIMAL(5,2)) AS LeavePercentage
    FROM StaffAttendance sa
    INNER JOIN UserMaster um ON sa.EmployeeID = um.UserID
    WHERE sa.SchoolID = @SchoolID
    AND sa.IsDeleted = 0
    AND (@FromDate IS NULL OR sa.AttendanceDate >= @FromDate)
    AND (@ToDate IS NULL OR sa.AttendanceDate <= @ToDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status)
    AND (@EmploymentType IS NULL OR um.EmploymentType = @EmploymentType);
END
