-- Procedure to get Staff Attendance Statistics, Graph Data, and Paginated Records
CREATE OR REPLACE FUNCTION Proc_Staff_AttendanceReport_Get(
    p_SchoolID INTEGER,
    p_StartDate DATE,
    p_EndDate DATE,
    p_EmployeeID INTEGER DEFAULT NULL,
    p_Status VARCHAR DEFAULT NULL,
    p_Page INTEGER DEFAULT 1,
    p_PageSize INTEGER DEFAULT 10
)
RETURNS JSONB AS $$
DECLARE
    v_Result JSONB;
    v_Stats JSONB;
    v_GraphData JSONB;
    v_Records JSONB;
    v_TotalPresent INTEGER := 0;
    v_TotalAbsent INTEGER := 0;
    v_TotalLate INTEGER := 0;
    v_TotalLeave INTEGER := 0;
    v_TotalMarked INTEGER := 0;
    v_Offset INTEGER;
BEGIN
    v_Offset := (p_Page - 1) * p_PageSize;

    -- 1. Calculate Overall Statistics using the filters
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'present' OR "Status" ILIKE 'P'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'absent' OR "Status" ILIKE 'A'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'late' OR "Status" ILIKE 'L'),
        COUNT(*) FILTER (WHERE "Status" ILIKE 'leave' OR "Status" ILIKE 'LV')
    INTO 
        v_TotalMarked, v_TotalPresent, v_TotalAbsent, v_TotalLate, v_TotalLeave
    FROM "StaffAttendance"
    WHERE ("SchoolID" = p_SchoolID OR p_SchoolID IS NULL)
      AND (p_StartDate IS NULL OR "AttendanceDate" >= p_StartDate)
      AND (p_EndDate IS NULL OR "AttendanceDate" <= p_EndDate)
      AND (p_EmployeeID IS NULL OR "EmployeeID" = p_EmployeeID)
      AND (p_Status IS NULL OR "Status" ILIKE p_Status)
      AND COALESCE("IsDeleted", FALSE) = FALSE;

    v_Stats := jsonb_build_object(
        'present', jsonb_build_object('count', v_TotalPresent, 'percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalPresent::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END),
        'absent', jsonb_build_object('count', v_TotalAbsent, 'percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalAbsent::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END),
        'late', jsonb_build_object('count', v_TotalLate, 'percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalLate::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END),
        'leave', jsonb_build_object('count', v_TotalLeave, 'percentage', CASE WHEN v_TotalMarked > 0 THEN ROUND((v_TotalLeave::NUMERIC / v_TotalMarked) * 100, 1) ELSE 0 END),
        'total', v_TotalMarked
    );

    -- 2. Graph Data (Distribution by Status)
    v_GraphData := jsonb_build_array(
        jsonb_build_object('label', 'Present', 'value', v_TotalPresent),
        jsonb_build_object('label', 'Absent', 'value', v_TotalAbsent),
        jsonb_build_object('label', 'Late', 'value', v_TotalLate),
        jsonb_build_object('label', 'Leave', 'value', v_TotalLeave)
    );

    -- 3. Paginated Staff Records
    SELECT jsonb_agg(t)
    INTO v_Records
    FROM (
        SELECT 
            sa."AttendanceID" as id,
            sa."AttendanceDate" as date,
            sa."Status" as status,
            sa."Remarks" as remarks,
            sa."AttendanceState" as state,
            um."UserName" as employee_name,
            um."UserCode" as employee_code,
            pm."ProfileName" as role
        FROM "StaffAttendance" sa
        INNER JOIN "UserMaster" um ON sa."EmployeeID" = um."UserID"
        INNER JOIN "ProfileMaster" pm ON um."ProfileID" = pm."ProfileID"
        WHERE (sa."SchoolID" = p_SchoolID OR p_SchoolID IS NULL)
          AND (p_StartDate IS NULL OR sa."AttendanceDate" >= p_StartDate)
          AND (p_EndDate IS NULL OR sa."AttendanceDate" <= p_EndDate)
          AND (p_EmployeeID IS NULL OR sa."EmployeeID" = p_EmployeeID)
          AND (p_Status IS NULL OR sa."Status" ILIKE p_Status)
          AND COALESCE(sa."IsDeleted", FALSE) = FALSE
        ORDER BY sa."AttendanceDate" DESC, um."UserName" ASC
        LIMIT p_PageSize OFFSET v_Offset
    ) t;

    -- 4. Combine Everything into Final Result
    v_Result := jsonb_build_object(
        'stats', v_Stats,
        'graph_data', v_GraphData,
        'records', COALESCE(v_Records, '[]'::jsonb),
        'pagination', jsonb_build_object(
            'total_items', v_TotalMarked,
            'page', p_Page,
            'page_size', p_PageSize,
            'total_pages', CEIL(v_TotalMarked::NUMERIC / p_PageSize)
        )
    );

    RETURN v_Result;
END;
$$ LANGUAGE plpgsql;
