-- PostgreSQL Function for Dashboard Ticket Statistics
-- Returns: Overall Pulse, Trends, Category Breakdown, and Leaderboard

CREATE OR REPLACE FUNCTION "Proc_DashboardTicketStats_Get"(
    v_UserID INTEGER,
    v_RoleName VARCHAR,
    v_TargetSchoolID INTEGER DEFAULT NULL,
    v_FromDate TIMESTAMP DEFAULT NULL,
    v_ToDate TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
    "PulseJSON" TEXT,
    "TrendJSON" TEXT,
    "DistributionJSON" TEXT,
    "LeaderboardJSON" TEXT
) AS $$
DECLARE
    v_UserSchoolID INTEGER;
    v_RealFromDate TIMESTAMP;
    v_RealToDate TIMESTAMP;
    v_PulseJSON TEXT;
    v_TrendJSON TEXT;
    v_DistributionJSON TEXT;
    v_LeaderboardJSON TEXT;
BEGIN
    -- Set default date range (Last 30 days)
    v_RealFromDate := COALESCE(v_FromDate, CURRENT_TIMESTAMP - INTERVAL '30 days');
    v_RealToDate := COALESCE(v_ToDate, CURRENT_TIMESTAMP);

    -- Get user context school
    SELECT "SchoolID" INTO v_UserSchoolID FROM "UserMaster" WHERE "UserID" = v_UserID;

    -- 1. Pulse Statistics (High-level actionable metrics)
    WITH TicketStats AS (
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Open', 'Pending', 'New')) as open_count,
            COUNT(*) FILTER (WHERE "CurrentStatus" = 'In Progress') as in_progress,
            COUNT(*) FILTER (WHERE "CurrentStatus" IN ('Resolved', 'Closed')) as resolved,
            COUNT(*) FILTER (WHERE "Priority" = 4) as critical,
            AVG(EXTRACT(EPOCH FROM (COALESCE("ResolvedAt", "ClosedAt") - "CreatedAt"))) FILTER (WHERE "ResolvedAt" IS NOT NULL OR "ClosedAt" IS NOT NULL) as avg_time_sec
        FROM "TicketMaster"
        WHERE "IsDeleted" = FALSE
          AND "CreatedAt" BETWEEN v_RealFromDate AND v_RealToDate
          AND (
               (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR "SchoolID" = v_TargetSchoolID))
               OR (v_RoleName = 'School Admin' AND "SchoolID" = v_UserSchoolID)
               OR (v_RoleName = 'Support Executive' AND "AssignedToUserID" = v_UserID)
          )
    )
    SELECT json_build_object(
        'ResolutionRate', CASE WHEN total > 0 THEN ROUND((resolved * 100.0 / total), 1) ELSE 0 END,
        'AvgResolutionTimeHours', ROUND(COALESCE(avg_time_sec / 3600.0, 0), 1),
        'CriticalVolume', critical,
        'CapacityPulse', CASE WHEN total > 0 THEN 'Active' ELSE 'Idle' END,
        'TotalInPeriod', total,
        'OpenCount', open_count,
        'InProgressCount', in_progress,
        'ResolvedCount', resolved
    )::TEXT INTO v_PulseJSON
    FROM TicketStats;

    -- 2. Daily Trend (Volume vs Resolution)
    WITH RECURSIVE Days AS (
        SELECT v_RealFromDate::DATE as d
        UNION ALL
        SELECT (d + 1)::DATE FROM Days WHERE d < v_RealToDate::DATE
    )
    SELECT json_agg(t)::TEXT INTO v_TrendJSON
    FROM (
        SELECT 
            TO_CHAR(d.d, 'DD Mon') as "Date",
            COUNT(tm."TicketID") as "Volume",
            COUNT(tm."TicketID") FILTER (WHERE tm."CurrentStatus" IN ('Resolved', 'Closed')) as "Resolved"
        FROM Days d
        LEFT JOIN "TicketMaster" tm ON tm."CreatedAt"::DATE = d.d
          AND tm."IsDeleted" = FALSE
          AND (
               (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR tm."SchoolID" = v_TargetSchoolID))
               OR (v_RoleName = 'School Admin' AND tm."SchoolID" = v_UserSchoolID)
               OR (v_RoleName = 'Support Executive' AND tm."AssignedToUserID" = v_UserID)
          )
        GROUP BY d.d
        ORDER BY d.d ASC
    ) t;

    -- 3. Distribution (Priority Matrix & Category Share)
    SELECT json_build_object(
        'Priorities', (
            SELECT json_agg(p) FROM (
                SELECT tp."PriorityName", COUNT(tm."TicketID") as count
                FROM "TicketPriority" tp
                LEFT JOIN "TicketMaster" tm ON tm."Priority" = tp."PriorityLevel"
                  AND tm."IsDeleted" = FALSE 
                  AND tm."CreatedAt" BETWEEN v_RealFromDate AND v_RealToDate
                  AND (
                       (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR tm."SchoolID" = v_TargetSchoolID))
                       OR (v_RoleName = 'School Admin' AND tm."SchoolID" = v_UserSchoolID)
                       OR (v_RoleName = 'Support Executive' AND tm."AssignedToUserID" = v_UserID)
                  )
                GROUP BY tp."PriorityName", tp."PriorityLevel"
                ORDER BY tp."PriorityLevel" DESC
            ) p
        ),
        'Categories', (
            SELECT json_agg(c) FROM (
                SELECT tc."CategoryName", COUNT(tm."TicketID") as count
                FROM "TicketCategory" tc
                LEFT JOIN "TicketMaster" tm ON tm."CategoryID" = tc."CategoryID"
                  AND tm."IsDeleted" = FALSE 
                  AND tm."CreatedAt" BETWEEN v_RealFromDate AND v_RealToDate
                  AND (
                       (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR tm."SchoolID" = v_TargetSchoolID))
                       OR (v_RoleName = 'School Admin' AND tm."SchoolID" = v_UserSchoolID)
                       OR (v_RoleName = 'Support Executive' AND tm."AssignedToUserID" = v_UserID)
                  )
                WHERE tc."IsDeleted" = FALSE
                GROUP BY tc."CategoryName"
                HAVING COUNT(tm."TicketID") > 0
                ORDER BY count DESC
                LIMIT 5
            ) c
        )
    )::TEXT INTO v_DistributionJSON;

    -- 4. Performer Leaderboard (Only for Admin roles)
    IF v_RoleName IN ('Super Admin', 'School Admin') THEN
        SELECT json_agg(l)::TEXT INTO v_LeaderboardJSON
        FROM (
            SELECT 
                u."UserName",
                COUNT(tm."TicketID") as assigned,
                COUNT(tm."TicketID") FILTER (WHERE tm."CurrentStatus" IN ('Resolved', 'Closed')) as resolved,
                ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(tm."ResolvedAt", tm."ClosedAt") - tm."CreatedAt")) / 3600.0) FILTER (WHERE tm."ResolvedAt" IS NOT NULL OR tm."ClosedAt" IS NOT NULL), 1) as avg_speed
            FROM "UserMaster" u
            JOIN "TicketMaster" tm ON tm."AssignedToUserID" = u."UserID"
            WHERE tm."IsDeleted" = FALSE 
              AND tm."CreatedAt" BETWEEN v_RealFromDate AND v_RealToDate
              AND (
                   (v_RoleName = 'Super Admin' AND (v_TargetSchoolID IS NULL OR tm."SchoolID" = v_TargetSchoolID))
                   OR (v_RoleName = 'School Admin' AND tm."SchoolID" = v_UserSchoolID)
              )
            GROUP BY u."UserName"
            ORDER BY resolved DESC
            LIMIT 5
        ) l;
    ELSE
        v_LeaderboardJSON := '[]';
    END IF;

    RETURN QUERY SELECT v_PulseJSON, v_TrendJSON, v_DistributionJSON, v_LeaderboardJSON;
END;
$$ LANGUAGE plpgsql;
