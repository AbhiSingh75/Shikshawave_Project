-- Student Documents Table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'StudentDocuments')
BEGIN
    CREATE TABLE StudentDocuments (
        Document_ID INT IDENTITY(1,1) PRIMARY KEY,
        StudentID INT NOT NULL,
        School_ID INT NOT NULL,
        DocumentType NVARCHAR(100) NOT NULL,
        DocumentData NVARCHAR(MAX),
        GeneratedBy INT NOT NULL,
        Generated_Date DATETIME NOT NULL DEFAULT GETDATE(),
        Status NVARCHAR(50) NOT NULL DEFAULT 'Generated',
        Remarks NVARCHAR(500),
        Created_At DATETIME NOT NULL DEFAULT GETDATE(),
        Updated_At DATETIME NOT NULL DEFAULT GETDATE(),
        FOREIGN KEY (School_ID) REFERENCES Schools(School_ID)
    );
    
    PRINT 'StudentDocuments table created successfully';
END
ELSE
BEGIN
    -- Add DocumentData column if table exists but column doesn't
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('StudentDocuments') AND name = 'DocumentData')
    BEGIN
        ALTER TABLE StudentDocuments ADD DocumentData NVARCHAR(MAX);
        PRINT 'DocumentData column added to StudentDocuments table';
    END
    ELSE
    BEGIN
        PRINT 'StudentDocuments table already exists with DocumentData column';
    END
END
GO
