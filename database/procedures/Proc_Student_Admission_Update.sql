CREATE OR REPLACE FUNCTION proc_student_admission_update(
    p_student_code VARCHAR,
    p_admission_class INT,
    p_section INT,
    p_stream VARCHAR,
    p_mode_of_admission VARCHAR,
    p_admission_date DATE,
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
    SET "AdmissionClass" = p_admission_class,
        "Section" = p_section,
        "Stream" = p_stream,
        "ModeOfAdmission" = p_mode_of_admission,
        "AdmissionDate" = p_admission_date,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_updated_by
    WHERE "StudentID" = v_student_id;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Admission details updated successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
