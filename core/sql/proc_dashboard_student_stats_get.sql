-- Centralized Dashboard Student Statistics Procedure (FIXED CASTING)
-- Returns 3 result sets via refcursors: rs_overall, rs_breakdown, rs_trend

CREATE OR REPLACE FUNCTION "Proc_DashboardStudentStats_Get"(
    p_SchoolID INTEGER,
    p_ClassID INTEGER DEFAULT NULL,
    p_SectionID INTEGER DEFAULT NULL,
    p_Gender VARCHAR DEFAULT NULL,
    p_Category VARCHAR DEFAULT NULL,
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
    -- 1. Overall Student Stats
    OPEN rs_overall FOR
    SELECT 
        COALESCE(COUNT(DISTINCT s."StudentID"), 0) AS "TotalStudents",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Gender" = 'Male' THEN s."StudentID" END), 0) AS "MaleStudents",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Gender" = 'Female' THEN s."StudentID" END), 0) AS "FemaleStudents",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Category" = 'General' THEN s."StudentID" END), 0) AS "GeneralCategory",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Category" = 'OBC' THEN s."StudentID" END), 0) AS "OBCCategory",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Category" = 'SC' THEN s."StudentID" END), 0) AS "SCCategory",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Category" = 'ST' THEN s."StudentID" END), 0) AS "STCategory",
        COALESCE(COUNT(DISTINCT CASE WHEN s."IsDeleted" IS NOT TRUE THEN s."StudentID" END), 0) AS "ActiveStudents",
        COALESCE(COUNT(DISTINCT CASE WHEN s."IsDeleted" IS TRUE THEN s."StudentID" END), 0) AS "InactiveStudents"
    FROM "Student" s
    WHERE s."SchoolID" = p_SchoolID
      AND (p_ClassID IS NULL OR (CASE WHEN s."AdmissionClass" ~ '^[0-9]+$' THEN s."AdmissionClass"::integer ELSE NULL END) = p_ClassID)
      AND (p_SectionID IS NULL OR (CASE WHEN s."Section" ~ '^[0-9]+$' THEN s."Section"::integer ELSE NULL END) = p_SectionID)
      AND (p_Gender IS NULL OR s."Gender" = p_Gender)
      AND (p_Category IS NULL OR s."Category" = p_Category)
      AND (p_FromDate IS NULL OR s."CreatedAt"::DATE >= p_FromDate)
      AND (p_ToDate IS NULL OR s."CreatedAt"::DATE <= p_ToDate)
      AND (NOT p_ShowActiveOnly OR s."IsDeleted" IS NOT TRUE);
    RETURN NEXT rs_overall;

    -- 2. Class-wise Breakdown (including Admission Revenue)
    OPEN rs_breakdown FOR
    SELECT 
        c."ClassID",
        c."ClassName",
        COALESCE(COUNT(DISTINCT s."StudentID"), 0) AS "StudentCount",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Gender" = 'Male' THEN s."StudentID" END), 0) AS "MaleCount",
        COALESCE(COUNT(DISTINCT CASE WHEN s."Gender" = 'Female' THEN s."StudentID" END), 0) AS "FemaleCount",
        COALESCE(SUM(pay."PaidAmount" + COALESCE(pay."Discountvalue", 0)), 0) AS "AdmissionRevenue"
    FROM "ClassMaster" c
    LEFT JOIN "Student" s ON c."ClassID" = (CASE WHEN s."AdmissionClass" ~ '^[0-9]+$' THEN s."AdmissionClass"::integer ELSE NULL END)
        AND s."SchoolID" = p_SchoolID
        AND (p_SectionID IS NULL OR (CASE WHEN s."Section" ~ '^[0-9]+$' THEN s."Section"::integer ELSE NULL END) = p_SectionID)
        AND (p_Gender IS NULL OR s."Gender" = p_Gender)
        AND (p_Category IS NULL OR s."Category" = p_Category)
        AND (p_FromDate IS NULL OR s."CreatedAt"::DATE >= p_FromDate)
        AND (p_ToDate IS NULL OR s."CreatedAt"::DATE <= p_ToDate)
        AND (NOT p_ShowActiveOnly OR s."IsDeleted" IS NOT TRUE)
    LEFT JOIN "Payment" pay ON s."StudentID" = pay."EntityID" 
        AND pay."PaymentFor" = 'Admission'
        AND COALESCE(pay."IsDeleted", FALSE) = FALSE
        AND (p_FromDate IS NULL OR pay."PaymentDate"::DATE >= p_FromDate)
        AND (p_ToDate IS NULL OR pay."PaymentDate"::DATE <= p_ToDate)
    WHERE c."SchoolID" = p_SchoolID
    GROUP BY c."ClassID", c."ClassName"
    ORDER BY c."ClassID";
    RETURN NEXT rs_breakdown;

    -- 3. Monthly Admission Trend
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
        COUNT(DISTINCT s."StudentID") AS "NewAdmissions"
    FROM MonthRange m
    LEFT JOIN "Student" s ON 
        DATE_TRUNC('month', s."CreatedAt") = m.MonthDate
        AND s."SchoolID" = p_SchoolID
        AND (p_ClassID IS NULL OR (CASE WHEN s."AdmissionClass" ~ '^[0-9]+$' THEN s."AdmissionClass"::integer ELSE NULL END) = p_ClassID)
        AND (p_SectionID IS NULL OR (CASE WHEN s."Section" ~ '^[0-9]+$' THEN s."Section"::integer ELSE NULL END) = p_SectionID)
        AND (p_Gender IS NULL OR s."Gender" = p_Gender)
        AND (p_Category IS NULL OR s."Category" = p_Category)
        AND s."IsDeleted" IS NOT TRUE
    GROUP BY m.MonthDate
    ORDER BY m.MonthDate;
    RETURN NEXT rs_trend;
END;
$$ LANGUAGE plpgsql;
