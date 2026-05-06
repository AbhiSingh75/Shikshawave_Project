-- ============================================================
-- ShikshaWave - Leave Management SQL Procedures
-- Run this file ONCE against the PostgreSQL database
-- ============================================================

-- ============================================================
-- TABLES
-- ============================================================

-- Leave Type Master (per school)
CREATE TABLE IF NOT EXISTS "LeaveTypeMaster" (
    "LeaveTypeID"    SERIAL PRIMARY KEY,
    "SchoolID"       INTEGER REFERENCES "SchoolMaster"("SchoolID"), -- NULL for Global Policies
    "LeaveTypeName"  VARCHAR(100) NOT NULL,
    "LeaveCode"      VARCHAR(10)  NOT NULL,
    "TotalDays"      INTEGER      NOT NULL DEFAULT 0,
    "CarryForward"   BOOLEAN      NOT NULL DEFAULT FALSE,
    "MaxCarryDays"   INTEGER               DEFAULT 0,
    "IsActive"       BOOLEAN      NOT NULL DEFAULT TRUE,
    "CreatedBy"      INTEGER               REFERENCES "UserMaster"("UserID"),
    "CreatedAt"      TIMESTAMPTZ           DEFAULT NOW(),
    "UpdatedBy"      INTEGER               REFERENCES "UserMaster"("UserID"),
    "UpdatedAt"      TIMESTAMPTZ,
    "IsDeleted"      BOOLEAN      NOT NULL DEFAULT FALSE,
    "DeletedBy"      INTEGER               REFERENCES "UserMaster"("UserID"),
    "DeletedAt"      TIMESTAMPTZ
);

-- Leave Balance (per employee, per year)
CREATE TABLE IF NOT EXISTS "LeaveBalance" (
    "BalanceID"     SERIAL PRIMARY KEY,
    "SchoolID"      INTEGER REFERENCES "SchoolMaster"("SchoolID"), -- NULL for Global Staff
    "EmployeeID"    INTEGER NOT NULL  REFERENCES "UserMaster"("UserID"),
    "LeaveTypeID"   INTEGER NOT NULL  REFERENCES "LeaveTypeMaster"("LeaveTypeID"),
    "Year"          INTEGER NOT NULL,
    "TotalDays"     NUMERIC(5,1)  NOT NULL DEFAULT 0,
    "UsedDays"      NUMERIC(5,1)  NOT NULL DEFAULT 0,
    "PendingDays"   NUMERIC(5,1)  NOT NULL DEFAULT 0,
    "CarryDays"     NUMERIC(5,1)  NOT NULL DEFAULT 0,
    "UpdatedAt"     TIMESTAMPTZ           DEFAULT NOW(),
    UNIQUE ("EmployeeID", "LeaveTypeID", "Year")
);

-- Leave Request
CREATE TABLE IF NOT EXISTS "LeaveRequest" (
    "RequestID"     SERIAL PRIMARY KEY,
    "SchoolID"      INTEGER REFERENCES "SchoolMaster"("SchoolID"), -- NULL for Global Staff
    "EmployeeID"    INTEGER NOT NULL  REFERENCES "UserMaster"("UserID"),
    "LeaveTypeID"   INTEGER NOT NULL  REFERENCES "LeaveTypeMaster"("LeaveTypeID"),
    "FromDate"      DATE    NOT NULL,
    "ToDate"        DATE    NOT NULL,
    "IsHalfDay"     BOOLEAN NOT NULL DEFAULT FALSE,
    "HalfDayPart"   VARCHAR(10)       DEFAULT NULL, -- 'First' or 'Second'
    "Reason"        TEXT,
    "Status"        VARCHAR(20) NOT NULL DEFAULT 'Pending',  -- Pending/Approved/Rejected/Cancelled
    "RequestedOn"   TIMESTAMPTZ         DEFAULT NOW(),
    "ApprovedBy"    INTEGER             REFERENCES "UserMaster"("UserID"),
    "ApprovedOn"    TIMESTAMPTZ,
    "Remarks"       TEXT,
    "IsDeleted"     BOOLEAN     NOT NULL DEFAULT FALSE
);

-- Indices for performance (nullable SchoolID)
CREATE INDEX IF NOT EXISTS "IDX_UserMaster_SchoolID" ON "UserMaster"("SchoolID") WHERE "IsActive" = TRUE AND "IsDeleted" = FALSE;
CREATE INDEX IF NOT EXISTS "IDX_LeaveType_SchoolID" ON "LeaveTypeMaster"("SchoolID") WHERE "IsActive" = TRUE AND "IsDeleted" = FALSE;
CREATE INDEX IF NOT EXISTS "IDX_LeaveBalance_School" ON "LeaveBalance"("SchoolID", "Year");
CREATE INDEX IF NOT EXISTS "IDX_LeaveRequest_School" ON "LeaveRequest"("SchoolID", "Status");

