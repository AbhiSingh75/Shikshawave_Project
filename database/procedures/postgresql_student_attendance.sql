-- =============================================
-- PostgreSQL Script for Student Attendance Procedures
-- =============================================

-- =============================================
-- Procedure 1: Get Student List for Attendance Marking
-- =============================================
CREATE OR REPLACE FUNCTION "Proc_StudentList_Get"(
    p_SchoolID INT,
    p_ClassID INT,
    p_SectionID INT DEFAULT NULL,
    p_AttendanceDate DATE DEFAULT NULL
)
RETURNS TABLE (
    "StudentID" INT,
    "StudentCode" VARCHAR,
    "FullName" VARCHAR,
    "RollNo" VARCHAR,
    "Gender" VARCHAR,
    "ClassID" INT,
    "AdmissionClass" VARCHAR,
    "SectionID" INT,
    "Section" VARCHAR,
    "Status" VARCHAR,
    "Remarks" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s."StudentID",
        s."StudentCode",
        s."FullName",
        COALESCE(sat."RollNumber", '')::VARCHAR AS "RollNo",
        s."Gender",
        c."ClassID",
        c."ClassName" AS "AdmissionClass",
        sm."SectionID",
        sm."SectionName" AS "Section",
        COALESCE(sa."Status", 'present')::VARCHAR AS "Status",
        COALESCE(sa."Remarks", '')::VARCHAR AS "Remarks"
    FROM "Student" s
    LEFT JOIN "StudentAcademicTrack" sat ON s."StudentID" = sat."StudentID" AND sat."IsCurrent" = TRUE AND COALESCE(sat."IsDeleted", FALSE) = FALSE
    INNER JOIN "ClassMaster" c ON CAST(NULLIF(REGEXP_REPLACE(s."AdmissionClass"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = c."ClassID"
    LEFT JOIN "SectionMaster" sm ON CAST(NULLIF(REGEXP_REPLACE(s."Section"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = sm."SectionID"
    LEFT JOIN "StudentAttendance" sa ON s."StudentID" = sa."StudentID" 
        AND sa."AttendanceDate" = p_AttendanceDate 
        AND sa."IsDeleted" IS NOT TRUE
    WHERE s."SchoolID" = p_SchoolID
    AND c."ClassID" = p_ClassID
    AND (p_SectionID IS NULL OR sm."SectionID" = p_SectionID)
    AND s."IsDeleted" IS NOT TRUE
    AND s."IsDeleted" IS NOT TRUE
    ORDER BY s."FullName";
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 2: Mark/Update Student Attendance (Bulk)
-- =============================================
CREATE OR REPLACE FUNCTION "Proc_StudentAttendance_Mark_Bulk"(
    p_SchoolID INT,
    p_ClassID INT,
    p_SectionID INT,
    p_AttendanceDate DATE,
    p_AttendanceData JSONB,
    p_CreatedBy INT
)
RETURNS TABLE ("Result" VARCHAR, "Message" VARCHAR) AS $$
DECLARE
    v_Record JSONB;
BEGIN
    -- Process each attendance record in the JSON array
    FOR v_Record IN SELECT * FROM jsonb_array_elements(p_AttendanceData)
    LOOP
        -- First try to update existing record
        UPDATE "StudentAttendance"
        SET 
            "Status" = v_Record->>'Status',
            "Remarks" = COALESCE(v_Record->>'Remarks', ''),
            "UpdatedBy" = p_CreatedBy,
            "UpdatedAt" = CURRENT_TIMESTAMP
        WHERE "StudentID" = (v_Record->>'StudentID')::INT 
        AND "AttendanceDate" = p_AttendanceDate
        AND "IsDeleted" IS NOT TRUE;

        -- If no record was updated, insert a new one
        IF NOT FOUND THEN
            INSERT INTO "StudentAttendance" (
                "SchoolID", 
                "StudentID", 
                "ClassID", 
                "SectionID", 
                "AttendanceDate", 
                "Status", 
                "Remarks", 
                "CreatedBy", 
                "CreatedAt", 
                "IsDeleted"
            )
            VALUES (
                p_SchoolID, 
                (v_Record->>'StudentID')::INT, 
                p_ClassID, 
                COALESCE((v_Record->>'SectionID')::INT, p_SectionID),
                p_AttendanceDate, 
                v_Record->>'Status', 
                COALESCE(v_Record->>'Remarks', ''),
                p_CreatedBy, 
                CURRENT_TIMESTAMP, 
                FALSE
            );
        END IF;
    END LOOP;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Attendance saved successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Procedure 3: Get attendance records for a class on a specific date
-- =============================================
CREATE OR REPLACE FUNCTION "Proc_StudentAttendance_Get"(
    p_SchoolID INT,
    p_ClassID INT,
    p_AttendanceDate DATE
)
RETURNS TABLE (
    "StudentID" INT,
    "FullName" VARCHAR,
    "StudentCode" VARCHAR,
    "Status" VARCHAR,
    "AttendanceDate" DATE,
    "ClassName" VARCHAR,
    "SectionName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sa."StudentID",
        s."FullName",
        s."StudentCode",
        sa."Status",
        sa."AttendanceDate",
        c."ClassName",
        sm."SectionName"
    FROM "StudentAttendance" sa
    INNER JOIN "Student" s ON sa."StudentID" = s."StudentID"
    INNER JOIN "ClassMaster" c ON sa."ClassID" = c."ClassID"
    LEFT JOIN "SectionMaster" sm ON sa."SectionID" = sm."SectionID"
    WHERE sa."SchoolID" = p_SchoolID 
    AND sa."ClassID" = p_ClassID
    AND sa."AttendanceDate" = p_AttendanceDate
    AND sa."IsDeleted" = FALSE
    ORDER BY s."FullName";
END;
$$ LANGUAGE plpgsql;
