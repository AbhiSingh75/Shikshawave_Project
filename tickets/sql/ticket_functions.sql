-- Ticket Management PostgreSQL Functions (Refined for Service Alignment)
-- Author: Antigravity
-- Date: 2026-04-03

-- CLEANUP: Drop existing functions to avoid "AmbiguousFunction" errors
DROP FUNCTION IF EXISTS "Proc_Tickets_GetByRole"(INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS "Proc_Tickets_GetByRole"(INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, TIMESTAMP, TIMESTAMP, INTEGER, INTEGER, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS "Proc_Tickets_GetKPIs"(INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR);
DROP FUNCTION IF EXISTS "Proc_Tickets_GetKPIs"(INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, INTEGER, INTEGER, VARCHAR, TIMESTAMP, TIMESTAMP);
DROP FUNCTION IF EXISTS "Proc_Ticket_Insert"(INTEGER, VARCHAR, INTEGER, INTEGER, INTEGER, VARCHAR, TEXT, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS "Proc_Ticket_GetDetails"(INTEGER, VARCHAR, BIGINT);
DROP FUNCTION IF EXISTS "Proc_Ticket_UpdateStatus"(INTEGER, VARCHAR, BIGINT, VARCHAR, TEXT);
DROP FUNCTION IF EXISTS "Proc_Ticket_Assign"(INTEGER, VARCHAR, BIGINT, INTEGER, TEXT);
DROP FUNCTION IF EXISTS "Proc_Ticket_Insights_Dashboard"(INTEGER, VARCHAR, TIMESTAMP, TIMESTAMP);
DROP FUNCTION IF EXISTS "Proc_Ticket_Insights_Dashboard"(INTEGER, VARCHAR, TIMESTAMP, TIMESTAMP, INTEGER);
DROP FUNCTION IF EXISTS "Proc_Support_Executive_dropdown_list_get"();

-- 1. Get Tickets by Role with Full Filtering and Sorting
CREATE OR REPLACE FUNCTION "Proc_Tickets_GetByRole"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_SchoolID INTEGER,
    v_AssignedTo INTEGER,
    v_Status VARCHAR,
    v_Category INTEGER,
    v_Priority INTEGER,
    v_Search VARCHAR,
    v_FromDate TIMESTAMP,
    v_ToDate TIMESTAMP,
    v_PageNo INTEGER,
    v_PageSize INTEGER,
    v_SortColumn VARCHAR,
    v_SortDirection VARCHAR
)
RETURNS TABLE (
    "TicketID" BIGINT,
    "TicketNumber" VARCHAR,
    "Subject" VARCHAR,
    "Description" TEXT,
    "CurrentStatus" VARCHAR,
    "Priority" INTEGER,
    "PriorityName" VARCHAR,
    "CategoryID" INTEGER,
    "CategoryName" VARCHAR,
    "SchoolID" INTEGER,
    "SchoolName" VARCHAR,
    "CreatedByUserID" INTEGER,
    "CreatedByName" VARCHAR,
    "AssignedToUserID" INTEGER,
    "AssignedToName" VARCHAR,
    "CreatedAt" TIMESTAMP,
    "TotalCount" BIGINT
) AS $$
DECLARE
    v_Offset INTEGER;
    v_Query TEXT;
    v_UserContextSchoolID INTEGER;
BEGIN
    v_Offset := (v_PageNo - 1) * v_PageSize;
    
    -- Fetch the actual SchoolID for the user to enforce security boundaries
    SELECT um."SchoolID" INTO v_UserContextSchoolID FROM "UserMaster" um WHERE um."UserID" = v_UserID;
    
    -- Normalize sort parameters to prevent "zero-length delimited identifier" error
    v_SortColumn := COALESCE(NULLIF(v_SortColumn, ''), 'CreatedAt');
    v_SortDirection := COALESCE(NULLIF(v_SortDirection, ''), 'DESC');

    v_Query := '
        WITH FilteredTickets AS (
            SELECT 
                t.*,
                tp."PriorityName",
                tc."CategoryName",
                s."SchoolName",
                uc."UserName" as "CreatedByName",
                ua."UserName" as "AssignedToName"
            FROM "TicketMaster" t
            JOIN "TicketPriority" tp ON t."Priority" = tp."PriorityLevel"
            JOIN "TicketCategory" tc ON t."CategoryID" = tc."CategoryID"
            JOIN "SchoolMaster" s ON t."SchoolID" = s."SchoolID"
            JOIN "UserMaster" uc ON t."CreatedByUserID" = uc."UserID"
            LEFT JOIN "UserMaster" ua ON t."AssignedToUserID" = ua."UserID"
            WHERE t."IsDeleted" = FALSE
              AND (
                -- Super Admin: Full platform visibility
                $1 = ''Super Admin'' 
                -- School Admin: Strictly locked to their own school context
                OR ($1 = ''School Admin'' AND t."SchoolID" = ' || COALESCE(v_UserContextSchoolID, 0) || ')
                -- Support Executive: Restricted to their assigned tickets
                OR ($1 = ''Support Executive'' AND t."AssignedToUserID" = $3)
                -- Owner: Can see tickets they created
                OR (t."CreatedByUserID" = $3)
              )
              -- Optional Filters (Available to Super Admins & Support Executives)
              AND ($2 IS NULL OR t."SchoolID" = $2)
              AND ($4 IS NULL OR $4 = '''' OR t."CurrentStatus" = $4)
              AND ($5 IS NULL OR t."Priority" = $5)
              AND ($6 IS NULL OR t."CategoryID" = $6)
              AND ($7 IS NULL OR t."AssignedToUserID" = $7)
              AND ($9 IS NULL OR t."CreatedAt" >= $9)
              AND ($10 IS NULL OR t."CreatedAt" <= $10)
              AND ($8 IS NULL OR $8 = '''' OR 
                   t."TicketNumber" ILIKE ''%'' || $8 || ''%'' OR 
                   t."Subject" ILIKE ''%'' || $8 || ''%'' OR
                   t."Description" ILIKE ''%'' || $8 || ''%'')
        )
        SELECT 
            ft."TicketID", ft."TicketNumber", ft."Subject", ft."Description", ft."CurrentStatus",
            ft."Priority", ft."PriorityName", ft."CategoryID", ft."CategoryName",
            ft."SchoolID", ft."SchoolName", ft."CreatedByUserID", ft."CreatedByName",
            ft."AssignedToUserID", ft."AssignedToName", ft."CreatedAt",
            COUNT(*) OVER() as "TotalCount"
        FROM FilteredTickets ft
        ORDER BY ' || quote_ident(v_SortColumn) || ' ' || v_SortDirection || '
        LIMIT ' || v_PageSize || ' OFFSET ' || v_Offset;
    
    RETURN QUERY EXECUTE v_Query 
    USING v_RoleName, v_SchoolID, v_UserID, v_Status, v_Priority, v_Category, v_AssignedTo, v_Search, v_FromDate, v_ToDate;
END;
$$ LANGUAGE plpgsql;

-- 2. Get Ticket KPIs (Status Count)
CREATE OR REPLACE FUNCTION "Proc_Tickets_GetKPIs"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_SchoolID INTEGER,
    v_AssignedTo INTEGER,
    v_Status VARCHAR,
    v_Category INTEGER,
    v_Priority INTEGER,
    v_Search VARCHAR,
    v_FromDate TIMESTAMP DEFAULT NULL,
    v_ToDate TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
    "Open" BIGINT,
    "InProgress" BIGINT,
    "Resolved" BIGINT,
    "Closed" BIGINT,
    "Reopened" BIGINT
) AS $$
DECLARE
    v_UserContextSchoolID INTEGER;
BEGIN
    -- Fetch the actual SchoolID for the user to enforce security boundaries
    SELECT um."SchoolID" INTO v_UserContextSchoolID FROM "UserMaster" um WHERE um."UserID" = v_UserID;

    RETURN QUERY
    SELECT 
        COUNT(*) FILTER (WHERE "CurrentStatus" = 'Open') as "Open",
        COUNT(*) FILTER (WHERE "CurrentStatus" = 'In Progress') as "InProgress",
        COUNT(*) FILTER (WHERE "CurrentStatus" = 'Resolved') as "Resolved",
        COUNT(*) FILTER (WHERE "CurrentStatus" = 'Closed') as "Closed",
        COUNT(*) FILTER (WHERE "CurrentStatus" = 'Reopened') as "Reopened"
    FROM "TicketMaster"
    WHERE "IsDeleted" = FALSE
      AND (
        -- Super Admin: Full platform visibility
        v_RoleName = 'Super Admin' 
        -- School Admin: Strictly locked to their own school context
        OR (v_RoleName = 'School Admin' AND "SchoolID" = v_UserContextSchoolID)
        -- Support Executive: Restricted to their assigned tickets
        OR (v_RoleName = 'Support Executive' AND "AssignedToUserID" = v_UserID)
        -- Owner: Can see tickets they created
        OR ("CreatedByUserID" = v_UserID)
      )
      -- Optional Filters (Available to Super Admins & Support Executives)
      AND (v_SchoolID IS NULL OR "SchoolID" = v_SchoolID)
      AND (v_AssignedTo IS NULL OR "AssignedToUserID" = v_AssignedTo)
      AND (v_Category IS NULL OR "CategoryID" = v_Category)
      AND (v_Priority IS NULL OR "Priority" = v_Priority)
      AND (v_Search IS NULL OR v_Search = '' OR "Subject" ILIKE '%' || v_Search || '%')
      AND (v_FromDate IS NULL OR "CreatedAt" >= v_FromDate)
      AND (v_ToDate IS NULL OR "CreatedAt" <= v_ToDate);
END;
$$ LANGUAGE plpgsql;

-- 3. Insert New Ticket
CREATE OR REPLACE FUNCTION "Proc_Ticket_Insert"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_SchoolID INTEGER,
    v_CategoryID INTEGER,
    v_Priority INTEGER,
    v_Subject VARCHAR,
    v_Description TEXT,
    v_Reserved VARCHAR,
    v_Source VARCHAR
)
RETURNS TABLE ("NewTicketID" BIGINT, "Error" VARCHAR) AS $$
DECLARE
    v_NewID BIGINT;