-- Leave Request Audit History
CREATE TABLE IF NOT EXISTS "LeaveRequestHistory" (
    "HistoryID"   SERIAL PRIMARY KEY,
    "RequestID"   INTEGER NOT NULL  REFERENCES "LeaveRequest"("RequestID"),
    "ActionBy"    INTEGER NOT NULL  REFERENCES "UserMaster"("UserID"),
    "Action"      VARCHAR(30)  NOT NULL,   -- Applied/Approved/Rejected/Cancelled
    "Remarks"     TEXT,
    "ActionOn"    TIMESTAMPTZ  DEFAULT NOW()
);

-- Index helpers
CREATE INDEX IF NOT EXISTS idx_leave_request_emp   ON "LeaveRequest"("EmployeeID","Status");
CREATE INDEX IF NOT EXISTS idx_leave_request_school ON "LeaveRequest"("SchoolID","Status");
CREATE INDEX IF NOT EXISTS idx_leave_balance_emp    ON "LeaveBalance"("EmployeeID","Year");


-- ============================================================
-- PROCEDURE: Proc_LeaveType_Save (upsert)
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveType_Save(
    p_school_id      INTEGER,
    p_leave_type_id  INTEGER,   -- 0 or NULL = insert
    p_name           VARCHAR,
    p_code           VARCHAR,
    p_total_days     INTEGER,
    p_carry_forward  BOOLEAN,
    p_max_carry_days INTEGER,
    p_user_id        INTEGER
)
RETURNS TABLE(status TEXT, message TEXT, leave_type_id INTEGER)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_leave_type_id IS NULL OR p_leave_type_id = 0 THEN
        -- Check duplicate code in school (or global)
        IF EXISTS (
            SELECT 1 FROM "LeaveTypeMaster"
            WHERE (("SchoolID" = p_school_id) OR (p_school_id IS NULL AND "SchoolID" IS NULL))
              AND LOWER("LeaveCode") = LOWER(p_code)
              AND "IsDeleted" = FALSE
        ) THEN
            RETURN QUERY SELECT 'ERROR', 'Leave code already exists', 0;
            RETURN;
        END IF;

        INSERT INTO "LeaveTypeMaster"
            ("SchoolID","LeaveTypeName","LeaveCode","TotalDays","CarryForward","MaxCarryDays","CreatedBy","CreatedAt")
        VALUES
            (p_school_id, p_name, UPPER(p_code), p_total_days, p_carry_forward, p_max_carry_days, p_user_id, NOW())
        RETURNING "LeaveTypeID" INTO p_leave_type_id;

        RETURN QUERY SELECT 'SUCCESS', 'Leave type created successfully', p_leave_type_id;
    ELSE
        UPDATE "LeaveTypeMaster" SET
            "LeaveTypeName"  = p_name,
            "LeaveCode"      = UPPER(p_code),
            "TotalDays"      = p_total_days,
            "CarryForward"   = p_carry_forward,
            "MaxCarryDays"   = p_max_carry_days,
            "UpdatedBy"      = p_user_id,
            "UpdatedAt"      = NOW()
        WHERE "LeaveTypeID" = p_leave_type_id
          AND (("SchoolID" = p_school_id) OR (p_school_id IS NULL AND "SchoolID" IS NULL))
          AND "IsDeleted"   = FALSE;

        RETURN QUERY SELECT 'SUCCESS', 'Leave type updated successfully', p_leave_type_id;
    END IF;
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveType_List
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveType_List(p_school_id INTEGER)
RETURNS TABLE(
    "LeaveTypeID"   INTEGER,
    "LeaveTypeName" VARCHAR,
    "LeaveCode"     VARCHAR,
    "TotalDays"     INTEGER,
    "CarryForward"  BOOLEAN,
    "MaxCarryDays"  INTEGER,
    "IsActive"      BOOLEAN,
    "IsDeleted"     BOOLEAN
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT lt."LeaveTypeID", lt."LeaveTypeName", lt."LeaveCode",
           lt."TotalDays", lt."CarryForward", lt."MaxCarryDays",
           lt."IsActive", lt."IsDeleted"
    FROM "LeaveTypeMaster" lt
    WHERE (lt."SchoolID" = p_school_id OR (p_school_id IS NULL AND lt."SchoolID" IS NULL))
    ORDER BY lt."IsDeleted" ASC, lt."LeaveTypeName" ASC;
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveType_Delete
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveType_Delete(p_leave_type_id INTEGER, p_user_id INTEGER)
RETURNS TABLE(status TEXT, message TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "LeaveTypeMaster" SET
        "IsDeleted" = TRUE, "DeletedBy" = p_user_id, "DeletedAt" = NOW()
    WHERE "LeaveTypeID" = p_leave_type_id AND "IsDeleted" = FALSE;

    RETURN QUERY SELECT 'SUCCESS', 'Leave type deleted';
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveType_Restore
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveType_Restore(p_leave_type_id INTEGER, p_user_id INTEGER)
RETURNS TABLE(status TEXT, message TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE "LeaveTypeMaster" SET
        "IsDeleted" = FALSE, "DeletedBy" = NULL, "DeletedAt" = NULL,
        "UpdatedBy" = p_user_id, "UpdatedAt" = NOW()
    WHERE "LeaveTypeID" = p_leave_type_id;

    RETURN QUERY SELECT 'SUCCESS', 'Leave type restored';
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveBalance_Init
--   Allocates balances for ALL active employees in a school for a given year.
--   Uses ON CONFLICT to skip already-initialized records.
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveBalance_Init(
    p_school_id  INTEGER,
    p_year       INTEGER,
    p_user_id    INTEGER
)
RETURNS TABLE(status TEXT, message TEXT, records_created INTEGER)
LANGUAGE plpgsql AS $$
DECLARE
    v_count INTEGER := 0;
BEGIN
    INSERT INTO "LeaveBalance" ("SchoolID","EmployeeID","LeaveTypeID","Year","TotalDays","CarryDays","UpdatedAt")
    SELECT
        p_school_id,
        u."UserID",
        lt."LeaveTypeID",
        p_year,
        lt."TotalDays",
        0,
        NOW()
    FROM "UserMaster" u
    CROSS JOIN "LeaveTypeMaster" lt
    WHERE (u."SchoolID" = p_school_id OR (p_school_id IS NULL AND u."SchoolID" IS NULL))
      AND u."IsActive"   = TRUE
      AND COALESCE(u."IsDeleted", FALSE) = FALSE
      AND u."ProfileID" != 1  -- exclude Super Admin
      AND (lt."SchoolID" = p_school_id OR (p_school_id IS NULL AND lt."SchoolID" IS NULL))
      AND lt."IsDeleted" = FALSE
      AND lt."IsActive"  = TRUE
    ON CONFLICT ("EmployeeID","LeaveTypeID","Year") DO NOTHING;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN QUERY SELECT 'SUCCESS', 'Balance initialized', v_count;
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveBalance_Get
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveBalance_Get(
    p_school_id   INTEGER,
    p_employee_id INTEGER,
    p_year        INTEGER
)
RETURNS TABLE(
    "LeaveTypeID"   INTEGER,
    "LeaveTypeName" VARCHAR,
    "LeaveCode"     VARCHAR,
    "TotalDays"     NUMERIC,
    "UsedDays"      NUMERIC,
    "PendingDays"   NUMERIC,
    "CarryDays"     NUMERIC,
    "AvailableDays" NUMERIC
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        lt."LeaveTypeID",
        lt."LeaveTypeName",
        lt."LeaveCode",
        COALESCE(lb."TotalDays", lt."TotalDays"::NUMERIC)   AS "TotalDays",
        COALESCE(lb."UsedDays",  0::NUMERIC)                AS "UsedDays",
        COALESCE(lb."PendingDays", 0::NUMERIC)              AS "PendingDays",
        COALESCE(lb."CarryDays",  0::NUMERIC)               AS "CarryDays",
        GREATEST(
            COALESCE(lb."TotalDays", lt."TotalDays"::NUMERIC)
            + COALESCE(lb."CarryDays", 0)
            - COALESCE(lb."UsedDays", 0)
            - COALESCE(lb."PendingDays", 0),
            0
        )                                                   AS "AvailableDays"
    FROM "LeaveTypeMaster" lt
    LEFT JOIN "LeaveBalance" lb
           ON lb."LeaveTypeID" = lt."LeaveTypeID"
          AND lb."EmployeeID"  = p_employee_id
          AND lb."Year"        = p_year
    WHERE (lt."SchoolID" = p_school_id OR (p_school_id IS NULL AND lt."SchoolID" IS NULL))
      AND lt."IsDeleted" = FALSE
      AND lt."IsActive"  = TRUE
    ORDER BY lt."LeaveTypeName";
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveRequest_Apply
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveRequest_Apply(
    p_school_id     INTEGER,
    p_employee_id   INTEGER,
    p_leave_type_id INTEGER,
    p_from_date     DATE,
    p_to_date       DATE,
    p_is_half_day   BOOLEAN,
    p_half_day_part VARCHAR,   -- 'First' or 'Second' or NULL
    p_reason        TEXT,
    p_user_id       INTEGER
)
RETURNS TABLE(status TEXT, message TEXT, request_id INTEGER)
LANGUAGE plpgsql AS $$
DECLARE
    v_days      NUMERIC;
    v_available NUMERIC;
    v_year      INTEGER;
    v_req_id    INTEGER;
BEGIN
    -- Basic validation
    IF p_from_date > p_to_date THEN
        RETURN QUERY SELECT 'ERROR', 'From date cannot be after To date', 0;
        RETURN;
    END IF;

    -- Calculate days requested
    IF p_is_half_day THEN
        v_days := 0.5;
    ELSE
        v_days := (p_to_date - p_from_date) + 1;
    END IF;

    v_year := EXTRACT(YEAR FROM p_from_date);

    -- Check available balance
    SELECT GREATEST(
        COALESCE(lb."TotalDays", lt."TotalDays"::NUMERIC)
        + COALESCE(lb."CarryDays", 0)
        - COALESCE(lb."UsedDays", 0)
        - COALESCE(lb."PendingDays", 0),
        0
    )
    INTO v_available
    FROM "LeaveTypeMaster" lt
    LEFT JOIN "LeaveBalance" lb
           ON lb."LeaveTypeID" = lt."LeaveTypeID"
          AND lb."EmployeeID"  = p_employee_id
          AND lb."Year"        = v_year
    WHERE lt."LeaveTypeID" = p_leave_type_id;

    IF v_available IS NULL OR v_days > v_available THEN
        RETURN QUERY SELECT 'ERROR',
            format('Insufficient leave balance. Available: %s days, Requested: %s days',
                   COALESCE(v_available, 0), v_days),
            0;
        RETURN;
    END IF;

    -- Check if overlapping pending/approved leave exists
    IF EXISTS (
        SELECT 1 FROM "LeaveRequest"
        WHERE "EmployeeID" = p_employee_id
          AND "Status" IN ('Pending','Approved')
          AND "IsDeleted" = FALSE
          AND "FromDate" <= p_to_date
          AND "ToDate"   >= p_from_date
    ) THEN
        RETURN QUERY SELECT 'ERROR', 'You already have a leave request overlapping these dates', 0;
        RETURN;
    END IF;

    -- Insert request
    INSERT INTO "LeaveRequest"
        ("SchoolID","EmployeeID","LeaveTypeID","FromDate","ToDate",
         "IsHalfDay","HalfDayPart","Reason","Status","RequestedOn")
    VALUES
        (p_school_id, p_employee_id, p_leave_type_id, p_from_date, p_to_date,
         p_is_half_day, p_half_day_part, p_reason, 'Pending', NOW())
    RETURNING "RequestID" INTO v_req_id;

    -- Update pending days in balance (create record if absent)
    INSERT INTO "LeaveBalance" ("SchoolID","EmployeeID","LeaveTypeID","Year",
                                 "TotalDays","PendingDays","UpdatedAt")
    VALUES (p_school_id, p_employee_id, p_leave_type_id, v_year,
            (SELECT "TotalDays" FROM "LeaveTypeMaster" WHERE "LeaveTypeID" = p_leave_type_id),
            v_days, NOW())
    ON CONFLICT ("EmployeeID","LeaveTypeID","Year")
    DO UPDATE SET
        "PendingDays" = "LeaveBalance"."PendingDays" + v_days,
        "UpdatedAt"   = NOW();

    -- Audit
    INSERT INTO "LeaveRequestHistory" ("RequestID","ActionBy","Action","Remarks","ActionOn")
    VALUES (v_req_id, p_user_id, 'Applied', p_reason, NOW());

    RETURN QUERY SELECT 'SUCCESS', 'Leave request submitted successfully', v_req_id;
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveRequest_List  (JSONB result)
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveRequest_List(
    p_school_id   INTEGER,
    p_employee_id INTEGER,   -- NULL = all employees (admin)
    p_status      VARCHAR,   -- NULL = all
    p_year        INTEGER,   -- NULL = current year
    p_page        INTEGER DEFAULT 1,
    p_page_size   INTEGER DEFAULT 20
)
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
    v_year      INTEGER := COALESCE(p_year, EXTRACT(YEAR FROM CURRENT_DATE));
    v_offset    INTEGER := (COALESCE(p_page, 1) - 1) * COALESCE(p_page_size, 20);
    v_total     INTEGER;
    v_records   JSONB;
BEGIN
    -- Total count
    SELECT COUNT(*) INTO v_total
    FROM "LeaveRequest" lr
    WHERE (lr."SchoolID" = p_school_id OR (p_school_id IS NULL AND lr."SchoolID" IS NULL))
      AND lr."IsDeleted" = FALSE
      AND (p_employee_id IS NULL OR lr."EmployeeID" = p_employee_id)
      AND (p_status IS NULL OR lr."Status" = p_status)
      AND EXTRACT(YEAR FROM lr."FromDate") = v_year;

    -- Records
    SELECT jsonb_agg(row_to_json(q)) INTO v_records
    FROM (
        SELECT
            lr."RequestID",
            lr."EmployeeID",
            u."UserName"                                     AS "EmployeeName",
            u."UserCode"                                     AS "EmployeeCode",
            lt."LeaveTypeName",
            lt."LeaveCode",
            lr."FromDate",
            lr."ToDate",
            lr."IsHalfDay",
            lr."HalfDayPart",
            lr."Reason",
            lr."Status",
            lr."RequestedOn",
            lr."Remarks",
            CASE WHEN lr."IsHalfDay" THEN 0.5
                 ELSE (lr."ToDate" - lr."FromDate") + 1 END AS "DaysRequested",
            app."UserName"                                   AS "ApprovedByName",
            lr."ApprovedOn"
        FROM "LeaveRequest" lr
        JOIN "UserMaster"      u   ON u."UserID"    = lr."EmployeeID"
        JOIN "LeaveTypeMaster" lt  ON lt."LeaveTypeID" = lr."LeaveTypeID"
        LEFT JOIN "UserMaster" app ON app."UserID"  = lr."ApprovedBy"
        WHERE (lr."SchoolID" = p_school_id OR (p_school_id IS NULL AND lr."SchoolID" IS NULL))
          AND lr."IsDeleted" = FALSE
          AND (p_employee_id IS NULL OR lr."EmployeeID" = p_employee_id)
          AND (p_status IS NULL OR lr."Status" = p_status)
          AND EXTRACT(YEAR FROM lr."FromDate") = v_year
        ORDER BY lr."RequestedOn" DESC
        LIMIT p_page_size OFFSET v_offset
    ) q;

    RETURN jsonb_build_object(
        'records',    COALESCE(v_records, '[]'::JSONB),
        'total',      v_total,
        'page',       COALESCE(p_page, 1),
        'page_size',  COALESCE(p_page_size, 20),
        'total_pages', CEIL(v_total::NUMERIC / COALESCE(p_page_size, 20))
    );
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveRequest_Approve
--   Approves or rejects a leave request.
--   On Approve: updates balance (used/pending) + marks StaffAttendance "On Leave"
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveRequest_Approve(
    p_request_id   INTEGER,
    p_approved_by  INTEGER,
    p_action       VARCHAR,   -- 'Approved' or 'Rejected'
    p_remarks      TEXT
)
RETURNS TABLE(status TEXT, message TEXT)
LANGUAGE plpgsql AS $$
DECLARE
    r              RECORD;
    v_days         NUMERIC;
    cur_date       DATE;
BEGIN
    -- Fetch the request
    SELECT * INTO r FROM "LeaveRequest"
    WHERE "RequestID" = p_request_id AND "Status" = 'Pending' AND "IsDeleted" = FALSE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT 'ERROR', 'Request not found or already processed';
        RETURN;
    END IF;

    -- Calculate days
    IF r."IsHalfDay" THEN
        v_days := 0.5;
    ELSE
        v_days := (r."ToDate" - r."FromDate") + 1;
    END IF;

    -- Update request status
    UPDATE "LeaveRequest" SET
        "Status"     = p_action,
        "ApprovedBy" = p_approved_by,
        "ApprovedOn" = NOW(),
        "Remarks"    = p_remarks
    WHERE "RequestID" = p_request_id;

    IF p_action = 'Approved' THEN
        -- Move from Pending → Used in balance
        UPDATE "LeaveBalance" SET
            "UsedDays"    = "UsedDays"    + v_days,
            "PendingDays" = GREATEST("PendingDays" - v_days, 0),
            "UpdatedAt"   = NOW()
        WHERE "EmployeeID"  = r."EmployeeID"
          AND "LeaveTypeID" = r."LeaveTypeID"
          AND "Year"        = EXTRACT(YEAR FROM r."FromDate");

        -- Mark attendance as "On Leave" for each day in range
        cur_date := r."FromDate";
        WHILE cur_date <= r."ToDate" LOOP
            -- Only insert/update if not already a weekend or holiday
            -- (We let the admin override; any existing record is updated)
            INSERT INTO "StaffAttendance"
                ("SchoolID","EmployeeID","AttendanceDate","Status","Remarks",
                 "AttendanceState","CreatedBy","CreatedAt","ApprovedBy","ApprovedAt","IsDeleted")
            VALUES
                (r."SchoolID", r."EmployeeID", cur_date, 'On Leave',
                 'Auto-marked: Leave #' || p_request_id,
                 'Approved', p_approved_by, NOW(), p_approved_by, NOW(), FALSE)
            ON CONFLICT ("EmployeeID","AttendanceDate")
            DO UPDATE SET
                "Status"          = 'On Leave',
                "Remarks"         = 'Auto-marked: Leave #' || p_request_id,
                "AttendanceState" = 'Approved',
                "ApprovedBy"      = p_approved_by,
                "ApprovedAt"      = NOW(),
                "UpdatedBy"       = p_approved_by,
                "UpdatedAt"       = NOW()
            WHERE "StaffAttendance"."IsDeleted" IS NOT TRUE;

            cur_date := cur_date + 1;
        END LOOP;

    ELSE  -- Rejected
        -- Release pending days
        UPDATE "LeaveBalance" SET
            "PendingDays" = GREATEST("PendingDays" - v_days, 0),
            "UpdatedAt"   = NOW()
        WHERE "EmployeeID"  = r."EmployeeID"
          AND "LeaveTypeID" = r."LeaveTypeID"
          AND "Year"        = EXTRACT(YEAR FROM r."FromDate");
    END IF;

    -- Audit
    INSERT INTO "LeaveRequestHistory"
        ("RequestID","ActionBy","Action","Remarks","ActionOn")
    VALUES (p_request_id, p_approved_by, p_action, p_remarks, NOW());

    RETURN QUERY SELECT 'SUCCESS', 'Request ' || p_action || ' successfully';
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveRequest_Cancel
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveRequest_Cancel(
    p_request_id   INTEGER,
    p_employee_id  INTEGER
)
RETURNS TABLE(status TEXT, message TEXT)
LANGUAGE plpgsql AS $$
DECLARE
    r      RECORD;
    v_days NUMERIC;
BEGIN
    SELECT * INTO r FROM "LeaveRequest"
    WHERE "RequestID"  = p_request_id
      AND "EmployeeID" = p_employee_id
      AND "Status"     = 'Pending'
      AND "IsDeleted"  = FALSE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT 'ERROR', 'Request not found or cannot be cancelled';
        RETURN;
    END IF;

    v_days := CASE WHEN r."IsHalfDay" THEN 0.5
                   ELSE (r."ToDate" - r."FromDate") + 1 END;

    UPDATE "LeaveRequest" SET "Status" = 'Cancelled', "IsDeleted" = TRUE
    WHERE "RequestID" = p_request_id;

    -- Release pending days
    UPDATE "LeaveBalance" SET
        "PendingDays" = GREATEST("PendingDays" - v_days, 0),
        "UpdatedAt"   = NOW()
    WHERE "EmployeeID"  = r."EmployeeID"
      AND "LeaveTypeID" = r."LeaveTypeID"
      AND "Year"        = EXTRACT(YEAR FROM r."FromDate");

    INSERT INTO "LeaveRequestHistory"
        ("RequestID","ActionBy","Action","Remarks","ActionOn")
    VALUES (p_request_id, p_employee_id, 'Cancelled', 'Cancelled by employee', NOW());

    RETURN QUERY SELECT 'SUCCESS', 'Leave request cancelled';
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveBalance_StaffList
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveBalance_StaffList(
    p_school_id   INTEGER,
    p_year        INTEGER,
    p_employee_id INTEGER DEFAULT NULL,
    p_search      VARCHAR DEFAULT NULL
)
RETURNS TABLE(
    "EmployeeID"    INTEGER,
    "EmployeeName"  VARCHAR,
    "EmployeeCode"  VARCHAR,
    "LeaveTypeID"   INTEGER,
    "LeaveTypeName" VARCHAR,
    "LeaveCode"     VARCHAR,
    "TotalDays"     NUMERIC,
    "UsedDays"      NUMERIC,
    "PendingDays"   NUMERIC,
    "CarryDays"     NUMERIC,
    "AvailableDays" NUMERIC
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH filtered_users AS (
        SELECT um."UserID", um."UserName", um."UserCode"
        FROM "UserMaster" um
        WHERE (um."SchoolID" = p_school_id OR (p_school_id IS NULL AND um."SchoolID" IS NULL))
          AND um."IsActive" = TRUE
          AND COALESCE(um."IsDeleted", FALSE) = FALSE
          AND um."ProfileID" != 1
          AND (p_employee_id IS NULL OR um."UserID" = p_employee_id)
          AND (p_search IS NULL OR 
               LOWER(um."UserName") LIKE '%' || LOWER(p_search) || '%' OR 
               LOWER(um."UserCode") LIKE '%' || LOWER(p_search) || '%')
    ),
    filtered_types AS (
        SELECT ltm."LeaveTypeID", ltm."LeaveTypeName", ltm."LeaveCode", ltm."TotalDays"
        FROM "LeaveTypeMaster" ltm
        WHERE (ltm."SchoolID" = p_school_id OR (p_school_id IS NULL AND ltm."SchoolID" IS NULL))
          AND ltm."IsActive" = TRUE
          AND ltm."IsDeleted" = FALSE
    )
    SELECT
        u."UserID"                                          AS "EmployeeID",
        u."UserName"                                        AS "EmployeeName",
        u."UserCode"                                        AS "EmployeeCode",
        lt."LeaveTypeID",
        lt."LeaveTypeName",
        lt."LeaveCode",
        COALESCE(lb."TotalDays", lt."TotalDays"::NUMERIC)   AS "TotalDays",
        COALESCE(lb."UsedDays",  0::NUMERIC)                AS "UsedDays",
        COALESCE(lb."PendingDays", 0::NUMERIC)              AS "PendingDays",
        COALESCE(lb."CarryDays",  0::NUMERIC)               AS "CarryDays",
        GREATEST(
            COALESCE(lb."TotalDays", lt."TotalDays"::NUMERIC)
            + COALESCE(lb."CarryDays", 0)
            - COALESCE(lb."UsedDays", 0)
            - COALESCE(lb."PendingDays", 0),
            0
        )                                                   AS "AvailableDays"
    FROM filtered_users u
    CROSS JOIN filtered_types lt
    LEFT JOIN "LeaveBalance" lb
           ON lb."LeaveTypeID" = lt."LeaveTypeID"
          AND lb."EmployeeID"  = u."UserID"
          AND lb."Year"        = p_year
    ORDER BY u."UserName", lt."LeaveTypeName";
END;
$$;


-- ============================================================
-- PROCEDURE: Proc_LeaveReport_Get  (JSONB result)
-- ============================================================
CREATE OR REPLACE FUNCTION Proc_LeaveReport_Get(
    p_school_id   INTEGER,
    p_employee_id INTEGER,   -- NULL = all
    p_month       INTEGER,   -- NULL = all months
    p_year        INTEGER
)
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
    v_records JSONB;
    v_summary JSONB;
BEGIN
    -- Per-employee summary
    SELECT jsonb_agg(row_to_json(q)) INTO v_records
    FROM (
        SELECT
            u."UserID"                                          AS "EmployeeID",
            u."UserName"                                        AS "EmployeeName",
            u."UserCode"                                        AS "EmployeeCode",
            lt."LeaveTypeName",
            lt."LeaveCode",
            COUNT(lr."RequestID")                               AS "RequestCount",
            SUM(CASE WHEN lr."IsHalfDay" THEN 0.5
                     ELSE (lr."ToDate" - lr."FromDate") + 1 END
            )                                                   AS "TotalDaysTaken",
            COUNT(CASE WHEN lr."Status" = 'Approved'  THEN 1 END) AS "Approved",
            COUNT(CASE WHEN lr."Status" = 'Rejected'  THEN 1 END) AS "Rejected",
            COUNT(CASE WHEN lr."Status" = 'Pending'   THEN 1 END) AS "Pending",
            COUNT(CASE WHEN lr."Status" = 'Cancelled' THEN 1 END) AS "Cancelled"
        FROM "UserMaster" u
        JOIN "LeaveRequest" lr ON lr."EmployeeID" = u."UserID"
        JOIN "LeaveTypeMaster" lt ON lt."LeaveTypeID" = lr."LeaveTypeID"
        WHERE (lr."SchoolID" = p_school_id OR (p_school_id IS NULL AND lr."SchoolID" IS NULL))
          AND lr."IsDeleted" = FALSE
          AND EXTRACT(YEAR FROM lr."FromDate") = p_year
          AND (p_employee_id IS NULL OR u."UserID"  = p_employee_id)
          AND (p_month       IS NULL OR EXTRACT(MONTH FROM lr."FromDate") = p_month)
        GROUP BY u."UserID", u."UserName", u."UserCode", lt."LeaveTypeName", lt."LeaveCode"
        ORDER BY u."UserName", lt."LeaveTypeName"
    ) q;

    RETURN jsonb_build_object(
        'records', COALESCE(v_records, '[]'::JSONB),
        'year',    p_year,
        'month',   p_month
    );
END;
$$;


-- ============================================================
-- MENU: Add Leave Management to MenuMaster + ProfileMenuMapping
-- ============================================================
DO $$
DECLARE
    v_parent_menu_id   INTEGER;
    v_menu_apply_id    INTEGER;
    v_menu_requests_id INTEGER;
    v_menu_types_id    INTEGER;
    v_menu_report_id   INTEGER;
    pid                INTEGER;
    admin_user_id      INTEGER := 1;
    profile_ids        INTEGER[] := ARRAY[1,2,3,6,7,5,8]; -- Super Admin,School Admin,Teacher,Driver,Librarian,Accountant,Support Exec
BEGIN
    -- Check and insert parent menu
    IF NOT EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuURL" = '/leave/' AND "IsDeleted" = FALSE) THEN
        INSERT INTO "MenuMaster"
            ("MenuName","DisplayOrder","ParentMenuID","MenuURL","Icon","IsActive","IsDeleted","CreatedBy","CreatedAt")
        VALUES
            ('Leave Management', 65, NULL, '/leave/', 'fas fa-calendar-check', TRUE, FALSE, admin_user_id, NOW())
        RETURNING "MenuID" INTO v_parent_menu_id;
    ELSE
        SELECT "MenuID" INTO v_parent_menu_id FROM "MenuMaster" WHERE "MenuURL" = '/leave/' AND "IsDeleted" = FALSE LIMIT 1;
    END IF;

    -- Sub-menu: Apply Leave
    IF NOT EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuURL" = '/leave/apply/' AND "IsDeleted" = FALSE) THEN
        INSERT INTO "MenuMaster"
            ("MenuName","DisplayOrder","ParentMenuID","MenuURL","Icon","IsActive","IsDeleted","CreatedBy","CreatedAt")
        VALUES
            ('Apply Leave', 1, v_parent_menu_id, '/leave/apply/', 'fas fa-paper-plane', TRUE, FALSE, admin_user_id, NOW())
        RETURNING "MenuID" INTO v_menu_apply_id;
    ELSE
        SELECT "MenuID" INTO v_menu_apply_id FROM "MenuMaster" WHERE "MenuURL" = '/leave/apply/' AND "IsDeleted" = FALSE LIMIT 1;
    END IF;

    -- Sub-menu: Leave Dashboard (all requests)
    IF NOT EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuURL" = '/leave/' AND "ParentMenuID" = v_parent_menu_id AND "IsDeleted" = FALSE) THEN
        INSERT INTO "MenuMaster"
            ("MenuName","DisplayOrder","ParentMenuID","MenuURL","Icon","IsActive","IsDeleted","CreatedBy","CreatedAt")
        VALUES
            ('Leave Dashboard', 2, v_parent_menu_id, '/leave/', 'fas fa-tachometer-alt', TRUE, FALSE, admin_user_id, NOW())
        RETURNING "MenuID" INTO v_menu_requests_id;
    ELSE
        SELECT "MenuID" INTO v_menu_requests_id FROM "MenuMaster"
        WHERE "MenuURL" = '/leave/' AND "ParentMenuID" = v_parent_menu_id AND "IsDeleted" = FALSE LIMIT 1;
    END IF;

    -- Sub-menu: Leave Report
    IF NOT EXISTS (SELECT 1 FROM "MenuMaster" WHERE "MenuURL" = '/leave/report/' AND "IsDeleted" = FALSE) THEN
        INSERT INTO "MenuMaster"
            ("MenuName","DisplayOrder","ParentMenuID","MenuURL","Icon","IsActive","IsDeleted","CreatedBy","CreatedAt")
        VALUES
            ('Leave Report', 3, v_parent_menu_id, '/leave/report/', 'fas fa-chart-bar', TRUE, FALSE, admin_user_id, NOW())
        RETURNING "MenuID" INTO v_menu_report_id;
    ELSE
        SELECT "MenuID" INTO v_menu_report_id FROM "MenuMaster" WHERE "MenuURL" = '/leave/report/' AND "IsDeleted" = FALSE LIMIT 1;
    END IF;

    -- Map all menus to all staff profiles
    FOREACH pid IN ARRAY profile_ids LOOP
        -- parent
        INSERT INTO "ProfileMenuMapping" ("ProfileID","MenuID","CanView","CanAdd","CanEdit","CanDelete","IsDeleted","CreatedAt")
        VALUES (pid, v_parent_menu_id, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
        ON CONFLICT DO NOTHING;

        -- Apply Leave
        INSERT INTO "ProfileMenuMapping" ("ProfileID","MenuID","CanView","CanAdd","CanEdit","CanDelete","IsDeleted","CreatedAt")
        VALUES (pid, v_menu_apply_id, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
        ON CONFLICT DO NOTHING;

        -- Dashboard
        INSERT INTO "ProfileMenuMapping" ("ProfileID","MenuID","CanView","CanAdd","CanEdit","CanDelete","IsDeleted","CreatedAt")
        VALUES (pid, v_menu_requests_id, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
        ON CONFLICT DO NOTHING;

        -- Report
        INSERT INTO "ProfileMenuMapping" ("ProfileID","MenuID","CanView","CanAdd","CanEdit","CanDelete","IsDeleted","CreatedAt")
        VALUES (pid, v_menu_report_id, TRUE, TRUE, TRUE, TRUE, FALSE, NOW())
        ON CONFLICT DO NOTHING;
    END LOOP;

END;
$$;
