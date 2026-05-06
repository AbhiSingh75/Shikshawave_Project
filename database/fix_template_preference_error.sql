-- Fix for Template Preference Save Error
-- This script replaces the restrictive unique constraint with a partial unique index
-- and redefines the Proc_Template_Preference_Save function to be more robust.

-- 1. Redefine Unique Constraint
-- Drop the existing constraint if it exists (check both possible names)
ALTER TABLE "TemplateSettings" DROP CONSTRAINT IF EXISTS "UQ_TemplateSettings_School_TemplateType_IsDeleted";
ALTER TABLE "TemplateSettings" DROP CONSTRAINT IF EXISTS "UQ_TemplateSettings_SchoolID_TemplateType_IsDeleted";

-- Create a partial unique index that only applies to ACTIVE (not deleted) records.
-- This allows multiple soft-deleted records for history but only one active template at a time.
DROP INDEX IF EXISTS "UQ_TemplateSettings_Active_Only";
CREATE UNIQUE INDEX "UQ_TemplateSettings_Active_Only" 
ON "TemplateSettings" ("SchoolID", "TemplateType") 
WHERE "IsDeleted" = FALSE;

-- 2. Redefine Save Function
-- This version updates the existing active record instead of soft-deleting and re-inserting,
-- which avoids unnecessary row growth and potential constraint issues.
CREATE OR REPLACE FUNCTION "Proc_Template_Preference_Save"(
    p_schoolid INTEGER,
    p_templatetype CHARACTER VARYING,
    p_templatefile CHARACTER VARYING,
    p_createdby INTEGER
)
RETURNS TABLE (
    "Status" CHARACTER VARYING,
    "Message" CHARACTER VARYING
) AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    -- Check if an active preference already exists
    SELECT EXISTS (
        SELECT 1 FROM "TemplateSettings" 
        WHERE "SchoolID" = p_schoolid 
          AND "TemplateType" = p_templatetype 
          AND "IsDeleted" = FALSE
    ) INTO v_exists;

    IF v_exists THEN
        -- Update existing active record
        UPDATE "TemplateSettings"
        SET "TemplateFile" = p_templatefile,
            "ModifiedAt" = CURRENT_TIMESTAMP,
            "ModifiedBy" = p_createdby,
            "IsActive" = TRUE
        WHERE "SchoolID" = p_schoolid 
          AND "TemplateType" = p_templatetype 
          AND "IsDeleted" = FALSE;
        
        RETURN QUERY SELECT 'SUCCESS'::CHARACTER VARYING, 'Template preference updated successfully'::CHARACTER VARYING;
    ELSE
        -- Insert new active record
        INSERT INTO "TemplateSettings" (
            "SchoolID", "TemplateType", "TemplateName", "TemplateFile", 
            "IsActive", "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_schoolid, p_templatetype, p_templatetype, p_templatefile, 
            TRUE, p_createdby, CURRENT_TIMESTAMP, FALSE
        );
        
        RETURN QUERY SELECT 'SUCCESS'::CHARACTER VARYING, 'Template preference created successfully'::CHARACTER VARYING;
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::CHARACTER VARYING, SQLERRM::CHARACTER VARYING;
END;
$$ LANGUAGE plpgsql;
