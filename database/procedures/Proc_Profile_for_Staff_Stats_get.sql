-- =============================================
-- Stored Procedure: Proc_Profile_for_Staff_Stats_get
-- Description: Get profile types for staff statistics filter
-- Author: ShikshaWave Team
-- Created: 2024
-- =============================================

CREATE OR ALTER PROCEDURE Proc_Profile_for_Staff_Stats_get
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT ProfileID, ProfileName 
    FROM ProfileMaster  
    WHERE ProfileName IN (
        'School Admin',
        'Teacher',
        'Driver',
        'Librarian',
        'Accountant',
        'Support Executive'
    )
    AND IsDeleted = 0
    ORDER BY ProfileName;
END;
GO
