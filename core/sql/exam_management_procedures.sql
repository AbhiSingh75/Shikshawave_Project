-- ============================================================
-- Exam Management Procedures for PostgreSQL (REVISED SCHEMA)
-- ============================================================

-- Procedure: Proc_ExamMaster_View
-- Parameters:
--   p_school_id    : Required
--   p_page_num     : Current page (Default 1)
--   p_page_size    : Records per page (Default 10)
--   p_sort_col     : Column to sort by (Default 'StartDate')
--   p_sort_dir     : Sort direction ('ASC' or 'DESC', Default 'DESC')
--   p_search       : Global search string
--   p_year_id      : Filter by AcademicYearId
--   p_status       : Filter by IsPublish ('Yes' or 'No')
--   p_type         : Filter by ExamType
CREATE OR REPLACE FUNCTION Proc_ExamMaster_View(
    p_school_id        INTEGER,
    p_page_num         INTEGER DEFAULT 1,
    p_page_size        INTEGER DEFAULT 10,
    p_sort_col         VARCHAR DEFAULT 'StartDate',
    p_sort_dir         VARCHAR DEFAULT 'DESC',
    p_search           VARCHAR DEFAULT '',
    p_year_id          INTEGER DEFAULT NULL,
    p_status           VARCHAR DEFAULT '',
    p_type             VARCHAR DEFAULT ''
)
RETURNS TABLE(
    "ExamID"       INTEGER,
    "ExamCode"     VARCHAR,
    "ExamName"     VARCHAR,
    "ExamType"     VARCHAR,
    "StartDate"    DATE,
    "EndDate"      DATE,
    "AcademicYear" VARCHAR,
    "AcademicYearId" INTEGER,
    "IsPublish"    VARCHAR,
    "IsActive"     INTEGER,
    "TotalRecords" BIGINT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_offset INTEGER;
BEGIN
    v_offset := (p_page_num - 1) * p_page_size;

    RETURN QUERY
    WITH FilteredRows AS (
        SELECT 
            e."ExamID",
            ''::VARCHAR AS "ExamCode",
            e."ExamName",
            e."ExamType",
            e."StartDate",
            e."EndDate",
            ay."AcademicYear",
            e."AcademicYearId",
            e."IsPublish",
            CASE WHEN e."IsActive" THEN 1 ELSE 0 END AS "IsActive"
        FROM "ExamMaster" e
        LEFT JOIN "AcademicYear" ay ON e."AcademicYearId" = ay."AcademicYearID"
        WHERE e."SchoolID" = p_school_id AND e."IsActive" IS FALSE
          AND (COALESCE(p_search, '') = '' OR e."ExamName" ILIKE '%' || p_search || '%')
          AND (p_year_id IS NULL OR e."AcademicYearId" = p_year_id)
          AND (COALESCE(p_status, '') = '' OR e."IsPublish" = p_status)
          AND (COALESCE(p_type, '') = '' OR e."ExamType" = p_type)
    ),
    CountedRows AS (
        SELECT COUNT(*) AS total FROM FilteredRows
    )
    SELECT 
        f.*,
        c.total
    FROM FilteredRows f, CountedRows c
    ORDER BY 
        CASE WHEN p_sort_dir = 'ASC' THEN
            CASE 
                WHEN p_sort_col = 'ExamName' THEN f."ExamName"
                WHEN p_sort_col = 'ExamType' THEN f."ExamType"
                WHEN p_sort_col = 'AcademicYear' THEN f."AcademicYear"
                WHEN p_sort_col = 'IsPublish' THEN f."IsPublish"
                ELSE NULL
            END
        END ASC,
        CASE WHEN p_sort_dir = 'DESC' THEN
            CASE 
                WHEN p_sort_col = 'ExamName' THEN f."ExamName"
                WHEN p_sort_col = 'ExamType' THEN f."ExamType"
                WHEN p_sort_col = 'AcademicYear' THEN f."AcademicYear"
                WHEN p_sort_col = 'IsPublish' THEN f."IsPublish"
                ELSE NULL
            END
        END DESC,
        CASE WHEN p_sort_dir = 'ASC' THEN
            CASE 
                WHEN p_sort_col = 'StartDate' THEN f."StartDate"
                WHEN p_sort_col = 'EndDate' THEN f."EndDate"
                ELSE NULL
            END
        END ASC,
        CASE WHEN p_sort_dir = 'DESC' THEN
            CASE 
                WHEN p_sort_col = 'StartDate' THEN f."StartDate"
                WHEN p_sort_col = 'EndDate' THEN f."EndDate"
                ELSE NULL
            END
        END DESC
    LIMIT p_page_size
    OFFSET v_offset;
END;
$$;

-- Procedure: Proc_ExamMaster_Set
-- Handles: ADD, UPDATE, DELETE, RESTORE
CREATE OR REPLACE FUNCTION Proc_ExamMaster_Set(
    p_action          VARCHAR,
    p_exam_id         INTEGER DEFAULT NULL,
    p_school_id       INTEGER DEFAULT NULL,
    p_exam_name       VARCHAR DEFAULT NULL,
    p_exam_type       VARCHAR DEFAULT NULL,
    p_start_date      DATE DEFAULT NULL,
    p_end_date        DATE DEFAULT NULL,
    p_academic_year_id INTEGER DEFAULT NULL,
    p_is_publish      VARCHAR DEFAULT 'No',
    p_user_id         INTEGER DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_status  VARCHAR;
    v_message VARCHAR;
    v_new_id  INTEGER;
BEGIN
    IF p_action = 'INSERT' OR p_action = 'ADD' THEN
        INSERT INTO "ExamMaster" (
            "SchoolID", "ExamName", "ExamType", "StartDate", "EndDate", 
            "AcademicYearId", "IsPublish", "IsActive", "CreatedBy", "CreatedOn"
        )
        VALUES (
            p_school_id, p_exam_name, p_exam_type, p_start_date, p_end_date,
            p_academic_year_id, p_is_publish, FALSE, p_user_id, NOW()
        )
        RETURNING "ExamID" INTO v_new_id;
        
        v_status := 'SUCCESS';
        v_message := 'Exam created successfully';
        
    ELSIF p_action = 'UPDATE' THEN
        UPDATE "ExamMaster"
        SET "ExamName" = p_exam_name,
            "ExamType" = p_exam_type,
            "StartDate" = p_start_date,
            "EndDate" = p_end_date,
            "AcademicYearId" = p_academic_year_id,
            "IsPublish" = p_is_publish,
            "UpdatedBy" = p_user_id,
            "UpdatedOn" = NOW()
        WHERE "ExamID" = p_exam_id;
        
        v_status := 'SUCCESS';
        v_message := 'Exam updated successfully';
        v_new_id := p_exam_id;

    ELSIF p_action = 'DELETE' THEN
        UPDATE "ExamMaster"
        SET "IsActive" = TRUE,  -- TRUE means Deleted/Inactive
            "UpdatedBy" = p_user_id,
            "UpdatedOn" = NOW()
        WHERE "ExamID" = p_exam_id;
        
        v_status := 'SUCCESS';
        v_message := 'Exam deleted successfully';
        v_new_id := p_exam_id;

    ELSIF p_action = 'RESTORE' THEN
        UPDATE "ExamMaster"
        SET "IsActive" = FALSE,  -- FALSE means Active
            "UpdatedBy" = p_user_id,
            "UpdatedOn" = NOW()
        WHERE "ExamID" = p_exam_id;
        
        v_status := 'SUCCESS';
        v_message := 'Exam restored successfully';
        v_new_id := p_exam_id;
        
    ELSE
        v_status := 'ERROR';
        v_message := 'Invalid action: ' || p_action;
    END IF;

    RETURN json_build_object(
        'Status', v_status,
        'Message', v_message,
        'ExamID', v_new_id
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'Status', 'ERROR',
        'Message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;