BEGIN
    INSERT INTO "TicketMaster" (
        "SchoolID", "CreatedByUserID", "CategoryID", 
        "Priority", "Subject", "Description", "CurrentStatus", 
        "Sources", "CreatedAt", "UpdatedAt", "IsDeleted"
    ) VALUES (
        v_SchoolID, v_UserID, v_CategoryID,
        v_Priority, v_Subject, v_Description, 'Open',
        COALESCE(v_Source, 'Website'), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, FALSE
    ) RETURNING "TicketID" INTO v_NewID;

    INSERT INTO "TicketActivityLog" (
        "TicketID", "ActionByUserID", "ActionType", "NewStatus", "Comment", "Timestamp"
    ) VALUES (
        v_NewID, v_UserID, 'Created', 'Open', 'Ticket created manually', CURRENT_TIMESTAMP
    );

    RETURN QUERY SELECT v_NewID, NULL::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- 4. Get Ticket Details with JSON Return (PostgreSQL Compatible)
CREATE OR REPLACE FUNCTION "Proc_Ticket_GetDetails"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_TicketID BIGINT
)
RETURNS TABLE (
    "TicketData" TEXT,
    "ActivitiesData" TEXT,
    "CommentsData" TEXT,
    "AttachmentsData" TEXT,
    "Error" VARCHAR
) AS $$
DECLARE
    v_TicketData TEXT;
    v_ActivitiesData TEXT;
    v_CommentsData TEXT;
    v_AttachmentsData TEXT;
    v_Error VARCHAR;
