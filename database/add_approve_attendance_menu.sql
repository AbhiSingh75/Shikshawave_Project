-- Add Approve Staff Attendance submenu
DECLARE @AttendanceMenuID INT;

SELECT @AttendanceMenuID = MenuID FROM MenuMaster 
WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0;

IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Approve Employee/Staff Attendance' AND IsDeleted = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
    VALUES ('Approve Employee/Staff Attendance', '/attendance/approve-employee/', 'fas fa-check-circle', @AttendanceMenuID, 5, 1, GETDATE(), 0);
    
    PRINT 'Approve Employee/Staff Attendance menu added';
END

-- Map to School Admin only (ProfileID = 2)
DECLARE @ApproveMenuID INT;
SELECT @ApproveMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Approve Employee/Staff Attendance' AND IsDeleted = 0;

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @ApproveMenuID)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
    VALUES (2, @ApproveMenuID, 1, 1, 1, 0, 0, GETDATE());
    
    PRINT 'Approve menu mapped to School Admin';
END

PRINT 'Approval menu setup complete!';
