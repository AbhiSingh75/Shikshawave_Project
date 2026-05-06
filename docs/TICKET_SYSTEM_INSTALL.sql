-- =============================================
-- Ticket Management System - Quick Installation Script
-- Run this script to install the complete ticket system
-- =============================================

USE ShikshaWave;
GO

PRINT '========================================';
PRINT 'Installing Ticket Management System';
PRINT '========================================';

-- Step 1: Create Tables
PRINT 'Step 1: Creating tables...';

-- Drop existing tables if they exist
IF OBJECT_ID('TicketActivityLog', 'U') IS NOT NULL DROP TABLE TicketActivityLog;
IF OBJECT_ID('TicketAttachments', 'U') IS NOT NULL DROP TABLE TicketAttachments;
IF OBJECT_ID('TicketComments', 'U') IS NOT NULL DROP TABLE TicketComments;
IF OBJECT_ID('TicketMaster', 'U') IS NOT NULL DROP TABLE TicketMaster;
IF OBJECT_ID('TicketCategory', 'U') IS NOT NULL DROP TABLE TicketCategory;
IF OBJECT_ID('TicketPriority', 'U') IS NOT NULL DROP TABLE TicketPriority;

-- Create tables (from TicketSystem.sql)
-- [Tables creation code here - see database/tables/TicketSystem.sql]

PRINT 'Tables created successfully';

-- Step 2: Create Stored Procedures
PRINT 'Step 2: Creating stored procedures...';

-- [Stored procedures code here - see database/procedures/*.sql]

PRINT 'Stored procedures created successfully';

-- Step 3: Add Menu Items
PRINT 'Step 3: Adding menu items...';

DECLARE @TicketMenuID INT;

-- Check if menu already exists
IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Tickets' AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedAt, IsDeleted)
    VALUES ('Tickets', 50, NULL, '/tickets/', 'fas fa-ticket-alt', 1, GETDATE(), 0);
    
    SET @TicketMenuID = SCOPE_IDENTITY();
    PRINT 'Ticket menu created with ID: ' + CAST(@TicketMenuID AS VARCHAR);
END
ELSE
BEGIN
    SELECT @TicketMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Tickets' AND ISNULL(IsDeleted, 0) = 0;
    PRINT 'Ticket menu already exists with ID: ' + CAST(@TicketMenuID AS VARCHAR);
END

-- Step 4: Grant Permissions
PRINT 'Step 4: Granting permissions...';

-- Super Admin (Role 1) - Full access
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 1 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (1, @TicketMenuID, 1, 1, 1, 1, GETDATE(), 0);
    PRINT 'Granted permissions to Super Admin';
END

-- School Admin (Role 2) - Create and view
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 2 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (2, @TicketMenuID, 1, 1, 0, 0, GETDATE(), 0);
    PRINT 'Granted permissions to School Admin';
END

-- Support Executive (Role 4) - View and edit
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE ProfileID = 4 AND MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0)
BEGIN
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
    VALUES (4, @TicketMenuID, 1, 0, 1, 0, GETDATE(), 0);
    PRINT 'Granted permissions to Support Executive';
END

-- Step 5: Verification
PRINT 'Step 5: Verifying installation...';

DECLARE @TableCount INT, @ProcCount INT, @MenuCount INT, @PermCount INT;

SELECT @TableCount = COUNT(*) FROM sys.tables WHERE name IN ('TicketMaster', 'TicketCategory', 'TicketPriority', 'TicketActivityLog', 'TicketComments', 'TicketAttachments');
SELECT @ProcCount = COUNT(*) FROM sys.procedures WHERE name LIKE 'Proc_Ticket%';
SELECT @MenuCount = COUNT(*) FROM MenuMaster WHERE MenuName = 'Tickets' AND ISNULL(IsDeleted, 0) = 0;
SELECT @PermCount = COUNT(*) FROM ProfileMenuMapping WHERE MenuID = @TicketMenuID AND ISNULL(IsDeleted, 0) = 0;

PRINT '----------------------------------------';
PRINT 'Installation Summary:';
PRINT 'Tables created: ' + CAST(@TableCount AS VARCHAR) + '/6';
PRINT 'Stored procedures created: ' + CAST(@ProcCount AS VARCHAR) + '/5';
PRINT 'Menu items created: ' + CAST(@MenuCount AS VARCHAR) + '/1';
PRINT 'Permissions granted: ' + CAST(@PermCount AS VARCHAR) + '/3';
PRINT '----------------------------------------';

IF @TableCount = 6 AND @ProcCount >= 5 AND @MenuCount = 1 AND @PermCount = 3
BEGIN
    PRINT 'SUCCESS: Ticket Management System installed successfully!';
    PRINT '';
    PRINT 'Next Steps:';
    PRINT '1. Add tickets app to Django INSTALLED_APPS';
    PRINT '2. Add path(''tickets/'', include(''tickets.urls'')) to core/urls.py';
    PRINT '3. Create at least one Support Executive user (ProfileID = 4)';
    PRINT '4. Test the system by creating a ticket';
END
ELSE
BEGIN
    PRINT 'WARNING: Installation may be incomplete. Please check the counts above.';
END

PRINT '========================================';
PRINT 'Installation Complete';
PRINT '========================================';
GO