BEGIN
    -- 1. Get Ticket Metadata
    SELECT json_build_object(
        'TicketID', t."TicketID",
        'TicketNumber', t."TicketNumber",
        'Subject', t."Subject",
        'Description', t."Description",
        'CurrentStatus', t."CurrentStatus",
        'Priority', t."Priority",
        'PriorityName', tp."PriorityName",
        'CategoryID', t."CategoryID",
        'CategoryName', tc."CategoryName",
        'SchoolID', t."SchoolID",
        'SchoolName', s."SchoolName",
        'CreatedByUserID', t."CreatedByUserID",
        'CreatedByName', uc."UserName",
        'AssignedToUserID', t."AssignedToUserID",
        'AssignedToName', ua."UserName",
        'CreatedAt', t."CreatedAt",
        'UpdatedAt', t."UpdatedAt",
        'Source', t."Sources"
    )::TEXT INTO v_TicketData
    FROM "TicketMaster" t
    JOIN "SchoolMaster" s ON t."SchoolID" = s."SchoolID"
    JOIN "UserMaster" uc ON t."CreatedByUserID" = uc."UserID"
    LEFT JOIN "UserMaster" ua ON t."AssignedToUserID" = ua."UserID"
    JOIN "TicketPriority" tp ON t."Priority" = tp."PriorityLevel"
    JOIN "TicketCategory" tc ON t."CategoryID" = tc."CategoryID"
    WHERE t."TicketID" = v_TicketID;

    -- Basic Permission Check (Harden School-level isolation)
    IF v_TicketData IS NULL THEN
        v_Error := 'Ticket not found';
    ELSIF v_RoleName != 'Super Admin' AND v_RoleName != 'Support Executive' THEN
        -- Strictly enforce school context OR creator ownership
        IF NOT EXISTS (
            SELECT 1 FROM "TicketMaster" t
            JOIN "UserMaster" u ON u."UserID" = v_UserID
            WHERE t."TicketID" = v_TicketID 
              AND (t."SchoolID" = u."SchoolID" OR t."CreatedByUserID" = v_UserID)
        ) THEN
            v_Error := 'Access denied (Cross-school or Unauthorized)';
        END IF;
    END IF;

    IF v_Error IS NOT NULL THEN
        RETURN QUERY SELECT NULL::TEXT, NULL::TEXT, NULL::TEXT, NULL::TEXT, v_Error;
        RETURN;
    END IF;

    -- 2. Get Activity Log
    SELECT json_agg(act)::TEXT INTO v_ActivitiesData
    FROM (
        SELECT l.*, u."UserName" as "ActionByName", un."UserName" as "NewAssigneeName"
        FROM "TicketActivityLog" l
        JOIN "UserMaster" u ON l."ActionByUserID" = u."UserID"
        LEFT JOIN "UserMaster" un ON l."NewAssignee" = un."UserID"
        WHERE l."TicketID" = v_TicketID
        ORDER BY l."Timestamp" ASC
    ) act;

    -- 3. Get Comments
    SELECT json_agg(cmt)::TEXT INTO v_CommentsData
    FROM (
        SELECT c.*, u."UserName" as "CommentByName", tr."CommentText" as "ReplyToText", ur."UserName" as "ReplyToUserName",
               att."FileName" as "AttachmentName"
        FROM "TicketComments" c
        JOIN "UserMaster" u ON c."CommentByUserID" = u."UserID"
        LEFT JOIN "TicketComments" tr ON c."ReplyToCommentID" = tr."CommentID"
        LEFT JOIN "UserMaster" ur ON tr."CommentByUserID" = ur."UserID"
        LEFT JOIN "TicketAttachments" att ON c."AttachmentID" = att."AttachmentID"
        WHERE c."TicketID" = v_TicketID AND c."IsDeleted" = FALSE
        ORDER BY c."CreatedAt" ASC
    ) cmt;

    -- 4. Get Attachments
    SELECT json_agg(attch)::TEXT INTO v_AttachmentsData
    FROM (
        SELECT a.*, u."UserName" as "UploadedByName"
        FROM "TicketAttachments" a
        JOIN "UserMaster" u ON a."UploadedByUserID" = u."UserID"
        WHERE a."TicketID" = v_TicketID AND a."IsDeleted" = FALSE
    ) attch;

    RETURN QUERY SELECT v_TicketData, v_ActivitiesData, v_CommentsData, v_AttachmentsData, NULL::VARCHAR;
