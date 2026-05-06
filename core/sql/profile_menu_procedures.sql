-- Function to List Profile Menu Mappings
DROP FUNCTION IF EXISTS Proc_ProfileMenuMapping_List(INT);

CREATE OR REPLACE FUNCTION Proc_ProfileMenuMapping_List(param_ProfileID INT DEFAULT NULL)
RETURNS TABLE (
    "MappingID" INT,
    "ProfileID" INT,
    "ProfileName" VARCHAR,
    "MenuID" INT,
    "MenuName" VARCHAR,
    "CanView" BOOLEAN,
    "CanAdd" BOOLEAN,
    "CanEdit" BOOLEAN,
    "CanDelete" BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pmm."MappingID",
        pmm."ProfileID",
        p."ProfileName",
        pmm."MenuID",
        m."MenuName",
        pmm."CanView",
        pmm."CanAdd",
        pmm."CanEdit",
        pmm."CanDelete"
    FROM "ProfileMenuMapping" pmm
    JOIN "ProfileMaster" p ON pmm."ProfileID" = p."ProfileID"
    JOIN "MenuMaster" m ON pmm."MenuID" = m."MenuID"
    WHERE COALESCE(pmm."IsDeleted", FALSE) = FALSE
      AND (param_ProfileID IS NULL OR pmm."ProfileID" = param_ProfileID)
    ORDER BY p."ProfileName", m."MenuName";
END;
$$ LANGUAGE plpgsql;

-- Procedure to Manage Profile Menu Mappings
DROP PROCEDURE IF EXISTS Proc_ProfileMenuMapping_Manage;

CREATE OR REPLACE PROCEDURE Proc_ProfileMenuMapping_Manage(
    param_Action VARCHAR,
    param_MappingID INT,
    param_ProfileID INT,
    param_MenuID INT,
    param_CanView INT,   -- Python passes 0/1 integer validation
    param_CanAdd INT,
    param_CanEdit INT,
    param_CanDelete INT,
    param_UserID INT,
    INOUT param_Message VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    -- Convert Integer flags to Boolean
    val_CanView BOOLEAN := (param_CanView = 1);
    val_CanAdd BOOLEAN := (param_CanAdd = 1);
    val_CanEdit BOOLEAN := (param_CanEdit = 1);
    val_CanDelete BOOLEAN := (param_CanDelete = 1);
BEGIN
    -- INSERT Action
    IF param_Action = 'INSERT' THEN
        -- Check duplicate
        IF EXISTS (SELECT 1 FROM "ProfileMenuMapping" WHERE "ProfileID" = param_ProfileID AND "MenuID" = param_MenuID AND "IsDeleted" = FALSE) THEN
             param_Message := '{"status": "error", "message": "Mapping already exists for this Profile and Menu"}';
        ELSE
            INSERT INTO "ProfileMenuMapping" (
                "ProfileID", "MenuID", "CanView", "CanAdd", "CanEdit", "CanDelete", 
                "CreatedBy", "CreatedAt", "IsDeleted"
            ) VALUES (
                param_ProfileID, param_MenuID, val_CanView, val_CanAdd, val_CanEdit, val_CanDelete,
                param_UserID, CURRENT_TIMESTAMP, FALSE
            );
            param_Message := '{"status": "success", "message": "Profile menu mapping added successfully"}';
        END IF;

    -- UPDATE Action
    ELSIF param_Action = 'UPDATE' THEN
        IF EXISTS (SELECT 1 FROM "ProfileMenuMapping" WHERE "MappingID" = param_MappingID) THEN
            UPDATE "ProfileMenuMapping"
            SET 
                "ProfileID" = param_ProfileID,
                "MenuID" = param_MenuID,
                "CanView" = val_CanView,
                "CanAdd" = val_CanAdd,
                "CanEdit" = val_CanEdit,
                "CanDelete" = val_CanDelete,
                -- "UpdatedBy" columns not defined in standard Django model for this table usually? 
                -- Wait, models.py usually has CreatedBy but maybe not UpdatedBy?
                -- Checking models.py above: CreatedBy, DeletedBy. NO UpdatedBy!
                -- Ah, let's re-read models.py in step 929.
                -- It DOES NOT have UpdatedBy. It DOES have CreatedBy, DeletedBy.
                -- So we won't update any auditing columns for update unless we add them. 
                -- We will just update fields.
                "IsDeleted" = FALSE -- Ensure it is active
            WHERE "MappingID" = param_MappingID;
            
            param_Message := '{"status": "success", "message": "Profile menu mapping updated successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Mapping not found"}';
        END IF;

    -- DELETE Action
    ELSIF param_Action = 'DELETE' THEN
        IF EXISTS (SELECT 1 FROM "ProfileMenuMapping" WHERE "MappingID" = param_MappingID) THEN
            UPDATE "ProfileMenuMapping"
            SET 
                "IsDeleted" = TRUE,
                "DeletedBy" = param_UserID,
                "DeletedAt" = CURRENT_TIMESTAMP
            WHERE "MappingID" = param_MappingID;
            param_Message := '{"status": "success", "message": "Profile menu mapping deleted successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Mapping not found"}';
        END IF;

    -- RESTORE Action
    ELSIF param_Action = 'RESTORE' THEN
        IF EXISTS (SELECT 1 FROM "ProfileMenuMapping" WHERE "MappingID" = param_MappingID) THEN
            UPDATE "ProfileMenuMapping"
            SET 
                "IsDeleted" = FALSE,
                "DeletedBy" = NULL,
                "DeletedAt" = NULL
            WHERE "MappingID" = param_MappingID;
            param_Message := '{"status": "success", "message": "Profile menu mapping restored successfully"}';
        ELSE
            param_Message := '{"status": "error", "message": "Mapping not found"}';
        END IF;

    ELSE
        param_Message := '{"status": "error", "message": "Invalid Action"}';
    END IF;

EXCEPTION WHEN OTHERS THEN
    param_Message := '{"status": "error", "message": "' || SQLERRM || '"}';
END;
$$;
