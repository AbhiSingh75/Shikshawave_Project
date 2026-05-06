-- Academic Year Stored Procedures
-- Fixed: Using table alias to avoid column name ambiguity

-- 1. Upsert (Insert/Update)
DROP FUNCTION IF EXISTS "Proc_AcademicYear_Set"(INT, INT, VARCHAR, DATE, DATE, BOOLEAN, BOOLEAN, INT);

CREATE OR REPLACE FUNCTION "Proc_AcademicYear_Set"(
    p_AcademicYearID INT,
    p_SchoolID INT,
    p_AcademicYear VARCHAR(20),
    p_StartDate DATE,
    p_EndDate DATE,
    p_IsCurrent BOOLEAN,
    p_IsActive BOOLEAN,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR,
    "AcademicYearID" INT
) AS $$
DECLARE
    v_Id INT;
BEGIN
    -- If p_IsCurrent is TRUE, set all other years for this school to FALSE
    IF p_IsCurrent THEN
        UPDATE "AcademicYear" ay
        SET "IsCurrent" = FALSE,
            "UpdatedBy" = p_UserID,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE ay."SchoolID" = p_SchoolID;
    END IF;

    IF p_AcademicYearID IS NULL OR p_AcademicYearID = 0 THEN
        -- Insert new record
        INSERT INTO "AcademicYear" (
            "SchoolID", "AcademicYear", "StartDate", "EndDate", 
            "IsCurrent", "IsActive", "CreatedBy", "CreatedAt"
        ) VALUES (
            p_SchoolID, p_AcademicYear, p_StartDate, p_EndDate, 
            p_IsCurrent, p_IsActive, p_UserID, CURRENT_TIMESTAMP
        );
        
        -- Get the inserted ID
        SELECT currval(pg_get_serial_sequence('"AcademicYear"', 'AcademicYearID')) INTO v_Id;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Academic Year created successfully'::VARCHAR, v_Id;
    ELSE
        -- Update existing record
        UPDATE "AcademicYear" ay
        SET "AcademicYear" = p_AcademicYear,
            "StartDate" = p_StartDate,
            "EndDate" = p_EndDate,
            "IsCurrent" = p_IsCurrent,
            "IsActive" = p_IsActive,
            "UpdatedBy" = p_UserID,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE ay."AcademicYearID" = p_AcademicYearID;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Academic Year updated successfully'::VARCHAR, p_AcademicYearID;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR, 0;
END;
$$ LANGUAGE plpgsql;

-- 2. List
DROP FUNCTION IF EXISTS "Proc_AcademicYear_List"(INT);

CREATE OR REPLACE FUNCTION "Proc_AcademicYear_List"(
    p_SchoolID INT
)
RETURNS TABLE (
    "AcademicYearID" INT,
    "SchoolID" INT,
    "AcademicYear" VARCHAR,
    "StartDate" DATE,
    "EndDate" DATE,
    "IsCurrent" BOOLEAN,
    "IsActive" BOOLEAN
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        ay."AcademicYearID",
        ay."SchoolID",
        ay."AcademicYear"::VARCHAR,
        ay."StartDate",
        ay."EndDate",
        ay."IsCurrent",
        ay."IsActive"
    FROM "AcademicYear" ay
    WHERE ay."SchoolID" = p_SchoolID
    ORDER BY ay."StartDate" DESC;
END;
$$ LANGUAGE plpgsql;

-- 3. Delete
DROP FUNCTION IF EXISTS "Proc_AcademicYear_Delete"(INT, INT, INT);

CREATE OR REPLACE FUNCTION "Proc_AcademicYear_Delete"(
    p_AcademicYearID INT,
    p_SchoolID INT,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
BEGIN
    DELETE FROM "AcademicYear" ay
    WHERE ay."AcademicYearID" = p_AcademicYearID AND ay."SchoolID" = p_SchoolID;
    
    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Academic Year deleted successfully'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Academic Year not found or permission denied'::VARCHAR;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