END;
$$ LANGUAGE plpgsql;


-- 5. Update Ticket Status
CREATE OR REPLACE FUNCTION "Proc_Ticket_UpdateStatus"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_TicketID BIGINT,
    v_NewStatus VARCHAR,
    v_Comment TEXT
)
RETURNS TABLE ("Error" VARCHAR) AS $$
    DECLARE
    v_OldStatus VARCHAR;
    v_TicketSchoolID INTEGER;
    v_UserSchoolID INTEGER;
BEGIN
    -- Permission Check BEFORE Update
    SELECT "CurrentStatus", "SchoolID" INTO v_OldStatus, v_TicketSchoolID FROM "TicketMaster" WHERE "TicketID" = v_TicketID;
    SELECT "SchoolID" INTO v_UserSchoolID FROM "UserMaster" WHERE "UserID" = v_UserID;

    IF v_OldStatus IS NULL THEN
        RETURN QUERY SELECT 'Ticket not found'::VARCHAR;
        RETURN;
    END IF;

    -- Standardize Role Check
    IF TRIM(v_RoleName) NOT IN ('Super Admin', 'Support Executive') THEN
        IF COALESCE(v_TicketSchoolID, 0) != COALESCE(v_UserSchoolID, 0) THEN
             RETURN QUERY SELECT 'Unauthorized Status Change: Cross-school access denied'::VARCHAR;
             RETURN;
        END IF;
    END IF;
    
    UPDATE "TicketMaster" 
    SET "CurrentStatus" = v_NewStatus, 
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "ResolvedAt" = CASE WHEN v_NewStatus = 'Resolved' THEN CURRENT_TIMESTAMP ELSE "ResolvedAt" END,
        "ClosedAt" = CASE WHEN v_NewStatus = 'Closed' THEN CURRENT_TIMESTAMP ELSE "ClosedAt" END
    WHERE "TicketID" = v_TicketID;

    INSERT INTO "TicketActivityLog" (
        "TicketID", "ActionByUserID", "ActionType", "OldStatus", "NewStatus", "Comment", "Timestamp"
    ) VALUES (
        v_TicketID, v_UserID, 'StatusChanged', v_OldStatus, v_NewStatus, v_Comment, CURRENT_TIMESTAMP
    );

    RETURN QUERY SELECT NULL::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- 6. Assign Ticket
