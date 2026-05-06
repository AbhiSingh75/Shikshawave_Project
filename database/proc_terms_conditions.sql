-- Terms & Conditions PostgreSQL Functions
-- Converted from SQL Server procedures to PostgreSQL compatible functions

-- =====================================================
-- 1. LIST - Get all terms & conditions for a school
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_TermsConditions_List"(INT);

CREATE OR REPLACE FUNCTION "Proc_TermsConditions_List"(
    p_SchoolID INT
)
RETURNS TABLE (
    "Id" INT,
    "SchoolId" INT,
    "Title" VARCHAR,
    "Description" TEXT,
    "Category" VARCHAR,
    "IsActive" BOOLEAN,
    "DisplayOrder" INT,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMPTZ,
    "UpdatedBy" INT,
    "UpdatedAt" TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        tc."Id",
        tc."SchoolId",
        tc."Title"::VARCHAR,
        tc."Description"::TEXT,
        tc."Category"::VARCHAR,
        tc."IsActive",
        tc."DisplayOrder",
        tc."CreatedBy",
        tc."CreatedAt",
        tc."UpdatedBy",
        tc."UpdatedAt"
    FROM "TermsConditions" tc
    WHERE tc."SchoolId" = p_SchoolID
    ORDER BY tc."DisplayOrder", tc."Id";
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. SAVE - Insert or Update terms & conditions
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_TermsConditions_Save"(INT, INT, VARCHAR, TEXT, VARCHAR, BOOLEAN, INT, INT);

CREATE OR REPLACE FUNCTION "Proc_TermsConditions_Save"(
    p_Id INT,
    p_SchoolID INT,
    p_Title VARCHAR(200),
    p_Description TEXT,
    p_Category VARCHAR(100),
    p_IsActive BOOLEAN,
    p_DisplayOrder INT,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR,
    "Id" INT
) AS $$
DECLARE
    v_Id INT;
BEGIN
    IF p_Id IS NULL OR p_Id = 0 THEN
        -- Insert new record
        INSERT INTO "TermsConditions" (
            "SchoolId", "Title", "Description", "Category", 
            "IsActive", "DisplayOrder", "CreatedBy", "CreatedAt", "UpdatedBy", "UpdatedAt"
        ) VALUES (
            p_SchoolID, p_Title, p_Description, p_Category, 
            p_IsActive, p_DisplayOrder, p_UserID, CURRENT_TIMESTAMP, p_UserID, CURRENT_TIMESTAMP
        )
        RETURNING "TermsConditions"."Id" INTO v_Id;
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Terms & Conditions added successfully'::VARCHAR, v_Id;
    ELSE
        -- Update existing record
        UPDATE "TermsConditions" tc
        SET "Title" = p_Title,
            "Description" = p_Description,
            "Category" = p_Category,
            "IsActive" = p_IsActive,
            "DisplayOrder" = p_DisplayOrder,
            "UpdatedBy" = p_UserID,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE tc."Id" = p_Id AND tc."SchoolId" = p_SchoolID;
        
        IF FOUND THEN
            RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Terms & Conditions updated successfully'::VARCHAR, p_Id;
        ELSE
            RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Record not found or permission denied'::VARCHAR, 0;
        END IF;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR, 0;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. DELETE - Delete terms & conditions
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_TermsConditions_Delete"(INT, INT);

CREATE OR REPLACE FUNCTION "Proc_TermsConditions_Delete"(
    p_Id INT,
    p_SchoolID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
BEGIN
    DELETE FROM "TermsConditions" tc
    WHERE tc."Id" = p_Id AND tc."SchoolId" = p_SchoolID;
    
    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Terms & Conditions deleted successfully'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Record not found or permission denied'::VARCHAR;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
