-- PostgreSQL functions for Notification System and School Management

-- 1. Proc_Notification_GetUnreadCount
CREATE OR REPLACE FUNCTION "Proc_Notification_GetUnreadCount"(
    p_UserID INT,
    p_SchoolID INT
) RETURNS INT AS $$
DECLARE
    v_UnreadCount INT;
BEGIN
    SELECT COUNT(*) INTO v_UnreadCount
    FROM "NotificationRecipients" nr
    INNER JOIN "NotificationMaster" n ON nr."NotificationID" = n."NotificationID"
    WHERE nr."UserID" = p_UserID 
        AND (p_SchoolID IS NULL OR n."SchoolID" = p_SchoolID)
        AND nr."IsRead" = FALSE 
        AND nr."IsDeleted" = FALSE 
        AND n."IsDeleted" = FALSE
        AND (n."ExpiresAt" IS NULL OR n."ExpiresAt" > CURRENT_TIMESTAMP);
    
    RETURN COALESCE(v_UnreadCount, 0);
END;
$$ LANGUAGE plpgsql;

-- 2. Proc_Notification_MarkRead
CREATE OR REPLACE FUNCTION "Proc_Notification_MarkRead"(
    p_NotificationID BIGINT,
    p_UserID INT
) RETURNS INT AS $$
DECLARE
    v_RowsAffected INT;
BEGIN
    UPDATE "NotificationRecipients"
    SET "IsRead" = TRUE, "ReadAt" = CURRENT_TIMESTAMP
    WHERE "NotificationID" = p_NotificationID AND "UserID" = p_UserID;
    
    GET DIAGNOSTICS v_RowsAffected = ROW_COUNT;
    RETURN v_RowsAffected;
END;
$$ LANGUAGE plpgsql;

-- 3. Proc_Notification_MarkAllRead
CREATE OR REPLACE FUNCTION "Proc_Notification_MarkAllRead"(
    p_UserID INT,
    p_SchoolID INT
) RETURNS INT AS $$
DECLARE
    v_RowsAffected INT;
BEGIN
    UPDATE "NotificationRecipients" nr
    SET "IsRead" = TRUE, "ReadAt" = CURRENT_TIMESTAMP
    FROM "NotificationMaster" n
    WHERE nr."NotificationID" = n."NotificationID"
        AND nr."UserID" = p_UserID 
        AND (p_SchoolID IS NULL OR n."SchoolID" = p_SchoolID)
        AND nr."IsRead" = FALSE 
        AND n."IsDeleted" = FALSE 
        AND nr."IsDeleted" = FALSE;
    
    GET DIAGNOSTICS v_RowsAffected = ROW_COUNT;
    RETURN v_RowsAffected;
END;
$$ LANGUAGE plpgsql;

-- 4. Proc_Notification_GetList
CREATE OR REPLACE FUNCTION "Proc_Notification_GetList"(
    p_UserID INT,
    p_SchoolID INT,
    p_PageNumber INT DEFAULT 1,
    p_PageSize INT DEFAULT 20,
    p_UnreadOnly INT DEFAULT 0
) RETURNS TABLE (
    "NotificationID" BIGINT,
    "Title" VARCHAR,
    "Message" TEXT,
    "TargetURL" VARCHAR,
    "TargetModule" VARCHAR,
    "TargetRecordID" BIGINT,
    "TypeName" VARCHAR,
    "TypeCategory" VARCHAR,
    "IconClass" VARCHAR,
    "ColorCode" VARCHAR,
    "IsRead" BOOLEAN,
    "ReadAt" TIMESTAMP,
    "CreatedAt" TIMESTAMP,
    "CreatedByUserName" VARCHAR,
    "TotalCount" BIGINT
) AS $$
DECLARE
    v_Offset INT := (p_PageNumber - 1) * p_PageSize;
    v_TotalCount BIGINT;
