-- Stored Procedure: Proc_Student_Staging_Commit
-- Purpose: Commit validated student records from staging to Student table
-- Author: ShikshaWave Team

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
        SET @ErrorMessage = NULL;
        
        -- Validate import exists and belongs to school
        IF NOT EXISTS (SELECT 1 FROM DataImportLog WHERE ImportID = @ImportID AND SchoolID = @SchoolID)
        BEGIN
            SET @ErrorMessage = 'Import not found or access denied';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Check if there are valid records to commit
        IF NOT EXISTS (SELECT 1 FROM Student_Staging WHERE ImportID = @ImportID AND IsValid = 1)
        BEGIN
            SET @ErrorMessage = 'No valid records found to commit';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Update import log status
        UPDATE DataImportLog
        SET Status = 'Importing',
            ImportStartedAt = GETDATE()
        WHERE ImportID = @ImportID;
        
        -- Insert valid records into Student table in batches
        DECLARE @BatchSize INT = 500;
        DECLARE @CurrentBatch INT = 0;
        DECLARE @TotalRecords INT;
        
        SELECT @TotalRecords = COUNT(*) FROM Student_Staging WHERE ImportID = @ImportID AND IsValid = 1;
        
        WHILE @CurrentBatch * @BatchSize < @TotalRecords
        BEGIN
            INSERT INTO Student (
                SchoolID, StudentCode, FullName, Gender, DateOfBirth, Age,
                BloodGroup, Category, Religion, Nationality, StudentAadhaar,
                MotherTongue, PresentAddress, PermanentAddress, District, State, Country,
                ParentMobile, AlternateNumber, Email,
                FatherName, FatherOccupation, FatherQualification, FatherAadhaar, FatherMobile,
                MotherName, MotherOccupation, MotherQualification, MotherAadhaar, MotherMobile,
                GuardianName, GuardianRelation, GuardianMobile,
                LastSchool, LastClass, TCNumber, MediumOfInstruction,
                AdmissionClass, Section, Stream, ModeOfAdmission, AdmissionDate,
                CreatedBy, CreatedAt, IsDeleted
            )
            SELECT TOP (@BatchSize)
                @SchoolID,
                ISNULL(s.StudentCode, 'STU' + CAST(@SchoolID AS NVARCHAR) + RIGHT('0000' + CAST(ROW_NUMBER() OVER (ORDER BY s.StagingID) + 
                    ISNULL((SELECT MAX(CAST(SUBSTRING(StudentCode, LEN(StudentCode) - 3, 4) AS INT)) FROM Student WHERE SchoolID = @SchoolID), 0) AS NVARCHAR), 4)),
                s.FullName, s.Gender, s.DateOfBirth,
                ISNULL(s.Age, DATEDIFF(YEAR, s.DateOfBirth, GETDATE())),
                s.BloodGroup, s.Category, s.Religion, s.Nationality, s.StudentAadhaar,
                s.MotherTongue, s.PresentAddress, s.PermanentAddress, s.District, s.State, s.Country,
                s.ParentMobile, s.AlternateNumber, s.Email,
                s.FatherName, s.FatherOccupation, s.FatherQualification, s.FatherAadhaar, s.FatherMobile,
                s.MotherName, s.MotherOccupation, s.MotherQualification, s.MotherAadhaar, s.MotherMobile,
                s.GuardianName, s.GuardianRelation, s.GuardianMobile,
                s.LastSchool, s.LastClass, s.TCNumber, s.MediumOfInstruction,
                s.AdmissionClass, s.Section, s.Stream, s.ModeOfAdmission, s.AdmissionDate,
                @CommittedBy, GETDATE(), 0
            FROM Student_Staging s
            WHERE s.ImportID = @ImportID 
                AND s.IsValid = 1
                AND s.StagingID NOT IN (
                    SELECT TOP (@CurrentBatch * @BatchSize) StagingID 
                    FROM Student_Staging 
                    WHERE ImportID = @ImportID AND IsValid = 1
                    ORDER BY StagingID
                )
            ORDER BY s.StagingID;
            
            SET @SuccessCount = @SuccessCount + @@ROWCOUNT;
            SET @CurrentBatch = @CurrentBatch + 1;
        END
        
        -- Count failed records
        SELECT @FailureCount = COUNT(*) FROM Student_Staging WHERE ImportID = @ImportID AND IsValid = 0;
        
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
        
        SET @ErrorMessage = 'Commit completed: ' + CAST(@SuccessCount AS NVARCHAR) + ' records inserted, ' + CAST(@FailureCount AS NVARCHAR) + ' failed';
        
        COMMIT TRANSACTION;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SET @ErrorMessage = ERROR_MESSAGE();
        SET @SuccessCount = 0;
        
        -- Update import log with error
        UPDATE DataImportLog
        SET Status = 'Failed',
            ImportCompletedAt = GETDATE(),
            Remarks = @ErrorMessage
        WHERE ImportID = @ImportID;
    END CATCH
END
GO

PRINT 'Proc_Student_Staging_Commit created successfully';
