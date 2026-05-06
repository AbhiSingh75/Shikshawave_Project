"""Direct fix for proc_student_fee_structure_get"""
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix proc_student_fee_structure_get'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Drop existing function
            self.stdout.write("Dropping existing function...")
            cursor.execute("DROP FUNCTION IF EXISTS public.proc_student_fee_structure_get(integer, character varying)")
            
            # Create new function with proper type casting
            self.stdout.write("Creating fixed function...")
            cursor.execute("""
CREATE OR REPLACE FUNCTION public.proc_student_fee_structure_get(p_student_id integer, p_student_code character varying)
    RETURNS TABLE(
        "FeeAssignmentID" integer, 
        "StudentID" integer, 
        "StudentCode" character varying, 
        student_name character varying, 
        "FeeTypeId" integer, 
        fee_name character varying, 
        default_amount numeric, 
        discount_percentage numeric, 
        amount numeric, 
        "FeeMonth" character varying,
        "AssignedDate" date, 
        "SchoolId" integer, 
        school_name character varying
    ) 
    LANGUAGE plpgsql
AS $$
DECLARE
    v_actual_student_id INT;
BEGIN
    IF p_student_code IS NOT NULL THEN
        SELECT s."StudentID" INTO v_actual_student_id 
        FROM public."Student" s 
        WHERE s."StudentCode" = p_student_code 
        LIMIT 1;
    ELSE
        v_actual_student_id := p_student_id;
    END IF;

    RETURN QUERY
    SELECT 
        sfa."StudentFeeId" AS "FeeAssignmentID",
        sfa."StudentId",
        s."StudentCode"::VARCHAR,
        s."FullName"::VARCHAR AS student_name,
        sfa."FeeTypeId",
        ft."FeeTypeName"::VARCHAR AS fee_name,
        sfa."FeeAmount" AS default_amount,
        sfa."DiscountPercentage" AS discount_percentage,
        sfa."FinalAmount" AS amount,
        TRIM(sfa."FeeMonth")::VARCHAR AS "FeeMonth",
        CAST(sfa."DueDate" AS DATE) AS "AssignedDate",
        sfa."SchoolId",
        sch."SchoolName"::VARCHAR AS school_name
    FROM public."Student_Fee_Assignment" sfa
    JOIN public."Student" s ON sfa."StudentId" = s."StudentID"
    JOIN public."FeeType_Master" ft ON sfa."FeeTypeId" = ft."FeeTypeId"
    LEFT JOIN public."SchoolMaster" sch ON sfa."SchoolId" = sch."SchoolID"
    WHERE sfa."StudentId" = v_actual_student_id
      AND COALESCE(sfa."IsDeleted", false) = false
    ORDER BY sfa."DueDate" DESC, ft."FeeTypeName";
END;
$$
            """)
            
            # Verify
            self.stdout.write("Verifying...")
            try:
                cursor.execute("SELECT * FROM proc_student_fee_structure_get(NULL, 'STU0000003') LIMIT 1")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS(f"Function works! Got data with FeeMonth: {result[9]}"))
                else:
                    self.stdout.write(self.style.WARNING("Function works but no data returned"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Verification failed: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Done!"))
