-- =============================================
-- Stored Procedure: Proc_Dashboard_Employees_Get
-- Description: Get employee/teacher/staff statistics for dashboard
-- Author: ShikshaWave Team
-- Created: 2024
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Dashboard_Employees_Get
    @SchoolID INT = NULL,
    @Department NVARCHAR(100) = NULL,
    @Gender NVARCHAR(10) = NULL,
    @EmploymentType NVARCHAR(50) = NULL,
    @FromDate DATE = NULL,
    @ToDate DATE = NULL,
    @ShowActiveOnly BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Get total employee statistics with filters
        SELECT 
            COUNT(DISTINCT e.EmployeeID) AS TotalEmployees,
            COUNT(DISTINCT CASE WHEN e.Gender = 'Male' THEN e.EmployeeID END) AS MaleEmployees,
            COUNT(DISTINCT CASE WHEN e.Gender = 'Female' THEN e.EmployeeID END) AS FemaleEmployees,
            COUNT(DISTINCT CASE WHEN e.EmploymentType = 'Permanent' THEN e.EmployeeID END) AS PermanentEmployees,
            COUNT(DISTINCT CASE WHEN e.EmploymentType = 'Contract' THEN e.EmployeeID END) AS ContractEmployees,
            COUNT(DISTINCT CASE WHEN e.EmploymentType = 'Guest' THEN e.EmployeeID END) AS GuestEmployees,
            COUNT(DISTINCT CASE WHEN ISNULL(e.IsDeleted, 0) = 0 THEN e.EmployeeID END) AS ActiveEmployees,
            COUNT(DISTINCT CASE WHEN ISNULL(e.IsDeleted, 1) = 1 THEN e.EmployeeID END) AS InactiveEmployees
        FROM EmployeeMaster e
        LEFT JOIN ProfileMaster AS P ON E.ProfileId = p.ProfileID AND p.IsDeleted = 0
        WHERE 
            (@SchoolID IS NULL OR e.SchoolID = @SchoolID)
            AND (@Department IS NULL OR p.ProfileName = @Department)
            AND (@Gender IS NULL OR e.Gender = @Gender)
            AND (@EmploymentType IS NULL OR e.EmploymentType = @EmploymentType)
            AND (@FromDate IS NULL OR CAST(e.DOJ AS DATE) >= @FromDate)
            AND (@ToDate IS NULL OR CAST(e.DOJ AS DATE) <= @ToDate)
            AND (@ShowActiveOnly = 0 OR ISNULL(e.IsDeleted, 0) = 0);
            
        -- Get department-wise breakdown
        SELECT 
            ISNULL(p.ProfileName, 'Not Assigned') AS EmployeeType,
            COUNT(DISTINCT e.EmployeeID) AS EmployeeCount,
            COUNT(DISTINCT CASE WHEN e.Gender = 'Male' THEN e.EmployeeID END) AS MaleCount,
            COUNT(DISTINCT CASE WHEN e.Gender = 'Female' THEN e.EmployeeID END) AS FemaleCount
        FROM EmployeeMaster e
        LEFT JOIN ProfileMaster AS P ON E.ProfileId = p.ProfileID AND p.IsDeleted = 0
        WHERE 
            (@SchoolID IS NULL OR e.SchoolID = @SchoolID)
            AND (@FromDate IS NULL OR CAST(e.DOJ AS DATE) >= @FromDate)
            AND (@ToDate IS NULL OR CAST(e.DOJ AS DATE) <= @ToDate)
            AND (@ShowActiveOnly = 0 OR ISNULL(e.IsDeleted, 0) = 0)
        GROUP BY p.ProfileName
        ORDER BY EmployeeCount DESC;
        
    END TRY
    BEGIN CATCH
        SELECT 
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_MESSAGE() AS ErrorMessage;
    END CATCH
END;
GO
