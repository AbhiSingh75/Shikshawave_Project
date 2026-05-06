-- Stored Procedure to Get Salary Component List
-- Filters by SchoolID (NULL for all schools - Super Admin)

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
