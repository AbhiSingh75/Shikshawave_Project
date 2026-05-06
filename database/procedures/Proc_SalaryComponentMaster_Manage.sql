-- Unified Salary Component Master CRUD Procedure
-- Handles INSERT, UPDATE, DELETE, and RESTORE operations

IF EXISTS (SELECT * FROM sys.objects WHERE name = 'Proc_SalaryComponentMaster_Manage' AND type = 'P')
    DROP PROCEDURE Proc_SalaryComponentMaster_Manage;
GO

CREATE PROCEDURE Proc_SalaryComponentMaster_Manage
(
    @Action NVARCHAR(20),               -- INSERT / UPDATE / DELETE / RESTORE
    @ComponentID INT = NULL,
    @SchoolID INT = NULL,
    @ComponentName NVARCHAR(100) = NULL,
    @ComponentType NVARCHAR(20) = NULL, -- 'Earning' or 'Deduction'
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
            -- Validate required fields
            IF @SchoolID IS NULL OR @ComponentName IS NULL OR @ComponentType IS NULL
            BEGIN
                SET @Message = '{"status":"error","message":"School ID, Component Name, and Component Type are required"}';
                ROLLBACK TRAN;
                RETURN;
            END

            -- Prevent duplicate component for same school
            IF EXISTS (
                SELECT 1 
                FROM SalaryComponentMaster 
                WHERE SchoolID = @SchoolID 
                  AND LTRIM(RTRIM(ComponentName)) = LTRIM(RTRIM(@ComponentName))
                  AND ISNULL(IsDeleted, 0) = 0
            )
            BEGIN
                SET @Message = '{"status":"error","message":"Salary component with this name already exists for this school"}';
                ROLLBACK TRAN;
                RETURN;
            END

            -- Validate component type
            IF @ComponentType NOT IN ('Earning', 'Deduction')
            BEGIN
                SET @Message = '{"status":"error","message":"Component Type must be either Earning or Deduction"}';
                ROLLBACK TRAN;
                RETURN;
            END

            INSERT INTO SalaryComponentMaster
            (
                SchoolID, ComponentName, ComponentType, 
                CreatedBy, CreatedAt, IsDeleted
            )
            VALUES
            (
                @SchoolID, @ComponentName, @ComponentType,
                @UserId, GETDATE(), 0
            );

            COMMIT TRAN;
            SET @Message = '{"status":"success","message":"Salary component created successfully"}';
            RETURN;
        END

        ELSE IF @Action = 'UPDATE'
        BEGIN
            IF @ComponentID IS NULL
            BEGIN
                SET @Message = '{"status":"error","message":"Component ID is required"}';
                ROLLBACK TRAN;
                RETURN;
            END

            IF NOT EXISTS (SELECT 1 FROM SalaryComponentMaster WHERE ComponentID = @ComponentID)
            BEGIN
                SET @Message = '{"status":"error","message":"Salary component not found"}';
                ROLLBACK TRAN;
                RETURN;
            END

            -- Prevent duplicate name for same school
            IF EXISTS (
                SELECT 1 
                FROM SalaryComponentMaster 
                WHERE SchoolID = @SchoolID 
                  AND LTRIM(RTRIM(ComponentName)) = LTRIM(RTRIM(@ComponentName))
                  AND ComponentID <> @ComponentID
                  AND ISNULL(IsDeleted, 0) = 0
            )
            BEGIN
                SET @Message = '{"status":"error","message":"Another salary component with this name already exists for this school"}';
                ROLLBACK TRAN;
                RETURN;
            END

            -- Validate component type
            IF @ComponentType NOT IN ('Earning', 'Deduction')
            BEGIN
                SET @Message = '{"status":"error","message":"Component Type must be either Earning or Deduction"}';
                ROLLBACK TRAN;
                RETURN;
            END

            UPDATE SalaryComponentMaster
            SET 
                ComponentName = @ComponentName,
                ComponentType = @ComponentType,
                UpdatedBy = @UserId,
                UpdatedAt = GETDATE()
            WHERE ComponentID = @ComponentID;

            COMMIT TRAN;
            SET @Message = '{"status":"success","message":"Salary component updated successfully"}';
            RETURN;
        END

        ELSE IF @Action = 'DELETE'
        BEGIN
            IF @ComponentID IS NULL
            BEGIN
                SET @Message = '{"status":"error","message":"Component ID is required"}';
                ROLLBACK TRAN;
                RETURN;
            END

            IF NOT EXISTS (SELECT 1 FROM SalaryComponentMaster WHERE ComponentID = @ComponentID)
            BEGIN
                SET @Message = '{"status":"error","message":"Salary component not found"}';
                ROLLBACK TRAN;
                RETURN;
            END

            UPDATE SalaryComponentMaster
            SET 
                IsDeleted = 1,
                DeletedBy = @UserId,
                DeletedAt = GETDATE()
            WHERE ComponentID = @ComponentID;

            COMMIT TRAN;
            SET @Message = '{"status":"success","message":"Salary component deleted successfully"}';
            RETURN;
        END

        ELSE IF @Action = 'RESTORE'
        BEGIN
            IF @ComponentID IS NULL
            BEGIN
                SET @Message = '{"status":"error","message":"Component ID is required"}';
                ROLLBACK TRAN;
                RETURN;
            END

            IF NOT EXISTS (SELECT 1 FROM SalaryComponentMaster WHERE ComponentID = @ComponentID)
            BEGIN
                SET @Message = '{"status":"error","message":"Salary component not found"}';
                ROLLBACK TRAN;
                RETURN;
            END

            UPDATE SalaryComponentMaster
            SET 
                IsDeleted = 0,
                UpdatedBy = @UserId,
                UpdatedAt = GETDATE(),
                DeletedBy = NULL,
                DeletedAt = NULL
            WHERE ComponentID = @ComponentID;

            COMMIT TRAN;
            SET @Message = '{"status":"success","message":"Salary component restored successfully"}';
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
GO
