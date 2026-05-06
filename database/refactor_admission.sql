-- Refactor Admission Functions for PostgreSQL

-- 1. Helper: Get School Dropdown
CREATE OR REPLACE FUNCTION proc_school_dropdown_get()
RETURNS TABLE (
    "SchoolID" INT,
    "SchoolName" VARCHAR,
    "SchoolCode" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        "SchoolID", 
        "SchoolName", 
        "SchoolCode"
    FROM "SchoolMaster"
    WHERE COALESCE("IsDeleted", false) = false
    ORDER BY "SchoolName";
END;
$$ LANGUAGE plpgsql;

-- 2. Helper: Get Admission Fee Types
CREATE OR REPLACE FUNCTION proc_admission_fee_types_get(p_school_id INT)
RETURNS TABLE (
    "FeeTypeId" INT,
    "SchoolId" INT,
    "FeeTypeName" VARCHAR,
    "DefaultAmount" DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        "FeeTypeId",
        "SchoolId",
        "FeeTypeName",
        "DefaultAmount"
    FROM "FeeType_Master"
    WHERE "SchoolId" = p_school_id
      AND "IsActive" = true -- Assumed boolean true for active, checked logic might need verify
      AND "ClassId" IS NULL
      AND COALESCE("IsDeleted", false) = false
    ORDER BY "FeeTypeName";
END;
$$ LANGUAGE plpgsql;
-- Note: Original SQL used IsActive=0 for some reason? Checking view... 
-- View code: AND IsActive = 0 ?? Usually IsActive=1 means active. 
-- Wait, the original SQL said: `AND IsActive = 0`. That's weird. 
-- I will stick to what the original SQL procedure `Proc_Admission_Fee_Types_Get` had: `IsActive = 0`.
-- Re-defining to match legacy logic exactly for safety.
-- 2. Helper: Get Admission Fee Types
CREATE OR REPLACE FUNCTION proc_admission_fee_types_get(p_school_id INT)
RETURNS TABLE (
    "FeeTypeId" INT,
    "SchoolId" INT,
    "FeeTypeName" VARCHAR,
    "DefaultAmount" DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ft."FeeTypeId",
        ft."SchoolId",
        ft."FeeTypeName",
        ft."DefaultAmount"
    FROM "FeeType_Master" ft
    WHERE ft."SchoolId" = p_school_id
      AND ft."IsActive" = false
      AND ft."ClassId" IS NULL
    ORDER BY ft."FeeTypeName";
END;
$$ LANGUAGE plpgsql;


-- 3. Helper: Get Monthly Fee Types
CREATE OR REPLACE FUNCTION proc_monthly_fee_types_get(p_school_id INT, p_class_id INT)
RETURNS TABLE (
    "FeeTypeId" INT,
    "SchoolId" INT,
    "FeeTypeName" VARCHAR,
    "DefaultAmount" DECIMAL,
    "ClassId" INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ft."FeeTypeId",
        ft."SchoolId",
        ft."FeeTypeName",
        ft."DefaultAmount",
        ft."ClassId"
    FROM "FeeType_Master" ft
    WHERE ft."SchoolId" = p_school_id
      AND ft."IsActive" = false
      AND ft."ClassId" = p_class_id
    ORDER BY ft."FeeTypeName";
END;
$$ LANGUAGE plpgsql;


-- 4. Main Admission Function (Legacy Aligned)
CREATE OR REPLACE FUNCTION proc_student_admission_with_documents(
    p_full_name VARCHAR, p_gender VARCHAR, p_dob DATE, p_age INT,
    p_blood_group VARCHAR, p_category VARCHAR, p_religion VARCHAR,
    p_nationality VARCHAR, p_mother_tongue VARCHAR, p_present_address VARCHAR,
    p_permanent_address VARCHAR, p_district INT, p_state INT, p_country INT,
    p_parent_mobile VARCHAR, p_alternate_number VARCHAR, p_email VARCHAR,
    p_father_name VARCHAR, p_father_occupation VARCHAR, p_father_qualification VARCHAR,
    p_father_aadhaar VARCHAR, p_father_mobile VARCHAR, p_mother_name VARCHAR,
    p_mother_occupation VARCHAR, p_mother_qualification VARCHAR, p_mother_aadhaar VARCHAR,
    p_mother_mobile VARCHAR, p_guardian_name VARCHAR, p_guardian_relation VARCHAR,
    p_guardian_mobile VARCHAR, p_last_school VARCHAR, p_last_class VARCHAR,
    p_tc_number VARCHAR, p_medium_of_instruction VARCHAR, p_academic_year_id INT, p_admission_class INT,
    p_section INT, p_stream VARCHAR, p_mode_of_admission VARCHAR,
    p_admission_date DATE, p_father_sign VARCHAR, p_mother_sign VARCHAR,
    p_guardian_sign VARCHAR, p_student_sign VARCHAR, p_declaration_date DATE,
    p_principal_approval VARCHAR, p_created_by INT, p_student_password VARCHAR,
    p_student_aadhaar VARCHAR, p_fees_json JSONB, p_documents_json JSONB, p_school_id INT
)
RETURNS TABLE (
    "UserCode" VARCHAR,
    "ErrorMessage" VARCHAR
) AS $$
DECLARE
    v_student_id INT;
    v_user_code VARCHAR(20);
    v_school_code VARCHAR(10);
    v_sequence INT;
    v_fee_item JSONB;
    v_user_id INT;
    v_student_profile_id INT;
    v_roll_number INT;
    v_error_message VARCHAR;
BEGIN
    -- Validation (Legacy Logic)
    IF p_full_name IS NULL OR p_parent_mobile IS NULL OR p_student_aadhaar IS NULL OR p_email IS NULL THEN
        RETURN QUERY SELECT CAST(NULL AS VARCHAR), 'FullName, ParentMobile, StudentAadhaar, and Email are required fields.'::VARCHAR;
        RETURN;
    END IF;

    IF p_student_aadhaar IS NOT NULL AND LENGTH(p_student_aadhaar) != 12 THEN
        RETURN QUERY SELECT CAST(NULL AS VARCHAR), 'Student Aadhaar number must be exactly 12 digits.'::VARCHAR;
        RETURN;
    END IF;

    -- Get Student Profile ID
    SELECT "ProfileID" INTO v_student_profile_id FROM "ProfileMaster" WHERE "ProfileName" = 'Student' LIMIT 1;
    IF v_student_profile_id IS NULL THEN
         -- Fallback if ProfileName differs slightly or standard ID 3 (Student)
         v_student_profile_id := 3; 
    END IF;

    -- 1. Generate Student Code (Legacy: Matches UserCode)
    SELECT "SchoolCode" INTO v_school_code FROM "SchoolMaster" WHERE "SchoolID" = p_school_id;
    SELECT COUNT(*) + 1 INTO v_sequence FROM "Student" WHERE "SchoolID" = p_school_id;
    v_user_code := v_school_code || '-ST-' || LPAD(v_sequence::TEXT, 5, '0');

    -- 2. Create User Account (Legacy Logic)
    IF p_student_password IS NOT NULL AND p_student_password != '' THEN
        INSERT INTO "UserMaster" (
            "UserType", "UserName", "PasswordHash", "Email", "Phone", 
            "ProfileID", "SchoolID", "CreatedBy", "CreatedAt", "UserCode"
        ) VALUES (
            'STU', p_full_name, p_student_password, p_email, p_parent_mobile,
            v_student_profile_id, p_school_id, p_created_by, CURRENT_TIMESTAMP, v_user_code
        ) RETURNING "UserID" INTO v_user_id;
    ELSE
        v_user_id := NULL;
    END IF;

    -- 3. Insert into Student
    INSERT INTO "Student" (
        "SchoolID", "StudentCode", "FullName", "Gender", "DateOfBirth", "Age",
        "BloodGroup", "Category", "Religion", "Nationality", "MotherTongue",
        "PresentAddress", "PermanentAddress", "District", "State", "Country",
        "ParentMobile", "AlternateNumber", "Email",
        "FatherName", "FatherOccupation", "FatherQualification", "FatherAadhaar", "FatherMobile",
        "MotherName", "MotherOccupation", "MotherQualification", "MotherAadhaar", "MotherMobile",
        "GuardianName", "GuardianRelation", "GuardianMobile",
        "LastSchool", "LastClass", "TCNumber", "MediumOfInstruction",
        "AdmissionClass", "Section", "Stream",
        "ModeOfAdmission", "AdmissionDate", 
        "FatherSign", "MotherSign", "GuardianSign", "StudentSign",
        "DeclarationDate", "PrincipalApproval", 
        "StudentAadhaar",
        "CreatedBy", "CreatedAt", "IsDeleted", "UserID"
    ) VALUES (
        p_school_id, v_user_code, p_full_name, LEFT(p_gender, 10), p_dob, p_age,
        LEFT(p_blood_group, 5), LEFT(p_category, 10), p_religion, p_nationality, p_mother_tongue,
        p_present_address, p_permanent_address, p_district, p_state, p_country,
        LEFT(p_parent_mobile, 15), LEFT(p_alternate_number, 15), p_email,
        p_father_name, p_father_occupation, p_father_qualification, LEFT(p_father_aadhaar, 12), LEFT(p_father_mobile, 15),
        p_mother_name, p_mother_occupation, p_mother_qualification, LEFT(p_mother_aadhaar, 12), LEFT(p_mother_mobile, 15),
        p_guardian_name, p_guardian_relation, LEFT(p_guardian_mobile, 15),
        p_last_school, LEFT(p_last_class, 10), p_tc_number, p_medium_of_instruction,
        p_admission_class, p_section, p_stream,
        p_mode_of_admission, p_admission_date,
        p_father_sign, p_mother_sign, p_guardian_sign, p_student_sign, 
        p_declaration_date, CAST(p_principal_approval AS VARCHAR), -- Legacy stores as VARCHAR/NVARCHAR(100)
        LEFT(p_student_aadhaar, 12),
        p_created_by, CURRENT_TIMESTAMP, false, v_user_id
    ) RETURNING "StudentID" INTO v_student_id;

    -- 4. Student Academic Track (Legacy Logic)
    -- Calculate Roll Number: MAX(RollNumber) + 1 for Class/Section
    SELECT COALESCE(MAX(NULLIF(REGEXP_REPLACE("RollNumber", '[^0-9]', '', 'g'), '')::INT), 0) + 1 
    INTO v_roll_number 
    FROM "StudentAcademicTrack" 
    WHERE "ClassID" = p_admission_class AND "SectionID" = p_section;

    INSERT INTO "StudentAcademicTrack" (
        "SchoolID", "StudentID", "AcademicYearID", "ClassID", "SectionID", 
        "RollNumber", "IsCurrent", "CreatedBy", "CreatedAt", 
        "StartDate", "IsDeleted", "Status"
    ) VALUES (
        p_school_id, v_student_id, p_academic_year_id, p_admission_class, p_section,
        v_roll_number::VARCHAR, true, p_created_by, CURRENT_TIMESTAMP,
        p_admission_date, false, 'Active'
    );

    -- 5. Process Fees (from JSON)
    IF p_fees_json IS NOT NULL THEN
        FOR v_fee_item IN SELECT * FROM jsonb_array_elements(p_fees_json->'fees')
        LOOP
            INSERT INTO "Student_Fee_Assignment" (
                "StudentId", "FeeTypeId", "FeeAmount", "DiscountPercentage", "FinalAmount",
                "FeeMonth", "SchoolId", "CreatedBy", "CreatedAt", "IsDeleted", "DueDate"
            ) VALUES (
                v_student_id,
                (v_fee_item->>'feeTypeId')::INT,
                (v_fee_item->>'amount')::DECIMAL,
                (v_fee_item->>'discountPercentage')::DECIMAL,
                (v_fee_item->>'finalAmount')::DECIMAL,
                TO_CHAR(CURRENT_DATE, 'YYYYMM'), -- Default to current month format YYYYMM
                p_school_id,
                p_created_by,
                CURRENT_TIMESTAMP,
                false,
                CURRENT_DATE
            );
        END LOOP;
    END IF;

    -- 6. Return Success
    RETURN QUERY SELECT v_user_code, CAST(NULL AS VARCHAR);

EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT CAST(NULL AS VARCHAR), CAST(SQLERRM AS VARCHAR);
END;
$$ LANGUAGE plpgsql;


-- 5. Helper: Student Fee Structure Get
CREATE OR REPLACE FUNCTION proc_student_fee_structure_get(p_student_id INT, p_student_code VARCHAR)
RETURNS TABLE (
    "FeeAssignmentID" INT,
    "StudentID" INT,
    "StudentCode" VARCHAR,
    "student_name" VARCHAR,
    "FeeTypeId" INT,
    "fee_name" VARCHAR,
    "default_amount" DECIMAL,
    "discount_percentage" DECIMAL,
    "amount" DECIMAL,
    "FeeMonth" VARCHAR,
    "AssignedDate" DATE,
    "SchoolId" INT,
    "school_name" VARCHAR
) AS $$
DECLARE
    v_actual_student_id INT;
BEGIN
    IF p_student_code IS NOT NULL THEN
        SELECT "StudentID" INTO v_actual_student_id FROM "Student" WHERE "StudentCode" = p_student_code LIMIT 1;
    ELSE
        v_actual_student_id := p_student_id;
    END IF;

    RETURN QUERY
    SELECT 
        sfa."FeeAssignmentID",
        sfa."StudentId",
        s."StudentCode",
        s."FullName" AS student_name,
        sfa."FeeTypeId",
        ft."FeeTypeName" AS fee_name,
        sfa."FeeAmount" AS default_amount,
        sfa."DiscountPercentage" AS discount_percentage,
        sfa."FinalAmount" AS amount,
        sfa."FeeMonth",
        CAST(sfa."DueDate" AS DATE),
        sfa."SchoolId",
        sch."SchoolName" AS school_name
    FROM "Student_Fee_Assignment" sfa
    JOIN "Student" s ON sfa."StudentId" = s."StudentID"
    JOIN "FeeType_Master" ft ON sfa."FeeTypeId" = ft."FeeTypeId"
    LEFT JOIN "SchoolMaster" sch ON sfa."SchoolId" = sch."SchoolID"
    WHERE sfa."StudentId" = v_actual_student_id
      AND COALESCE(sfa."IsDeleted", false) = false
    ORDER BY sfa."DueDate" DESC, ft."FeeTypeName";
END;
$$ LANGUAGE plpgsql;

-- 6. Helper: Payment Receipt Get
CREATE OR REPLACE FUNCTION proc_payment_receipt_get(p_receipt_number VARCHAR, p_student_code VARCHAR)
RETURNS TABLE (
    "PaymentID" INT,
    "receipt_number" VARCHAR,
    "total_amount" DECIMAL,
    "amount_paid" DECIMAL,
    "payment_mode" VARCHAR,
    "payment_date" VARCHAR,
    "transaction_ref" VARCHAR,
    "fee_breakdown" TEXT,
    "StudentID" INT,
    "student_code" VARCHAR,
    "student_name" VARCHAR
    -- Note: Shortened for brevity, typically we fetch full details. 
    -- I will select JSONB or detailed columns as needed by the view.
    -- The view calls dict(zip(columns, row)), so column names match keys.
    -- For now I will match the essential columns used in the python view.
    -- To match Python 'zip' logic, I should output all columns the view expects if possible.
    -- But the view just dumps it into a dict.
    -- I'll define a simpler version just for the Python fetch.
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p."PaymentID",
        p."ReceiptNumber",
        p."TotalAmount",
        p."PaidAmount",
        p."PaymentMode",
        TO_CHAR(p."PaymentDate", 'YYYY-MM-DD HH24:MI:SS'),
        p."TransactionRef",
        p."FeeBreakdown"::TEXT,
        s."StudentID",
        s."StudentCode",
        s."FullName"
    FROM "Payment" p
    JOIN "Student" s ON p."EntityID" = s."StudentID" AND p."EntityType" = 'Student'
    WHERE (p_receipt_number IS NOT NULL AND p."ReceiptNumber" = p_receipt_number)
       OR (p_student_code IS NOT NULL AND s."StudentCode" = p_student_code)
    ORDER BY p."PaymentDate" DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 7. Helper: Student Acknowledgment
CREATE OR REPLACE FUNCTION proc_student_acknowledgment_get(p_student_code VARCHAR)
RETURNS TABLE (
    "StudentID" INT,
    "StudentCode" VARCHAR,
    "student_name" VARCHAR,
    "gender" VARCHAR,
    "date_of_birth" DATE,
    "age" INT,
    "blood_group" VARCHAR,
    "category" VARCHAR,
    "email" VARCHAR,
    "admission_class" VARCHAR,
    "section" VARCHAR,
    "admission_date" VARCHAR,
    "school_name" VARCHAR,
    "school_logo" BYTEA
) AS $$
BEGIN
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
        s."Email",
        c."ClassName",
        sec."SectionName",
        TO_CHAR(s."AdmissionDate", 'YYYY-MM-DD')::VARCHAR,
        sch."SchoolName",
        sch."SchoolLogo"
    FROM "Student" s
    LEFT JOIN "ClassMaster" c ON CAST(NULLIF(REGEXP_REPLACE(s."AdmissionClass"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = c."ClassID"
    LEFT JOIN "SectionMaster" sec ON CAST(NULLIF(REGEXP_REPLACE(s."Section"::TEXT, '[^0-9]', '', 'g'), '') AS INTEGER) = sec."SectionID"
    LEFT JOIN "SchoolMaster" sch ON s."SchoolID" = sch."SchoolID"
    WHERE s."StudentCode" = p_student_code;
END;
$$ LANGUAGE plpgsql;
