from django.db import migrations


class Migration(migrations.Migration):
    """
    Fix Proc_FeeReport_get: Quote all column aliases so PostgreSQL preserves their
    TitleCase. Previously unquoted aliases like 'StudentName' were being lowercased
    to 'studentname' by PostgreSQL, causing the template to display '-' for student names.
    Also uses actual PaymentStatus from the Payment table instead of hardcoding 'Paid'.
    """

    dependencies = [
        ('core', '0079_fix_fee_history_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE FUNCTION "Proc_FeeReport_get"(
    mint_SchoolID INTEGER,
    mvar_FromDate DATE DEFAULT NULL,
    mvar_ToDate DATE DEFAULT NULL,
    mvar_ClassID INTEGER DEFAULT NULL,
    mvar_SectionID INTEGER DEFAULT NULL,
    mvar_FeeMonth VARCHAR DEFAULT NULL,
    mvar_StudentName VARCHAR DEFAULT NULL,
    mvar_StudentCode VARCHAR DEFAULT NULL,
    mvar_Email VARCHAR DEFAULT NULL,
    mvar_PaymentStatus VARCHAR DEFAULT NULL,
    mvar_ShowReportList INTEGER DEFAULT 0
)
RETURNS SETOF refcursor AS $$
DECLARE
    rs_overview refcursor := 'rs_overview';
    rs_details refcursor := 'rs_details';
BEGIN
    -- 1. OVERVIEW STATISTICS
    OPEN rs_overview FOR
    WITH FilteredStudents AS (
        SELECT s."StudentID"
        FROM "Student" s
        LEFT JOIN "StudentAcademicTrack" sat ON s."StudentID" = sat."StudentID" AND sat."IsCurrent" = TRUE
        WHERE s."SchoolID" = mint_SchoolID
          AND s."IsDeleted" = FALSE
          AND (mvar_ClassID IS NULL OR sat."ClassID" = mvar_ClassID)
          AND (mvar_SectionID IS NULL OR sat."SectionID" = mvar_SectionID)
          AND (mvar_StudentName IS NULL OR s."FullName" ILIKE '%' || mvar_StudentName || '%')
          AND (mvar_StudentCode IS NULL OR s."StudentCode" = mvar_StudentCode)
          AND (mvar_Email IS NULL OR s."Email" = mvar_Email)
    ),
    PaymentStats AS (
        SELECT 
            SUM(COALESCE(p."PaidAmount", 0)) as TotalCollected,
            COUNT(DISTINCT p."EntityID") as StudentsWhoPaid
        FROM "Payment" p
        WHERE p."EntityID" IN (SELECT "StudentID" FROM FilteredStudents)
          AND p."EntityType" = 'Student'
          AND p."SchoolID" = mint_SchoolID
          AND p."IsDeleted" = FALSE
          AND (mvar_FromDate IS NULL OR p."PaymentDate"::DATE >= mvar_FromDate)
          AND (mvar_ToDate IS NULL OR p."PaymentDate"::DATE <= mvar_ToDate)
          AND (mvar_FeeMonth IS NULL OR p."PaymentMonth" = mvar_FeeMonth)
    ),
    AssignmentStats AS (
        SELECT 
            SUM(COALESCE(fa."FeeAmount", 0)) as TotalGenerated,
            COUNT(DISTINCT fa."StudentId") as TotalStudentsBilled
        FROM "Student_Fee_Assignment" fa
        WHERE fa."StudentId" IN (SELECT "StudentID" FROM FilteredStudents)
          AND fa."SchoolId" = mint_SchoolID
          AND fa."IsDeleted" = FALSE
          AND (mvar_FeeMonth IS NULL OR fa."FeeMonth" = mvar_FeeMonth)
    )
    SELECT 
        COALESCE(ast.TotalGenerated, 0) as TotalGenerated,
        COALESCE(pst.TotalCollected, 0) as TotalCollected,
        (COALESCE(ast.TotalGenerated, 0) - COALESCE(pst.TotalCollected, 0)) as TotalPending,
        COALESCE(ast.TotalStudentsBilled, 0) as TotalStudentsBilled,
        CASE 
            WHEN COALESCE(ast.TotalGenerated, 0) > 0 THEN (COALESCE(pst.TotalCollected, 0) / COALESCE(ast.TotalGenerated, 0)) * 100
            ELSE 0 
        END as CollectionPercentage,
        COALESCE((SELECT SUM("PaidAmount") FROM "Payment" 
                  WHERE "SchoolID" = mint_SchoolID 
                    AND "EntityType" = 'Student' 
                    AND "IsDeleted" = FALSE 
                    AND "PaymentDate"::DATE BETWEEN COALESCE(mvar_FromDate, '2000-01-01') AND COALESCE(mvar_ToDate, '2099-12-31')), 0) as PaidAmountTotal,
        0 as PartialAmountTotal,
        0 as PendingAmountTotal
    FROM AssignmentStats ast, PaymentStats pst;

    RETURN NEXT rs_overview;

    -- 2. DETAILED REPORT LIST
    IF mvar_ShowReportList = 1 THEN
        OPEN rs_details FOR
        SELECT 
            s."StudentCode",
            s."FullName" as "StudentName",
            c."ClassName",
            sm."SectionName",
            p."ReceiptNumber",
            p."PaidAmount" as "PaidAmount",
            p."PaymentMode",
            p."PaymentDate",
            p."PaymentMonth",
            COALESCE(p."PaymentStatus", 'Paid') as "PaymentStatus"
        FROM "Payment" p
        INNER JOIN "Student" s ON p."EntityID" = s."StudentID" AND p."EntityType" = 'Student'
        LEFT JOIN "StudentAcademicTrack" sat ON s."StudentID" = sat."StudentID" AND sat."IsCurrent" = TRUE
        LEFT JOIN "ClassMaster" c ON sat."ClassID" = c."ClassID"
        LEFT JOIN "SectionMaster" sm ON sat."SectionID" = sm."SectionID"
        WHERE s."SchoolID" = mint_SchoolID
          AND p."IsDeleted" = FALSE
          AND (mvar_FromDate IS NULL OR p."PaymentDate"::DATE >= mvar_FromDate)
          AND (mvar_ToDate IS NULL OR p."PaymentDate"::DATE <= mvar_ToDate)
          AND (mvar_ClassID IS NULL OR sat."ClassID" = mvar_ClassID)
          AND (mvar_SectionID IS NULL OR sat."SectionID" = mvar_SectionID)
          AND (mvar_FeeMonth IS NULL OR p."PaymentMonth" = mvar_FeeMonth)
          AND (mvar_StudentName IS NULL OR s."FullName" ILIKE '%' || mvar_StudentName || '%')
          AND (mvar_StudentCode IS NULL OR s."StudentCode" = mvar_StudentCode)
          AND (mvar_PaymentStatus IS NULL OR p."PaymentStatus" = mvar_PaymentStatus)
        ORDER BY p."PaymentDate" DESC;

        RETURN NEXT rs_details;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql;
            """,
            reverse_sql='-- No reverse needed for function update'
        ),
    ]
