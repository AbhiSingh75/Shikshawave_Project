-- Implementation of Email Template procedures for PostgreSQL

-- 1. Proc_EmailTemplate_List
CREATE OR REPLACE FUNCTION "Proc_EmailTemplate_List"(
    mint_userId INTEGER,
    mint_SchoolId INTEGER,
    mstr_search CHARACTER VARYING DEFAULT NULL
)
RETURNS TABLE (
    "Id" INTEGER,
    "Code" CHARACTER VARYING,
    "SchoolId" INTEGER,
    "Language" CHARACTER VARYING,
    "SubjectTemplate" TEXT,
    "BodyTextTemplate" TEXT,
    "BodyHtmlTemplate" TEXT,
    "DefaultFrom" CHARACTER VARYING,
    "Cc" TEXT,
    "Bcc" TEXT,
    "Placeholders" TEXT,
    "IsActive" BOOLEAN,
    "CreatedAt" TIMESTAMP WITH TIME ZONE,
    "UpdatedAt" TIMESTAMP WITH TIME ZONE,
    "SchoolName" CHARACTER VARYING,
    "SchoolCode" CHARACTER VARYING
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        et."Id", et."Code", et."SchoolId", et."Language", et."SubjectTemplate", 
        et."BodyTextTemplate", et."BodyHtmlTemplate", et."DefaultFrom", 
        et."Cc", et."Bcc", et."Placeholders", et."IsActive", et."CreatedAt", et."UpdatedAt",
        s."SchoolName", s."SchoolCode"
    FROM "EmailTemplate" et
    LEFT JOIN "SchoolMaster" s ON et."SchoolId" = s."SchoolID"
    WHERE (mint_SchoolId IS NULL OR et."SchoolId" = mint_SchoolId OR et."SchoolId" IS NULL)
      AND (mstr_search IS NULL OR et."Code" ILIKE '%' || mstr_search || '%' OR et."SubjectTemplate" ILIKE '%' || mstr_search || '%')
    ORDER BY et."UpdatedAt" DESC;
END;
$$ LANGUAGE plpgsql;

-- 2. Proc_EmailTemplate_Manage
CREATE OR REPLACE FUNCTION "Proc_EmailTemplate_Manage"(
    p_action CHARACTER VARYING,
    p_id INTEGER DEFAULT NULL,
    p_code CHARACTER VARYING DEFAULT NULL,
    p_schoolId INTEGER DEFAULT NULL,
    p_language CHARACTER VARYING DEFAULT 'en',
    p_subject CHARACTER VARYING DEFAULT NULL,
    p_bodyText TEXT DEFAULT NULL,
    p_bodyHtml TEXT DEFAULT NULL,
    p_defaultFrom CHARACTER VARYING DEFAULT NULL,
    p_cc TEXT DEFAULT NULL,
    p_bcc TEXT DEFAULT NULL,
    p_placeholders TEXT DEFAULT NULL,
    p_isActive BOOLEAN DEFAULT TRUE,
    p_userId INTEGER DEFAULT NULL
)
RETURNS TABLE ("Message" TEXT) AS $$
DECLARE
    v_msg TEXT;
BEGIN
    IF p_action = 'INSERT' THEN
        INSERT INTO "EmailTemplate" (
            "Code", "SchoolId", "Language", "SubjectTemplate", 
            "BodyTextTemplate", "BodyHtmlTemplate", "DefaultFrom", 
            "Cc", "Bcc", "Placeholders", "IsActive", "CreatedAt", "UpdatedAt"
        ) VALUES (
            p_code, p_schoolId, p_language, p_subject, 
            p_bodyText, p_bodyHtml, p_defaultFrom, 
            p_cc, p_bcc, p_placeholders, p_isActive, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        );
        v_msg := '✅ Email template created successfully.';
        
    ELSIF p_action = 'UPDATE' THEN
        UPDATE "EmailTemplate" SET
            "Code" = COALESCE(p_code, "EmailTemplate"."Code"),
            "SchoolId" = p_schoolId, -- Allow setting to NULL
            "Language" = COALESCE(p_language, "EmailTemplate"."Language"),
            "SubjectTemplate" = COALESCE(p_subject, "EmailTemplate"."SubjectTemplate"),
            "BodyTextTemplate" = p_bodyText,
            "BodyHtmlTemplate" = p_bodyHtml,
            "DefaultFrom" = p_defaultFrom,
            "Cc" = p_cc,
            "Bcc" = p_bcc,
            "Placeholders" = p_placeholders,
            "IsActive" = p_isActive,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "Id" = p_id;
        v_msg := '✅ Email template updated successfully.';
        
    ELSIF p_action = 'DELETE' THEN
        -- Soft delete by setting IsActive = FALSE
        UPDATE "EmailTemplate" SET "IsActive" = FALSE, "UpdatedAt" = CURRENT_TIMESTAMP WHERE "Id" = p_id;
        v_msg := '🗑️ Email template moved to inactive successfully.';
        
    ELSIF p_action = 'RESTORE' THEN
        -- Restore by setting IsActive = TRUE
        UPDATE "EmailTemplate" SET "IsActive" = TRUE, "UpdatedAt" = CURRENT_TIMESTAMP WHERE "Id" = p_id;
        v_msg := '♻️ Email template restored successfully.';
    END IF;

    RETURN QUERY SELECT v_msg;
END;
$$ LANGUAGE plpgsql;
