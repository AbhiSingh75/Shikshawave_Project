-- PostgreSQL Function: Proc_User_DeleteRestore
-- Purpose: Soft-delete or Restore a user in UserMaster table

CREATE OR REPLACE FUNCTION "Proc_User_DeleteRestore"(
    p_UserID INTEGER,
    p_Action TEXT, -- 'DELETE' or 'RESTORE'
    p_PerformedBy INTEGER
)
RETURNS JSON AS $$
DECLARE
    v_Success BOOLEAN := FALSE;
    v_Message TEXT := '';
BEGIN
    -- Validate action
    IF p_Action NOT IN ('DELETE', 'RESTORE') THEN
        RETURN json_build_object('success', false, 'message', 'Invalid action. Must be DELETE or RESTORE.');
    END IF;

    -- Perform action
    IF p_Action = 'DELETE' THEN
        UPDATE "UserMaster"
        SET "IsDeleted" = TRUE,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "UserID" = p_UserID;
        
        v_Message := 'User deleted (soft) successfully.';
        v_Success := TRUE;
    ELSE
        UPDATE "UserMaster"
        SET "IsDeleted" = FALSE,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "UserID" = p_UserID;
        
        v_Message := 'User restored successfully.';
        v_Success := TRUE;
    END IF;

    -- Log the action (if we had an audit table, we'd insert here)
    -- RAISE NOTICE 'User % action performed by %', p_UserID, p_PerformedBy;

    RETURN json_build_object('success', v_Success, 'message', v_Message);
END;
$$ LANGUAGE plpgsql;
