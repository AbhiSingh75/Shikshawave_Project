-- Remove Import Submenus (Keep only Import Dashboard)
USE ShikshaWaveDB;
GO

-- Delete ProfileMenuMapping for all import submenus except Dashboard
DELETE FROM ProfileMenuMapping
WHERE MenuID IN (
    SELECT MenuID 
    FROM MenuMaster 
    WHERE ParentMenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import')
    AND MenuName != 'Import Dashboard'
);

-- Delete all import submenus except Dashboard
DELETE FROM MenuMaster
WHERE ParentMenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import')
AND MenuName != 'Import Dashboard';

-- Update Import Dashboard URL to main dashboard
UPDATE MenuMaster
SET MenuURL = '/data-import/dashboard/'
WHERE MenuName = 'Import Dashboard';

PRINT 'Import submenus removed successfully. Only Import Dashboard remains.';

-- Verify remaining menu structure
SELECT 
    m.MenuID,
    m.MenuName,
    m.MenuURL,
    m.DisplayOrder
FROM MenuMaster m
WHERE m.ParentMenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Data Import')
OR m.MenuName = 'Data Import'
ORDER BY m.ParentMenuID, m.DisplayOrder;

GO
