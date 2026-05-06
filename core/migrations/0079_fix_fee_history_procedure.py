from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0078_update_payment_insert_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
CREATE OR REPLACE FUNCTION public."Proc_Student_fee_Details_get"(
	p_student_code character varying,
	p_action character varying DEFAULT NULL::character varying)
    RETURNS SETOF refcursor 
    LANGUAGE 'plpgsql'
AS $BODY$
            DECLARE
                ref1 refcursor := 'rs1';
                ref2 refcursor := 'rs2';
                ref3 refcursor := 'rs3';
                p_student_id INTEGER;
            BEGIN
                -- Identify StudentID for downstream lookups (Fixed "IsDeleted" casing)
                SELECT "StudentID" INTO p_student_id 
                FROM "Student" 
                WHERE "IsDeleted" = FALSE AND "StudentCode" = p_student_code 
                LIMIT 1;

                -- 1. Result Set: Student Information
                OPEN ref1 FOR
                SELECT 
                    s."StudentID",
                    s."StudentCode",
                    sat."RollNumber",
                    s."FullName",
                    s."FatherName",
                    s."GuardianName",
                    c."ClassName",
                    sec."SectionName",
                    s."AdmissionDate",
                    SD."DocumentData"::TEXT AS "StudentPhotoBase64"
                FROM "Student" s
                LEFT JOIN "StudentAcademicTrack" sat ON s."StudentID" = sat."StudentID" AND sat."IsCurrent" = TRUE
                LEFT JOIN "ClassMaster" c ON sat."ClassID" = c."ClassID"
                LEFT JOIN "SectionMaster" sec ON sat."SectionID" = sec."SectionID"
				LEFT JOIN public."StudentDocuments" AS SD
				ON SD."StudentID"=s."StudentID" and SD."DocumentType"='Student Passport Photo'

                WHERE s."StudentCode" = p_student_code AND s."IsDeleted" = FALSE;
                RETURN NEXT ref1;

                -- 2. Result Set: Fee Structure
                OPEN ref2 FOR
                SELECT 
                    sfa."StudentFeeId" as "FeeAssignmentID",
                    sfa."StudentId",
                    s."StudentCode",
                    s."FullName" AS "student_name",
                    fs."FeeTypeId" as "FeeTypeId",
                    fs."FeeTypeName" AS "fee_name",
                    fs."DefaultAmount" AS "default_amount",
                    sfa."DiscountPercentage" AS "discount_percentage",
                    sfa."FeeAmount" AS "amount",
                    sfa."FeeMonth"
                FROM "Student_Fee_Assignment" sfa
                INNER JOIN "Student" s ON sfa."StudentId" = s."StudentID"
                LEFT JOIN public."FeeType_Master" fs ON sfa."FeeTypeId" = fs."FeeTypeId"
                WHERE sfa."StudentId" = p_student_id AND sfa."IsDeleted" = FALSE;
                RETURN NEXT ref2;

                -- 3. Result Set: Paid Months (Payment history) - FIXED: Using "Payment" table
                OPEN ref3 FOR
                SELECT 
                    fp."PaymentDate",
                    fp."ReceiptNumber",
                    fp."TotalAmount",
                    fp."PaidAmount",
                    fp."PaymentMode",
                    fp."PaymentMonth"
                FROM "Payment" fp
                WHERE fp."EntityID" = p_student_id AND fp."EntityType" = 'Student' AND fp."IsDeleted" = FALSE
                ORDER BY fp."PaymentDate" DESC;
                RETURN NEXT ref3;
            END;
$BODY$;
            """,
            reverse_sql="-- No reverse sql needed for simple fix"
        )
    ]
