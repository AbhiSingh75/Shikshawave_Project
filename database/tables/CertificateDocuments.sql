CREATE TABLE CertificateDocuments (
    Certificate_ID INT IDENTITY(1,1) PRIMARY KEY,
    StudentID INT NOT NULL,
    School_ID INT NOT NULL,
    CertificateType NVARCHAR(100) NOT NULL,
    CertificateNumber NVARCHAR(50),
    CertificateData NVARCHAR(MAX),
    IssueDate DATE NOT NULL DEFAULT GETDATE(),
    GeneratedBy INT NOT NULL,
    Status NVARCHAR(50) NOT NULL DEFAULT 'Issued',
    Remarks NVARCHAR(500),
    FOREIGN KEY (School_ID) REFERENCES Schools(School_ID)
);
GO
