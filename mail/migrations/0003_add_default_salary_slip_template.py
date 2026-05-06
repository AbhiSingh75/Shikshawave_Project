from django.db import migrations

def add_default_salary_slip_template(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Check if default SALARY_SLIP template already exists
        cursor.execute("""
            SELECT COUNT(*) FROM "EmailTemplate" 
            WHERE "Code" = 'SALARY_SLIP' AND "SchoolId" IS NULL AND "Language" = 'en'
        """)
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("""
                INSERT INTO "EmailTemplate" ("Code", "SchoolId", "Language", "SubjectTemplate", "BodyTextTemplate", "BodyHtmlTemplate", "IsActive", "CreatedAt", "UpdatedAt")
                VALUES (
                    'SALARY_SLIP',
                    NULL,
                    'en',
                    'Salary Slip for {{ month }} {{ year }}',
                    'Dear {{ employee_name }},\n\nPlease find attached your salary slip for {{ month }} {{ year }}.\n\nGross Salary: {{ gross_salary }}\nNet Salary: {{ net_salary }}\n\nBest regards,\n{{ school_name }}',
                    '<html><body><p>Dear <strong>{{ employee_name }}</strong>,</p><p>Please find attached your salary slip for <strong>{{ month }} {{ year }}</strong>.</p><table border="1" cellpadding="5"><tr><td>Gross Salary:</td><td>{{ gross_salary }}</td></tr><tr><td>Net Salary:</td><td>{{ net_salary }}</td></tr></table><p>Best regards,<br>{{ school_name }}</p></body></html>',
                    1,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """)

class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0002_emailtracking'),
    ]

    operations = [
        migrations.RunPython(add_default_salary_slip_template),
    ]
