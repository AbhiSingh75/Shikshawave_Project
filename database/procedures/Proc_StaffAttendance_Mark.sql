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
