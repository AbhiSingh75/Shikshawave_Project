-- Function to get Menu List
DROP FUNCTION IF EXISTS Proc_menu_list_get();

CREATE OR REPLACE FUNCTION Proc_menu_list_get()
RETURNS TABLE (
    "MenuID" INT,
    "MenuName" VARCHAR,
    "MenuURL" VARCHAR,
    "Icon" VARCHAR,
    "DisplayOrder" INT,
    "ParentMenuID" INT,
    "IsActive" BOOLEAN,
    "ParentMenuName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m."MenuID",
        m."MenuName",
        m."MenuURL",
        m."Icon",
        m."DisplayOrder",
        m."ParentMenuID",
        m."IsActive",
        p."MenuName" AS "ParentMenuName"
    FROM "MenuMaster" m
    LEFT JOIN "MenuMaster" p ON m."ParentMenuID" = p."MenuID"
    WHERE COALESCE(m."IsDeleted", FALSE) = FALSE
    ORDER BY m."DisplayOrder", m."MenuName";
END;
$$ LANGUAGE plpgsql;

-- Procedure to Manage Menu Master (Add, Update, Delete, Restore)
DROP PROCEDURE IF EXISTS Proc_MenuMaster_Manage;

CREATE OR REPLACE PROCEDURE Proc_MenuMaster_Manage(
    param_Action VARCHAR,
    param_MenuID INT,
    param_MenuName VARCHAR,
    param_ParentMenuID INT,
    param_MenuURL VARCHAR,
    param_Icon VARCHAR,
    param_DisplayOrder INT,
    param_IsActive BOOLEAN,
    param_UserID INT,
    INOUT param_Message VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- INSERT Action
    IF param_Action = 'INSERT' THEN
        INSERT INTO "MenuMaster" (
            "MenuName", "ParentMenuID", "MenuURL", "Icon", "DisplayOrder", "IsActive", "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            param_MenuName, param_ParentMenuID, param_MenuURL, param_Icon, param_DisplayOrder, param_IsActive, param_UserID, CURRENT_TIMESTAMP, FALSE
        );
        param_Message := '{"status": "success", "message": "Menu added successfully"}';

    -- UPDATE Action
    ELSIF param_Action = 'UPDATE' THEN
        IF EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuID" = param_MenuID) THEN
            UPDATE "MenuMaster"
            SET 
                "MenuName" = param_MenuName,
                "ParentMenuID" = param_ParentMenuID,
                "MenuURL" = param_MenuURL,
                "Icon" = param_Icon,
                "DisplayOrder" = param_DisplayOrder,
                "IsActive" = param_IsActive,
                "UpdatedBy" = param_UserID,
                "UpdatedAt" = CURRENT_TIMESTAMP
            WHERE "MenuID" = param_MenuID;
            param_Message := '{"status": "success", "message": "Menu updated successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Menu not found"}';
        END IF;

    -- DELETE Action (Soft Delete)
    ELSIF param_Action = 'DELETE' THEN
        IF EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuID" = param_MenuID) THEN
            UPDATE "MenuMaster"
            SET 
                "IsDeleted" = TRUE,
                "DeletedBy" = param_UserID,
                "DeletedAt" = CURRENT_TIMESTAMP
            WHERE "MenuID" = param_MenuID;
            param_Message := '{"status": "success", "message": "Menu deleted successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Menu not found"}';
        END IF;

    -- RESTORE Action
    ELSIF param_Action = 'RESTORE' THEN
        IF EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuID" = param_MenuID) THEN
            UPDATE "MenuMaster"
            SET 
                "IsDeleted" = FALSE,
                "UpdatedBy" = param_UserID,
                "UpdatedAt" = CURRENT_TIMESTAMP,
                "DeletedBy" = NULL,
                "DeletedAt" = NULL
            WHERE "MenuID" = param_MenuID;
            param_Message := '{"status": "success", "message": "Menu restored successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Menu not found"}';
        END IF;
        
    ELSE
        param_Message := '{"status": "error", "message": "Invalid Action"}';
    END IF;

EXCEPTION WHEN OTHERS THEN
    param_Message := '{"status": "error", "message": "' || SQLERRM || '"}';
END;
$$;
