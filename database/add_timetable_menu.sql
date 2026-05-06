-- Update existing Timetable menus to use new timetable management system

-- Update 'Create Timetable' menu (MenuID 29)
UPDATE MenuMaster 
SET MenuURL = '/timetable/management/?tab=create', 
    Icon = 'fa fa-plus',
    UpdatedAt = GETDATE()
WHERE MenuID = 29;

-- Update 'View Timetable' menu (MenuID 30)
UPDATE MenuMaster 
SET MenuURL = '/timetable/management/?tab=view',
    Icon = 'fa fa-eye',
    UpdatedAt = GETDATE()
WHERE MenuID = 30;

-- Ensure permissions exist for MenuID 29 (Create Timetable)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID = 29 AND ProfileID = 1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (1, 29, 1, 1, 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID = 29 AND ProfileID = 2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (2, 29, 1, 1, 1, 1, GETDATE());

-- Ensure permissions exist for MenuID 30 (View Timetable)
IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID = 30 AND ProfileID = 1)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (1, 30, 1, 1, 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID = 30 AND ProfileID = 2)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (2, 30, 1, 1, 1, 1, GETDATE());

IF NOT EXISTS (SELECT 1 FROM ProfileMenuMapping WHERE MenuID = 30 AND ProfileID = 3)
    INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt)
    VALUES (3, 30, 1, 0, 0, 0, GETDATE());

PRINT 'Timetable menus updated successfully';
PRINT 'Create Timetable: /timetable/management/?tab=create';
PRINT 'View Timetable: /timetable/management/?tab=view';
GO
