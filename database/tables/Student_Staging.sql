-- Student_Staging Table
-- Purpose: Temporary storage for bulk student uploads with validation status
-- Author: ShikshaWave Team

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Student_Staging')
BEGIN
    CREATE TABLE Student_Staging (
        StagingID INT IDENTITY(1,1) PRIMARY KEY,
        ImportID INT NOT NULL,
        SchoolID INT NOT NULL,
        RowNumber INT NOT NULL,
        RawJson NVARCHAR(MAX) NOT NULL,
        IsValid BIT DEFAULT 0,
        ErrorMessages NVARCHAR(MAX) NULL,
        
        -- Parsed Student Fields
        StudentCode NVARCHAR(20) NULL,
        FullName NVARCHAR(100) NULL,
        Gender NVARCHAR(10) NULL,
        DateOfBirth DATE NULL,
        Age INT NULL,
        BloodGroup NVARCHAR(10) NULL,
        Category NVARCHAR(50) NULL,
        Religion NVARCHAR(50) NULL,
        Nationality NVARCHAR(50) NULL,
        StudentAadhaar NVARCHAR(12) NULL,
        MotherTongue NVARCHAR(50) NULL,
        PresentAddress NVARCHAR(500) NULL,
        PermanentAddress NVARCHAR(500) NULL,
        District NVARCHAR(100) NULL,
        State NVARCHAR(100) NULL,
        Country NVARCHAR(100) NULL,
        ParentMobile NVARCHAR(10) NULL,
        AlternateNumber NVARCHAR(10) NULL,
        Email NVARCHAR(100) NULL,
        FatherName NVARCHAR(100) NULL,
        FatherOccupation NVARCHAR(100) NULL,
        FatherQualification NVARCHAR(100) NULL,
        FatherAadhaar NVARCHAR(12) NULL,
        FatherMobile NVARCHAR(10) NULL,
        MotherName NVARCHAR(100) NULL,
        MotherOccupation NVARCHAR(100) NULL,
        MotherQualification NVARCHAR(100) NULL,
        MotherAadhaar NVARCHAR(12) NULL,
        MotherMobile NVARCHAR(10) NULL,
        GuardianName NVARCHAR(100) NULL,
        GuardianRelation NVARCHAR(50) NULL,
        GuardianMobile NVARCHAR(10) NULL,
        LastSchool NVARCHAR(200) NULL,
        LastClass NVARCHAR(50) NULL,
        TCNumber NVARCHAR(50) NULL,
        MediumOfInstruction NVARCHAR(50) NULL,
        AdmissionClass INT NULL,
        Section INT NULL,
        Stream NVARCHAR(50) NULL,
        ModeOfAdmission NVARCHAR(50) NULL,
        AdmissionDate DATE NULL,
        
        UploadedBy INT NOT NULL,
        UploadedAt DATETIME DEFAULT GETDATE(),
        
        CONSTRAINT FK_Student_Staging_Import FOREIGN KEY (ImportID) REFERENCES DataImportLog(ImportID),
        CONSTRAINT FK_Student_Staging_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_Student_Staging_User FOREIGN KEY (UploadedBy) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_Student_Staging_ImportID ON Student_Staging(ImportID);
    CREATE INDEX IX_Student_Staging_SchoolID ON Student_Staging(SchoolID);
    CREATE INDEX IX_Student_Staging_IsValid ON Student_Staging(IsValid);
    
    PRINT 'Student_Staging table created successfully';
END
ELSE
BEGIN
    PRINT 'Student_Staging table already exists';
END
GO
