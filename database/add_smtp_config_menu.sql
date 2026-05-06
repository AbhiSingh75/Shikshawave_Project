-- Add SMTP Configuration menu under Master Data (PostgreSQL Version)
-- Run this script after creating the stored procedures

DO $$
DECLARE
    v_MasterDataMenuID INT;
    v_NewMenuID INT;
BEGIN
    -- Get Master Data parent menu ID
    SELECT "MenuID" INTO v_MasterDataMenuID
    FROM "MenuMaster" 
    WHERE "MenuName" = 'Master Data' AND COALESCE("IsDeleted", FALSE) = FALSE;

    -- Check if menu already exists
    IF NOT EXISTS (
        SELECT 1 FROM "MenuMaster" 
        WHERE "MenuURL" = '/master-data/smtp-configuration/' 
        AND COALESCE("IsDeleted", FALSE) = FALSE
    ) THEN
        -- Insert SMTP Configuration menu
        INSERT INTO "MenuMaster" (
            "MenuName", 
            "MenuURL", 
            "MenuIcon", 
            "ParentMenuID", 
            "DisplayOrder", 
            "IsActive", 
            "CreatedAt", 
            "IsDeleted"
        )
        VALUES (
            'SMTP Configuration',
            '/master-data/smtp-configuration/',
            'fas fa-envelope-open-text',
            v_MasterDataMenuID,
            55,
            TRUE,
            CURRENT_TIMESTAMP,
            FALSE
        )
        RETURNING "MenuID" INTO v_NewMenuID;

        RAISE NOTICE 'SMTP Configuration menu added with MenuID: %', v_NewMenuID;

        -- Add permissions for Super Admin (ProfileID = 1)
        IF NOT EXISTS (
            SELECT 1 FROM "ProfileMenuMapping" 
            WHERE "ProfileID" = 1 AND "MenuID" = v_NewMenuID
        ) THEN
            INSERT INTO "ProfileMenuMapping" (
                "ProfileID", 
                "MenuID", 
                "CanView", 
                "CanAdd", 
                "CanEdit", 
                "CanDelete", 
                "CreatedAt", 
                "IsDeleted"
            )
            VALUES (
                1, 
                v_NewMenuID, 
                TRUE, 
                TRUE, 
                TRUE, 
                TRUE, 
                CURRENT_TIMESTAMP, 
                FALSE
            );
            RAISE NOTICE 'Permissions added for Super Admin';
        END IF;

        -- Add permissions for School Admin (ProfileID = 2)
        IF NOT EXISTS (
            SELECT 1 FROM "ProfileMenuMapping" 
            WHERE "ProfileID" = 2 AND "MenuID" = v_NewMenuID
        ) THEN
            INSERT INTO "ProfileMenuMapping" (
                "ProfileID", 
                "MenuID", 
                "CanView", 
                "CanAdd", 
                "CanEdit", 
                "CanDelete", 
                "CreatedAt", 
                "IsDeleted"
            )
            VALUES (
                2, 
                v_NewMenuID, 
                TRUE, 
                TRUE, 
                TRUE, 
                TRUE, 
                CURRENT_TIMESTAMP, 
                FALSE
            );
            RAISE NOTICE 'Permissions added for School Admin';
        END IF;
    ELSE
        RAISE NOTICE 'SMTP Configuration menu already exists';
    END IF;
END $$;

-- Display result
SELECT 
    m."MenuID",
    m."MenuName",
    m."MenuURL",
    m."MenuIcon",
    pm."MenuName" as "ParentMenu",
    m."DisplayOrder",
    m."IsActive"
FROM "MenuMaster" m
LEFT JOIN "MenuMaster" pm ON m."ParentMenuID" = pm."MenuID"
WHERE m."MenuURL" = '/master-data/smtp-configuration/'
AND COALESCE(m."IsDeleted", FALSE) = FALSE;
