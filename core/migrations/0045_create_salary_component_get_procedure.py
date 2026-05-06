from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_create_salary_component_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'Proc_SalaryComponentMaster_Get')
                DROP PROCEDURE Proc_SalaryComponentMaster_Get;
            """,
            reverse_sql="-- No reverse"
        ),
        migrations.RunSQL(
            sql="""
            CREATE PROCEDURE Proc_SalaryComponentMaster_Get
                @SchoolID INT = NULL
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @SchoolID IS NULL
                BEGIN
                    -- Super Admin: Get all components
                    SELECT 
                        sc.ComponentID,
                        sc.SchoolID,
                        s.SchoolName,
                        sc.ComponentName,
                        sc.ComponentType,
                        ISNULL(sc.IsDeleted, 0) as IsDeleted
                    FROM SalaryComponentMaster sc
                    LEFT JOIN SchoolMaster s ON sc.SchoolID = s.SchoolID
                    ORDER BY sc.ComponentID DESC;
                END
                ELSE
                BEGIN
                    -- School Admin: Get only their school's components
                    SELECT 
                        sc.ComponentID,
                        sc.SchoolID,
                        s.SchoolName,
                        sc.ComponentName,
                        sc.ComponentType,
                        ISNULL(sc.IsDeleted, 0) as IsDeleted
                    FROM SalaryComponentMaster sc
                    LEFT JOIN SchoolMaster s ON sc.SchoolID = s.SchoolID
                    WHERE sc.SchoolID = @SchoolID
                    ORDER BY sc.ComponentID DESC;
                END
            END;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS Proc_SalaryComponentMaster_Get;"
        ),
    ]
