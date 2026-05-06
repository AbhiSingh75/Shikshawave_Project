# Generated migration for attendance menu update
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_dataimporterror_dataimportlog'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add new profile types if they don't exist
            IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 5)
            BEGIN
                SET IDENTITY_INSERT ProfileMaster ON;
                INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
                VALUES (5, 'Accountant', 'School Accountant', 0);
                SET IDENTITY_INSERT ProfileMaster OFF;
            END

            IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 6)
            BEGIN
                SET IDENTITY_INSERT ProfileMaster ON;
                INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
                VALUES (6, 'Driver', 'School Driver', 0);
                SET IDENTITY_INSERT ProfileMaster OFF;
            END

            IF NOT EXISTS (SELECT 1 FROM ProfileMaster WHERE ProfileID = 7)
            BEGIN
                SET IDENTITY_INSERT ProfileMaster ON;
                INSERT INTO ProfileMaster (ProfileID, ProfileName, Description, IsDeleted)
                VALUES (7, 'Librarian', 'School Librarian', 0);
                SET IDENTITY_INSERT ProfileMaster OFF;
            END

            -- Get or create Attendance parent menu
            DECLARE @AttendanceMenuID INT;

            IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0)
            BEGIN
                INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
                VALUES ('Attendance', NULL, 'fas fa-calendar-check', NULL, 30, 1, GETDATE(), 0);
            END

            SELECT @AttendanceMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0;

            -- Update existing student attendance submenus
            DECLARE @MarkStudentAttendanceID INT, @ViewStudentAttendanceID INT;

            IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                UPDATE MenuMaster 
                SET MenuName = 'Mark Student Attendance'
                WHERE MenuName = 'Mark Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;
            END
            ELSE IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
                VALUES ('Mark Student Attendance', '/attendance/mark/', 'fas fa-user-check', @AttendanceMenuID, 1, 1, GETDATE(), 0);
            END

            SELECT @MarkStudentAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'Mark Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            IF EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                UPDATE MenuMaster 
                SET MenuName = 'View Student Attendance'
                WHERE MenuName = 'View Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;
            END
            ELSE IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
                VALUES ('View Student Attendance', '/attendance/view/', 'fas fa-eye', @AttendanceMenuID, 2, 1, GETDATE(), 0);
            END

            SELECT @ViewStudentAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'View Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            -- Add new employee/staff attendance submenus
            DECLARE @MarkEmployeeAttendanceID INT, @ViewEmployeeAttendanceID INT;

            IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'Mark Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
                VALUES ('Mark Employee/Staff Attendance', '/attendance/mark-employee/', 'fas fa-user-tie', @AttendanceMenuID, 3, 1, GETDATE(), 0);
            END

            SELECT @MarkEmployeeAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'Mark Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            IF NOT EXISTS (SELECT 1 FROM MenuMaster WHERE MenuName = 'View Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0)
            BEGIN
                INSERT INTO MenuMaster (MenuName, MenuURL, Icon, ParentMenuID, DisplayOrder, IsActive, CreatedAt, IsDeleted)
                VALUES ('View Employee/Staff Attendance', '/attendance/view-employee/', 'fas fa-users', @AttendanceMenuID, 4, 1, GETDATE(), 0);
            END

            SELECT @ViewEmployeeAttendanceID = MenuID FROM MenuMaster WHERE MenuName = 'View Employee/Staff Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            -- Map menus to profiles
            INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
            SELECT p.ProfileID, @AttendanceMenuID, 1, 0, 0, 0, 0, GETDATE()
            FROM ProfileMaster p
            WHERE p.IsDeleted = 0 
            AND NOT EXISTS (
                SELECT 1 FROM ProfileMenuMapping 
                WHERE ProfileID = p.ProfileID AND MenuID = @AttendanceMenuID
            );

            INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
            SELECT p.ProfileID, @MarkStudentAttendanceID, 1, 1, 1, 0, 0, GETDATE()
            FROM ProfileMaster p
            WHERE p.ProfileID IN (2, 3)
            AND p.IsDeleted = 0 
            AND NOT EXISTS (
                SELECT 1 FROM ProfileMenuMapping 
                WHERE ProfileID = p.ProfileID AND MenuID = @MarkStudentAttendanceID
            );

            INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
            SELECT p.ProfileID, @ViewStudentAttendanceID, 1, 0, 0, 0, 0, GETDATE()
            FROM ProfileMaster p
            WHERE p.ProfileID IN (2, 3)
            AND p.IsDeleted = 0 
            AND NOT EXISTS (
                SELECT 1 FROM ProfileMenuMapping 
                WHERE ProfileID = p.ProfileID AND MenuID = @ViewStudentAttendanceID
            );

            INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
            SELECT p.ProfileID, @MarkEmployeeAttendanceID, 1, 1, 1, 0, 0, GETDATE()
            FROM ProfileMaster p
            WHERE p.ProfileID IN (2, 3, 5, 6, 7)
            AND p.IsDeleted = 0 
            AND NOT EXISTS (
                SELECT 1 FROM ProfileMenuMapping 
                WHERE ProfileID = p.ProfileID AND MenuID = @MarkEmployeeAttendanceID
            );

            INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, IsDeleted, CreatedAt)
            SELECT p.ProfileID, @ViewEmployeeAttendanceID, 1, 0, 0, 0, 0, GETDATE()
            FROM ProfileMaster p
            WHERE p.ProfileID IN (2, 3, 5, 6, 7)
            AND p.IsDeleted = 0 
            AND NOT EXISTS (
                SELECT 1 FROM ProfileMenuMapping 
                WHERE ProfileID = p.ProfileID AND MenuID = @ViewEmployeeAttendanceID
            );
            """,
            reverse_sql="""
            -- Reverse migration: restore original menu names
            DECLARE @AttendanceMenuID INT;
            SELECT @AttendanceMenuID = MenuID FROM MenuMaster WHERE MenuName = 'Attendance' AND ParentMenuID IS NULL AND IsDeleted = 0;

            UPDATE MenuMaster 
            SET MenuName = 'Mark Attendance'
            WHERE MenuName = 'Mark Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            UPDATE MenuMaster 
            SET MenuName = 'View Attendance'
            WHERE MenuName = 'View Student Attendance' AND ParentMenuID = @AttendanceMenuID AND IsDeleted = 0;

            -- Delete employee attendance menus
            DELETE FROM ProfileMenuMapping WHERE MenuID IN (
                SELECT MenuID FROM MenuMaster WHERE MenuName IN ('Mark Employee/Staff Attendance', 'View Employee/Staff Attendance')
            );

            DELETE FROM MenuMaster WHERE MenuName IN ('Mark Employee/Staff Attendance', 'View Employee/Staff Attendance');
            """
        ),
    ]
