-- PostgreSQL Procedures for Salary Module

-- 1. Create EmployeeSalaryPayment table if not exists (Inferred Schema)
CREATE TABLE IF NOT EXISTS "EmployeeSalaryPayment" (
    "PaymentID" SERIAL PRIMARY KEY,
    "SchoolID" INT,
    "EmployeeID" INT,
    "PaymentYear" INT,
    "PaymentMonth" INT,
    "GrossSalary" DECIMAL(18,2),
    "TotalDeductions" DECIMAL(18,2),
    "NetSalary" DECIMAL(18,2),
    "PaymentStatus" VARCHAR(50) DEFAULT 'Pending', -- Pending, Paid
    "PaymentDate" TIMESTAMP,
    "PaymentMode" VARCHAR(50),
    "ReferenceNo" VARCHAR(100),
    "SalaryReferenceId" VARCHAR(50),
    "Remarks" TEXT,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "UpdatedBy" INT,
    "UpdatedAt" TIMESTAMP
);

-- 2. Create EmployeeSalaryStructure table if not exists (Inferred Schema)
CREATE TABLE IF NOT EXISTS "EmployeeSalaryStructure" (
    "StructureID" SERIAL PRIMARY KEY,
    "SchoolID" INT,
    "EmployeeID" INT,
    "ComponentID" INT,
    "Amount" DECIMAL(18,2),
    "EffectiveDate" DATE,
    "IsActive" BOOLEAN DEFAULT TRUE,
    "CreatedBy" INT,
    "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "UpdatedBy" INT,
    "UpdatedAt" TIMESTAMP
);

-- 3. Proc_Salary_Get
DROP FUNCTION IF EXISTS "Proc_Salary_Get"(INT, VARCHAR, INT, VARCHAR);
DROP FUNCTION IF EXISTS "Proc_Salary_Get"(INT, VARCHAR, BIGINT, VARCHAR);
CREATE OR REPLACE FUNCTION "Proc_Salary_Get"(
    p_SchoolID INT DEFAULT NULL,
    p_Month VARCHAR DEFAULT NULL, -- Format: 'YYYY-MM'
    p_EmployeeID BIGINT DEFAULT NULL,
    p_Search VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    "PaymentID" BIGINT,
    "EmployeeID" BIGINT,
    "EmployeeCode" VARCHAR,
    "EmployeeName" VARCHAR,
    "Email" VARCHAR,
    "Designation" VARCHAR,
    "SalaryMonth" VARCHAR,
    "GrossSalary" DECIMAL,
    "Deductions" DECIMAL,
    "NetSalary" DECIMAL,
    "PaymentStatus" VARCHAR,
    "PaymentDate" TIMESTAMP,
    "PaymentMode" VARCHAR,
    "ReferenceNo" VARCHAR,
    "SalaryReferenceId" VARCHAR
) AS $$
DECLARE
    v_Year INT;
    v_Month INT;
BEGIN
    IF p_Month IS NOT NULL AND p_Month <> '' THEN
        v_Year := NULLIF(SPLIT_PART(p_Month, '-', 1), '')::INT;
        v_Month := NULLIF(SPLIT_PART(p_Month, '-', 2), '')::INT;
    END IF;

    RETURN QUERY
    SELECT 
        esp."PaymentID"::BIGINT,
        e."EmployeeID"::BIGINT,
        e."EmployeeCode"::VARCHAR,
        e."EmployeeName"::VARCHAR,
        e."Email"::VARCHAR,
        p."ProfileName"::VARCHAR,
        TO_CHAR(TO_DATE(esp."PaymentYear"::text || '-' || esp."PaymentMonth"::text || '-01', 'YYYY-MM-DD'), 'Month YYYY')::VARCHAR,
        esp."GrossSalary"::DECIMAL,
        esp."TotalDeductions"::DECIMAL,
        esp."NetSalary"::DECIMAL,
        esp."PaymentStatus"::VARCHAR,
        esp."PaymentDate"::TIMESTAMP,
        esp."PaymentMode"::VARCHAR,
        esp."ReferenceNo"::VARCHAR,
        esp."SalaryReferenceId"::VARCHAR
    FROM "EmployeeSalaryPayment" esp
    INNER JOIN "EmployeeMaster" e ON esp."EmployeeID" = e."EmployeeID"
    LEFT JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
    WHERE (p_SchoolID IS NULL OR esp."SchoolID" = p_SchoolID)
    AND (p_EmployeeID IS NULL OR e."EmployeeID" = p_EmployeeID)
    AND (v_Year IS NULL OR esp."PaymentYear" = v_Year)
    AND (v_Month IS NULL OR esp."PaymentMonth" = v_Month)
    AND (p_Search IS NULL OR p_Search = '' OR 
         e."EmployeeName" ILIKE '%' || p_Search || '%' OR 
         e."EmployeeCode" ILIKE '%' || p_Search || '%')
    ORDER BY esp."PaymentYear" DESC, esp."PaymentMonth" DESC, e."EmployeeName";
