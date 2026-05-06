-- Subject Master PostgreSQL Functions
-- Converted from SQL Server procedures to PostgreSQL compatible functions

-- =====================================================
-- 1. LIST - Get all subjects for a school with optional class filter
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_SubjectMaster_List"(INT, INT);

CREATE OR REPLACE FUNCTION "Proc_SubjectMaster_List"(
    p_SchoolID INT,
    p_ClassId INT DEFAULT NULL
)
RETURNS TABLE (
    "SubjectID" INT,
    "SchoolID" INT,
    "ClassId" INT,
    "ClassName" VARCHAR,
    "SubjectName" VARCHAR,
    "SubjectCode" VARCHAR,
    "Description" VARCHAR,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        s."SubjectID",
        s."SchoolID",
        s."ClassId",
        c."ClassName"::VARCHAR,
        s."SubjectName"::VARCHAR,
        s."SubjectCode"::VARCHAR,
        s."Description"::VARCHAR,
        s."CreatedBy",
        s."CreatedAt"
    FROM "SubjectMaster" s
    LEFT JOIN "ClassMaster" c ON s."ClassId" = c."ClassID" AND c."IsDeleted" = FALSE
    WHERE s."SchoolID" = p_SchoolID 
    AND s."IsDeleted" = FALSE
    AND (p_ClassId IS NULL OR s."ClassId" = p_ClassId OR s."ClassId" IS NULL)
    ORDER BY s."SubjectName";
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. SAVE - Insert or Update subject
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_SubjectMaster_Save"(INT, INT, INT, VARCHAR, VARCHAR, VARCHAR, INT);

CREATE OR REPLACE FUNCTION "Proc_SubjectMaster_Save"(
    p_SubjectID INT,
    p_SchoolID INT,
    p_ClassId INT,
    p_SubjectName VARCHAR(150),
    p_SubjectCode VARCHAR(50),
    p_Description VARCHAR(500),
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR,
    "ResultID" INT
) AS $$
DECLARE
    v_SubjectID INT;
BEGIN
    -- Handle NULL or 0 SubjectID as an INSERT
    IF p_SubjectID IS NULL OR p_SubjectID = 0 THEN
        -- Check for duplicate subject name in same school
        IF EXISTS (
            SELECT 1 FROM "SubjectMaster" sm
            WHERE sm."SchoolID" = p_SchoolID 
            AND sm."SubjectName" = p_SubjectName 
            AND sm."IsDeleted" = FALSE
        ) THEN
            RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Subject name already exists'::VARCHAR, 0;
            RETURN;
        END IF;
        
        -- Insert new record
        INSERT INTO "SubjectMaster" (
            "SchoolID", "ClassId", "SubjectName", "SubjectCode", "Description",
            "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_SchoolID, p_ClassId, p_SubjectName, p_SubjectCode, p_Description,
            p_UserID, CURRENT_TIMESTAMP, FALSE
        )
        RETURNING "SubjectMaster"."SubjectID" INTO v_SubjectID;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subject created successfully'::VARCHAR, v_SubjectID;
    ELSE
        -- Update existing record
        -- Check for duplicate subject name (excluding current record)
        IF EXISTS (
            SELECT 1 FROM "SubjectMaster" sm
            WHERE sm."SchoolID" = p_SchoolID 
            AND sm."SubjectName" = p_SubjectName 
            AND sm."IsDeleted" = FALSE
            AND sm."SubjectID" != p_SubjectID
        ) THEN
            RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Subject name already exists'::VARCHAR, p_SubjectID;
            RETURN;
        END IF;
        
        UPDATE "SubjectMaster"
        SET "ClassId" = p_ClassId,
            "SubjectName" = p_SubjectName,
            "SubjectCode" = p_SubjectCode,
            "Description" = p_Description,
            "UpdatedBy" = p_UserID,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "SubjectID" = p_SubjectID AND "SchoolID" = p_SchoolID;
        
        IF FOUND THEN
            RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subject updated successfully'::VARCHAR, p_SubjectID;
        ELSE
            -- If not found, maybe it's because of SchoolID mismatch or SubjectID doesn't exist
            IF EXISTS (SELECT 1 FROM "SubjectMaster" sm WHERE sm."SubjectID" = p_SubjectID) THEN
                 RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Record found but school mismatch'::VARCHAR, p_SubjectID;
            ELSE
                 RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Record not found'::VARCHAR, p_SubjectID;
            END IF;
        END IF;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR, 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. DELETE - Soft delete subject
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_SubjectMaster_Delete"(INT, INT, INT);

CREATE OR REPLACE FUNCTION "Proc_SubjectMaster_Delete"(
    p_SubjectID INT,
    p_SchoolID INT,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
BEGIN
    UPDATE "SubjectMaster"
    SET "IsDeleted" = TRUE,
        "DeletedBy" = p_UserID,
        "DeletedAt" = CURRENT_TIMESTAMP
    WHERE "SubjectID" = p_SubjectID AND "SchoolID" = p_SchoolID;
    
    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Subject deleted successfully'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Record not found or permission denied'::VARCHAR;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
