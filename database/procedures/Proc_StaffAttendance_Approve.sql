CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Approve
    @AttendanceID INT,
    @ApprovedBy INT,
    @AttendanceState VARCHAR(20), -- 'Approved' or 'Rejected'
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
