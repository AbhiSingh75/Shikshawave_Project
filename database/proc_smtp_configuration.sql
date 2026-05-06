-- PostgreSQL functions for SMTP Configuration management
-- This file creates table and stored procedures for managing school-specific SMTP settings
-- SchoolID = NULL represents the default ShikshaWave SMTP configuration

-- Create SMTP Configuration table if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'SMTPConfiguration') THEN
        CREATE TABLE "SMTPConfiguration" (
            "ConfigID" SERIAL PRIMARY KEY,
            "SchoolID" INT REFERENCES "SchoolMaster"("SchoolID") ON DELETE CASCADE,
            "ConfigName" VARCHAR(100) NOT NULL,
            "SMTPHost" VARCHAR(255) NOT NULL,
            "SMTPPort" INT NOT NULL DEFAULT 587,
            "UseTLS" BOOLEAN DEFAULT TRUE,
            "UseSSL" BOOLEAN DEFAULT FALSE,
            "Username" VARCHAR(255) NOT NULL,
            "Password" VARCHAR(512) NOT NULL,
            "FromEmail" VARCHAR(255) NOT NULL,
            "FromName" VARCHAR(100),
            "IsActive" BOOLEAN DEFAULT TRUE,
            "IsDefault" BOOLEAN DEFAULT FALSE,
            "IsDeleted" BOOLEAN DEFAULT FALSE,
            "CreatedBy" INT,
            "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            "UpdatedBy" INT,
            "UpdatedAt" TIMESTAMP,
            "DeletedBy" INT,
            "DeletedAt" TIMESTAMP
        );
        
        -- Create index for quick lookup by SchoolID
        CREATE INDEX idx_smtp_config_school ON "SMTPConfiguration"("SchoolID");
        
        RAISE NOTICE 'Created SMTPConfiguration table';
    END IF;
END $$;

