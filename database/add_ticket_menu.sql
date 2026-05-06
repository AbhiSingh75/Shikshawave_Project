-- =============================================
-- Add Ticket Management Menu and Assign to Profiles
-- =============================================

USE ShikshaWave;
GO

PRINT 'Adding Ticket Management Menu...';

DECLARE @TicketMenuID INT;

-- Check if menu already exists
IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Tickets' AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    SELECT @TicketMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Tickets' AND ISNULL(IsDeleted, 0) = 0;
    PRINT 'Ticket menu already exists with ID: ' + CAST(@TicketMenuID AS VARCHAR);
END
ELSE
BEGIN
    -- Insert Ticket menu
    INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedAt, IsDeleted)
    VALUES ('Tickets', 50, NULL, '/tickets/', 'fas fa-ticket-alt', 1, GETDATE(), 0);
    
    SET @TicketMenuID = SCOPE_IDENTITY();
    PRINT 'Ticket menu created with ID: ' + CAST(@TicketMenuID AS VARCHAR);
END

-- Assign to Super Admin (Role 1) - Full access
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 1 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @TicketMenuID, 1, 1, 1, 1, GETDATE(), 0);
    PRINT 'Assigned to Super Admin (Role 1)';
END
ELSE
    PRINT 'Super Admin already has access';

-- Assign to School Admin (Role 2) - Create and view
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @TicketMenuID, 1, 1, 0, 0, GETDATE(), 0);
    PRINT 'Assigned to School Admin (Role 2)';
END
ELSE
    PRINT 'School Admin already has access';

-- Assign to Support Executive (Role 4) - View and edit
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 4 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (4, @TicketMenuID, 1, 0, 1, 0, GETDATE(), 0);
    PRINT 'Assigned to Support Executive (Role 4)';
END
ELSE
    PRINT 'Support Executive already has access';

-- Verify
SELECT 
    p.ProfileID,
    p.ProfileName,
    m.MenuName,
    pmm.CanView,
    pmm.CanAdd,
    pmm.CanEdit,
    pmm.CanDelete
FROM ProfileMenuMapping pmm
INNER JOIN ProfileMaster p ON pmm.ProfileID = p.ProfileID
INNER JOIN MenuMaster m ON pmm.MenuID = m.MenuID
WHERE m.MenuID = @TicketMenuID AND pmm.IsDeleted = 0;

PRINT 'Menu setup complete!';
GO
