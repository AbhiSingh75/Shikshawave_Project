-- Data Import Tracking Tables for ShikshaWave ERP
-- Purpose: Track all legacy data imports with audit trail

-- Table 1: DataImportLog - Main import tracking
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DataImportLog') AND type = 'U')
BEGIN
    CREATE TABLE DataImportLog (
        ImportID INT IDENTITY(1,1) PRIMARY KEY,
        SchoolID INT NOT NULL,
        ImportType NVARCHAR(50) NOT NULL, -- Students, Teachers, Salary, Fee, Attendance, Exam, ExamResult, ClassMaster, SectionMaster, SubjectMaster
        FileName NVARCHAR(255) NOT NULL,
        FilePath NVARCHAR(500) NULL,
        FileSize BIGINT NULL, -- in bytes
        TotalRows INT NOT NULL,
        ValidRows INT DEFAULT 0,
        InvalidRows INT DEFAULT 0,
        SuccessRows INT DEFAULT 0,
        FailedRows INT DEFAULT 0,
        SkippedRows INT DEFAULT 0,
        Status NVARCHAR(20) NOT NULL DEFAULT 'Pending', -- Pending, Validating, Validated, Importing, Completed, Failed, PartialSuccess
        ValidationStartedAt DATETIME NULL,
        ValidationCompletedAt DATETIME NULL,
        ImportStartedAt DATETIME NULL,
        ImportCompletedAt DATETIME NULL,
        CreatedBy INT NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        ErrorFilePath NVARCHAR(500) NULL,
        ErrorFileGenerated BIT DEFAULT 0,
        Remarks NVARCHAR(1000) NULL,
        CONSTRAINT FK_DataImportLog_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_DataImportLog_User FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_DataImportLog_School ON DataImportLog(SchoolID);
    CREATE INDEX IX_DataImportLog_Status ON DataImportLog(Status);
    CREATE INDEX IX_DataImportLog_Type ON DataImportLog(ImportType);
    CREATE INDEX IX_DataImportLog_CreatedAt ON DataImportLog(CreatedAt DESC);
    
    PRINT 'DataImportLog table created successfully';
END
ELSE
BEGIN
    PRINT 'DataImportLog table already exists';
END
GO

-- Table 2: DataImportErrors - Detailed error tracking
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DataImportErrors') AND type = 'U')
BEGIN
    CREATE TABLE DataImportErrors (
        ErrorID INT IDENTITY(1,1) PRIMARY KEY,
        ImportID INT NOT NULL,
        RowNumber INT NOT NULL,
        ColumnName NVARCHAR(100) NULL,
        ColumnValue NVARCHAR(500) NULL,
        ErrorType NVARCHAR(50) NOT NULL, -- Validation, FK, Duplicate, Format, Required, Range
        ErrorMessage NVARCHAR(1000) NOT NULL,
        ErrorSeverity NVARCHAR(20) DEFAULT 'Error', -- Warning, Error, Critical
        RowData NVARCHAR(MAX) NULL, -- JSON of entire row
        CreatedAt DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_DataImportErrors_Import FOREIGN KEY (ImportID) REFERENCES DataImportLog(ImportID) ON DELETE CASCADE
    );
    
    CREATE INDEX IX_DataImportErrors_Import ON DataImportErrors(ImportID);
    CREATE INDEX IX_DataImportErrors_Row ON DataImportErrors(RowNumber);
    
    PRINT 'DataImportErrors table created successfully';
END
ELSE
BEGIN
    PRINT 'DataImportErrors table already exists';
END
GO

-- Table 3: DataImportMapping - Track field mappings for flexible imports
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DataImportMapping') AND type = 'U')
BEGIN
    CREATE TABLE DataImportMapping (
        MappingID INT IDENTITY(1,1) PRIMARY KEY,
        SchoolID INT NOT NULL,
        ImportType NVARCHAR(50) NOT NULL,
        SourceColumn NVARCHAR(100) NOT NULL,
        TargetColumn NVARCHAR(100) NOT NULL,
        IsRequired BIT DEFAULT 0,
        DefaultValue NVARCHAR(255) NULL,
        ValidationRule NVARCHAR(500) NULL,
        CreatedBy INT NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        IsActive BIT DEFAULT 1,
        CONSTRAINT FK_DataImportMapping_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_DataImportMapping_User FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_DataImportMapping_School_Type ON DataImportMapping(SchoolID, ImportType);
    
    PRINT 'DataImportMapping table created successfully';
END
ELSE
BEGIN
    PRINT 'DataImportMapping table already exists';
END
GO

-- Table 4: DataImportTemplate - Store template configurations
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DataImportTemplate') AND type = 'U')
BEGIN
    CREATE TABLE DataImportTemplate (
        TemplateID INT IDENTITY(1,1) PRIMARY KEY,
        ImportType NVARCHAR(50) NOT NULL,
        TemplateName NVARCHAR(100) NOT NULL,
        TemplateVersion NVARCHAR(20) DEFAULT '1.0',
        ColumnDefinitions NVARCHAR(MAX) NOT NULL, -- JSON array of column definitions
        SampleData NVARCHAR(MAX) NULL, -- JSON array of sample rows
        ValidationRules NVARCHAR(MAX) NULL, -- JSON object of validation rules
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME NULL
    );
    
    CREATE INDEX IX_DataImportTemplate_Type ON DataImportTemplate(ImportType);
    
    PRINT 'DataImportTemplate table created successfully';
END
ELSE
BEGIN
    PRINT 'DataImportTemplate table already exists';
END
GO

PRINT 'All Data Import tables created/verified successfully';