CREATE OR REPLACE FUNCTION "Proc_Ticket_Assign"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_TicketID BIGINT,
    v_AssignToUserID INTEGER,
    v_Comment TEXT
)
RETURNS TABLE ("Error" VARCHAR) AS $$
    DECLARE
    v_OldAssignee INTEGER;
    v_TicketSchoolID INTEGER;
    v_UserSchoolID INTEGER;
BEGIN
    -- Permission Check BEFORE Assignment
    SELECT "AssignedToUserID", "SchoolID" INTO v_OldAssignee, v_TicketSchoolID FROM "TicketMaster" WHERE "TicketID" = v_TicketID;
    SELECT "SchoolID" INTO v_UserSchoolID FROM "UserMaster" WHERE "UserID" = v_UserID;

    IF v_OldAssignee IS NULL AND NOT EXISTS (SELECT 1 FROM "TicketMaster" WHERE "TicketID" = v_TicketID) THEN
        RETURN QUERY SELECT 'Ticket not found'::VARCHAR;
        RETURN;
    END IF;

    IF v_RoleName != 'Super Admin' THEN
         RETURN QUERY SELECT 'Unauthorized Assignment (High-level admin role required)'::VARCHAR;
         RETURN;
    END IF;

    UPDATE "TicketMaster" 
    SET "AssignedToUserID" = v_AssignToUserID, "UpdatedAt" = CURRENT_TIMESTAMP 
    WHERE "TicketID" = v_TicketID;

    INSERT INTO "TicketActivityLog" (
        "TicketID", "ActionByUserID", "ActionType", "OldAssignee", "NewAssignee", "Comment", "Timestamp"
    ) VALUES (
        v_TicketID, v_UserID, 'Assigned', v_OldAssignee, v_AssignToUserID, v_Comment, CURRENT_TIMESTAMP
    );

    RETURN QUERY SELECT NULL::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- 7. Insights Dashboard (Returning JSON strings as columns to match service expectations)
