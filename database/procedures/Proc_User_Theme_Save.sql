CREATE OR REPLACE FUNCTION "Proc_User_Theme_Save"(
    p_UserID INT,
    p_IsDarkMode BOOLEAN
) RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
DECLARE
    v_ThemeValue VARCHAR;
BEGIN
    v_ThemeValue := CASE WHEN p_IsDarkMode THEN 'Yes' ELSE 'No' END;
    
    UPDATE "UserMaster" 
    SET "DarkTheme" = v_ThemeValue,
        "UpdatedAt" = CURRENT_TIMESTAMP
    WHERE "UserID" = p_UserID;

    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Theme preference updated'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'FAILED'::VARCHAR, 'User not found'::VARCHAR;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'FAILED'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
