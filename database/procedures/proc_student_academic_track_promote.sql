-- Promote Students to Next Class/Section (PostgreSQL)
CREATE OR REPLACE FUNCTION "func_student_academic_track_promote"(
    p_SchoolID INT,
    p_StudentIDs TEXT, -- Comma-separated student IDs
    p_PromotedToClassID INT,
    p_PromotedToSectionID INT,
    p_NewAcademicYear VARCHAR, -- Expecting Year string (e.g., '2024-2025')
    p_Remarks TEXT,
    p_UserID INT
)
RETURNS TABLE (
    "PromotedCount" INT,
    "FailedCount" INT,
    "ErrorMessage" VARCHAR
) AS $$
DECLARE
    v_NewAcademicYearID INT;
    v_CurrentAcademicYearID INT;
    v_StudentID INT;
    v_PromotedCount INT := 0;
    v_FailedCount INT := 0;
    v_StudentIDsArr INT[];
BEGIN
    -- Get New AcademicYearID
    SELECT "AcademicYearID" INTO v_NewAcademicYearID 
    FROM "AcademicYear" 
    WHERE "SchoolID" = p_SchoolID AND "AcademicYear" = p_NewAcademicYear;

    IF v_NewAcademicYearID IS NULL THEN
        RETURN QUERY SELECT 0, 0, 'Invalid Academic Year selected'::VARCHAR;
        RETURN;
    END IF;

    -- Get Current Active Academic Year (assuming only one active per school)
    SELECT "AcademicYearID" INTO v_CurrentAcademicYearID 
    FROM "AcademicYear" 
    WHERE "SchoolID" = p_SchoolID AND "IsActive" = TRUE;
    -- LIMIT 1; -- Removed LIMIT 1 as generic query, though logic implies singular active year

    -- Convert comma-separated string to array
    v_StudentIDsArr := string_to_array(p_StudentIDs, ',')::INT[];

    -- Process each student
    FOREACH v_StudentID IN ARRAY v_StudentIDsArr
    LOOP
        -- Check if student belongs to school and has current active track
        IF EXISTS (
            SELECT 1 FROM "StudentAcademicTrack" 
            WHERE "StudentID" = v_StudentID 
            AND "SchoolID" = p_SchoolID 
            AND "IsCurrent" = TRUE 
            AND "IsDeleted" = FALSE
        ) THEN
            -- Update old track
            UPDATE "StudentAcademicTrack"
            SET 
                "Status" = 'Promoted',
                "PromotedToClassID" = p_PromotedToClassID,
                "PromotedToSectionID" = p_PromotedToSectionID,
                "PromotionDate" = CURRENT_DATE,
                "IsCurrent" = FALSE,
                "EndDate" = CURRENT_DATE,
                "UpdatedBy" = p_UserID,
                "UpdatedAt" = CURRENT_TIMESTAMP
            WHERE "StudentID" = v_StudentID 
            AND "IsCurrent" = TRUE;

            -- Insert new track
            INSERT INTO "StudentAcademicTrack" (
                "SchoolID", "StudentID", "AcademicYearID", "ClassID", "SectionID",
                "Status", "IsCurrent", "StartDate", "CreatedBy", "CreatedAt", "IsDeleted"
            ) VALUES (
                p_SchoolID, v_StudentID, v_NewAcademicYearID, p_PromotedToClassID, p_PromotedToSectionID,
                'Active', TRUE, CURRENT_DATE, p_UserID, CURRENT_TIMESTAMP, FALSE
            );
            
            v_PromotedCount := v_PromotedCount + 1;
        ELSE
            v_FailedCount := v_FailedCount + 1;
        END IF;
    END LOOP;

    RETURN QUERY SELECT v_PromotedCount, v_FailedCount, NULL::VARCHAR;
END;
$$ LANGUAGE plpgsql;
