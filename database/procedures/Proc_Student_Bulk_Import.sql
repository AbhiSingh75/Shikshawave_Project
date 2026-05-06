-- Stored Procedure: Proc_Student_Bulk_Import
-- Purpose: Bulk import students from Excel with validation and error tracking
-- Author: ShikshaWave Team
-- Date: 2024

CREATE OR ALTER PROCEDURE Proc_Student_Bulk_Import
    @SchoolID INT,
    @ImportID INT,
    @StudentsJSON NVARCHAR(MAX), -- JSON array of student records
    @CreatedBy INT,
    @SuccessCount INT OUTPUT,
    @FailureCount INT OUTPUT,
    @ErrorMessage NVARCHAR(4000) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    
    DECLARE @RowNumber INT = 0;
    DECLARE @TotalRows INT = 0;
    
    BEGIN TRY
        -- Initialize output parameters
        SET @SuccessCount = 0;
        SET @FailureCount = 0;
        SET @ErrorMessage = NULL;
        
        -- Create temp table for JSON parsing
        CREATE TABLE #TempStudents (
            RowNum INT,
            StudentCode NVARCHAR(20),
            FullName NVARCHAR(100),
            Gender NVARCHAR(10),
            DateOfBirth DATE,
            Age INT,
            BloodGroup NVARCHAR(10),
            Category NVARCHAR(50),
            Religion NVARCHAR(50),
            Nationality NVARCHAR(50),
            MotherTongue NVARCHAR(50),
            StudentAadhaar NVARCHAR(12),
            PresentAddress NVARCHAR(500),
            ParentMobile NVARCHAR(10),
            AlternateNumber NVARCHAR(10),
            Email NVARCHAR(100),
            FatherName NVARCHAR(100),
            FatherMobile NVARCHAR(10),
            MotherName NVARCHAR(100),
            MotherMobile NVARCHAR(10),
            GuardianName NVARCHAR(100),
            GuardianMobile NVARCHAR(10),
            AdmissionClass INT,
            Section INT,
            Stream NVARCHAR(50),
            AdmissionDate DATE,
            Photo NVARCHAR(MAX) -- Base64 encoded
        );
        
        -- Parse JSON into temp table
        INSERT INTO #TempStudents
        SELECT 
            ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS RowNum,
            StudentCode,
            FullName,
            Gender,
            TRY_CAST(DateOfBirth AS DATE),
            Age,
            BloodGroup,
            Category,
            Religion,
            Nationality,
            MotherTongue,
            StudentAadhaar,
            PresentAddress,
            ParentMobile,
            AlternateNumber,
            Email,
            FatherName,
            FatherMobile,
            MotherName,
            MotherMobile,
            GuardianName,
            GuardianMobile,
            AdmissionClass,
            Section,
            Stream,
            TRY_CAST(AdmissionDate AS DATE),
            Photo
        FROM OPENJSON(@StudentsJSON)
        WITH (
            StudentCode NVARCHAR(20) '$.StudentCode',
            FullName NVARCHAR(100) '$.FullName',
            Gender NVARCHAR(10) '$.Gender',
            DateOfBirth NVARCHAR(20) '$.DateOfBirth',
            Age INT '$.Age',
            BloodGroup NVARCHAR(10) '$.BloodGroup',
            Category NVARCHAR(50) '$.Category',
            Religion NVARCHAR(50) '$.Religion',
            Nationality NVARCHAR(50) '$.Nationality',
            MotherTongue NVARCHAR(50) '$.MotherTongue',
            StudentAadhaar NVARCHAR(12) '$.StudentAadhaar',
            PresentAddress NVARCHAR(500) '$.PresentAddress',
            ParentMobile NVARCHAR(10) '$.ParentMobile',
            AlternateNumber NVARCHAR(10) '$.AlternateNumber',
            Email NVARCHAR(100) '$.Email',
            FatherName NVARCHAR(100) '$.FatherName',
            FatherMobile NVARCHAR(10) '$.FatherMobile',
            MotherName NVARCHAR(100) '$.MotherName',
            MotherMobile NVARCHAR(10) '$.MotherMobile',
            GuardianName NVARCHAR(100) '$.GuardianName',
            GuardianMobile NVARCHAR(10) '$.GuardianMobile',
            AdmissionClass INT '$.AdmissionClass',
            Section INT '$.Section',
            Stream NVARCHAR(50) '$.Stream',
            AdmissionDate NVARCHAR(20) '$.AdmissionDate',
            Photo NVARCHAR(MAX) '$.Photo'
        );
        
        SELECT @TotalRows = COUNT(*) FROM #TempStudents;
        
        -- Update import log
        UPDATE DataImportLog
        SET Status = 'Importing',
            ImportStartedAt = GETDATE(),
            TotalRows = @TotalRows
        WHERE ImportID = @ImportID;
        
        -- Process each student
        DECLARE @CurrentRow INT = 1;
        DECLARE @StudentCode NVARCHAR(20);
        DECLARE @FullName NVARCHAR(100);
        DECLARE @Gender NVARCHAR(10);
        DECLARE @DateOfBirth DATE;
        DECLARE @Age INT;
        DECLARE @ParentMobile NVARCHAR(10);
        DECLARE @FatherName NVARCHAR(100);
        DECLARE @AdmissionClass INT;
        DECLARE @Section INT;
        DECLARE @AdmissionDate DATE;
        DECLARE @StudentAadhaar NVARCHAR(12);
        DECLARE @Email NVARCHAR(100);
        DECLARE @ErrorMsg NVARCHAR(1000);
        DECLARE @PhotoBinary VARBINARY(MAX);
        
        WHILE @CurrentRow <= @TotalRows
        BEGIN
            BEGIN TRY
                -- Get current row data
                SELECT 
                    @StudentCode = StudentCode,
                    @FullName = FullName,
                    @Gender = Gender,
                    @DateOfBirth = DateOfBirth,
                    @Age = Age,
                    @ParentMobile = ParentMobile,
                    @FatherName = FatherName,
                    @AdmissionClass = AdmissionClass,
                    @Section = Section,
                    @AdmissionDate = AdmissionDate,
                    @StudentAadhaar = StudentAadhaar,
                    @Email = Email
                FROM #TempStudents
                WHERE RowNum = @CurrentRow;
                
                -- Validation: Required fields
                IF @FullName IS NULL OR LTRIM(RTRIM(@FullName)) = ''
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'FullName', 'Required', 'Full Name is required');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                IF @Gender NOT IN ('Male', 'Female', 'Other')
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ColumnValue, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'Gender', @Gender, 'Validation', 'Gender must be Male, Female, or Other');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                IF @DateOfBirth IS NULL OR @DateOfBirth > GETDATE()
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'DateOfBirth', 'Validation', 'Date of Birth is required and cannot be in future');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                IF @ParentMobile IS NULL OR LEN(@ParentMobile) != 10 OR @ParentMobile NOT LIKE '[6-9]%'
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ColumnValue, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'ParentMobile', @ParentMobile, 'Validation', 'Parent Mobile must be 10 digits starting with 6-9');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                -- Validation: FK - ClassID must exist
                IF NOT EXISTS (SELECT 1 FROM ClassMaster WHERE ClassID = @AdmissionClass AND SchoolID = @SchoolID AND IsDeleted = 0)
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ColumnValue, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'AdmissionClass', CAST(@AdmissionClass AS NVARCHAR), 'FK', 'Class does not exist for this school');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                -- Validation: FK - SectionID must exist
                IF NOT EXISTS (SELECT 1 FROM SectionMaster WHERE SectionID = @Section AND ClassID = @AdmissionClass AND IsDeleted = 0)
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ColumnValue, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'Section', CAST(@Section AS NVARCHAR), 'FK', 'Section does not exist for this class');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                -- Validation: Duplicate Aadhaar
                IF @StudentAadhaar IS NOT NULL AND EXISTS (SELECT 1 FROM Student WHERE StudentAadhaar = @StudentAadhaar AND SchoolID = @SchoolID AND IsDeleted = 0)
                BEGIN
                    INSERT INTO DataImportErrors (ImportID, RowNumber, ColumnName, ColumnValue, ErrorType, ErrorMessage)
                    VALUES (@ImportID, @CurrentRow, 'StudentAadhaar', @StudentAadhaar, 'Duplicate', 'Student with this Aadhaar already exists');
                    SET @FailureCount = @FailureCount + 1;
                    SET @CurrentRow = @CurrentRow + 1;
                    CONTINUE;
                END
                
                -- Auto-generate StudentCode if not provided
                IF @StudentCode IS NULL OR LTRIM(RTRIM(@StudentCode)) = ''
                BEGIN
                    DECLARE @MaxCode INT;
                    SELECT @MaxCode = ISNULL(MAX(CAST(SUBSTRING(StudentCode, LEN(StudentCode) - 3, 4) AS INT)), 0)
                    FROM Student
                    WHERE SchoolID = @SchoolID AND StudentCode LIKE 'STU' + CAST(@SchoolID AS NVARCHAR) + '%';
                    
                    SET @StudentCode = 'STU' + CAST(@SchoolID AS NVARCHAR) + RIGHT('0000' + CAST(@MaxCode + 1 AS NVARCHAR), 4);
                END
                
                -- Calculate Age if not provided
                IF @Age IS NULL OR @Age = 0
                BEGIN
                    SET @Age = DATEDIFF(YEAR, @DateOfBirth, GETDATE());
                END
                
                -- Convert Photo from Base64 to binary (if provided)
                SET @PhotoBinary = NULL;
                -- Photo conversion would be handled in application layer
                
                -- Insert student record
                INSERT INTO Student (
                    SchoolID, StudentCode, FullName, Gender, DateOfBirth, Age,
                    BloodGroup, Category, Religion, Nationality, MotherTongue,
                    StudentAadhaar, PresentAddress, ParentMobile, AlternateNumber,
                    Email, FatherName, FatherMobile, MotherName, MotherMobile,
                    GuardianName, GuardianMobile, AdmissionClass, Section, Stream,
                    AdmissionDate, Photo, CreatedBy, CreatedAt, IsDeleted
                )
                SELECT 
                    @SchoolID, @StudentCode, FullName, Gender, DateOfBirth, Age,
                    BloodGroup, Category, Religion, Nationality, MotherTongue,
                    StudentAadhaar, PresentAddress, ParentMobile, AlternateNumber,
                    Email, FatherName, FatherMobile, MotherName, MotherMobile,
                    GuardianName, GuardianMobile, AdmissionClass, Section, Stream,
                    AdmissionDate, @PhotoBinary, @CreatedBy, GETDATE(), 0
                FROM #TempStudents
                WHERE RowNum = @CurrentRow;
                
                SET @SuccessCount = @SuccessCount + 1;
                
            END TRY
            BEGIN CATCH
                -- Log error
                INSERT INTO DataImportErrors (ImportID, RowNumber, ErrorType, ErrorMessage)
                VALUES (@ImportID, @CurrentRow, 'Exception', ERROR_MESSAGE());
                
                SET @FailureCount = @FailureCount + 1;
            END CATCH
            
            SET @CurrentRow = @CurrentRow + 1;
        END
        
        -- Update import log with final status
        UPDATE DataImportLog
        SET Status = CASE 
                        WHEN @FailureCount = 0 THEN 'Completed'
                        WHEN @SuccessCount = 0 THEN 'Failed'
                        ELSE 'PartialSuccess'
                     END,
            SuccessRows = @SuccessCount,
            FailedRows = @FailureCount,
            ImportCompletedAt = GETDATE()
        WHERE ImportID = @ImportID;
        
        -- Clean up
        DROP TABLE #TempStudents;
        
        SET @ErrorMessage = 'Import completed: ' + CAST(@SuccessCount AS NVARCHAR) + ' success, ' + CAST(@FailureCount AS NVARCHAR) + ' failed';
        
    END TRY
    BEGIN CATCH
        SET @ErrorMessage = ERROR_MESSAGE();
        SET @FailureCount = @TotalRows;
        SET @SuccessCount = 0;
        
        -- Update import log with error
        UPDATE DataImportLog
        SET Status = 'Failed',
            FailedRows = @TotalRows,
            ImportCompletedAt = GETDATE(),
            Remarks = @ErrorMessage
        WHERE ImportID = @ImportID;
        
        -- Clean up
        IF OBJECT_ID('tempdb..#TempStudents') IS NOT NULL
            DROP TABLE #TempStudents;
    END CATCH
END
GO

PRINT 'Proc_Student_Bulk_Import created successfully';
