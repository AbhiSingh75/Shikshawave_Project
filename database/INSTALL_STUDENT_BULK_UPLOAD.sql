-- Installation Script for Student Bulk Upload Feature
-- Run this script to set up all required database objects

PRINT 'Installing Student Bulk Upload Feature...';
GO

-- Step 1: Create Student_Staging Table
PRINT 'Creating Student_Staging table...';
GO

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
    PRINT 'Student_Staging table already exists';
GO

-- Step 2: Create Commit Stored Procedure
PRINT 'Creating Proc_Student_Staging_Commit...';
GO

CREATE OR ALTER PROCEDURE Proc_Student_Staging_Commit
    @ImportID INT,
    @SchoolID INT,
    @CommittedBy INT,
    @SuccessCount INT OUTPUT,
    @FailureCount INT OUTPUT,
    @ErrorMessage NVARCHAR(4000) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        SET @SuccessCount = 0;
        SET @FailureCount = 0;
        
        IF NOT EXISTS (SELECT 1 FROM DataImportLog WHERE ImportID = @ImportID AND SchoolID = @SchoolID)
        BEGIN
            SET @ErrorMessage = 'Import not found';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        UPDATE DataImportLog SET Status = 'Importing', ImportStartedAt = GETDATE() WHERE ImportID = @ImportID;
        
        INSERT INTO Student (
            SchoolID, StudentCode, FullName, Gender, DateOfBirth, Age, BloodGroup, Category, Religion, Nationality,
            StudentAadhaar, MotherTongue, PresentAddress, PermanentAddress, District, State, Country,
            ParentMobile, AlternateNumber, Email, FatherName, FatherOccupation, FatherQualification,
            FatherAadhaar, FatherMobile, MotherName, MotherOccupation, MotherQualification, MotherAadhaar,
            MotherMobile, GuardianName, GuardianRelation, GuardianMobile, LastSchool, LastClass, TCNumber,
            MediumOfInstruction, AdmissionClass, Section, Stream, ModeOfAdmission, AdmissionDate,
            CreatedBy, CreatedAt, IsDeleted
        )
        SELECT
            @SchoolID,
            ISNULL(s.StudentCode, 'STU' + CAST(@SchoolID AS NVARCHAR) + RIGHT('0000' + CAST(ROW_NUMBER() OVER (ORDER BY s.StagingID) + 
                ISNULL((SELECT MAX(CAST(SUBSTRING(StudentCode, LEN(StudentCode) - 3, 4) AS INT)) FROM Student WHERE SchoolID = @SchoolID), 0) AS NVARCHAR), 4)),
            s.FullName, s.Gender, s.DateOfBirth, ISNULL(s.Age, DATEDIFF(YEAR, s.DateOfBirth, GETDATE())),
            s.BloodGroup, s.Category, s.Religion, s.Nationality, s.StudentAadhaar, s.MotherTongue,
            s.PresentAddress, s.PermanentAddress, s.District, s.State, s.Country, s.ParentMobile,
            s.AlternateNumber, s.Email, s.FatherName, s.FatherOccupation, s.FatherQualification,
            s.FatherAadhaar, s.FatherMobile, s.MotherName, s.MotherOccupation, s.MotherQualification,
            s.MotherAadhaar, s.MotherMobile, s.GuardianName, s.GuardianRelation, s.GuardianMobile,
            s.LastSchool, s.LastClass, s.TCNumber, s.MediumOfInstruction, s.AdmissionClass, s.Section,
            s.Stream, s.ModeOfAdmission, s.AdmissionDate, @CommittedBy, GETDATE(), 0
        FROM Student_Staging s
        WHERE s.ImportID = @ImportID AND s.IsValid = 1;
        
        SET @SuccessCount = @@ROWCOUNT;
        SELECT @FailureCount = COUNT(*) FROM Student_Staging WHERE ImportID = @ImportID AND IsValid = 0;
        
        UPDATE DataImportLog
        SET Status = CASE WHEN @FailureCount = 0 THEN 'Completed' WHEN @SuccessCount = 0 THEN 'Failed' ELSE 'PartialSuccess' END,
            SuccessRows = @SuccessCount, FailedRows = @FailureCount, ImportCompletedAt = GETDATE()
        WHERE ImportID = @ImportID;
        
        SET @ErrorMessage = 'Commit completed: ' + CAST(@SuccessCount AS NVARCHAR) + ' inserted, ' + CAST(@FailureCount AS NVARCHAR) + ' failed';
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SET @ErrorMessage = ERROR_MESSAGE();
        UPDATE DataImportLog SET Status = 'Failed', ImportCompletedAt = GETDATE(), Remarks = @ErrorMessage WHERE ImportID = @ImportID;
    END CATCH
END
GO

PRINT 'Proc_Student_Staging_Commit created successfully';
PRINT 'Student Bulk Upload Feature installation completed!';
GO
