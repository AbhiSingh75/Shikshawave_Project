CREATE OR REPLACE FUNCTION "Proc_User_Manage"(
    p_Action TEXT,
    p_UserID INT DEFAULT NULL,
    p_UserName TEXT DEFAULT NULL,
    p_Email TEXT DEFAULT NULL,
    p_Phone TEXT DEFAULT NULL,
    p_ProfileID INT DEFAULT NULL,
    p_SchoolID INT DEFAULT NULL,
    p_UserPhoto BYTEA DEFAULT NULL,
    p_PasswordHash TEXT DEFAULT NULL,
    p_CreatedBy INT DEFAULT NULL,
    p_ModifiedBy INT DEFAULT NULL
)
RETURNS TABLE (
    "Status" TEXT,
    "Message" TEXT,
    "NewUserID" INT
) AS $$
DECLARE
    v_NewUserCode TEXT;
    v_NewUserID INT;
BEGIN
    IF p_Action = 'INSERT' THEN
        -- Generate UserCode (Pattern: SUS0000001)
        SELECT 'SUS' || LPAD((COALESCE(MAX(CAST(NULLIF(SUBSTRING("UserCode", 4), '') AS INT)), 0) + 1)::TEXT, 7, '0')
        INTO v_NewUserCode
        FROM "UserMaster";

        INSERT INTO "UserMaster" (
            "UserCode", "UserName", "PasswordHash", "Email", "Phone", 
            "ProfileID", "SchoolID", "UserPhoto", "IsActive", 
            "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            v_NewUserCode, p_UserName, p_PasswordHash, p_Email, p_Phone,
            p_ProfileID, p_SchoolID, p_UserPhoto, TRUE,
            p_CreatedBy, CURRENT_TIMESTAMP, FALSE
        ) RETURNING "UserID" INTO v_NewUserID;

        RETURN QUERY SELECT 'SUCCESS'::TEXT, 'User created successfully.'::TEXT, v_NewUserID;

    ELSIF p_Action = 'UPDATE' THEN
        UPDATE "UserMaster"
        SET "UserName" = COALESCE(p_UserName, "UserName"),
            "Email" = COALESCE(p_Email, "Email"),
            "Phone" = COALESCE(p_Phone, "Phone"),
            "ProfileID" = COALESCE(p_ProfileID, "ProfileID"),
            "SchoolID" = p_SchoolID, -- Explicitly set p_SchoolID which could be NULL
            "UserPhoto" = CASE WHEN p_UserPhoto IS NOT NULL THEN p_UserPhoto ELSE "UserPhoto" END,
            "PasswordHash" = CASE WHEN p_PasswordHash IS NOT NULL AND p_PasswordHash <> '' THEN p_PasswordHash ELSE "PasswordHash" END,
            "UpdatedBy" = p_ModifiedBy,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "UserID" = p_UserID AND "IsDeleted" = FALSE;

        IF FOUND THEN
            RETURN QUERY SELECT 'SUCCESS'::TEXT, 'User updated successfully.'::TEXT, p_UserID;
        ELSE
            RETURN QUERY SELECT 'FAILED'::TEXT, 'User not found or update failed.'::TEXT, p_UserID;
        END IF;

    ELSE
        RETURN QUERY SELECT 'FAILED'::TEXT, 'Invalid Action.'::TEXT, NULL::INT;
    END IF;
END;
$$ LANGUAGE plpgsql;
