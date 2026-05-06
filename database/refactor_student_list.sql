
-- Refactor Student List Functions for PostgreSQL

CREATE OR REPLACE FUNCTION proc_student_cards_full_get(
    p_school_id INT,
    p_class_id INT DEFAULT NULL,
    p_section_id INT DEFAULT NULL,
    p_search VARCHAR DEFAULT NULL,
    p_page_number INT DEFAULT 1,
    p_page_size INT DEFAULT 10
)
RETURNS TABLE (
    "StudentID" INT,
    "StudentCode" VARCHAR,
    "FullName" VARCHAR,
    "Gender" VARCHAR,
    "DateOfBirth" DATE,
    "Age" INT,
    "BloodGroup" VARCHAR,
    "Category" VARCHAR,
    "Religion" VARCHAR,
    "Nationality" VARCHAR,
    "MotherTongue" VARCHAR,
    "StudentAadhaar" VARCHAR,
    "PresentAddress" VARCHAR,
    "ParentMobile" VARCHAR,
    "AlternateNumber" VARCHAR,
    "Email" VARCHAR,
    "FatherName" VARCHAR,
    "FatherMobile" VARCHAR,
    "MotherName" VARCHAR,
    "MotherMobile" VARCHAR,
    "GuardianName" VARCHAR,
    "GuardianMobile" VARCHAR,
    "AdmissionClass" VARCHAR,
    "Section" VARCHAR,
    "Stream" VARCHAR,
    "AdmissionDate" DATE,
    "Photo" BYTEA,
    "ClassName" VARCHAR,
    "SectionName" VARCHAR,
    "SchoolName" VARCHAR,
    "SchoolLogo" BYTEA,
    "IsDeleted" BOOLEAN,
    "TotalCount" BIGINT
) AS $$
DECLARE
    v_offset INT;
BEGIN
    v_offset := (p_page_number - 1) * p_page_size;

    RETURN QUERY
    SELECT 
        s."StudentID",
        s."StudentCode",
        s."FullName",
        s."Gender",
        s."DateOfBirth",
        s."Age",
        s."BloodGroup",
        s."Category",
        s."Religion",
        s."Nationality",
        s."MotherTongue",
        s."StudentAadhaar",
        s."PresentAddress",
        s."ParentMobile",
        s."AlternateNumber",
        s."Email",
        s."FatherName",
        s."FatherMobile",
        s."MotherName",
        s."MotherMobile",
        s."GuardianName",
        s."GuardianMobile",
        s."AdmissionClass",
        s."Section",
        s."Stream",
        s."AdmissionDate",
        u."UserPhoto" AS "Photo",
        cm."ClassName",
        sm."SectionName",
        sch."SchoolName",
        sch."SchoolLogo",
        s."IsDeleted",
        COUNT(*) OVER() AS "TotalCount"
    FROM "Student" s
    LEFT JOIN "UserMaster" u ON s."UserID" = u."UserID"
    LEFT JOIN "ClassMaster" cm ON CAST(NULLIF(REGEXP_REPLACE(s."AdmissionClass"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = cm."ClassID"
    LEFT JOIN "SectionMaster" sm ON CAST(NULLIF(REGEXP_REPLACE(s."Section"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = sm."SectionID"
    LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
    WHERE (p_school_id IS NULL OR s."SchoolID" = p_school_id)
        AND COALESCE(s."IsDeleted", false) = false
        AND (p_class_id IS NULL OR CAST(NULLIF(REGEXP_REPLACE(s."AdmissionClass"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = p_class_id)
        AND (p_section_id IS NULL OR CAST(NULLIF(REGEXP_REPLACE(s."Section"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = p_section_id)
        AND (p_search IS NULL OR s."FullName" ILIKE '%' || p_search || '%' OR s."StudentCode" ILIKE '%' || p_search || '%')
    ORDER BY s."StudentCode"
    LIMIT p_page_size
    OFFSET v_offset;
END;
$$ LANGUAGE plpgsql;