END;
$$ LANGUAGE plpgsql;

-- 4. Proc_Salary_Pay
DROP FUNCTION IF EXISTS "Proc_Salary_Pay"(INT, DATE, VARCHAR, VARCHAR, TEXT, INT);
CREATE OR REPLACE FUNCTION "Proc_Salary_Pay"(
    p_PaymentID INT,
    p_PaymentDate DATE,
    p_PaymentMode VARCHAR,
    p_ReferenceNo VARCHAR,
    p_Remarks TEXT,
    p_UserId INT
)
RETURNS TABLE (
    status VARCHAR, 
    message VARCHAR
) AS $$
DECLARE
    v_SalaryRefID VARCHAR;
    v_SchoolID INT;
    v_EmployeeID INT;
    v_Year INT;
    v_Month INT;
BEGIN
    -- Get payment details for reference generation
    SELECT "SchoolID", "EmployeeID", "PaymentYear", "PaymentMonth" 
    INTO v_SchoolID, v_EmployeeID, v_Year, v_Month
    FROM "EmployeeSalaryPayment"
    WHERE "PaymentID" = p_PaymentID;

    -- Generate Reference ID: SAL-SchoolID-EmployeeID-YYYYMM-PaymentID
    v_SalaryRefID := 'SAL-' || v_SchoolID || '-' || v_EmployeeID || '-' || v_Year || LPAD(v_Month::text, 2, '0') || '-' || p_PaymentID;

    UPDATE "EmployeeSalaryPayment"
    SET 
        "PaymentStatus" = 'Paid',
        "PaymentDate" = p_PaymentDate,
        "PaymentMode" = p_PaymentMode,
        "ReferenceNo" = p_ReferenceNo,
        "SalaryReferenceId" = v_SalaryRefID,
        "Remarks" = p_Remarks,
        "UpdatedBy" = p_UserId,
        "UpdatedAt" = CURRENT_TIMESTAMP
    WHERE "PaymentID" = p_PaymentID;

    IF FOUND THEN
        RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Salary updated successfully'::VARCHAR;
    ELSE
        RETURN QUERY SELECT 'FAILED'::VARCHAR, 'Payment record not found'::VARCHAR;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 5. Proc_SalaryRelease_Generate
DROP FUNCTION IF EXISTS "Proc_SalaryRelease_Generate"(INT, VARCHAR, INT);
CREATE OR REPLACE FUNCTION "Proc_SalaryRelease_Generate"(
    p_SchoolID INT,
    p_Month VARCHAR, -- 'YYYY-MM'
    p_UserId INT
)
RETURNS TABLE (
    status VARCHAR,
    message VARCHAR
) AS $$
DECLARE
    v_Year INT;
    v_Month INT;
    v_Employee RECORD;
    v_Gross DECIMAL(18,2);
    v_Deductions DECIMAL(18,2);
    v_Net DECIMAL(18,2);
    v_Count INT := 0;
