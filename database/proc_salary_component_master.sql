-- PostgreSQL functions for Salary Component Master management

-- Function to list salary components
CREATE OR REPLACE FUNCTION "Proc_SalaryComponentMaster_List"(
    p_SchoolID INT DEFAULT NULL
)
RETURNS TABLE (
    "ComponentID" INT,
    "SchoolID" INT,
    "SchoolName" VARCHAR,
    "ComponentName" VARCHAR,
    "ComponentType" VARCHAR,
    "IsDeleted" BOOLEAN,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        s."ComponentID",
        s."SchoolID",
        sch."SchoolName"::VARCHAR,
        s."ComponentName"::VARCHAR,
        s."ComponentType"::VARCHAR,
        s."IsDeleted",
        s."CreatedBy",
        s."CreatedAt"
    FROM "SalaryComponentMaster" s
    LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
    WHERE (p_SchoolID IS NULL OR s."SchoolID" = p_SchoolID)
    ORDER BY s."ComponentType", s."ComponentName";
END;
$$ LANGUAGE plpgsql;

-- Unified Manage Function for INSERT, UPDATE, DELETE, RESTORE
CREATE OR REPLACE FUNCTION "Proc_SalaryComponentMaster_Manage"(
    p_Action VARCHAR,               -- 'INSERT' / 'UPDATE' / 'DELETE' / 'RESTORE'
    p_ComponentID INT DEFAULT NULL,
    p_SchoolID INT DEFAULT NULL,
    p_ComponentName VARCHAR DEFAULT NULL,
    p_ComponentType VARCHAR DEFAULT NULL, -- 'Earning' / 'Deduction'
    p_UserId INT DEFAULT NULL
)
RETURNS VARCHAR AS $$
DECLARE
    v_Message VARCHAR;
BEGIN
    -- INSERT Operation
    IF p_Action = 'INSERT' THEN
        -- Validation
        IF p_SchoolID IS NULL OR p_ComponentName IS NULL OR p_ComponentType IS NULL THEN
            RETURN '{"status":"error","message":"School, Name and Type are required"}';
        END IF;

        -- Duplicate Check
        IF EXISTS (
            SELECT 1 FROM "SalaryComponentMaster" 
            WHERE "SchoolID" = p_SchoolID 
            AND LOWER(TRIM("ComponentName")) = LOWER(TRIM(p_ComponentName))
            AND "IsDeleted" = FALSE
        ) THEN
            RETURN '{"status":"error","message":"A component with this name already exists"}';
        END IF;

        INSERT INTO "SalaryComponentMaster" (
            "SchoolID", "ComponentName", "ComponentType", "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_SchoolID, p_ComponentName, p_ComponentType, p_UserId, CURRENT_TIMESTAMP, FALSE
        );
        
        RETURN '{"status":"success","message":"Salary component created successfully"}';

    -- UPDATE Operation
    ELSIF p_Action = 'UPDATE' THEN
        IF p_ComponentID IS NULL THEN
            RETURN '{"status":"error","message":"Component ID is required"}';
        END IF;

        -- Duplicate Check
        IF EXISTS (
            SELECT 1 FROM "SalaryComponentMaster" 
            WHERE "SchoolID" = p_SchoolID 
            AND LOWER(TRIM("ComponentName")) = LOWER(TRIM(p_ComponentName))
            AND "ComponentID" <> p_ComponentID
            AND "IsDeleted" = FALSE
        ) THEN
            RETURN '{"status":"error","message":"Another component with this name already exists"}';
        END IF;

        UPDATE "SalaryComponentMaster"
        SET 
            "ComponentName" = p_ComponentName,
            "ComponentType" = p_ComponentType,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "ComponentID" = p_ComponentID;

        RETURN '{"status":"success","message":"Salary component updated successfully"}';

    -- DELETE Operation (Soft Delete)
    ELSIF p_Action = 'DELETE' THEN
        IF p_ComponentID IS NULL THEN
            RETURN '{"status":"error","message":"Component ID is required"}';
        END IF;

        UPDATE "SalaryComponentMaster"
        SET 
            "IsDeleted" = TRUE,
            "DeletedBy" = p_UserId,
            "DeletedAt" = CURRENT_TIMESTAMP
        WHERE "ComponentID" = p_ComponentID;

        RETURN '{"status":"success","message":"Salary component deleted successfully"}';

    -- RESTORE Operation
    ELSIF p_Action = 'RESTORE' THEN
        IF p_ComponentID IS NULL THEN
            RETURN '{"status":"error","message":"Component ID is required"}';
        END IF;

        UPDATE "SalaryComponentMaster"
        SET 
            "IsDeleted" = FALSE,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = CURRENT_TIMESTAMP,
            "DeletedBy" = NULL,
            "DeletedAt" = NULL
        WHERE "ComponentID" = p_ComponentID;

        RETURN '{"status":"success","message":"Salary component restored successfully"}';

    ELSE
        RETURN '{"status":"error","message":"Invalid Action"}';
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN '{"status":"error","message":"' || SQLERRM || '"}';
END;
$$ LANGUAGE plpgsql;
