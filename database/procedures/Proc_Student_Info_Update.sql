CREATE OR REPLACE FUNCTION proc_student_info_update(
    p_student_code VARCHAR,
    p_full_name VARCHAR,
    p_gender VARCHAR,
    p_date_of_birth DATE,
    p_age INT,
    p_blood_group VARCHAR,
    p_category VARCHAR,
    p_religion VARCHAR,
    p_nationality VARCHAR,
    p_mother_tongue VARCHAR,
    p_student_aadhaar VARCHAR,
    p_updated_by INT
)
RETURNS TABLE (
    "Status" VARCHAR,
    "Message" VARCHAR
) AS $$
DECLARE
    v_school_id INT;
    v_student_id INT;
BEGIN
    SELECT "StudentID", "SchoolID" INTO v_student_id, v_school_id
    FROM "Student"
    WHERE "StudentCode" = p_student_code;

    IF v_student_id IS NULL THEN
        RETURN QUERY SELECT 'ERROR'::VARCHAR, 'Student not found'::VARCHAR;
        RETURN;
    END IF;

    UPDATE "Student"
    SET "FullName" = p_full_name,
        "Gender" = p_gender,
        "DateOfBirth" = p_date_of_birth,
        "Age" = p_age,
        "BloodGroup" = p_blood_group,
        "Category" = p_category,
        "Religion" = p_religion,
        "Nationality" = p_nationality,
        "MotherTongue" = p_mother_tongue,
        "StudentAadhaar" = p_student_aadhaar,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_updated_by
    WHERE "StudentID" = v_student_id;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Student information updated successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
