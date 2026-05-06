-- 1. Function for rate limiting check
CREATE OR REPLACE FUNCTION "Proc_FaceAuthRateLimit_Check"(
    p_UserID INT DEFAULT NULL,
    p_IPAddress VARCHAR(45) DEFAULT NULL,
    p_MaxAttempts INT DEFAULT 10
)
RETURNS TABLE (
    "IsBlocked" BOOLEAN,
    "CurrentAttempts" INT,
    "MaxAttempts" INT,
    "MinutesUntilReset" INT
) AS $$
DECLARE
    v_CurrentAttempts INT;
    v_IsBlocked BOOLEAN := FALSE;
    v_MinutesUntilReset INT := 0;
BEGIN
    -- Count attempts in the last hour
    SELECT COUNT(*)::INT
    INTO v_CurrentAttempts
    FROM "FaceAuthLogs"
    WHERE (p_UserID IS NULL OR "UserID" = p_UserID)
      AND (p_IPAddress IS NULL OR "IPAddress" = p_IPAddress)
      AND "AttemptTime" >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    -- Check if blocked
    IF v_CurrentAttempts >= p_MaxAttempts THEN
        v_IsBlocked := TRUE;
        
        -- Calculate minutes until reset
        SELECT EXTRACT(MINUTE FROM (MIN("AttemptTime") + INTERVAL '1 hour' - CURRENT_TIMESTAMP))::INT
        INTO v_MinutesUntilReset
        FROM "FaceAuthLogs"
        WHERE (p_UserID IS NULL OR "UserID" = p_UserID)
          AND (p_IPAddress IS NULL OR "IPAddress" = p_IPAddress)
          AND "AttemptTime" >= CURRENT_TIMESTAMP - INTERVAL '1 hour';
          
        v_MinutesUntilReset := COALESCE(v_MinutesUntilReset, 0);
        IF v_MinutesUntilReset < 0 THEN v_MinutesUntilReset := 0; END IF;
    END IF;
    
    RETURN QUERY SELECT v_IsBlocked, v_CurrentAttempts, p_MaxAttempts, v_MinutesUntilReset;
END;
$$ LANGUAGE plpgsql;

-- 2. Function for logging face auth attempts
CREATE OR REPLACE FUNCTION "Proc_FaceAuthAttempt_Log"(
    p_UserID INT DEFAULT NULL,
    p_TemplateID INT DEFAULT NULL,
    p_Similarity DECIMAL(5,2) DEFAULT NULL,
    p_IsSuccessful BOOLEAN DEFAULT FALSE,
    p_IPAddress VARCHAR(45) DEFAULT NULL,
    p_DeviceInfo VARCHAR(2000) DEFAULT NULL,
    p_ErrorMessage VARCHAR(1000) DEFAULT NULL
)
RETURNS INT AS $$
DECLARE
    v_LogID INT;
BEGIN
    INSERT INTO "FaceAuthLogs" (
        "UserID", 
        "TemplateID", 
        "Similarity", 
        "Success", 
        "IPAddress", 
        "DeviceInfo", 
        "AttemptTime"
    )
    VALUES (
        p_UserID, 
        p_TemplateID, 
        p_Similarity, 
        p_IsSuccessful, 
        p_IPAddress, 
        p_DeviceInfo, 
        CURRENT_TIMESTAMP
    )
    RETURNING "LogID" INTO v_LogID;
    
    RETURN v_LogID;
END;
$$ LANGUAGE plpgsql;
