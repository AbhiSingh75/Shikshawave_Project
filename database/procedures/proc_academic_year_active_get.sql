-- Proc_AcademicYear_Active_Get
-- Fetches the active academic year for a school.

CREATE OR REPLACE FUNCTION "Proc_AcademicYear_Active_Get"(p_SchoolID INT)
RETURNS TABLE ("AcademicYear" VARCHAR) AS $$
BEGIN
    RETURN QUERY 
    SELECT ay."AcademicYear"
    FROM "AcademicYear" ay
    WHERE ay."SchoolID" = p_SchoolID AND ay."IsCurrent" = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;
