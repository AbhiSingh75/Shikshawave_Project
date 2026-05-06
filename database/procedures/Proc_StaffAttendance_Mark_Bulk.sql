CREATE OR ALTER PROCEDURE Proc_StaffAttendance_Mark_Bulk
    @SchoolID INT = NULL,
    @AttendanceDate DATE,
    @AttendanceData NVARCHAR(MAX),
    @CreatedBy INT,
    @ProfileName VARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @AttendanceState VARCHAR(20);
    DECLARE @ApprovedBy INT = NULL;
    
    -- If School Admin or Super Admin, auto-approve
    IF @ProfileName IN ('School Admin', 'Super Admin')
    BEGIN
        SET @AttendanceState = 'Approved';
        SET @ApprovedBy = @CreatedBy;
    END
    ELSE
    BEGIN
        -- Support Executive and others need approval
        SET @AttendanceState = 'Pending';
    END
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        MERGE StaffAttendance AS target
        USING (
            SELECT 
                COALESCE(@SchoolID, um.SchoolID) AS SchoolID,
                CAST(JSON_VALUE(value, '$.EmployeeID') AS INT) AS EmployeeID,
                @AttendanceDate AS AttendanceDate,
                JSON_VALUE(value, '$.Status') AS Status,
                JSON_VALUE(value, '$.Remarks') AS Remarks
            FROM OPENJSON(@AttendanceData)
            LEFT JOIN UserMaster um ON um.UserID = CAST(JSON_VALUE(value, '$.EmployeeID') AS INT)
        ) AS source
        ON (target.SchoolID = source.SchoolID OR (target.SchoolID IS NULL AND source.SchoolID IS NULL))
            AND target.EmployeeID = source.EmployeeID 
            AND target.AttendanceDate = source.AttendanceDate 
            AND target.IsDeleted = 0
        WHEN MATCHED THEN
            UPDATE SET 
                Status = source.Status,
                Remarks = source.Remarks,
                UpdatedBy = @CreatedBy,
                UpdatedAt = GETDATE(),
                AttendanceState = @AttendanceState,
                ApprovedBy = @ApprovedBy,
                ApprovedAt = CASE WHEN @AttendanceState = 'Approved' THEN GETDATE() ELSE NULL END
        WHEN NOT MATCHED THEN
            INSERT (SchoolID, EmployeeID, AttendanceDate, Status, Remarks, AttendanceState, CreatedBy, CreatedAt, ApprovedBy, ApprovedAt, IsDeleted)
            VALUES (source.SchoolID, source.EmployeeID, source.AttendanceDate, source.Status, source.Remarks, @AttendanceState, @CreatedBy, GETDATE(), @ApprovedBy, CASE WHEN @AttendanceState = 'Approved' THEN GETDATE() ELSE NULL END, 0);
        
        COMMIT TRANSACTION;
        SELECT 'SUCCESS' AS Result, 'Attendance saved successfully' AS Message;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        SELECT 'ERROR' AS Result, ERROR_MESSAGE() AS Message;
    END CATCH
END
