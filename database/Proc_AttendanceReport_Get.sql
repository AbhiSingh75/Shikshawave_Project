-- Procedure to get Attendance Statistics and Student Data in a single JSON result
CREATE OR REPLACE FUNCTION "Proc_AttendanceReport_Get"(
    p_SchoolID INTEGER,
    p_ClassID INTEGER,
    p_SectionID INTEGER,
    p_Date DATE
)
RETURNS JSONB AS $$
DECLARE
    v_Result JSONB;
    v_Stats JSONB;
    v_Students JSONB;
    v_TotalPresent INTEGER := 0;
    v_TotalAbsent INTEGER := 0;
    v_TotalLate INTEGER := 0;
    v_TotalHoliday INTEGER := 0;
    v_TotalMarked INTEGER := 0;
BEGIN
    -- 1. Calculate Statistics
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'P' OR "Status" ILIKE 'PRESENT'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'A' OR "Status" ILIKE 'ABSENT'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'L' OR "Status" ILIKE 'LATE'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'H' OR "Status" ILIKE 'HOLIDAY')
    INTO 
        v_TotalMarked, v_TotalPresent, v_TotalAbsent, v_TotalLate, v_TotalHoliday
    FROM "StudentAttendance"
    WHERE "SchoolID" = p_SchoolID
      AND "ClassID"::INTEGER = p_ClassID
      AND (p_SectionID IS NULL OR "SectionID"::INTEGER = p_SectionID)
      AND "AttendanceDate" = p_Date
      AND COALESCE("IsDeleted", FALSE) = FALSE;

    v_Stats := jsonb_build_object(
        'present', v_TotalPresent,
        'absent', v_TotalAbsent,
        'late', v_TotalLate,
        'holiday', v_TotalHoliday,
        'total', v_TotalMarked,
        'present_percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalPresent::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END,
        'absent_percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalAbsent::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END,
        'late_percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalLate::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END,
        'holiday_percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalHoliday::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END
    );

    -- 2. Get Student Data
    SELECT jsonb_agg(t)
    INTO v_Students
    FROM (
        SELECT 
            s."StudentID" as id,
            s."StudentName" as name,
            s."StudentCode" as code,
            a."Status" as status,
            a."AttendanceDate" as date,
            c."ClassName" as class,
            sec."SectionName" as section,
            s."RollNo" as roll_no,
            CASE 
                WHEN a."Status" ILIKE 'P' OR a."Status" ILIKE 'PRESENT' THEN 'present'
                WHEN a."Status" ILIKE 'A' OR a."Status" ILIKE 'ABSENT' THEN 'absent'
                WHEN a."Status" ILIKE 'L' OR a."Status" ILIKE 'LATE' THEN 'late'
                WHEN a."Status" ILIKE 'H' OR a."Status" ILIKE 'HOLIDAY' THEN 'holiday'
                ELSE 'unknown'
            END as status_class
        FROM "StudentAttendance" a
        INNER JOIN "Student" s ON a."StudentID" = s."StudentID"
        INNER JOIN "ClassMaster" c ON a."ClassID"::INTEGER = c."ClassID"
        LEFT JOIN "SectionMaster" sec ON a."SectionID"::INTEGER = sec."SectionID"
        WHERE a."SchoolID" = p_SchoolID
          AND a."ClassID"::INTEGER = p_ClassID
          AND (p_SectionID IS NULL OR a."SectionID"::INTEGER = p_SectionID)
          AND a."AttendanceDate" = p_Date
          AND COALESCE(a."IsDeleted", FALSE) = FALSE
        ORDER BY s."StudentName"
    ) t;

    -- 3. Combine Result
    v_Result := jsonb_build_object(
        'stats', v_Stats,
        'students', COALESCE(v_Students, '[]'::jsonb)
    );

    RETURN v_Result;
END;
$$ LANGUAGE plpgsql;
