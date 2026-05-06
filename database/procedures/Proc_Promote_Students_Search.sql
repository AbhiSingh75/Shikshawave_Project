-- Search students for promotion page (PostgreSQL)
CREATE OR REPLACE FUNCTION "func_promote_students_search"(
    p_SchoolID INT,
    p_ClassID INT DEFAULT NULL,
    p_SectionID INT DEFAULT NULL,
    p_SearchParam VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    "StudentID" INT,
    "StudentCode" VARCHAR,
    "StudentName" VARCHAR,
    "ClassID" INT,
    "ClassName" VARCHAR,
    "SectionID" INT,
    "SectionName" VARCHAR,
    "RollNumber" VARCHAR,
    "AcademicYearID" INT,
    "AcademicYear" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t."StudentID",
        s."StudentCode",
        s."FullName"::VARCHAR AS "StudentName",
        t."ClassID",
        c."ClassName",
        t."SectionID",
        sm."SectionName",
        t."RollNumber",
        t."AcademicYearID",
        a."AcademicYear"
    FROM "StudentAcademicTrack" AS t
    INNER JOIN "Student" AS s ON s."StudentID" = t."StudentID" AND t."SchoolID" = s."SchoolID"
    LEFT JOIN "ClassMaster" AS c ON c."ClassID" = t."ClassID"
    LEFT JOIN "SectionMaster" AS sm ON sm."SectionID" = t."SectionID"
    LEFT JOIN "AcademicYear" AS a ON a."AcademicYearID" = t."AcademicYearID"
    WHERE t."IsCurrent" = TRUE
        AND t."SchoolID" = p_SchoolID
        AND (p_ClassID IS NULL OR t."ClassID" = p_ClassID)
        AND (p_SectionID IS NULL OR t."SectionID" = p_SectionID)
        AND (p_SearchParam IS NULL OR 
             s."StudentCode" ILIKE '%' || p_SearchParam || '%' OR 
             s."FullName" ILIKE '%' || p_SearchParam || '%')
    ORDER BY c."ClassName", sm."SectionName", t."RollNumber";
END;
$$ LANGUAGE plpgsql;
