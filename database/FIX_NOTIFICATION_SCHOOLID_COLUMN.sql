-- =============================================
-- Fix NotificationMaster SchoolID to Allow NULL
-- Super Admin and Support Executive don't require SchoolID
-- =============================================

USE ShikshaWaveDB;
GO

-- Drop foreign key constraint
IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_Notification_School')
BEGIN
    ALTER TABLE NotificationMaster DROP CONSTRAINT FK_Notification_School;
    PRINT 'Dropped FK_Notification_School constraint';
END
GO

-- Alter column to allow NULL
ALTER TABLE NotificationMaster
ALTER COLUMN SchoolID INT NULL;
GO

PRINT 'SchoolID column altered to allow NULL';
GO

-- Re-create foreign key constraint (allowing NULL)
ALTER TABLE NotificationMaster
ADD CONSTRAINT FK_Notification_School 
FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID);
GO

PRINT 'Re-created FK_Notification_School constraint';
GO

PRINT 'NotificationMaster table updated successfully!';
PRINT 'SchoolID is now nullable for Super Admin and Support Executive notifications.';
GO
