# Generated manually to create unified Fee Type CRUD procedure

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_add_missing_feetype_columns'),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Drop existing procedure if exists
            IF EXISTS (SELECT * FROM sys.objects WHERE name = 'Proc_FeeTypeMaster_Manage' AND type = 'P')
                DROP PROCEDURE Proc_FeeTypeMaster_Manage;
            """,
            reverse_sql=""
        ),
        migrations.RunSQL(
            """
            -- Create unified procedure for Fee Type CRUD operations
            CREATE PROCEDURE Proc_FeeTypeMaster_Manage
            (
                @Action NVARCHAR(20),               -- INSERT / UPDATE / DELETE / RESTORE
                @FeeTypeId INT = NULL,
                @SchoolId INT = NULL,
                @ClassId INT = NULL,
                @FeeTypeName NVARCHAR(200) = NULL,
                @DefaultAmount DECIMAL(18,2) = NULL,
                @IsActive BIT = 1,
                @UserId INT = NULL,
                @Message NVARCHAR(500) OUTPUT
            )
            AS
            BEGIN
                SET NOCOUNT ON;

                BEGIN TRY
                    BEGIN TRAN;

                    IF @Action = 'INSERT'
                    BEGIN
                        -- Prevent duplicate FeeType for same School & Class
                        IF EXISTS (
                            SELECT 1 
                            FROM FeeType_Master 
                            WHERE SchoolId = @SchoolId 
                              AND ClassId = @ClassId 
                              AND LTRIM(RTRIM(FeeTypeName)) = LTRIM(RTRIM(@FeeTypeName))
                        )
                        BEGIN
                            SET @Message = '{"status":"error","message":"Duplicate Fee Type already exists for this school and class"}';
                            ROLLBACK TRAN;
                            RETURN;
                        END

                        INSERT INTO FeeType_Master
                        (
                            SchoolId, ClassId, FeeTypeName, DefaultAmount, IsActive, 
                            CreatedBy, CreatedAt
                        )
                        VALUES
                        (
                            @SchoolId, @ClassId, @FeeTypeName, @DefaultAmount, @IsActive,
                            @UserId, GETDATE()
                        );

                        COMMIT TRAN;
                        SET @Message = '{"status":"success","message":"Fee Type created successfully"}';
                        RETURN;
                    END

                    ELSE IF @Action = 'UPDATE'
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM FeeType_Master WHERE FeeTypeId = @FeeTypeId)
                        BEGIN
                            SET @Message = '{"status":"error","message":"Fee Type not found"}';
                            ROLLBACK TRAN;
                            RETURN;
                        END

                        -- Prevent duplicate name for same School & Class
                        IF EXISTS (
                            SELECT 1 
                            FROM FeeType_Master 
                            WHERE SchoolId = @SchoolId 
                              AND ClassId = @ClassId 
                              AND LTRIM(RTRIM(FeeTypeName)) = LTRIM(RTRIM(@FeeTypeName))
                              AND FeeTypeId <> @FeeTypeId
                        )
                        BEGIN
                            SET @Message = '{"status":"error","message":"Another Fee Type with same name already exists for this school and class"}';
                            ROLLBACK TRAN;
                            RETURN;
                        END

                        UPDATE FeeType_Master
                        SET 
                            SchoolId = @SchoolId,
                            ClassId = @ClassId,
                            FeeTypeName = @FeeTypeName,
                            DefaultAmount = @DefaultAmount,
                            IsActive = @IsActive,
                            UpdatedBy = @UserId,
                            UpdatedAt = GETDATE()
                        WHERE FeeTypeId = @FeeTypeId;

                        COMMIT TRAN;
                        SET @Message = '{"status":"success","message":"Fee Type updated successfully"}';
                        RETURN;
                    END

                    ELSE IF @Action = 'DELETE'
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM FeeType_Master WHERE FeeTypeId = @FeeTypeId)
                        BEGIN
                            SET @Message = '{"status":"error","message":"Fee Type not found"}';
                            ROLLBACK TRAN;
                            RETURN;
                        END

                        UPDATE FeeType_Master
                        SET 
                            IsActive = 0,
                            UpdatedBy = @UserId,
                            UpdatedAt = GETDATE()
                        WHERE FeeTypeId = @FeeTypeId;

                        COMMIT TRAN;
                        SET @Message = '{"status":"success","message":"Fee Type deactivated successfully"}';
                        RETURN;
                    END

                    ELSE IF @Action = 'RESTORE'
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM FeeType_Master WHERE FeeTypeId = @FeeTypeId)
                        BEGIN
                            SET @Message = '{"status":"error","message":"Fee Type not found"}';
                            ROLLBACK TRAN;
                            RETURN;
                        END

                        UPDATE FeeType_Master
                        SET 
                            IsActive = 1,
                            UpdatedBy = @UserId,
                            UpdatedAt = GETDATE()
                        WHERE FeeTypeId = @FeeTypeId;

                        COMMIT TRAN;
                        SET @Message = '{"status":"success","message":"Fee Type restored successfully"}';
                        RETURN;
                    END

                    ELSE
                    BEGIN
                        ROLLBACK TRAN;
                        SET @Message = '{"status":"error","message":"Invalid Action. Use INSERT, UPDATE, DELETE or RESTORE."}';
                        RETURN;
                    END

                END TRY
                BEGIN CATCH
                    ROLLBACK TRAN;
                    SET @Message = '{"status":"error","message":"' + ERROR_MESSAGE() + '"}';
                END CATCH
            END;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS Proc_FeeTypeMaster_Manage;"
        ),
    ]
