-- Centralized Dashboard Expense Statistics Procedure
-- Returns 3 result sets via refcursors: rs_overall, rs_breakdown, rs_trend

CREATE OR REPLACE FUNCTION "Proc_DashboardExpenseStats_Get"(
    p_SchoolID INTEGER,
    p_FromDate DATE DEFAULT NULL,
    p_ToDate DATE DEFAULT NULL
) 
RETURNS SETOF REFCURSOR AS $$
DECLARE
    rs_overall REFCURSOR := 'rs_overall';
    rs_breakdown REFCURSOR := 'rs_breakdown';
    rs_trend REFCURSOR := 'rs_trend';
BEGIN
    -- 1. Overall Expense Stats
    OPEN rs_overall FOR
    SELECT 
        COALESCE(SUM(esp."GrossSalary"), 0) AS "TotalExpense",
        COALESCE(SUM(CASE WHEN esp."PaymentStatus" = 'Paid' THEN esp."NetSalary" ELSE 0 END), 0) AS "TotalPaid",
        COALESCE(SUM(CASE WHEN esp."PaymentStatus" != 'Paid' THEN esp."NetSalary" ELSE 0 END), 0) AS "TotalPending",
        COUNT(DISTINCT esp."EmployeeID") AS "TotalEmployeesProcessed",
        COUNT(DISTINCT CASE WHEN esp."PaymentStatus" = 'Paid' THEN esp."EmployeeID" END) AS "PaidEmployees",
        COUNT(DISTINCT CASE WHEN esp."PaymentStatus" != 'Paid' THEN esp."EmployeeID" END) AS "UnpaidEmployees",
        COALESCE(SUM(CASE WHEN em."EmploymentType" = 'Permanent' THEN esp."GrossSalary" ELSE 0 END), 0) AS "PermanentExpense",
        COALESCE(SUM(CASE WHEN em."EmploymentType" = 'Contract' THEN esp."GrossSalary" ELSE 0 END), 0) AS "ContractExpense",
        COALESCE(SUM(CASE WHEN em."EmploymentType" = 'Guest' THEN esp."GrossSalary" ELSE 0 END), 0) AS "GuestExpense"
    FROM "EmployeeSalaryPayment" esp
    LEFT JOIN "EmployeeMaster" em ON esp."EmployeeID" = em."EmployeeID"
    WHERE esp."SchoolID" = p_SchoolID
      AND COALESCE(esp."IsDeleted", FALSE) = FALSE
      AND (p_FromDate IS NULL OR COALESCE(esp."PaymentDate", esp."CreatedAt")::DATE >= p_FromDate)
      AND (p_ToDate IS NULL OR COALESCE(esp."PaymentDate", esp."CreatedAt")::DATE <= p_ToDate);
    RETURN NEXT rs_overall;

    -- 2. Profile-wise Breakdown
    OPEN rs_breakdown FOR
    SELECT 
        pm."ProfileName" AS "Label",
        COALESCE(SUM(esp."GrossSalary"), 0) AS "Amount",
        COUNT(DISTINCT esp."EmployeeID") AS "Count"
    FROM "ProfileMaster" pm
    LEFT JOIN "EmployeeMaster" em ON pm."ProfileID" = em."ProfileId"
    LEFT JOIN "EmployeeSalaryPayment" esp ON em."EmployeeID" = esp."EmployeeID"
        AND esp."SchoolID" = p_SchoolID
        AND COALESCE(esp."IsDeleted", FALSE) = FALSE
        AND (p_FromDate IS NULL OR COALESCE(esp."PaymentDate", esp."CreatedAt")::DATE >= p_FromDate)
        AND (p_ToDate IS NULL OR COALESCE(esp."PaymentDate", esp."CreatedAt")::DATE <= p_ToDate)
    WHERE pm."ProfileName" IN ('Teacher', 'Driver', 'Librarian', 'Accountant', 'Support Executive', 'Security', 'Hostel Warden')
    GROUP BY pm."ProfileName"
    HAVING SUM(esp."GrossSalary") > 0 OR pm."ProfileName" = 'Teacher'
    ORDER BY "Amount" DESC;
    RETURN NEXT rs_breakdown;

    -- 3. Monthly Expense Trend (Last 12 Months)
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
        COALESCE(SUM(esp."GrossSalary"), 0) AS "Expense"
    FROM MonthRange m
    LEFT JOIN "EmployeeSalaryPayment" esp ON 
        (esp."PaymentYear"::text || '-' || LPAD(esp."PaymentMonth"::text, 2, '0') || '-01')::DATE = m.MonthDate
        AND esp."SchoolID" = p_SchoolID
        AND COALESCE(esp."IsDeleted", FALSE) = FALSE
    GROUP BY m.MonthDate
    ORDER BY m.MonthDate;
    RETURN NEXT rs_trend;
END;
$$ LANGUAGE plpgsql;
