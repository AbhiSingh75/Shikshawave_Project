CREATE OR ALTER PROCEDURE Proc_TermsConditions_Delete
    @Id INT,
    @SchoolId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DELETE FROM TermsConditions
    WHERE Id = @Id AND SchoolId = @SchoolId;
    
    SELECT 'SUCCESS' AS Status, 'Terms & Conditions deleted successfully' AS Message;
END
GO