CREATE OR REPLACE FUNCTION "Proc_Ticket_Insights_Dashboard"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_StartDate TIMESTAMP,
    v_EndDate TIMESTAMP,
    v_TargetSchoolID INTEGER DEFAULT NULL
)
RETURNS TABLE (
    "Stats" TEXT,
    "Trends" TEXT,
    "Categories" TEXT,
    "Priorities" TEXT,
    "Performers" TEXT,
    "Schools" TEXT
) AS $$
DECLARE
    v_SchoolID INTEGER;
    v_RealStartDate TIMESTAMP;
    v_RealEndDate TIMESTAMP;
BEGIN
    -- Set default date range if NULL (last 15 days)
    v_RealStartDate := COALESCE(v_StartDate, CURRENT_TIMESTAMP - INTERVAL '15 days');
    v_RealEndDate := COALESCE(v_EndDate, CURRENT_TIMESTAMP);

    -- Get user's school
    SELECT "SchoolID" INTO v_SchoolID FROM "UserMaster" WHERE "UserID" = v_UserID;

    RETURN QUERY
    WITH FilteredTickets AS (
        SELECT t.*, tc."CategoryName", tp."PriorityName", s."SchoolName", u."UserName"
        FROM "TicketMaster" t
        JOIN "TicketCategory" tc ON t."CategoryID" = tc."CategoryID"
        JOIN "TicketPriority" tp ON t."Priority" = tp."PriorityLevel"
        JOIN "SchoolMaster" s ON t."SchoolID" = s."SchoolID"
        LEFT JOIN "UserMaster" u ON t."AssignedToUserID" = u."UserID"
        WHERE t."IsDeleted" = FALSE
          AND t."CreatedAt" BETWEEN v_RealStartDate AND v_RealEndDate
          AND (
            -- Super Admin: Full platform, narrowed by school filter if provided
            (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR t."SchoolID" = v_TargetSchoolID))
            
            -- School Admin: Strictly limited to their own school context
            OR (v_RoleName = 'School Admin' AND t."SchoolID" = v_SchoolID)
            
            -- Support Executive: Restricted to their assigned tickets, narrowed by school filter if provided
            OR (v_RoleName = 'Support Executive' AND t."AssignedToUserID" = v_UserID AND (v_TargetSchoolID IS NULL OR t."SchoolID" = v_TargetSchoolID))
          )
    ),
    StatsCTE AS (
        SELECT json_build_object(
            'TotalTickets', COUNT(*),
            'OpenTickets', COUNT(*) FILTER (WHERE "CurrentStatus" = 'Open'),
            'InProgressTickets', COUNT(*) FILTER (WHERE "CurrentStatus" = 'In Progress'),
            'ResolvedTickets', COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')),
            'ClosedTickets', COUNT(*) FILTER (WHERE "CurrentStatus" = 'Closed'),
            'ReopenedTickets', COUNT(*) FILTER (WHERE "CurrentStatus" = 'Reopened'),
            'AvgResolutionTimeHours', COALESCE(EXTRACT(EPOCH FROM AVG(COALESCE("ResolvedAt", "ClosedAt") - "CreatedAt") FILTER (WHERE "ResolvedAt" IS NOT NULL OR "ClosedAt" IS NOT NULL)) / 3600, 0),
            'CriticalTickets', COUNT(*) FILTER (WHERE "Priority" = 4)
        )::TEXT as stats
        FROM FilteredTickets
    ),
    TrendsCTE AS (
        SELECT json_agg(t)::TEXT as trends
        FROM (
            SELECT 
                d.day::DATE as "Date",
                COUNT(ft."TicketID") as "TicketCount",
                COUNT(ft."TicketID") FILTER (WHERE ft."CurrentStatus" IN ('Resolved', 'Closed')) as "ResolvedCount"
            FROM generate_series(v_RealStartDate::DATE, v_RealEndDate::DATE, INTERVAL '1 day') d(day)
            LEFT JOIN FilteredTickets ft ON ft."CreatedAt"::DATE = d.day::DATE
            GROUP BY d.day
            ORDER BY d.day ASC
        ) t
    ),
    CategoriesCTE AS (
        SELECT json_agg(c)::TEXT as categories
        FROM (
            SELECT 
                "CategoryName",
                COUNT(*) as "TicketCount",
                ROUND(COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')) * 100.0 / COUNT(*), 1) as "ResolutionRate"
            FROM FilteredTickets
            GROUP BY "CategoryName"
            ORDER BY "TicketCount" DESC
            LIMIT 5
        ) c
    ),
    PrioritiesCTE AS (
        SELECT json_agg(p)::TEXT as priorities
        FROM (
            SELECT 
                "PriorityName",
                "Priority",
                COUNT(*) as "TicketCount",
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FilteredTickets), 1) as "Percentage"
            FROM FilteredTickets
            GROUP BY "PriorityName", "Priority"
            ORDER BY "Priority" DESC
        ) p
    ),
    PerformersCTE AS (
        SELECT json_agg(perf)::TEXT as performers
        FROM (
            SELECT 
                "UserName",
                COUNT(*) as "AssignedTickets",
                COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')) as "ResolvedTickets",
                ROUND(COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')) * 100.0 / COUNT(*), 1) as "ResolutionRate"
            FROM FilteredTickets
            WHERE "AssignedToUserID" IS NOT NULL
            GROUP BY "UserName"
            ORDER BY "ResolvedTickets" DESC
            LIMIT 5
        ) perf
        WHERE (v_RoleName IN ('Super Admin', 'School Admin'))
    ),
    SchoolsCTE AS (
        SELECT json_agg(sch)::TEXT as schools
        FROM (
            SELECT 
                "SchoolName",
                COUNT(*) as "TicketCount",
                COUNT(*) FILTER (WHERE "CurrentStatus" = 'Open') as "OpenTickets",
                COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')) as "ResolvedTickets"
            FROM FilteredTickets
            GROUP BY "SchoolName"
            ORDER BY "TicketCount" DESC
            LIMIT 10
        ) sch
        WHERE v_RoleName = 'Super Admin'
    )
    SELECT 
        COALESCE((SELECT stats FROM StatsCTE), '{}'),
        COALESCE((SELECT trends FROM TrendsCTE), '[]'),
        COALESCE((SELECT categories FROM CategoriesCTE), '[]'),
        COALESCE((SELECT priorities FROM PrioritiesCTE), '[]'),
        COALESCE((SELECT performers FROM PerformersCTE), '[]'),
        COALESCE((SELECT schools FROM SchoolsCTE), '[]')
    ;
END;
$$ LANGUAGE plpgsql;

-- 8. Get Support Executives Dropdown List (Strictly Support Executive Profile)
CREATE OR REPLACE FUNCTION "Proc_Support_Executive_dropdown_list_get"()
RETURNS TABLE (
    "UserID" INTEGER,
    "UserName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u."UserID",
        u."UserName"
    FROM "UserMaster" u
    JOIN "ProfileMaster" p ON u."ProfileID" = p."ProfileID"
    WHERE p."ProfileName" = 'Support Executive'
      AND u."IsActive" = TRUE
      AND COALESCE(u."IsDeleted", FALSE) = FALSE
    ORDER BY u."UserName" ASC;
END;
$$ LANGUAGE plpgsql;