-- Function to list SMTP configurations
CREATE OR REPLACE FUNCTION "Proc_SMTPConfiguration_List"(
    p_SchoolID INT DEFAULT NULL,
    p_IncludeDefault BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    "ConfigID" INT,
    "SchoolID" INT,
    "SchoolName" VARCHAR,
    "ConfigName" VARCHAR,
    "SMTPHost" VARCHAR,
    "SMTPPort" INT,
    "UseTLS" BOOLEAN,
    "UseSSL" BOOLEAN,
    "Username" VARCHAR,
    "FromEmail" VARCHAR,
    "FromName" VARCHAR,
    "IsActive" BOOLEAN,
    "IsDefault" BOOLEAN,
    "IsDeleted" BOOLEAN,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        s."ConfigID",
        s."SchoolID",
        COALESCE(sch."SchoolName", 'ShikshaWave Default')::VARCHAR AS "SchoolName",
        s."ConfigName"::VARCHAR,
        s."SMTPHost"::VARCHAR,
        s."SMTPPort",
        s."UseTLS",
        s."UseSSL",
        s."Username"::VARCHAR,
        s."FromEmail"::VARCHAR,
        s."FromName"::VARCHAR,
        s."IsActive",
        s."IsDefault",
        s."IsDeleted",
        s."CreatedBy",
        s."CreatedAt"
    FROM "SMTPConfiguration" s
    LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
    WHERE (
        (p_SchoolID IS NULL AND p_IncludeDefault = TRUE AND s."SchoolID" IS NULL)
        OR (p_SchoolID IS NOT NULL AND s."SchoolID" = p_SchoolID)
        OR (p_SchoolID IS NULL AND p_IncludeDefault = FALSE)
    )
    ORDER BY s."SchoolID" NULLS FIRST, s."ConfigName";
END;
$$ LANGUAGE plpgsql;

-- Function to get active SMTP configuration for a school (with fallback to default)
CREATE OR REPLACE FUNCTION "Proc_SMTPConfiguration_GetBySchool"(
    p_SchoolID INT
)
RETURNS TABLE (
    "ConfigID" INT,
    "SchoolID" INT,
    "ConfigName" VARCHAR,
    "SMTPHost" VARCHAR,
    "SMTPPort" INT,
    "UseTLS" BOOLEAN,
    "UseSSL" BOOLEAN,
    "Username" VARCHAR,
    "Password" VARCHAR,
    "FromEmail" VARCHAR,
    "FromName" VARCHAR
) AS $$
BEGIN
    -- First try to get school-specific active config
    RETURN QUERY
    SELECT 
        s."ConfigID",
        s."SchoolID",
        s."ConfigName"::VARCHAR,
        s."SMTPHost"::VARCHAR,
        s."SMTPPort",
        s."UseTLS",
        s."UseSSL",
        s."Username"::VARCHAR,
        s."Password"::VARCHAR,
        s."FromEmail"::VARCHAR,
        s."FromName"::VARCHAR
    FROM "SMTPConfiguration" s
    WHERE s."SchoolID" = p_SchoolID
      AND s."IsActive" = TRUE
      AND s."IsDeleted" = FALSE
    LIMIT 1;
    
    -- If no school-specific config found, return default (SchoolID IS NULL)
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT 
            s."ConfigID",
            s."SchoolID",
            s."ConfigName"::VARCHAR,
            s."SMTPHost"::VARCHAR,
            s."SMTPPort",
            s."UseTLS",
            s."UseSSL",
            s."Username"::VARCHAR,
            s."Password"::VARCHAR,
            s."FromEmail"::VARCHAR,
            s."FromName"::VARCHAR
        FROM "SMTPConfiguration" s
        WHERE s."SchoolID" IS NULL
          AND s."IsActive" = TRUE
          AND s."IsDeleted" = FALSE
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to get default SMTP (SchoolID IS NULL)
CREATE OR REPLACE FUNCTION "Proc_SMTPConfiguration_GetDefault"()
RETURNS TABLE (
    "ConfigID" INT,
    "SMTPHost" VARCHAR,
    "SMTPPort" INT,
    "UseTLS" BOOLEAN,
    "UseSSL" BOOLEAN,
    "Username" VARCHAR,
    "Password" VARCHAR,
    "FromEmail" VARCHAR,
    "FromName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s."ConfigID",
        s."SMTPHost"::VARCHAR,
        s."SMTPPort",
        s."UseTLS",
        s."UseSSL",
        s."Username"::VARCHAR,
        s."Password"::VARCHAR,
        s."FromEmail"::VARCHAR,
        s."FromName"::VARCHAR
    FROM "SMTPConfiguration" s
    WHERE s."SchoolID" IS NULL
      AND s."IsActive" = TRUE
      AND s."IsDeleted" = FALSE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Unified Manage Function for INSERT, UPDATE, DELETE, RESTORE
CREATE OR REPLACE FUNCTION "Proc_SMTPConfiguration_Manage"(
    p_Action VARCHAR,
    p_ConfigID INT DEFAULT NULL,
    p_SchoolID INT DEFAULT NULL,
    p_ConfigName VARCHAR DEFAULT NULL,
    p_SMTPHost VARCHAR DEFAULT NULL,
    p_SMTPPort INT DEFAULT NULL,
    p_UseTLS BOOLEAN DEFAULT NULL,
    p_UseSSL BOOLEAN DEFAULT NULL,
    p_Username VARCHAR DEFAULT NULL,
    p_Password VARCHAR DEFAULT NULL,
    p_FromEmail VARCHAR DEFAULT NULL,
    p_FromName VARCHAR DEFAULT NULL,
    p_IsActive BOOLEAN DEFAULT NULL,
    p_IsDefault BOOLEAN DEFAULT NULL,
    p_UserId INT DEFAULT NULL
)
RETURNS VARCHAR AS $$
DECLARE
    v_NewConfigID INT;
BEGIN
    -- INSERT Operation
    IF p_Action = 'INSERT' THEN
        -- Validation
        IF p_ConfigName IS NULL OR p_SMTPHost IS NULL OR p_Username IS NULL OR p_Password IS NULL OR p_FromEmail IS NULL THEN
            RETURN '{"status":"error","message":"Config Name, SMTP Host, Username, Password and From Email are required"}';
        END IF;

        -- Check for duplicate active config for same school
        IF EXISTS (
            SELECT 1 FROM "SMTPConfiguration" 
            WHERE (
                (p_SchoolID IS NULL AND "SchoolID" IS NULL) 
                OR "SchoolID" = p_SchoolID
            )
            AND "IsActive" = TRUE
            AND "IsDeleted" = FALSE
        ) THEN
            -- Deactivate existing config if setting new one as active
            IF COALESCE(p_IsActive, TRUE) = TRUE THEN
                UPDATE "SMTPConfiguration"
                SET "IsActive" = FALSE, "UpdatedBy" = p_UserId, "UpdatedAt" = CURRENT_TIMESTAMP
                WHERE (
                    (p_SchoolID IS NULL AND "SchoolID" IS NULL) 
                    OR "SchoolID" = p_SchoolID
                )
                AND "IsActive" = TRUE
                AND "IsDeleted" = FALSE;
            END IF;
        END IF;

        INSERT INTO "SMTPConfiguration" (
            "SchoolID", "ConfigName", "SMTPHost", "SMTPPort", "UseTLS", "UseSSL",
            "Username", "Password", "FromEmail", "FromName", "IsActive", "IsDefault",
            "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_SchoolID, p_ConfigName, p_SMTPHost, COALESCE(p_SMTPPort, 587), 
            COALESCE(p_UseTLS, TRUE), COALESCE(p_UseSSL, FALSE),
            p_Username, p_Password, p_FromEmail, p_FromName, 
            COALESCE(p_IsActive, TRUE), COALESCE(p_IsDefault, FALSE),
            p_UserId, CURRENT_TIMESTAMP, FALSE
        )
        RETURNING "ConfigID" INTO v_NewConfigID;
        
        RETURN '{"status":"success","message":"SMTP configuration created successfully","configId":' || v_NewConfigID || '}';

    -- UPDATE Operation
    ELSIF p_Action = 'UPDATE' THEN
        IF p_ConfigID IS NULL THEN
            RETURN '{"status":"error","message":"Config ID is required for update"}';
        END IF;

        -- If setting as active, deactivate other configs for same school
        IF COALESCE(p_IsActive, FALSE) = TRUE THEN
            UPDATE "SMTPConfiguration"
            SET "IsActive" = FALSE, "UpdatedBy" = p_UserId, "UpdatedAt" = CURRENT_TIMESTAMP
            WHERE "ConfigID" <> p_ConfigID
            AND (
                SELECT "SchoolID" FROM "SMTPConfiguration" WHERE "ConfigID" = p_ConfigID
            ) IS NOT DISTINCT FROM "SchoolID"
            AND "IsActive" = TRUE
            AND "IsDeleted" = FALSE;
        END IF;

        UPDATE "SMTPConfiguration"
        SET 
            "ConfigName" = COALESCE(p_ConfigName, "ConfigName"),
            "SMTPHost" = COALESCE(p_SMTPHost, "SMTPHost"),
            "SMTPPort" = COALESCE(p_SMTPPort, "SMTPPort"),
            "UseTLS" = COALESCE(p_UseTLS, "UseTLS"),
            "UseSSL" = COALESCE(p_UseSSL, "UseSSL"),
            "Username" = COALESCE(p_Username, "Username"),
            "Password" = CASE WHEN p_Password IS NOT NULL AND p_Password <> '' THEN p_Password ELSE "Password" END,
            "FromEmail" = COALESCE(p_FromEmail, "FromEmail"),
            "FromName" = COALESCE(p_FromName, "FromName"),
            "IsActive" = COALESCE(p_IsActive, "IsActive"),
            "IsDefault" = COALESCE(p_IsDefault, "IsDefault"),
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "ConfigID" = p_ConfigID;

        RETURN '{"status":"success","message":"SMTP configuration updated successfully"}';

    -- DELETE Operation (Soft Delete)
    ELSIF p_Action = 'DELETE' THEN
        IF p_ConfigID IS NULL THEN
            RETURN '{"status":"error","message":"Config ID is required for delete"}';
        END IF;

        UPDATE "SMTPConfiguration"
        SET 
            "IsDeleted" = TRUE,
            "IsActive" = FALSE,
            "DeletedBy" = p_UserId,
            "DeletedAt" = CURRENT_TIMESTAMP
        WHERE "ConfigID" = p_ConfigID;

        RETURN '{"status":"success","message":"SMTP configuration deleted successfully"}';

    -- RESTORE Operation
    ELSIF p_Action = 'RESTORE' THEN
        IF p_ConfigID IS NULL THEN
            RETURN '{"status":"error","message":"Config ID is required for restore"}';
        END IF;

        UPDATE "SMTPConfiguration"
        SET 
            "IsDeleted" = FALSE,
            "UpdatedBy" = p_UserId,
            "UpdatedAt" = CURRENT_TIMESTAMP,
            "DeletedBy" = NULL,
            "DeletedAt" = NULL
        WHERE "ConfigID" = p_ConfigID;

        RETURN '{"status":"success","message":"SMTP configuration restored successfully"}';

    ELSE
        RETURN '{"status":"error","message":"Invalid Action. Use INSERT, UPDATE, DELETE, or RESTORE"}';
    END IF;

EXCEPTION WHEN OTHERS THEN
    RETURN '{"status":"error","message":"' || SQLERRM || '"}';
END;
$$ LANGUAGE plpgsql;
