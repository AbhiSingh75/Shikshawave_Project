CREATE OR ALTER PROCEDURE Proc_Certificate_Insert
    @StudentID INT,
    @School_ID INT,
    @CertificateType NVARCHAR(100),
    @CertificateNumber NVARCHAR(50),
    @CertificateData NVARCHAR(MAX),
    @GeneratedBy INT,
    @Remarks NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO CertificateDocuments (StudentID, School_ID, CertificateType, CertificateNumber, CertificateData, IssueDate, GeneratedBy, Status, Remarks)
    VALUES (@StudentID, @School_ID, @CertificateType, @CertificateNumber, @CertificateData, GETDATE(), @GeneratedBy, 'Issued', @Remarks);
    
    SELECT SCOPE_IDENTITY() AS Certificate_ID;
END
GO
