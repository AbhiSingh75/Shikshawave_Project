-- =============================================
-- PostgreSQL Script for Staff Attendance Procedures
-- =============================================

-- =============================================
-- Procedure 1: Get Staff List for Attendance Marking
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffList_Get(
    p_SchoolID INT,
    p_AttendanceDate DATE DEFAULT NULL,
    p_LoginUserID INT DEFAULT NULL,
    p_LoginProfileName VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    "EmployeeID" INT,
    "EmployeeName" TEXT,
    "EmployeeCode" VARCHAR,
    "Role" VARCHAR,
    "Status" VARCHAR,
    "Remarks" VARCHAR,
    "AttendanceID" INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        um."UserID" AS "EmployeeID",
        (um."UserCode" || ' - ' || um."UserName")::TEXT AS "EmployeeName",
        um."UserCode" AS "EmployeeCode",
        pm."ProfileName" AS "Role",
        sa."Status",
        sa."Remarks",
        sa."AttendanceID"
    FROM "UserMaster" um
    INNER JOIN "ProfileMaster" pm ON um."ProfileID" = pm."ProfileID"
    LEFT JOIN "StaffAttendance" sa ON um."UserID" = sa."EmployeeID" 
        AND sa."AttendanceDate" = p_AttendanceDate 
        AND sa."IsDeleted" IS NOT TRUE
    WHERE ((p_SchoolID IS NULL AND um."SchoolID" IS NULL) OR (p_SchoolID IS NOT NULL AND um."SchoolID" = p_SchoolID))
    AND um."ProfileID" IN (2, 3, 5, 6, 7, 8) -- School Admin, Teacher, Accountant, Driver, Librarian, Support Exec
    AND um."IsDeleted" IS NOT TRUE
    AND um."IsActive" IS TRUE
    ORDER BY pm."ProfileID", um."UserName";
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 2: Mark/Update Staff Attendance (Bulk)
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffAttendance_Mark_Bulk(
    p_SchoolID INT,
    p_AttendanceDate DATE,
    p_AttendanceData JSONB,
    p_CreatedBy INT,
    p_ProfileName VARCHAR
)
RETURNS TABLE ("Result" VARCHAR, "Message" VARCHAR) AS $$
DECLARE
    v_AttendanceState VARCHAR(20);
    v_ApprovedBy INT := NULL;
    v_Record JSONB;
BEGIN
    -- Determine Approval State based on Profile
    IF p_ProfileName IN ('School Admin', 'Super Admin') THEN
        v_AttendanceState := 'Approved';
        v_ApprovedBy := p_CreatedBy;
    ELSE
        v_AttendanceState := 'Pending';
    END IF;

    -- Process each attendance record in the JSON array
    FOR v_Record IN SELECT * FROM jsonb_array_elements(p_AttendanceData)
    LOOP
        INSERT INTO "StaffAttendance" (
            "SchoolID", 
            "EmployeeID", 
            "AttendanceDate", 
            "Status", 
            "Remarks", 
            "AttendanceState", 
            "CreatedBy", 
            "CreatedAt", 
            "ApprovedBy", 
            "ApprovedAt", 
            "IsDeleted"
        )
        VALUES (
            p_SchoolID, 
            (v_Record->>'EmployeeID')::INT, 
            p_AttendanceDate, 
            v_Record->>'Status', 
            v_Record->>'Remarks', 
            v_AttendanceState, 
            p_CreatedBy, 
            CURRENT_TIMESTAMP, 
            v_ApprovedBy, 
            CASE WHEN v_AttendanceState = 'Approved' THEN CURRENT_TIMESTAMP ELSE NULL END, 
            FALSE
        )
        ON CONFLICT ("EmployeeID", "AttendanceDate") DO UPDATE 
        SET 
            "Status" = EXCLUDED."Status",
            "Remarks" = EXCLUDED."Remarks",
            "UpdatedBy" = EXCLUDED."CreatedBy",
            "UpdatedAt" = CURRENT_TIMESTAMP,
            "AttendanceState" = v_AttendanceState,
            "ApprovedBy" = v_ApprovedBy,
            "ApprovedAt" = CASE WHEN v_AttendanceState = 'Approved' THEN CURRENT_TIMESTAMP ELSE NULL END
        WHERE "StaffAttendance"."IsDeleted" IS NOT TRUE;
    END LOOP;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Attendance saved successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 3: Get Staff Attendance Records with Filters
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffAttendance_Get(
    p_SchoolID INT DEFAULT NULL,
    p_StartDate DATE DEFAULT NULL,
    p_EndDate DATE DEFAULT NULL,
    p_EmployeeID INT DEFAULT NULL,
    p_Status VARCHAR DEFAULT NULL,
    p_PageNumber INT DEFAULT 1,
    p_PageSize INT DEFAULT 50
)
RETURNS TABLE (
    "AttendanceID" INT,
    "AttendanceDate" DATE,
    "Status" VARCHAR,
    "Remarks" VARCHAR,
    "AttendanceState" VARCHAR,
    "EmployeeID" INT,
    "EmployeeName" VARCHAR,
    "EmployeeCode" VARCHAR,
    "Role" VARCHAR,
    "ApprovedByName" VARCHAR,
    "ApprovedAt" TIMESTAMP,
    "TotalRecords" BIGINT
) AS $$
DECLARE
    v_Offset INT := (p_PageNumber - 1) * p_PageSize;
BEGIN
    RETURN QUERY
    WITH CountQuery AS (
        SELECT COUNT(*) AS total
        FROM "StaffAttendance" sa
        INNER JOIN "UserMaster" um ON sa."EmployeeID" = um."UserID"
        WHERE ((p_SchoolID IS NULL AND sa."SchoolID" IS NULL) OR (p_SchoolID IS NOT NULL AND sa."SchoolID" = p_SchoolID))
        AND sa."IsDeleted" IS NOT TRUE
        AND (p_StartDate IS NULL OR sa."AttendanceDate" >= p_StartDate)
        AND (p_EndDate IS NULL OR sa."AttendanceDate" <= p_EndDate)
        AND (p_EmployeeID IS NULL OR sa."EmployeeID" = p_EmployeeID)
        AND (p_Status IS NULL OR sa."Status" = p_Status)
    )
    SELECT 
        sa."AttendanceID",
        sa."AttendanceDate",
        sa."Status",
        sa."Remarks"::VARCHAR,
        sa."AttendanceState"::VARCHAR,
        um."UserID"::INT AS "EmployeeID",
        um."UserName"::VARCHAR AS "EmployeeName",
        um."UserCode"::VARCHAR AS "EmployeeCode",
        pm."ProfileName"::VARCHAR AS "Role",
        approver."UserName"::VARCHAR AS "ApprovedByName",
        sa."ApprovedAt",
        (SELECT total FROM CountQuery) AS "TotalRecords"
    FROM "StaffAttendance" sa
    INNER JOIN "UserMaster" um ON sa."EmployeeID" = um."UserID"
    INNER JOIN "ProfileMaster" pm ON um."ProfileID" = pm."ProfileID"
    LEFT JOIN "UserMaster" approver ON sa."ApprovedBy" = approver."UserID"
    WHERE ((p_SchoolID IS NULL AND sa."SchoolID" IS NULL) OR (p_SchoolID IS NOT NULL AND sa."SchoolID" = p_SchoolID))
    AND sa."IsDeleted" IS NOT TRUE
    AND (p_StartDate IS NULL OR sa."AttendanceDate" >= p_StartDate)
    AND (p_EndDate IS NULL OR sa."AttendanceDate" <= p_EndDate)
    AND (p_EmployeeID IS NULL OR sa."EmployeeID" = p_EmployeeID)
    AND (p_Status IS NULL OR sa."Status" = p_Status)
    ORDER BY sa."AttendanceDate" DESC, um."UserName"
    OFFSET v_Offset LIMIT p_PageSize;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 4: Get Pending Staff Attendance
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffAttendance_Pending(
    p_SchoolID INT DEFAULT NULL,
    p_LoginUserID INT DEFAULT NULL,
    p_LoginProfileName VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    "AttendanceID" INT,
    "AttendanceDate" DATE,
    "Status" VARCHAR,
    "Remarks" VARCHAR,
    "EmployeeID" INT,
    "EmployeeName" VARCHAR,
    "EmployeeCode" VARCHAR,
    "Role" VARCHAR,
    "CreatedByName" VARCHAR,
    "CreatedAt" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa."AttendanceID",
        sa."AttendanceDate",
        sa."Status",
        sa."Remarks"::VARCHAR,
        um."UserID"::INT AS "EmployeeID",
        um."UserName"::VARCHAR AS "EmployeeName",
        um."UserCode"::VARCHAR AS "EmployeeCode",
        pm."ProfileName"::VARCHAR AS "Role",
        creator."UserName"::VARCHAR AS "CreatedByName",
        sa."CreatedAt"
    FROM "StaffAttendance" sa
    INNER JOIN "UserMaster" um ON sa."EmployeeID" = um."UserID"
    INNER JOIN "ProfileMaster" pm ON um."ProfileID" = pm."ProfileID"
    LEFT JOIN "UserMaster" creator ON sa."CreatedBy" = creator."UserID"
    WHERE sa."AttendanceState" = 'Pending'
    AND sa."IsDeleted" IS NOT TRUE
    AND (
        (p_LoginProfileName = 'Super Admin')
        OR
        (p_LoginProfileName = 'School Admin' AND sa."SchoolID" = p_SchoolID)
        OR
        (p_LoginProfileName = 'Support Executive' AND um."UserID" = p_LoginUserID)
    )
    ORDER BY sa."AttendanceDate" DESC, um."UserName";
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 5: Approve/Reject Pending Attendance
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffAttendance_Approve(
    p_AttendanceID INT,
    p_ApprovedBy INT,
    p_AttendanceState VARCHAR,
    p_ApprovalRemarks VARCHAR DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE "StaffAttendance"
    SET 
        "AttendanceState" = p_AttendanceState,
        "ApprovedBy" = p_ApprovedBy,
        "ApprovedAt" = CURRENT_TIMESTAMP,
        "ApprovalRemarks" = p_ApprovalRemarks,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_ApprovedBy
    WHERE "AttendanceID" = p_AttendanceID
    AND "IsDeleted" IS NOT TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 6: Get Staff Attendance Stats
-- =============================================
CREATE OR REPLACE FUNCTION Proc_StaffAttendance_Stats(
    p_SchoolID INT DEFAULT NULL,
    p_StartDate DATE DEFAULT NULL,
    p_EndDate DATE DEFAULT NULL,
    p_EmployeeID INT DEFAULT NULL,
    p_Status VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    "TotalEmployees" BIGINT,
    "TotalPresent" BIGINT,
    "TotalAbsent" BIGINT,
    "TotalLeave" BIGINT,
    "TotalHalfDay" BIGINT,
    "TotalLate" BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT um."UserID") AS "TotalEmployees",
        SUM(CASE WHEN sa."Status" = 'Present' THEN 1 ELSE 0 END) AS "TotalPresent",
        SUM(CASE WHEN sa."Status" = 'Absent' THEN 1 ELSE 0 END) AS "TotalAbsent",
        SUM(CASE WHEN sa."Status" = 'Leave' THEN 1 ELSE 0 END) AS "TotalLeave",
        SUM(CASE WHEN sa."Status" = 'Half Day' THEN 1 ELSE 0 END) AS "TotalHalfDay",
        SUM(CASE WHEN sa."Status" = 'Late' THEN 1 ELSE 0 END) AS "TotalLate"
    FROM "UserMaster" um
    LEFT JOIN "StaffAttendance" sa ON um."UserID" = sa."EmployeeID"
        AND sa."IsDeleted" IS NOT TRUE
        AND (p_StartDate IS NULL OR sa."AttendanceDate" >= p_StartDate)
        AND (p_EndDate IS NULL OR sa."AttendanceDate" <= p_EndDate)
        AND (p_Status IS NULL OR sa."Status" = p_Status)
    WHERE ((p_SchoolID IS NULL AND um."SchoolID" IS NULL) OR (p_SchoolID IS NOT NULL AND um."SchoolID" = p_SchoolID))
    AND um."ProfileID" IN (2, 3, 5, 6, 7, 8)
    AND um."IsDeleted" IS NOT TRUE
    AND um."IsActive" IS TRUE
    AND (p_EmployeeID IS NULL OR um."UserID" = p_EmployeeID);
END;
$$ LANGUAGE plpgsql;
