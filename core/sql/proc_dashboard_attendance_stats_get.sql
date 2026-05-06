-- core/sql/proc_dashboard_attendance_stats_get.sql

CREATE OR REPLACE FUNCTION "Proc_DashboardAttendanceStats_Get"(
    "p_SchoolID" INTEGER,
    "p_ClassID" INTEGER DEFAULT NULL,
    "p_SectionID" INTEGER DEFAULT NULL,
    "p_AttendanceDate" DATE DEFAULT CURRENT_DATE,
    "p_FromDate" DATE DEFAULT NULL,
    "p_ToDate" DATE DEFAULT NULL
)
RETURNS SETOF REFCURSOR AS $$
DECLARE
    "rs_overall" REFCURSOR := 'rs_overall';
    "rs_gender" REFCURSOR := 'rs_gender';
    "rs_class" REFCURSOR := 'rs_class';
    "rs_trend" REFCURSOR := 'rs_trend';
    "v_StartDate" DATE;
    "v_EndDate" DATE;
BEGIN
    -- Resolve date range
    IF "p_FromDate" IS NOT NULL AND "p_ToDate" IS NOT NULL THEN
        "v_StartDate" := "p_FromDate";
        "v_EndDate" := "p_ToDate";
    ELSIF "p_AttendanceDate" IS NOT NULL THEN
        "v_StartDate" := "p_AttendanceDate";
        "v_EndDate" := "p_AttendanceDate";
    ELSE
        "v_StartDate" := CURRENT_DATE;
        "v_EndDate" := CURRENT_DATE;
    END IF;

    -- 1. Overall Attendance Stats
    OPEN "rs_overall" FOR
    SELECT 
        COALESCE(COUNT(*), 0) AS "TotalMarked",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN 1 ELSE 0 END), 0) AS "PresentCount",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN 1 ELSE 0 END), 0) AS "AbsentCount",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('leave', 'lv') THEN 1 ELSE 0 END), 0) AS "LeaveCount",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('late', 'l') THEN 1 ELSE 0 END), 0) AS "LateCount",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('holiday', 'h') THEN 1 ELSE 0 END), 0) AS "HolidayCount",
        CASE 
            WHEN COUNT(*) > 0 THEN ROUND((COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN 1 ELSE 0 END), 0) * 100.0 / COUNT(*)), 2)
            ELSE 0 
        END AS "AttendancePercentage",
        CASE 
            WHEN COUNT(*) > 0 THEN ROUND((COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN 1 ELSE 0 END), 0) * 100.0 / COUNT(*)), 2)
            ELSE 0 
        END AS "AbsentPercentage",
        CASE 
            WHEN COUNT(*) > 0 THEN ROUND((COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('late', 'l') THEN 1 ELSE 0 END), 0) * 100.0 / COUNT(*)), 2)
            ELSE 0 
        END AS "LatePercentage"
    FROM "StudentAttendance" a
    INNER JOIN "Student" s ON a."StudentID" = s."StudentID" AND COALESCE(s."IsDeleted", FALSE) = FALSE
    WHERE a."SchoolID" = "p_SchoolID"
    AND a."AttendanceDate" BETWEEN "v_StartDate" AND "v_EndDate"
    AND COALESCE(a."IsDeleted", FALSE) = FALSE
    AND ("p_ClassID" IS NULL OR a."ClassID"::integer = "p_ClassID")
    AND ("p_SectionID" IS NULL OR a."SectionID" = "p_SectionID");
    RETURN NEXT "rs_overall";

    -- 2. Gender-wise Stats
    OPEN "rs_gender" FOR
    SELECT 
        s."Gender",
        COALESCE(COUNT(*), 0) AS "TotalMarked",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN 1 ELSE 0 END), 0) AS "PresentCount",
        COALESCE(SUM(CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN 1 ELSE 0 END), 0) AS "AbsentCount"
    FROM "StudentAttendance" a
    INNER JOIN "Student" s ON a."StudentID" = s."StudentID" AND COALESCE(s."IsDeleted", FALSE) = FALSE
    WHERE a."SchoolID" = "p_SchoolID"
    AND a."AttendanceDate" BETWEEN "v_StartDate" AND "v_EndDate"
    AND COALESCE(a."IsDeleted", FALSE) = FALSE
    AND ("p_ClassID" IS NULL OR a."ClassID"::integer = "p_ClassID")
    AND ("p_SectionID" IS NULL OR a."SectionID" = "p_SectionID")
    GROUP BY s."Gender";
    RETURN NEXT "rs_gender";

    -- 3. Class-wise Breakdown
    OPEN "rs_class" FOR
    SELECT 
        c."ClassID",
        c."ClassName",
        COALESCE(COUNT(DISTINCT a."StudentID"), 0) AS "TotalMarked",
        COALESCE(COUNT(DISTINCT CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN a."StudentID" END), 0) AS "PresentCount",
        COALESCE(COUNT(DISTINCT CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN a."StudentID" END), 0) AS "AbsentCount"
    FROM "ClassMaster" c
    LEFT JOIN "StudentAttendance" a ON c."ClassID" = a."ClassID"::integer 
        AND a."AttendanceDate" BETWEEN "v_StartDate" AND "v_EndDate"
        AND COALESCE(a."IsDeleted", FALSE) = FALSE
    LEFT JOIN "Student" s ON a."StudentID" = s."StudentID" AND COALESCE(s."IsDeleted", FALSE) = FALSE
    WHERE c."SchoolID" = "p_SchoolID"
    AND ("p_ClassID" IS NULL OR c."ClassID" = "p_ClassID")
    GROUP BY c."ClassID", c."ClassName"
    ORDER BY c."ClassID";
    RETURN NEXT "rs_class";

    -- 4. 6-Month Trend
    OPEN "rs_trend" FOR
    WITH RECURSIVE MonthRange AS (
        SELECT (DATE_TRUNC('month', CURRENT_TIMESTAMP) - INTERVAL '5 months')::DATE AS "MonthDate"
        UNION ALL
        SELECT ("MonthDate" + INTERVAL '1 month')::DATE
        FROM MonthRange
        WHERE "MonthDate" + INTERVAL '1 month' <= (DATE_TRUNC('month', CURRENT_TIMESTAMP))::DATE
    )
    SELECT 
        TO_CHAR(m."MonthDate", 'Mon YYYY') AS "MonthYear",
        EXTRACT(MONTH FROM m."MonthDate")::INT AS "Month",
        EXTRACT(YEAR FROM m."MonthDate")::INT AS "Year",
        COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('present', 'p') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS "PresentPercentage",
        COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('absent', 'a') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS "AbsentPercentage",
        COALESCE(ROUND(AVG(CASE WHEN LOWER(a."Status") IN ('late', 'l') THEN 100.0 ELSE 0 END)::NUMERIC, 2), 0) AS "LatePercentage"
    FROM MonthRange m
    LEFT JOIN "StudentAttendance" a ON DATE_TRUNC('month', a."AttendanceDate") = m."MonthDate"
        AND a."SchoolID" = "p_SchoolID"
        AND COALESCE(a."IsDeleted", FALSE) = FALSE
        AND ("p_ClassID" IS NULL OR a."ClassID"::integer = "p_ClassID")
        AND ("p_SectionID" IS NULL OR a."SectionID" = "p_SectionID")
    GROUP BY m."MonthDate"
    ORDER BY m."MonthDate";
    RETURN NEXT "rs_trend";

END;
$$ LANGUAGE plpgsql;
