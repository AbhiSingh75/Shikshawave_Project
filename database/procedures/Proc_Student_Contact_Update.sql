CREATE OR REPLACE FUNCTION proc_student_contact_update(
    p_student_code VARCHAR,
    p_parent_mobile VARCHAR,
    p_alternate_number VARCHAR,
    p_email VARCHAR,
    p_present_address VARCHAR,
    p_permanent_address VARCHAR,
    p_district INT,
    p_state INT,
    p_country INT,
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
    SET "ParentMobile" = p_parent_mobile,
        "AlternateNumber" = p_alternate_number,
        "Email" = p_email,
        "PresentAddress" = p_present_address,
        "PermanentAddress" = p_permanent_address,
        "District" = p_district,
        "State" = p_state,
        "Country" = p_country,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_updated_by
    WHERE "StudentID" = v_student_id;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Contact information updated successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
