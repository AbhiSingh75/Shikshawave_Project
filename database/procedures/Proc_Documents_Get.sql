CREATE OR ALTER PROCEDURE Proc_Certificates_Get
    @School_ID INT,
    @StudentID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @StudentID IS NOT NULL
    BEGIN
        -- For student view
        SELECT c.Certificate_ID, c.CertificateType, c.CertificateNumber, c.CertificateData, c.IssueDate, c.Status, c.Remarks
        FROM CertificateDocuments c
        WHERE c.StudentID = @StudentID AND c.School_ID = @School_ID
        ORDER BY c.IssueDate DESC;
    END
    ELSE
    BEGIN
        -- For admin view
        SELECT c.Certificate_ID, c.CertificateType, c.CertificateNumber, c.CertificateData, s.FullName, s.StudentCode,
               cm.ClassName, sm.SectionName, c.IssueDate, c.Status, c.Remarks, u.User_Name
        FROM CertificateDocuments c
        LEFT JOIN Student s ON c.StudentID = s.StudentID
        LEFT JOIN ClassMaster cm ON s.AdmissionClass = cm.ClassID
        LEFT JOIN SectionMaster sm ON s.Section = sm.SectionID
        LEFT JOIN Users u ON c.GeneratedBy = u.User_ID
        WHERE c.School_ID = @School_ID
        ORDER BY c.IssueDate DESC;
    END
END
GO
