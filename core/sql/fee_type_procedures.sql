-- PostgreSQL Compatible Stored Procedures for Fee Type Master

-- Function: List Fee Types with Pagination
CREATE OR REPLACE FUNCTION "Proc_FeeTypeMaster_List"(
    p_SchoolID INT,
    p_ClassID INT,
    p_SearchText VARCHAR(100),
    p_PageNo INT DEFAULT 1,
    p_PageSize INT DEFAULT 10
)
RETURNS TABLE (
    "FeeTypeId" INT,
    "SchoolId" INT,
    "SchoolName" VARCHAR,
    "ClassId" INT,
    "ClassName" VARCHAR,
    "FeeTypeName" VARCHAR,
    "DefaultAmount" DECIMAL,
    "IsActive" INT -- 0=Active, 1=Inactive
) AS $$
DECLARE
    v_Offset INT;
BEGIN
    v_Offset := (p_PageNo - 1) * p_PageSize;

    RETURN QUERY
    SELECT 
        ft."FeeTypeId",
        ft."SchoolId",
        s."SchoolName",
        ft."ClassId",
        c."ClassName",
        ft."FeeTypeName",
        CAST(ft."DefaultAmount" AS DECIMAL(18,2)),
        CAST(ft."IsActive" AS INT)
    FROM "FeeType_Master" ft
    LEFT JOIN "SchoolMaster" s ON ft."SchoolId" = s."SchoolID"
    LEFT JOIN "ClassMaster" c ON ft."ClassId" = c."ClassID"
    WHERE 
        (p_SchoolID IS NULL OR ft."SchoolId" = p_SchoolID)
        AND (p_ClassID IS NULL OR ft."ClassId" = p_ClassID)
        AND (p_SearchText IS NULL OR ft."FeeTypeName" ILIKE '%' || p_SearchText || '%')
        AND CAST(ft."IsActive" AS INT) IN (0, 1) -- Active and Inactive
    ORDER BY ft."FeeTypeName"
    LIMIT p_PageSize OFFSET v_Offset;
END;
$$ LANGUAGE plpgsql;

-- Function: Manage Fee Type (Insert, Update, Delete)
CREATE OR REPLACE FUNCTION "Proc_FeeTypeMaster_Manage"(
    p_Action VARCHAR(20),
    p_FeeTypeId INT,
    p_SchoolId INT,
    p_ClassId INT,
    p_FeeTypeName VARCHAR(100),
    p_DefaultAmount DECIMAL(18,2),
    p_IsActive BOOLEAN,    -- Python passes boolean, but DB uses INT (0=Active, 1=Inactive)
    p_UserId INT
)
RETURNS VARCHAR AS $$
DECLARE
    v_IsActiveDB BOOLEAN;
    v_Message VARCHAR(500);
    v_Status VARCHAR(20);
BEGIN
    -- Logic Inversion: DB uses False for Active (0) and True for Inactive (1)
    -- Input p_IsActive is True for Active.
    IF p_IsActive THEN
        v_IsActiveDB := FALSE; -- Active
    ELSE
        v_IsActiveDB := TRUE; -- Inactive
    END IF;

    IF p_Action = 'INSERT' THEN
        INSERT INTO "FeeType_Master" (
            "SchoolId", "ClassId", "FeeTypeName", "DefaultAmount", "IsActive", "CreatedBy", "CreatedAt"
        ) VALUES (
            p_SchoolId, p_ClassId, p_FeeTypeName, p_DefaultAmount, v_IsActiveDB, p_UserId, NOW()
        );
        
        v_Status := 'success';
        v_Message := 'Fee Type added successfully.';

    ELSIF p_Action = 'UPDATE' THEN
        UPDATE "FeeType_Master"
        SET 
            "SchoolId" = p_SchoolId,
            "ClassId" = p_ClassId,
            "FeeTypeName" = p_FeeTypeName,
            "DefaultAmount" = p_DefaultAmount,
            "IsActive" = v_IsActiveDB,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = NOW()
        WHERE "FeeTypeId" = p_FeeTypeId;
        
        v_Status := 'success';
        v_Message := 'Fee Type updated successfully.';

    ELSIF p_Action = 'DELETE' THEN
        -- Soft Delete: Set IsActive to TRUE (Inactive)
        UPDATE "FeeType_Master"
        SET 
            "IsActive" = TRUE,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = NOW()
        WHERE "FeeTypeId" = p_FeeTypeId;
        
        v_Status := 'success';
        v_Message := 'Fee Type deleted successfully.';
        
    ELSIF p_Action = 'RESTORE' THEN
        -- Restore: Set IsActive to FALSE (Active)
        UPDATE "FeeType_Master"
        SET 
            "IsActive" = FALSE,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = NOW()
        WHERE "FeeTypeId" = p_FeeTypeId;
        
        v_Status := 'success';
        v_Message := 'Fee Type restored successfully.';
    END IF;

    RETURN '{"status": "' || v_Status || '", "message": "' || v_Message || '"}';
END;
$$ LANGUAGE plpgsql;
