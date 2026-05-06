-- ============================================================
-- Exam TimeTable Procedures for PostgreSQL
-- ============================================================

-- Procedure: Proc_ExamTimeTable_set
-- Handles: INSERT, UPDATE, DELETE
CREATE OR REPLACE FUNCTION "Proc_ExamTimeTable_set"(
    p_action              VARCHAR,
    p_timetable_id        INTEGER DEFAULT NULL,
    p_exam_id             INTEGER DEFAULT NULL,
    p_school_id           INTEGER DEFAULT NULL,
    p_class_id            INTEGER DEFAULT NULL,
    p_subject_id          INTEGER DEFAULT NULL,
    p_exam_date           DATE DEFAULT NULL,
    p_start_time          TIME DEFAULT NULL,
    p_end_time            TIME DEFAULT NULL,
    p_exam_mode           VARCHAR DEFAULT 'Offline',
    p_exam_location       VARCHAR DEFAULT NULL,
    p_room_no             VARCHAR DEFAULT NULL,
    p_invigilator         VARCHAR DEFAULT NULL,
    p_max_theory          DECIMAL DEFAULT 0,
    p_min_theory          DECIMAL DEFAULT 0,
    p_max_practical       DECIMAL DEFAULT 0,
    p_min_practical       DECIMAL DEFAULT 0,
    p_max_viva            DECIMAL DEFAULT 0,
    p_min_viva            DECIMAL DEFAULT 0,
    p_eval_type           VARCHAR DEFAULT 'Marks',
    p_passing_criteria    VARCHAR DEFAULT NULL,
    p_remarks             VARCHAR DEFAULT NULL,
    p_user_id             INTEGER DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_status  VARCHAR;
    v_message VARCHAR;
BEGIN
    IF p_action = 'INSERT' THEN
        INSERT INTO "ExamTimeTable" (
            "ExamID", "SchoolID", "ClassID", "SubjectID", "ExamDate", "StartTime", "EndTime",
            "ExamMode", "ExamLocation", "RoomNo", "Invigilator",
            "MaxTheoryMarks", "MinTheoryMarks", "MaxPracticalMarks", "MinPracticalMarks",
            "MaxVivaMarks", "MinVivaMarks", "EvaluationType", "PassingCriteria", "Remarks",
            "IsActive", "CreatedBy", "CreatedOn"
        )
        VALUES (
            p_exam_id, p_school_id, p_class_id, p_subject_id, p_exam_date, p_start_time, p_end_time,
            p_exam_mode, p_exam_location, p_room_no, p_invigilator,
            p_max_theory, p_min_theory, p_max_practical, p_min_practical,
            p_max_viva, p_min_viva, p_eval_type, p_passing_criteria, p_remarks,
            0, p_user_id, NOW()
        );
        
        v_status := 'SUCCESS';
        v_message := 'Timetable entry saved successfully';
        
    ELSIF p_action = 'UPDATE' THEN
        UPDATE "ExamTimeTable"
        SET "ClassID" = p_class_id,
            "SubjectID" = p_subject_id,
            "ExamDate" = p_exam_date,
            "StartTime" = p_start_time,
            "EndTime" = p_end_time,
            "ExamMode" = p_exam_mode,
            "ExamLocation" = p_exam_location,
            "RoomNo" = p_room_no,
            "Invigilator" = p_invigilator,
            "MaxTheoryMarks" = p_max_theory,
            "MinTheoryMarks" = p_min_theory,
            "MaxPracticalMarks" = p_max_practical,
            "MinPracticalMarks" = p_min_practical,
            "MaxVivaMarks" = p_max_viva,
            "MinVivaMarks" = p_min_viva,
            "EvaluationType" = p_eval_type,
            "PassingCriteria" = p_passing_criteria,
            "Remarks" = p_remarks,
            "UpdatedBy" = p_user_id,
            "UpdatedOn" = NOW()
        WHERE "ExamTimeTableID" = p_timetable_id AND "SchoolID" = p_school_id;
        
        v_status := 'SUCCESS';
        v_message := 'Timetable entry updated successfully';

    ELSIF p_action = 'DELETE' THEN
        UPDATE "ExamTimeTable"
        SET "IsActive" = 1,  -- 1 means Deleted/Inactive in this module's logic
            "UpdatedBy" = p_user_id,
            "UpdatedOn" = NOW()
        WHERE "ExamTimeTableID" = p_timetable_id AND "SchoolID" = p_school_id;
        
        v_status := 'SUCCESS';
        v_message := 'Timetable entry deleted successfully';
        
    ELSE
        v_status := 'ERROR';
        v_message := 'Invalid action: ' || p_action;
    END IF;

    RETURN json_build_object(
        'Status', v_status,
        'Message', v_message
    );
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'Status', 'ERROR',
        'Message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;