BEGIN
    v_Year := SPLIT_PART(p_Month, '-', 1)::INT;
    v_Month := SPLIT_PART(p_Month, '-', 2)::INT;

    -- Iterate over employees in the school who are not deleted
    FOR v_Employee IN 
        SELECT "EmployeeID" FROM "EmployeeMaster" 
        WHERE "SchoolID" = p_SchoolID AND COALESCE("IsDeleted", FALSE) = FALSE
    LOOP
        -- Check if salary already generated for this month
        IF EXISTS (SELECT 1 FROM "EmployeeSalaryPayment" 
                   WHERE "EmployeeID" = v_Employee."EmployeeID" 
                   AND "PaymentYear" = v_Year 
                   AND "PaymentMonth" = v_Month) THEN
            CONTINUE;
        END IF;

        -- Calculate Salary from Breakup
        SELECT 
            COALESCE(SUM(CASE WHEN sc."ComponentType" = 'Earning' THEN esb."Amount" ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN sc."ComponentType" = 'Deduction' THEN esb."Amount" ELSE 0 END), 0)
        INTO v_Gross, v_Deductions
        FROM "EmployeeSalaryBreakup" esb
        JOIN "SalaryComponentMaster" sc ON esb."ComponentID" = sc."ComponentID"
        WHERE esb."EmployeeID" = v_Employee."EmployeeID" AND COALESCE(esb."IsDeleted", FALSE) = FALSE;
        
        v_Net := v_Gross - v_Deductions;

        -- Insert if there is a salary structure defined (Gross > 0)
        IF v_Gross > 0 THEN
            INSERT INTO "EmployeeSalaryPayment" (
                "SchoolID", "EmployeeID", "PaymentYear", "PaymentMonth", 
                "GrossSalary", "TotalDeductions", "NetSalary", 
                "PaymentStatus", "CreatedBy"
            ) VALUES (
                p_SchoolID, v_Employee."EmployeeID", v_Year, v_Month,
                v_Gross, v_Deductions, v_Net,
                'Pending', p_UserId
            );
            v_Count := v_Count + 1;
        END IF;
    END LOOP;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, ('Generated ' || v_Count || ' salary records')::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- 6. Proc_SalarySlip_Get
DROP FUNCTION IF EXISTS "Proc_SalarySlip_Get"(INT);
CREATE OR REPLACE FUNCTION "Proc_SalarySlip_Get"(p_PaymentID INT)
RETURNS SETOF refcursor AS $$
DECLARE
    ref1 refcursor;
    ref2 refcursor;
    ref3 refcursor;
