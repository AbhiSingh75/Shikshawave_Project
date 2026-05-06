CREATE OR REPLACE FUNCTION "Proc_User_Manage"(
    p_Action VARCHAR,
    p_UserID INT DEFAULT NULL,
    p_UserName VARCHAR DEFAULT NULL,
    p_PasswordHash VARCHAR DEFAULT NULL,
    p_Email VARCHAR DEFAULT NULL,
    p_Phone VARCHAR DEFAULT NULL,
    p_ProfileID INT DEFAULT NULL,
    p_SchoolID INT DEFAULT NULL,
    p_UserPhoto BYTEA DEFAULT NULL,
    p_CreatedBy INT DEFAULT NULL,
    p_ModifiedBy INT DEFAULT NULL
) RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR,
    "NewUserID" INT
) AS $$
DECLARE
    v_Status VARCHAR;
    v_Message VARCHAR;
    v_NewUserID INT;
BEGIN
    IF p_Action = 'INSERT' THEN
        INSERT INTO "UserMaster" (
            "UserName", "PasswordHash", "Email", "Phone", "ProfileID", "SchoolID", "UserPhoto", 
            "IsActive", "CreatedBy", "CreatedAt", "IsDeleted"
        ) VALUES (
            p_UserName, p_PasswordHash, p_Email, p_Phone, p_ProfileID, p_SchoolID, p_UserPhoto,
            TRUE, p_CreatedBy, CURRENT_TIMESTAMP, FALSE
        ) RETURNING "UserID" INTO v_NewUserID;
        
        v_Status := 'SUCCESS';
        v_Message := 'User created successfully';
        
    ELSIF p_Action = 'UPDATE' THEN
        UPDATE "UserMaster" SET
            "UserName" = COALESCE(p_UserName, "UserName"),
            "Email" = COALESCE(p_Email, "Email"),
            "Phone" = COALESCE(p_Phone, "Phone"),
            "ProfileID" = COALESCE(p_ProfileID, "ProfileID"),
            "SchoolID" = p_SchoolID, -- Allow setting to NULL
            "UserPhoto" = COALESCE(p_UserPhoto, "UserPhoto"),
            "PasswordHash" = COALESCE(p_PasswordHash, "PasswordHash"),
            "UpdatedBy" = p_ModifiedBy,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "UserID" = p_UserID;
        
        v_Status := 'SUCCESS';
        v_Message := 'User updated successfully';
        v_NewUserID := p_UserID;
        
    ELSE
        v_Status := 'FAILED';
        v_Message := 'Invalid Action';
    END IF;

    RETURN QUERY SELECT v_Status, v_Message, v_NewUserID;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'FAILED'::VARCHAR, SQLERRM::VARCHAR, NULL::INT;
END;
$$ LANGUAGE plpgsql;
