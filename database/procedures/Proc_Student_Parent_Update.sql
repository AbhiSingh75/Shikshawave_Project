CREATE OR REPLACE FUNCTION proc_student_parent_update(
    p_student_code VARCHAR,
    p_father_name VARCHAR,
    p_father_occupation VARCHAR,
    p_father_qualification VARCHAR,
    p_father_aadhaar VARCHAR,
    p_father_mobile VARCHAR,
    p_mother_name VARCHAR,
    p_mother_occupation VARCHAR,
    p_mother_qualification VARCHAR,
    p_mother_aadhaar VARCHAR,
    p_mother_mobile VARCHAR,
    p_guardian_name VARCHAR,
    p_guardian_relation VARCHAR,
    p_guardian_mobile VARCHAR,
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
    SET "FatherName" = p_father_name,
        "FatherOccupation" = p_father_occupation,
        "FatherQualification" = p_father_qualification,
        "FatherAadhaar" = p_father_aadhaar,
        "FatherMobile" = p_father_mobile,
        "MotherName" = p_mother_name,
        "MotherOccupation" = p_mother_occupation,
        "MotherQualification" = p_mother_qualification,
        "MotherAadhaar" = p_mother_aadhaar,
        "MotherMobile" = p_mother_mobile,
        "GuardianName" = p_guardian_name,
        "GuardianRelation" = p_guardian_relation,
        "GuardianMobile" = p_guardian_mobile,
        "UpdatedAt" = CURRENT_TIMESTAMP,
        "UpdatedBy" = p_updated_by
    WHERE "StudentID" = v_student_id;

    RETURN QUERY SELECT 'SUCCESS'::VARCHAR, 'Parent information updated successfully'::VARCHAR;

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'ERROR'::VARCHAR, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
