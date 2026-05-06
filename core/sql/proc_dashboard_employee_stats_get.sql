-- Centralized Dashboard Employee Statistics Procedure
-- Returns 3 result sets via refcursors: rs_overall, rs_breakdown, rs_trend

CREATE OR REPLACE FUNCTION "Proc_DashboardEmployeeStats_Get"(
    p_SchoolID INTEGER,
    p_Department VARCHAR DEFAULT NULL,
    p_Gender VARCHAR DEFAULT NULL,
    p_EmploymentType VARCHAR DEFAULT NULL,
    p_FromDate DATE DEFAULT NULL,
    p_ToDate DATE DEFAULT NULL,
    p_ShowActiveOnly BOOLEAN DEFAULT TRUE
) 
RETURNS SETOF REFCURSOR AS $$
DECLARE
    rs_overall REFCURSOR := 'rs_overall';
    rs_breakdown REFCURSOR := 'rs_breakdown';
    rs_trend REFCURSOR := 'rs_trend';
BEGIN
    -- 1. Overall Employee Stats
    OPEN rs_overall FOR
    SELECT 
        COALESCE(COUNT(DISTINCT e."EmployeeID"), 0) AS "TotalEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."Gender" = 'Male' THEN e."EmployeeID" END), 0) AS "MaleEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."Gender" = 'Female' THEN e."EmployeeID" END), 0) AS "FemaleEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."EmploymentType" = 'Permanent' THEN e."EmployeeID" END), 0) AS "PermanentEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."EmploymentType" = 'Contract' THEN e."EmployeeID" END), 0) AS "ContractEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."EmploymentType" = 'Guest' THEN e."EmployeeID" END), 0) AS "GuestEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."IsDeleted" IS NOT TRUE THEN e."EmployeeID" END), 0) AS "ActiveEmployees",
        COALESCE(COUNT(DISTINCT CASE WHEN e."IsDeleted" IS TRUE THEN e."EmployeeID" END), 0) AS "InactiveEmployees"
    FROM "EmployeeMaster" e
    LEFT JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
    WHERE e."SchoolID" = p_SchoolID
      AND (p_Department IS NULL OR p."ProfileName" = p_Department)
      AND (p_Gender IS NULL OR e."Gender" = p_Gender)
      AND (p_EmploymentType IS NULL OR e."EmploymentType" = p_EmploymentType)
      AND (p_FromDate IS NULL OR e."DateOfJoining"::DATE >= p_FromDate)
      AND (p_ToDate IS NULL OR e."DateOfJoining"::DATE <= p_ToDate)
      AND (NOT p_ShowActiveOnly OR e."IsDeleted" IS NOT TRUE);
    RETURN NEXT rs_overall;

    -- 2. Profile-wise Breakdown
    OPEN rs_breakdown FOR
    SELECT 
        p."ProfileName" AS "EmployeeType",
        COALESCE(COUNT(DISTINCT e."EmployeeID"), 0) AS "EmployeeCount",
        COALESCE(COUNT(DISTINCT CASE WHEN e."Gender" = 'Male' THEN e."EmployeeID" END), 0) AS "MaleCount",
        COALESCE(COUNT(DISTINCT CASE WHEN e."Gender" = 'Female' THEN e."EmployeeID" END), 0) AS "FemaleCount"
    FROM "ProfileMaster" p
    LEFT JOIN "EmployeeMaster" e ON p."ProfileID" = e."ProfileId"
        AND e."SchoolID" = p_SchoolID
        AND (p_Gender IS NULL OR e."Gender" = p_Gender)
        AND (p_EmploymentType IS NULL OR e."EmploymentType" = p_EmploymentType)
        AND (p_FromDate IS NULL OR e."DateOfJoining"::DATE >= p_FromDate)
        AND (p_ToDate IS NULL OR e."DateOfJoining"::DATE <= p_ToDate)
        AND (NOT p_ShowActiveOnly OR e."IsDeleted" IS NOT TRUE)
    WHERE p."ProfileName" IN ('School Admin', 'Teacher', 'Driver', 'Librarian', 'Accountant', 'Support Executive', 'Security', 'Hostel Warden')
    GROUP BY p."ProfileName"
    HAVING COUNT(DISTINCT e."EmployeeID") > 0 OR p."ProfileName" = 'Teacher'
    ORDER BY "EmployeeCount" DESC;
    RETURN NEXT rs_breakdown;

    -- 3. Monthly Hiring Trend
    OPEN rs_trend FOR
    WITH RECURSIVE MonthRange AS (
        SELECT 
            CASE 
                WHEN p_FromDate IS NULL THEN (DATE_TRUNC('month', CURRENT_TIMESTAMP) - INTERVAL '5 months')::DATE
                ELSE DATE_TRUNC('month', p_FromDate)::DATE
            END AS MonthDate
        UNION ALL
        SELECT (MonthDate + INTERVAL '1 month')::DATE
        FROM MonthRange
        WHERE MonthDate + INTERVAL '1 month' <= 
            CASE 
                WHEN p_ToDate IS NULL THEN (DATE_TRUNC('month', CURRENT_TIMESTAMP))::DATE
                ELSE (DATE_TRUNC('month', p_ToDate))::DATE
            END
    )
    SELECT 
        TO_CHAR(m.MonthDate, 'Mon YYYY') AS "MonthYear",
        EXTRACT(MONTH FROM m.MonthDate)::INT AS "Month",
        EXTRACT(YEAR FROM m.MonthDate)::INT AS "Year",
        COUNT(DISTINCT e."EmployeeID") AS "NewHires"
    FROM MonthRange m
    LEFT JOIN "EmployeeMaster" e ON 
        DATE_TRUNC('month', e."DateOfJoining") = m.MonthDate
        AND e."SchoolID" = p_SchoolID
        AND (p_Department IS NULL OR (SELECT p."ProfileName" FROM "ProfileMaster" p WHERE p."ProfileID" = e."ProfileId") = p_Department)
        AND (p_Gender IS NULL OR e."Gender" = p_Gender)
        AND (p_EmploymentType IS NULL OR e."EmploymentType" = p_EmploymentType)
        AND e."IsDeleted" IS NOT TRUE
    GROUP BY m.MonthDate
    ORDER BY m.MonthDate;
    RETURN NEXT rs_trend;
END;
$$ LANGUAGE plpgsql;
