-- ============================================================
-- Exam Result Management Procedures for PostgreSQL
-- ============================================================

-- 1. Proc_GetStudentsForExamEntry
-- Returns students in a class for result entry
CREATE OR REPLACE FUNCTION Proc_GetStudentsForExamEntry(
    p_SchoolID INTEGER,
    p_ExamID   INTEGER,
    p_ClassID  INTEGER
)
RETURNS TABLE(
    "StudentID"   INTEGER,
    "StudentCode" VARCHAR,
    "StudentName" VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT s."StudentID", s."StudentCode", s."FullName" AS "StudentName"
    FROM "Student" s
    WHERE s."SchoolID" = p_SchoolID
      AND s."AdmissionClass"::integer = p_ClassID
      AND s."IsDeleted" IS NOT TRUE
    ORDER BY s."FullName";
END;
$$ LANGUAGE plpgsql;

-- 2. Proc_ExamResult_set
-- Handles saving/updating student marks
CREATE OR REPLACE FUNCTION Proc_ExamResult_set(
    p_Action              VARCHAR,
    p_ExamTimeTableID     INTEGER,
    p_SchoolID            INTEGER,
    p_StudentID           INTEGER,
    p_TheoryMarksObtained NUMERIC DEFAULT NULL,
    p_PracticalMarksObtained NUMERIC DEFAULT NULL,
    p_VivaMarksObtained    NUMERIC DEFAULT NULL,
    p_Grade               VARCHAR DEFAULT NULL,
    p_ResultStatus        VARCHAR DEFAULT NULL,
    p_Remarks             VARCHAR DEFAULT NULL,
    p_CreatedBy           INTEGER DEFAULT NULL,
    p_UpdatedBy           INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    IF p_Action = 'SAVE' THEN
        -- PostgreSQL ON CONFLICT requires a unique index/constraint.
        -- If none exists on (ExamTimeTableID, StudentID), we use manual check.
        IF EXISTS (SELECT 1 FROM "ExamResult" WHERE "ExamTimeTableID" = p_ExamTimeTableID AND "StudentID" = p_StudentID AND "SchoolID" = p_SchoolID) THEN
            UPDATE "ExamResult"
            SET "TheoryMarksObtained" = p_TheoryMarksObtained,
                "PracticalMarksObtained" = p_PracticalMarksObtained,
                "VivaMarksObtained" = p_VivaMarksObtained,
                "TotalMarksObtained" = COALESCE(p_TheoryMarksObtained, 0) + COALESCE(p_PracticalMarksObtained, 0) + COALESCE(p_VivaMarksObtained, 0),
                "Grade" = p_Grade,
                "ResultStatus" = p_ResultStatus,
                "Remarks" = p_Remarks,
                "UpdatedBy" = p_UpdatedBy,
                "UpdatedDate" = NOW()
            WHERE "ExamTimeTableID" = p_ExamTimeTableID AND "StudentID" = p_StudentID AND "SchoolID" = p_SchoolID;
        ELSE
            INSERT INTO "ExamResult" (
                "ExamTimeTableID", "SchoolID", "StudentID", 
                "TheoryMarksObtained", "PracticalMarksObtained", "VivaMarksObtained",
                "TotalMarksObtained", "Grade", "ResultStatus", "Remarks", 
                "CreatedBy", "CreatedDate"
            )
            VALUES (
                p_ExamTimeTableID, p_SchoolID, p_StudentID,
                p_TheoryMarksObtained, p_PracticalMarksObtained, p_VivaMarksObtained,
                COALESCE(p_TheoryMarksObtained, 0) + COALESCE(p_PracticalMarksObtained, 0) + COALESCE(p_VivaMarksObtained, 0),
                p_Grade, p_ResultStatus, p_Remarks,
                p_CreatedBy, NOW()
            );
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 3. Proc_GetExamSubjectMarksForEntry
-- Retrieves subject-wise marks config and existing results for a student
CREATE OR REPLACE FUNCTION Proc_GetExamSubjectMarksForEntry(
    p_SchoolID INTEGER,
    p_ExamID   INTEGER,
    p_ClassID  INTEGER,
    p_StudentID INTEGER
)
RETURNS TABLE(
    "ExamID"                INTEGER,
    "ExamTimeTableID"       INTEGER,
    "SubjectID"            INTEGER,
    "SubjectName"          VARCHAR,
    "MaxTheoryMarks"       INTEGER,
    "MinTheoryMarks"       INTEGER,
    "MaxPracticalMarks"    INTEGER,
    "MinPracticalMarks"    INTEGER,
    "MaxVivaMarks"         INTEGER,
    "MinVivaMarks"         INTEGER,
    "TotalMaxMarks"        INTEGER,
    "ExamResultID"         INTEGER,
    "TheoryMarksObtained"  NUMERIC,
    "PracticalMarksObtained" NUMERIC,
    "VivaMarksObtained"    NUMERIC,
    "TotalMarksObtained"   NUMERIC,
    "Grade"                VARCHAR,
    "ResultStatus"         VARCHAR,
    "Remarks"              VARCHAR,
    "IsPublished"          BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        et."ExamID",
        et."ExamTimeTableID",
        et."SubjectID",
        s."SubjectName",
        et."MaxTheoryMarks",
        et."MinTheoryMarks",
        et."MaxPracticalMarks",
        et."MinPracticalMarks",
        et."MaxVivaMarks",
        et."MinVivaMarks",
        et."TotalMaxMarks",
        er."ExamResultID",
        er."TheoryMarksObtained",
        er."PracticalMarksObtained",
        er."VivaMarksObtained",
        er."TotalMarksObtained",
        er."Grade",
        er."ResultStatus",
        er."Remarks",
        COALESCE(er."IsPublished", FALSE) AS "IsPublished"
    FROM "ExamTimeTable" et
    JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
    LEFT JOIN "ExamResult" er ON et."ExamTimeTableID" = er."ExamTimeTableID" AND er."StudentID" = p_StudentID
    WHERE et."ExamID" = p_ExamID
      AND et."ClassID" = p_ClassID
      AND et."SchoolID" = p_SchoolID
      AND et."IsActive" IS FALSE
    ORDER BY s."SubjectName";
END;
$$ LANGUAGE plpgsql;

-- 4. Proc_GetStudentExamResultList
-- Aggregates results for all students in a class
CREATE OR REPLACE FUNCTION Proc_GetStudentExamResultList(
    p_SchoolID INTEGER,
    p_ExamID   INTEGER,
    p_ClassID  INTEGER,
    p_Search   VARCHAR DEFAULT NULL
)
RETURNS TABLE(
    "StudentID"          INTEGER,
    "StudentCode"        VARCHAR,
    "StudentName"        VARCHAR,
    "TotalObtainedMarks" NUMERIC,
    "TotalMaxMarks"      NUMERIC,
    "Percentage"         NUMERIC,
    "ResultStatus"       VARCHAR,
    "PublishStatus"      BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH StudentMarks AS (
        SELECT 
            s."StudentID",
            s."StudentCode",
            s."FullName" AS "StudentName",
            SUM(COALESCE(er."TotalMarksObtained", 0)) AS "Obtained",
            SUM(COALESCE(et."TotalMaxMarks", 0)) AS "Max",
            BOOL_AND(COALESCE(er."IsPublished", FALSE)) AS "Published"
        FROM "Student" s
        CROSS JOIN "ExamTimeTable" et
        LEFT JOIN "ExamResult" er ON et."ExamTimeTableID" = er."ExamTimeTableID" AND s."StudentID" = er."StudentID"
        WHERE s."SchoolID" = p_SchoolID
          AND s."AdmissionClass"::integer = p_ClassID
          AND et."ExamID" = p_ExamID
          AND et."ClassID" = p_ClassID
          AND s."IsDeleted" IS NOT TRUE
          AND et."IsActive" IS FALSE
        GROUP BY s."StudentID", s."StudentCode", s."FullName"
    )
    SELECT 
        sm."StudentID",
        sm."StudentCode",
        sm."StudentName",
        sm."Obtained" AS "TotalObtainedMarks",
        sm."Max" AS "TotalMaxMarks",
        CASE WHEN sm."Max" > 0 THEN ROUND((sm."Obtained" / sm."Max") * 100, 2) ELSE 0 END AS "Percentage",
        CASE WHEN (CASE WHEN sm."Max" > 0 THEN (sm."Obtained" / sm."Max") * 100 ELSE 0 END) >= 33 THEN 'Pass'::VARCHAR ELSE 'Fail'::VARCHAR END AS "ResultStatus",
        sm."Published" AS "PublishStatus"
    FROM StudentMarks sm
    WHERE (p_Search IS NULL OR p_Search = '' OR sm."StudentName" ILIKE '%' || p_Search || '%' OR sm."StudentCode" ILIKE '%' || p_Search || '%')
    ORDER BY sm."StudentName";
END;
$$ LANGUAGE plpgsql;

-- 5 & 6. Proc_GetStudentExamResult (Split into Info and Subjects)

CREATE OR REPLACE FUNCTION Proc_GetStudentExamResult_Info(
    p_SchoolID INTEGER,
    p_ExamID   INTEGER,
    p_ClassID  INTEGER,
    p_StudentID INTEGER
)
RETURNS TABLE(
    "StudentCode"   VARCHAR,
    "StudentName"   VARCHAR,
    "ExamName"      VARCHAR,
    "ExamType"      VARCHAR,
    "ClassName"     VARCHAR,
    "SectionName"   VARCHAR,
    "StartDate"     DATE,
    "EndDate"       DATE,
    "PublishedDate" TIMESTAMP,
    "Ranks"         INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s."StudentCode",
        s."FullName" AS "StudentName",
        e."ExamName",
        e."ExamType",
        c."ClassName",
        ''::VARCHAR AS "SectionName",
        e."StartDate",
        e."EndDate",
        NOW()::TIMESTAMP AS "PublishedDate",
        0 AS "Ranks" -- Placeholder for now
    FROM "Student" s
    JOIN "ExamMaster" e ON e."ExamID" = p_ExamID
    JOIN "ClassMaster" c ON c."ClassID" = p_ClassID
    WHERE s."StudentID" = p_StudentID AND s."SchoolID" = p_SchoolID;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION Proc_GetStudentExamResult_Subjects(
    p_SchoolID INTEGER,
    p_ExamID   INTEGER,
    p_ClassID  INTEGER,
    p_StudentID INTEGER
)
RETURNS TABLE(
    "ExamTimeTableID"       INTEGER,
    "SubjectID"            INTEGER,
    "SubjectName"          VARCHAR,
    "MaxTheoryMarks"       INTEGER,
    "MinTheoryMarks"       INTEGER,
    "MaxPracticalMarks"    INTEGER,
    "MinPracticalMarks"    INTEGER,
    "MaxVivaMarks"         INTEGER,
    "MinVivaMarks"         INTEGER,
    "TotalMaxMarks"        INTEGER,
    "TheoryMarksObtained"  NUMERIC,
    "PracticalMarksObtained" NUMERIC,
    "VivaMarksObtained"    NUMERIC,
    "TotalMarksObtained"   NUMERIC,
    "Grade"                VARCHAR,
    "ResultStatus"         VARCHAR,
    "Remarks"              VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        et."ExamTimeTableID",
        et."SubjectID",
        s."SubjectName",
        et."MaxTheoryMarks",
        et."MinTheoryMarks",
        et."MaxPracticalMarks",
        et."MinPracticalMarks",
        et."MaxVivaMarks",
        et."MinVivaMarks",
        et."TotalMaxMarks",
        er."TheoryMarksObtained",
        er."PracticalMarksObtained",
        er."VivaMarksObtained",
        er."TotalMarksObtained",
        er."Grade",
        er."ResultStatus",
        er."Remarks"
    FROM "ExamTimeTable" et
    JOIN "SubjectMaster" s ON et."SubjectID" = s."SubjectID"
    LEFT JOIN "ExamResult" er ON et."ExamTimeTableID" = er."ExamTimeTableID" AND er."StudentID" = p_StudentID
    WHERE et."ExamID" = p_ExamID
      AND et."ClassID" = p_ClassID
      AND et."SchoolID" = p_SchoolID
      AND et."IsActive" IS FALSE
    ORDER BY s."SubjectName";
END;
$$ LANGUAGE plpgsql;
