CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Stats
    @SchoolID INT = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL,
    @EmployeeID INT = NULL,
    @Status VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @TotalRecords INT;
    
    SELECT @TotalRecords = COUNT(*)
    FROM StaffAttendance sa
    WHERE ((@SchoolID IS NULL AND sa.SchoolID IS NULL) OR (@SchoolID IS NOT NULL AND sa.SchoolID = @SchoolID))
    AND sa.IsDeleted = 0
    AND (@StartDate IS NULL OR sa.AttendanceDate >= @StartDate)
    AND (@EndDate IS NULL OR sa.AttendanceDate <= @EndDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status);
    
    SELECT 
        sa.Status,
        COUNT(*) AS Count,
        CAST(COUNT(*) * 100.0 / NULLIF(@TotalRecords, 0) AS DECIMAL(5,2)) AS Percentage,
        @TotalRecords AS TotalAttendance
    FROM StaffAttendance sa
    WHERE ((@SchoolID IS NULL AND sa.SchoolID IS NULL) OR (@SchoolID IS NOT NULL AND sa.SchoolID = @SchoolID))
    AND sa.IsDeleted = 0
    AND (@StartDate IS NULL OR sa.AttendanceDate >= @StartDate)
    AND (@EndDate IS NULL OR sa.AttendanceDate <= @EndDate)
    AND (@EmployeeID IS NULL OR sa.EmployeeID = @EmployeeID)
    AND (@Status IS NULL OR sa.Status = @Status)
    GROUP BY sa.Status;
END
