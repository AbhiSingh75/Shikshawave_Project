-- Admission Instructions PostgreSQL Functions
-- Converted from SQL Server procedures to PostgreSQL compatible functions

-- =====================================================
-- 1. LIST - Get all instructions for a school
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_AdmissionInstructions_List"(INT);

CREATE OR REPLACE FUNCTION "Proc_AdmissionInstructions_List"(
    p_SchoolID INT
)
RETURNS TABLE (
    "InstructionID" INT,
    "InstructionTitle" VARCHAR,
    "InstructionText" VARCHAR,
    "DisplayOrder" INT,
    "IsActive" BOOLEAN,
    "CreatedAt" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        ai."InstructionID",
        ai."InstructionTitle"::VARCHAR,
        ai."InstructionText"::VARCHAR,
        ai."DisplayOrder",
        ai."IsActive",
        ai."CreatedAt"
    FROM "AdmissionInstructions" ai
    WHERE ai."SchoolID" = p_SchoolID AND ai."IsDeleted" = FALSE
    ORDER BY ai."DisplayOrder", ai."InstructionID";
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 2. SAVE - Insert or Update an instruction
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_AdmissionInstructions_Save"(INT, INT, VARCHAR, VARCHAR, INT, BOOLEAN, INT);

CREATE OR REPLACE FUNCTION "Proc_AdmissionInstructions_Save"(
    p_InstructionID INT,
    p_SchoolID INT,
    p_InstructionTitle VARCHAR(200),
    p_InstructionText VARCHAR(1000),
    p_DisplayOrder INT,
    p_IsActive BOOLEAN,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
DECLARE
    v_Id INT;
BEGIN
    IF p_InstructionID IS NULL OR p_InstructionID = 0 THEN
        -- Insert new record
        INSERT INTO "AdmissionInstructions" (
            "SchoolID", "InstructionTitle", "InstructionText", 
            "DisplayOrder", "IsActive", "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_SchoolID, p_InstructionTitle, p_InstructionText, 
            p_DisplayOrder, p_IsActive, p_UserID, CURRENT_TIMESTAMP, FALSE
        );
        
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Instruction added successfully'::VARCHAR;
    ELSE
        -- Update existing record
        UPDATE "AdmissionInstructions" ai
        SET "InstructionTitle" = p_InstructionTitle,
            "InstructionText" = p_InstructionText,
            "DisplayOrder" = p_DisplayOrder,
            "IsActive" = p_IsActive,
            "ModifiedBy" = p_UserID,
            "ModifiedAt" = CURRENT_TIMESTAMP
        WHERE ai."InstructionID" = p_InstructionID 
          AND ai."SchoolID" = p_SchoolID 
          AND ai."IsDeleted" = FALSE;
        
        IF FOUND THEN
            RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Instruction updated successfully'::VARCHAR;
        ELSE
            RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Instruction not found or permission denied'::VARCHAR;
        END IF;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 3. DELETE - Soft delete an instruction
-- =====================================================
DROP FUNCTION IF EXISTS "Proc_AdmissionInstructions_Delete"(INT, INT, INT);

CREATE OR REPLACE FUNCTION "Proc_AdmissionInstructions_Delete"(
    p_InstructionID INT,
    p_SchoolID INT,
    p_UserID INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
BEGIN
    UPDATE "AdmissionInstructions" ai
    SET "IsDeleted" = TRUE,
        "ModifiedBy" = p_UserID,
        "ModifiedAt" = CURRENT_TIMESTAMP
    WHERE ai."InstructionID" = p_InstructionID 
      AND ai."SchoolID" = p_SchoolID;
    
    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Instruction deleted successfully'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Instruction not found or permission denied'::VARCHAR;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
