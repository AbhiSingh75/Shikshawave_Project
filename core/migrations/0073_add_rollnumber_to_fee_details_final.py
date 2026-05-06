from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0072_create_proc_payment_insert'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION "Proc_Student_fee_Details_get"(
                p_student_code CHARACTER VARYING,
                p_action CHARACTER VARYING DEFAULT NULL
            )
            RETURNS SETOF refcursor AS $$
            DECLARE
                ref1 refcursor := 'rs1';
                ref2 refcursor := 'rs2';
                ref3 refcursor := 'rs3';
                p_student_id INTEGER;
            BEGIN
                -- Identify StudentID for downstream lookups
                SELECT "StudentID" INTO p_student_id 
                FROM "Student" 
                WHERE "StudentCode" = p_student_code AND "IsDeleted" = FALSE 
                LIMIT 1;

                -- 1. Result Set: Student Information (Added RollNumber)
                OPEN ref1 FOR
                SELECT 
                    s."StudentID",
                    s."StudentCode",
                    s."RollNumber",
                    s."FullName",
                    s."FatherName",
                    s."GuardianName",
                    c."ClassName",
                    sec."SectionName",
                    s."AdmissionDate",
                    NULL::TEXT AS "StudentPhotoBase64"
                FROM "Student" s
                LEFT JOIN "StudentAcademicTrack" sat ON s."StudentID" = sat."StudentID" AND sat."IsCurrent" = TRUE
                LEFT JOIN "ClassMaster" c ON sat."ClassID" = c."ClassID"
                LEFT JOIN "SectionMaster" sec ON sat."SectionID" = sec."SectionID"
                WHERE s."StudentCode" = p_student_code AND s."IsDeleted" = FALSE;
                RETURN NEXT ref1;

                -- 2. Result Set: Fee Structure (Fixed column casing: StudentId, FeeId)
                OPEN ref2 FOR
                SELECT 
                    sfa."AssignmentID" as "FeeAssignmentID",
                    sfa."StudentId",
                    sfa."StudentID",
                    s."StudentCode",
                    s."FullName" AS "student_name",
                    fs."FeeID" as "FeeTypeId",
                    fs."FeeName" AS "fee_name",
                    fs."Amount" AS "default_amount",
                    0 AS "discount_percentage",
                    sfa."AssignedAmount" AS "amount",
                    NULL AS "FeeMonth"
                FROM "Student_Fee_Assignment" sfa
                INNER JOIN "Student" s ON (sfa."StudentId" = s."StudentID" OR sfa."StudentID" = s."StudentID")
                INNER JOIN "FeeStructure" fs ON (sfa."FeeId" = fs."FeeID" OR sfa."FeeID" = fs."FeeID")
                WHERE (sfa."StudentId" = p_student_id OR sfa."StudentID" = p_student_id) AND sfa."Status" != 'Deleted';
                RETURN NEXT ref2;

                -- 3. Result Set: Paid Months (Payment history)
                OPEN ref3 FOR
                SELECT 
                    fp."PaymentDate",
                    fp."ReceiptNumber",
                    fp."TotalAmount",
                    fp."PaymentMode"
                FROM "FeePayment" fp
                WHERE fp."StudentID" = p_student_id
                ORDER BY fp."PaymentDate" DESC;
                RETURN NEXT ref3;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql='-- Rollback'
        )
    ]
