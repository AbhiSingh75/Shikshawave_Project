-- Centralized Dashboard Revenue Statistics Procedure
-- Returns 3 result sets via refcursors: rs_overall, rs_breakdown, rs_trend

CREATE OR REPLACE FUNCTION "Proc_DashboardRevenueStats_Get"(
    p_SchoolID INTEGER,
    p_ClassID INTEGER DEFAULT NULL,
    p_FromDate DATE DEFAULT NULL,
    p_ToDate DATE DEFAULT NULL
) 
RETURNS SETOF REFCURSOR AS $$
DECLARE
    rs_overall REFCURSOR := 'rs_overall';
    rs_breakdown REFCURSOR := 'rs_breakdown';
    rs_trend REFCURSOR := 'rs_trend';
BEGIN
    -- 1. Overall Revenue Stats
    OPEN rs_overall FOR
    SELECT 
        COALESCE(SUM(p."PaidAmount" + COALESCE(p."Discountvalue", 0)), 0) AS "TotalRevenue",
        COUNT(DISTINCT p."PaymentID") AS "TotalTransactions",
        COUNT(DISTINCT p."EntityID") AS "TotalStudentsPaid",
        COALESCE(SUM(CASE WHEN p."PaymentMode" = 'Cash' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "CashRevenue",
        COALESCE(SUM(CASE WHEN p."PaymentMode" = 'Online' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "OnlineRevenue",
        COALESCE(SUM(CASE WHEN p."PaymentMode" = 'Cheque' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "ChequeRevenue",
        COALESCE(SUM(CASE WHEN p."PaymentMode" = 'Card' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "CardRevenue",
        0 AS "TotalPending",
        COALESCE(SUM(COALESCE(p."Discountvalue", 0)), 0) AS "TotalDiscount",
        COALESCE(SUM(CASE WHEN p."PaymentFor" = 'Admission' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "AdmissionRevenue",
        COALESCE(SUM(CASE WHEN p."PaymentFor" = 'Fees' THEN p."PaidAmount" + COALESCE(p."Discountvalue", 0) ELSE 0 END), 0) AS "FeeRevenue"
    FROM "Payment" p
    WHERE p."SchoolID" = p_SchoolID
      AND COALESCE(p."IsDeleted", FALSE) = FALSE
      AND (p_FromDate IS NULL OR COALESCE(p."PaymentDate", p."CreatedAt")::DATE >= p_FromDate)
      AND (p_ToDate IS NULL OR COALESCE(p."PaymentDate", p."CreatedAt")::DATE <= p_ToDate);
    RETURN NEXT rs_overall;

    -- 2. Class-wise Breakdown
    OPEN rs_breakdown FOR
    SELECT 
        c."ClassName",
        COALESCE(SUM(p."PaidAmount" + COALESCE(p."Discountvalue", 0)), 0) AS "Amount",
        COUNT(DISTINCT p."EntityID") AS "Count"
    FROM "ClassMaster" c
    LEFT JOIN "Student" s ON c."ClassID" = (CASE WHEN s."AdmissionClass" ~ '^[0-9]+$' THEN s."AdmissionClass"::integer ELSE NULL END)
    LEFT JOIN "Payment" p ON s."StudentID" = p."EntityID" 
        AND p."EntityType" = 'Student'
        AND COALESCE(p."IsDeleted", FALSE) = FALSE
        AND (p_FromDate IS NULL OR COALESCE(p."PaymentDate", p."CreatedAt")::DATE >= p_FromDate)
        AND (p_ToDate IS NULL OR COALESCE(p."PaymentDate", p."CreatedAt")::DATE <= p_ToDate)
    WHERE c."SchoolID" = p_SchoolID
      AND (p_ClassID IS NULL OR c."ClassID" = p_ClassID)
    GROUP BY c."ClassID", c."ClassName"
    HAVING SUM(p."PaidAmount") > 0
    ORDER BY c."ClassID";
    RETURN NEXT rs_breakdown;

    -- 3. Monthly Revenue Trend (Last 12 Months)
    OPEN rs_trend FOR
    WITH RECURSIVE MonthRange AS (
        SELECT (DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months')::DATE AS MonthDate
        UNION ALL
        SELECT (MonthDate + INTERVAL '1 month')::DATE
        FROM MonthRange
        WHERE MonthDate < DATE_TRUNC('month', CURRENT_DATE)::DATE
    )
    SELECT 
        TO_CHAR(m.MonthDate, 'Mon YYYY') AS "MonthYear",
        COALESCE(SUM(p."PaidAmount" + COALESCE(p."Discountvalue", 0)), 0) AS "Revenue"
    FROM MonthRange m
    LEFT JOIN "Payment" p ON DATE_TRUNC('month', p."PaymentDate") = m.MonthDate
        AND p."SchoolID" = p_SchoolID
        AND COALESCE(p."IsDeleted", FALSE) = FALSE
    GROUP BY m.MonthDate
    ORDER BY m.MonthDate;
    RETURN NEXT rs_trend;
END;
$$ LANGUAGE plpgsql;
