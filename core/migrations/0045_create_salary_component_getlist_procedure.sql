-- Migration to create Proc_SalaryComponentMaster_Get

-- Drop if exists
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'Proc_SalaryComponentMaster_Get')
    DROP PROCEDURE Proc_SalaryComponentMaster_Get;
GO

-- Create procedure
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
GO
