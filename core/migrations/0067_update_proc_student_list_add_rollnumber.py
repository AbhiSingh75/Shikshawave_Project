from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0066_fix_proc_student_list_boolean'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DROP FUNCTION IF EXISTS "Proc_Student_list_for_fee_get"(INTEGER, INTEGER, INTEGER);
                CREATE OR REPLACE FUNCTION "Proc_Student_list_for_fee_get"(
                    p_school_id INTEGER,
                    p_class_id INTEGER,
                    p_section_id INTEGER DEFAULT NULL
                ) 
                RETURNS TABLE ("StudentCode" VARCHAR, "FullName" VARCHAR, "RollNumber" VARCHAR) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        s."StudentCode"::VARCHAR, 
                        s."FullName"::VARCHAR,
                        sa."RollNumber"::VARCHAR
                    FROM "Student" AS s
                    LEFT JOIN "StudentAcademicTrack" AS sa 
                        ON s."StudentID" = sa."StudentID" AND sa."IsCurrent" = TRUE
                    WHERE s."SchoolID" = p_school_id 
                      AND sa."ClassID" = p_class_id
                      AND (p_section_id IS NULL OR sa."SectionID" = p_section_id)
                      AND s."IsDeleted" = FALSE;
                END;
                $$ LANGUAGE plpgsql;
            """,
            reverse_sql="""
                -- Revert to two-column version
                CREATE OR REPLACE FUNCTION "Proc_Student_list_for_fee_get"(
                    p_school_id INTEGER,
                    p_class_id INTEGER,
                    p_section_id INTEGER DEFAULT NULL
                ) 
                RETURNS TABLE ("StudentCode" VARCHAR, "FullName" VARCHAR) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        s."StudentCode"::VARCHAR, 
                        s."FullName"::VARCHAR
                    FROM "Student" AS s
                    LEFT JOIN "StudentAcademicTrack" AS sa 
                        ON s."StudentID" = sa."StudentID" AND sa."IsCurrent" = TRUE
                    WHERE s."SchoolID" = p_school_id 
                      AND sa."ClassID" = p_class_id
                      AND (p_section_id IS NULL OR sa."SectionID" = p_section_id)
                      AND s."IsDeleted" = FALSE;
                END;
                $$ LANGUAGE plpgsql;
            """
        ),
    ]