BEGIN
    -- Calculate TotalCount first
    SELECT COUNT(*) INTO v_TotalCount
    FROM "NotificationRecipients" nr
    INNER JOIN "NotificationMaster" n ON nr."NotificationID" = n."NotificationID"
    WHERE nr."UserID" = p_UserID AND (p_SchoolID IS NULL OR n."SchoolID" = p_SchoolID)
        AND n."IsDeleted" = FALSE AND nr."IsDeleted" = FALSE
        AND (n."ExpiresAt" IS NULL OR n."ExpiresAt" > CURRENT_TIMESTAMP)
        AND (p_UnreadOnly = 0 OR nr."IsRead" = FALSE);

    RETURN QUERY
    SELECT 
        n."NotificationID", n."Title", n."Message", n."TargetURL", n."TargetModule", n."TargetRecordID",
        nt."TypeName", nt."TypeCategory", nt."IconClass", nt."ColorCode",
        nr."IsRead", nr."ReadAt", n."CreatedAt", u."UserName"::VARCHAR AS "CreatedByUserName",
        v_TotalCount AS "TotalCount"
    FROM "NotificationRecipients" nr
    INNER JOIN "NotificationMaster" n ON nr."NotificationID" = n."NotificationID"
    INNER JOIN "NotificationTypeMaster" nt ON n."TypeID" = nt."TypeID"
    LEFT JOIN "UserMaster" u ON n."CreatedByUserID" = u."UserID"
    WHERE nr."UserID" = p_UserID AND (p_SchoolID IS NULL OR n."SchoolID" = p_SchoolID)
        AND n."IsDeleted" = FALSE AND nr."IsDeleted" = FALSE
        AND (n."ExpiresAt" IS NULL OR n."ExpiresAt" > CURRENT_TIMESTAMP)
        AND (p_UnreadOnly = 0 OR nr."IsRead" = FALSE)
    ORDER BY n."CreatedAt" DESC
    LIMIT p_PageSize OFFSET v_Offset;
END;
$$ LANGUAGE plpgsql;

-- 5. Proc_Notification_Create
CREATE OR REPLACE FUNCTION "Proc_Notification_Create"(
    p_SchoolID INT,
    p_TypeName VARCHAR,
    p_Title VARCHAR,
    p_Message TEXT,
    p_TargetURL VARCHAR,
    p_TargetModule VARCHAR,
    p_TargetRecordID BIGINT,
    p_CreatedByUserID INT,
    p_RecipientUserIDs TEXT,
    p_ExpiresAt TIMESTAMP
) RETURNS TABLE (
    "NewNotificationID" BIGINT,
    "ResultStatus" VARCHAR
) AS $$
DECLARE
    v_NotificationID BIGINT;
    v_TypeID INT;
BEGIN
    SELECT "TypeID" INTO v_TypeID FROM "NotificationTypeMaster" WHERE "TypeName" = p_TypeName AND "IsActive" = TRUE;
    
    IF v_TypeID IS NULL THEN
        RETURN QUERY SELECT 0::BIGINT, 'Invalid notification type'::VARCHAR;
        RETURN;
    END IF;
    
    INSERT INTO "NotificationMaster" (
        "SchoolID", "TypeID", "Title", "Message", "TargetURL", "TargetModule", "TargetRecordID", "CreatedByUserID", "ExpiresAt"
    )
    VALUES (
        p_SchoolID, v_TypeID, p_Title, p_Message, p_TargetURL, p_TargetModule, p_TargetRecordID, p_CreatedByUserID, p_ExpiresAt
    )
    RETURNING "NotificationID" INTO v_NotificationID;
    
    INSERT INTO "NotificationRecipients" ("NotificationID", "UserID")
    SELECT v_NotificationID, CAST(u_id AS INT)
    FROM unnest(string_to_array(p_RecipientUserIDs, ',')) AS u_id
    WHERE u_id IS NOT NULL AND u_id != '' AND u_id ~ '^[0-9]+$';
    
    RETURN QUERY SELECT v_NotificationID, 'Success'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- 6. Proc_SoftDeleteSchool
CREATE OR REPLACE FUNCTION "Proc_SoftDeleteSchool"(
    p_SchoolID INT,
    p_ModifiedBy INT,
    p_Action TEXT
) RETURNS VOID AS $$
BEGIN
    IF p_Action = 'DELETE' THEN
        UPDATE "SchoolMaster"
        SET "IsDeleted" = TRUE,
            "DeletedBy" = p_ModifiedBy,
            "DeletedAt" = CURRENT_TIMESTAMP
        WHERE "SchoolID" = p_SchoolID;
    ELSIF p_Action = 'Restore' THEN
        UPDATE "SchoolMaster"
        SET "IsDeleted" = FALSE,
            "DeletedBy" = NULL,
            "DeletedAt" = NULL
        WHERE "SchoolID" = p_SchoolID;
    END IF;
END;
$$ LANGUAGE plpgsql;
