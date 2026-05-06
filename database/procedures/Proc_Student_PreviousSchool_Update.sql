CREATE OR REPLACE FUNCTION proc_student_previousschool_update(
    p_student_code VARCHAR,
    p_last_school VARCHAR,
    p_last_class VARCHAR,
    p_tc_number VARCHAR,
    p_medium_of_instruction VARCHAR,
    p_updated_by INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
DECLARE
    v_student_id INT;
BEGIN
    SELECT "StudentID" INTO v_student_id
    FROM "Student"
    WHERE "StudentCode" = p_student_code;

    IF v_student_id IS NULL THEN
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Student not found'::VARCHAR;
        RETURN;
    END IF;

    UPDATE "Student"
    SET "LastSchool" = p_last_school,
        "LastClass" = p_last_class,
        "TCNumber" = p_tc_number,
        "MediumOfInstruction" = p_medium_of_instruction,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_updated_by
    WHERE "StudentID" = v_student_id;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Previous school details updated successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
