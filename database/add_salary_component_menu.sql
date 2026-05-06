-- Add Salary Component menu under Master Data
-- Run this script after migration to add menu item

DECLARE @MasterDataMenuID INT;
DECLARE @NewMenuID INT;

-- Get Master Data parent menu ID
SELECT @MasterDataMenuID = MenuID 
FROM MenuMaster 
WHERE MenuName = 'Master Data' AND ISNULL(IsDeleted, 0) = 0;

-- Check if menu already exists
IF NOT EXISTS (
    SELECT 1 FROM MenuMaster 
    WHERE MenuURL = '/master-data/salary-component/' 
    AND ISNULL(IsDeleted, 0) = 0
)
BEGIN
    -- Insert Salary Component menu
    INSERT INTO MenuMaster (
        MenuName, 
        MenuURL, 
        MenuIcon, 
        ParentMenuID, 
        DisplayOrder, 
        IsActive, 
        CreatedAt, 
        IsDeleted
    )
    VALUES (
        'Salary Components',
        '/master-data/salary-component/',
        'fas fa-money-check-alt',
        @MasterDataMenuID,
        50,
        1,
        GETDATE(),
        0
    );

    SET @NewMenuID = SCOPE_IDENTITY();

    PRINT 'Salary Component menu added successfully with MenuID: ' + CAST(@NewMenuID AS VARCHAR(10));

    -- Add permissions for Super Admin (ProfileID = 1)
    IF NOT EXISTS (
        SELECT 1 FROM ProfileMenuMapping 
        WHERE ProfileID = 1 AND MenuID = @NewMenuID
    )
    BEGIN
        INSERT INTO ProfileMenuMapping (
            ProfileID, 
            MenuID, 
            CanView, 
            CanAdd, 
            CanEdit, 
            CanDelete, 
            CreatedAt, 
            IsDeleted
        )
        VALUES (
            1, 
            @NewMenuID, 
            1, 
            1, 
            1, 
            1, 
            GETDATE(), 
            0
        );
        PRINT 'Permissions added for Super Admin';
    END

    -- Add permissions for School Admin (ProfileID = 2)
    IF NOT EXISTS (
        SELECT 1 FROM ProfileMenuMapping 
        WHERE ProfileID = 2 AND MenuID = @NewMenuID
    )
    BEGIN
        INSERT INTO ProfileMenuMapping (
            ProfileID, 
            MenuID, 
            CanView, 
            CanAdd, 
            CanEdit, 
            CanDelete, 
            CreatedAt, 
            IsDeleted
        )
        VALUES (
            2, 
            @NewMenuID, 
            1, 
            1, 
            1, 
            1, 
            GETDATE(), 
            0
        );
        PRINT 'Permissions added for School Admin';
    END
END
ELSE
BEGIN
    PRINT 'Salary Component menu already exists';
END

-- Display result
SELECT 
    m.MenuID,
    m.MenuName,
    m.MenuURL,
    m.MenuIcon,
    pm.MenuName as ParentMenu,
    m.DisplayOrder,
    m.IsActive
FROM MenuMaster m
LEFT JOIN MenuMaster pm ON m.ParentMenuID = pm.MenuID
WHERE m.MenuURL = '/master-data/salary-component/'
AND ISNULL(m.IsDeleted, 0) = 0;
