from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Setup EmployeeCoreSubjects table and standardize schema'

    def handle(self, *args, **options):
        self.stdout.write('Checking EmployeeCoreSubjects table...')

        with connection.cursor() as cursor:
            # Check if public.employeecoresubjects (lowercase) exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'employeecoresubjects'
                );
            """)
            lowercase_exists = cursor.fetchone()[0]

            # Check if "EmployeeCoreSubjects" (mixed case) exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'EmployeeCoreSubjects'
                );
            """)
            mixed_case_exists = cursor.fetchone()[0]

            if mixed_case_exists:
                self.stdout.write(self.style.SUCCESS('Table "EmployeeCoreSubjects" already exists.'))
            elif lowercase_exists:
                self.stdout.write(self.style.WARNING('Table "employeecoresubjects" (lowercase) found. Renaming to "EmployeeCoreSubjects"...'))
                cursor.execute('ALTER TABLE employeecoresubjects RENAME TO "EmployeeCoreSubjects";')
                # Also rename columns to keep consistent with Master tables if they were lowercase
                try:
                    cursor.execute('ALTER TABLE "EmployeeCoreSubjects" RENAME COLUMN employeeid TO "EmployeeID";')
                    cursor.execute('ALTER TABLE "EmployeeCoreSubjects" RENAME COLUMN subjectid TO "SubjectID";')
                    cursor.execute('ALTER TABLE "EmployeeCoreSubjects" RENAME COLUMN schoolid TO "SchoolID";')
                except Exception:
                    pass
                self.stdout.write(self.style.SUCCESS('Table renamed successfuly.'))
            else:
                self.stdout.write('Creating table "EmployeeCoreSubjects"...')
                cursor.execute("""
                    CREATE TABLE "EmployeeCoreSubjects" (
                        "MappingID" SERIAL PRIMARY KEY,
                        "EmployeeID" INT NOT NULL,
                        "SubjectID" INT NOT NULL,
                        "SchoolID" INT NOT NULL,
                        "CreatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_employee FOREIGN KEY ("EmployeeID") REFERENCES "EmployeeMaster"("EmployeeID"),
                        CONSTRAINT fk_subject FOREIGN KEY ("SubjectID") REFERENCES "SubjectMaster"("SubjectID"),
                        CONSTRAINT fk_school FOREIGN KEY ("SchoolID") REFERENCES "SchoolMaster"("SchoolID")
                    );
                """)
                self.stdout.write(self.style.SUCCESS('Table "EmployeeCoreSubjects" created successfully.'))

        self.stdout.write(self.style.SUCCESS('Database schema setup complete.'))