BEGIN
    OPEN ref1 FOR 
    SELECT 
        esp."PaymentID", -- 0
        esp."SchoolID", -- 1
        e."EmployeeCode", -- 2
        e."EmployeeName", -- 3
        e."Email", -- 4
        p."ProfileName" as "Designation", -- 5
        TO_CHAR(TO_DATE(esp."PaymentYear"::text || '-' || esp."PaymentMonth"::text || '-01', 'YYYY-MM-DD'), 'Month YYYY') as "SalaryMonth", -- 6
        esp."GrossSalary", -- 7
        esp."TotalDeductions", -- 8
        esp."NetSalary", -- 9
        esp."PaymentStatus", -- 10
        esp."PaymentDate", -- 11
        esp."PaymentMode", -- 12
        esp."ReferenceNo", -- 13
        esp."SalaryReferenceId", -- 14
        esp."Remarks", -- 15
        s."SchoolName", -- 16
        s."SchoolCode", -- 17
        s."Address" as "SchoolAddress", -- 18
        s."Phone" as "ContactNo", -- 19
        s."Email" as "SchoolEmail", -- 20
        s."SchoolLogo", -- 21
        'XXXX-XXXX-' || RIGHT('0000' || e."EmployeeID"::text, 4) as "BankAccountNo", -- 22
        e."EmployeeCode" || '@upi' as "IFSCCode", -- 23
        '1234-5678-' || RIGHT('0000' || e."EmployeeID"::text, 4) as "UANNumber" -- 24
    FROM "EmployeeSalaryPayment" esp
    INNER JOIN "EmployeeMaster" e ON esp."EmployeeID" = e."EmployeeID"
    INNER JOIN "SchoolMaster" s ON esp."SchoolID" = s."SchoolID"
    LEFT JOIN "ProfileMaster" p ON e."ProfileId" = p."ProfileID"
    WHERE esp."PaymentID" = p_PaymentID;
    RETURN NEXT ref1;

    OPEN ref2 FOR
    SELECT 
        sc."ComponentName", 
        sc."ComponentType", 
        esb."Amount"
    FROM "EmployeeSalaryBreakup" esb
    JOIN "SalaryComponentMaster" sc ON esb."ComponentID" = sc."ComponentID"
    JOIN "EmployeeSalaryPayment" esp ON esb."EmployeeID" = esp."EmployeeID"
    WHERE esp."PaymentID" = p_PaymentID 
    AND sc."ComponentType" = 'Earning'
    AND COALESCE(esb."IsDeleted", FALSE) = FALSE;
    RETURN NEXT ref2;

    OPEN ref3 FOR
    SELECT 
        sc."ComponentName", 
        sc."ComponentType", 
        esb."Amount"
    FROM "EmployeeSalaryBreakup" esb
    JOIN "SalaryComponentMaster" sc ON esb."ComponentID" = sc."ComponentID"
    JOIN "EmployeeSalaryPayment" esp ON esb."EmployeeID" = esp."EmployeeID"
    WHERE esp."PaymentID" = p_PaymentID 
    AND sc."ComponentType" = 'Deduction'
    AND COALESCE(esb."IsDeleted", FALSE) = FALSE;
    RETURN NEXT ref3;
END;
$$ LANGUAGE plpgsql;

-- 7. Fix Proc_Employee_Salary_Update
DROP FUNCTION IF EXISTS "Proc_Employee_Salary_Update"(VARCHAR, INT, JSONB, INT);
CREATE OR REPLACE FUNCTION "Proc_Employee_Salary_Update"(
    p_EmployeeCode VARCHAR,
    p_SchoolID INT,
    p_SalaryData JSONB,
    p_UserId INT
)
RETURNS TABLE (status VARCHAR, message VARCHAR) AS $$
DECLARE
    v_EmployeeID INT;
    v_Item JSONB;
    v_ComponentID INT;
    v_Amount DECIMAL;
BEGIN
    SELECT "EmployeeID" INTO v_EmployeeID FROM "EmployeeMaster" 
    WHERE "EmployeeCode" = p_EmployeeCode AND "SchoolID" = p_SchoolID;

    IF v_EmployeeID IS NULL THEN
        RETURN QUERY SELECT 'error'::VARCHAR, 'Employee not found'::VARCHAR;
        RETURN;
    END IF;

    -- Deactivate current breakup
    UPDATE "EmployeeSalaryBreakup" SET "IsDeleted" = TRUE, "UpdatedBy" = p_UserId, "UpdatedAt" = CURRENT_TIMESTAMP
    WHERE "EmployeeID" = v_EmployeeID;

    FOR v_Item IN SELECT * FROM jsonb_array_elements(p_SalaryData)
    LOOP
        v_ComponentID := (v_Item->>'ComponentID')::INT;
        v_Amount := (v_Item->>'Amount')::DECIMAL;
        
        IF v_ComponentID IS NOT NULL AND v_Amount > 0 THEN
            INSERT INTO "EmployeeSalaryBreakup" (
                "SchoolID", "EmployeeID", "ComponentID", "Amount", 
                "CreatedBy", "CreatedAt"
            ) VALUES (
                p_SchoolID, v_EmployeeID, v_ComponentID, v_Amount,
                p_UserId, CURRENT_TIMESTAMP
            );
        END IF;
    END LOOP;

    RETURN QUERY SELECT 'success'::VARCHAR, 'Salary structure updated successfully'::VARCHAR;
END;
$$ LANGUAGE plpgsql;
