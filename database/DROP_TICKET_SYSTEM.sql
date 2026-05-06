-- =============================================
-- Drop All Ticket Management System Components
-- =============================================

USE ShikshaWave;
GO

PRINT 'Dropping Ticket Management System...';

-- Drop ProfileMenuMapping for ticket menus
DELETE FROM ProfileMenuMapping 
WHERE MenuID IN (SELECT MenuID FROM MenuMaster WHERE MenuName LIKE '%Ticket%');

-- Drop ticket menus
DELETE FROM MenuMaster WHERE MenuName LIKE '%Ticket%';

-- Drop tables in correct order (respecting foreign keys)
IF OBJECT_ID('TicketAuditLog', 'U') IS NOT NULL DROP TABLE TicketAuditLog;
IF OBJECT_ID('TicketWatchers', 'U') IS NOT NULL DROP TABLE TicketWatchers;
IF OBJECT_ID('TicketNotifications', 'U') IS NOT NULL DROP TABLE TicketNotifications;
IF OBJECT_ID('TicketAssignmentHistory', 'U') IS NOT NULL DROP TABLE TicketAssignmentHistory;
IF OBJECT_ID('TicketStatusHistory', 'U') IS NOT NULL DROP TABLE TicketStatusHistory;
IF OBJECT_ID('TicketAttachments', 'U') IS NOT NULL DROP TABLE TicketAttachments;
IF OBJECT_ID('TicketComments', 'U') IS NOT NULL DROP TABLE TicketComments;
IF OBJECT_ID('TicketMaster', 'U') IS NOT NULL DROP TABLE TicketMaster;
IF OBJECT_ID('SupportExecutiveMaster', 'U') IS NOT NULL DROP TABLE SupportExecutiveMaster;
IF OBJECT_ID('TicketStatusMaster', 'U') IS NOT NULL DROP TABLE TicketStatusMaster;
IF OBJECT_ID('TicketPriorityMaster', 'U') IS NOT NULL DROP TABLE TicketPriorityMaster;
IF OBJECT_ID('TicketCategoryMaster', 'U') IS NOT NULL DROP TABLE TicketCategoryMaster;

-- Drop stored procedures
IF OBJECT_ID('Proc_Ticket_Create', 'P') IS NOT NULL DROP PROCEDURE Proc_Ticket_Create;
IF OBJECT_ID('Proc_Ticket_GetDetails', 'P') IS NOT NULL DROP PROCEDURE Proc_Ticket_GetDetails;
IF OBJECT_ID('Proc_Ticket_Report', 'P') IS NOT NULL DROP PROCEDURE Proc_Ticket_Report;
IF OBJECT_ID('Proc_Ticket_Assign', 'P') IS NOT NULL DROP PROCEDURE Proc_Ticket_Assign;

PRINT '✅ All Ticket Management components dropped successfully!';
GO
