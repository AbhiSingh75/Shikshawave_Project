-- Update Proc_Executive_set to include EmploymentType parameter
-- This script adds the @EmploymentType parameter to the existing stored procedure

-- First, check if the procedure exists and drop it
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'Proc_Executive_set')
BEGIN
    DROP PROCEDURE Proc_Executive_set;
END
GO

CREATE PROCEDURE Proc_Executive_set
    @SchoolID INT,
    @EmployeeName NVARCHAR(255),
    @MobileNo NVARCHAR(20) = NULL,
    @Email NVARCHAR(255) = NULL,
    @Password NVARCHAR(255),
    @DateOfBirth DATE = NULL,
    @ProfileId INT,
    @DateOfJoining DATE,
    @FatherOrHusbandName NVARCHAR(255) = NULL,
    @NationalID NVARCHAR(50) = NULL,
    @Gender NVARCHAR(10) = NULL,
    @Religion NVARCHAR(50) = NULL,
    @Education NVARCHAR(255) = NULL,
    @BloodGroup NVARCHAR(10) = NULL,
    @Country NVARCHAR(100) = NULL,
    @State NVARCHAR(100) = NULL,
    @District NVARCHAR(100) = NULL,
    @Pincode NVARCHAR(10) = NULL,
    @HomeAddress NVARCHAR(500) = NULL,
    @Experience NVARCHAR(MAX) = NULL,
    @EmploymentType NVARCHAR(50) = NULL,  -- NEW PARAMETER
    @CreatedBy INT,
    @SalaryComponents NVARCHAR(MAX) = NULL,
    @DocumentComponnents NVARCHAR(MAX) = NULL,
    @ResultJson NVARCHAR(MAX) OUTPUT,
    @UserCode NVARCHAR(50) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @EmployeeID INT;
    DECLARE @EmployeeCode NVARCHAR(50);
    DECLARE @Status NVARCHAR(50);
    DECLARE @Message NVARCHAR(500);
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Validate required fields
        IF @SchoolID IS NULL OR @SchoolID = 0
        BEGIN
            SET @Status = 'FAILED';
            SET @Message = 'School ID is required';
            SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '"}';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        IF @EmployeeName IS NULL OR LTRIM(RTRIM(@EmployeeName)) = ''
        BEGIN
            SET @Status = 'FAILED';
            SET @Message = 'Employee name is required';
            SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '"}';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        IF @ProfileId IS NULL OR @ProfileId = 0
        BEGIN
            SET @Status = 'FAILED';
            SET @Message = 'Profile/Role is required';
            SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '"}';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        IF @DateOfJoining IS NULL
        BEGIN
            SET @Status = 'FAILED';
            SET @Message = 'Date of joining is required';
            SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '"}';
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        -- Check if National ID already exists (if provided)
        IF @NationalID IS NOT NULL AND @NationalID != ''
        BEGIN
            IF EXISTS (SELECT 1 FROM EmployeeMaster WHERE NationalID = @NationalID AND SchoolID = @SchoolID AND IsDeleted = 0)
            BEGIN
                SET @Status = 'FAILED';
                SET @Message = 'National ID already exists in the system';
                SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '"}';
                ROLLBACK TRANSACTION;
                RETURN;
            END
        END
        
        -- Generate Employee Code
        DECLARE @MaxEmployeeID INT;
        SELECT @MaxEmployeeID = ISNULL(MAX(EmployeeID), 0) FROM EmployeeMaster WHERE SchoolID = @SchoolID;
        SET @EmployeeCode = 'EMP' + RIGHT('000000' + CAST(@MaxEmployeeID + 1 AS VARCHAR), 6);
        
        -- Insert into EmployeeMaster
        INSERT INTO EmployeeMaster (
            SchoolID, EmployeeCode, EmployeeName, MobileNo, Email, Password,
            DateOfBirth, ProfileId, DateOfJoining, FatherOrHusbandName, NationalID,
            Gender, Religion, Education, BloodGroup, Country, State, District,
            Pincode, HomeAddress, Experience, EmploymentType,
            CreatedBy, CreatedAt, IsDeleted
        )
        VALUES (
            @SchoolID, @EmployeeCode, @EmployeeName, @MobileNo, @Email, @Password,
            @DateOfBirth, @ProfileId, @DateOfJoining, @FatherOrHusbandName, @NationalID,
            @Gender, @Religion, @Education, @BloodGroup, @Country, @State, @District,
            @Pincode, @HomeAddress, @Experience, @EmploymentType,
            @CreatedBy, GETDATE(), 0
        );
        
        SET @EmployeeID = SCOPE_IDENTITY();
        
        -- Process Salary Components if provided
        IF @SalaryComponents IS NOT NULL AND @SalaryComponents != ''
        BEGIN
            DECLARE @SalaryTable TABLE (
                ComponentID INT,
                Amount DECIMAL(18, 2)
            );
            
            INSERT INTO @SalaryTable (ComponentID, Amount)
            SELECT 
                JSON_VALUE(value, '$.ComponentID') AS ComponentID,
                CAST(JSON_VALUE(value, '$.Amount') AS DECIMAL(18, 2)) AS Amount
            FROM OPENJSON(@SalaryComponents);
            
            -- Insert salary breakup records
            INSERT INTO EmployeeSalaryBreakup (
                EmployeeID, SchoolID, ComponentID, Amount, CreatedBy, CreatedAt, IsDeleted
            )
            SELECT 
                @EmployeeID, @SchoolID, ComponentID, Amount, @CreatedBy, GETDATE(), 0
            FROM @SalaryTable
            WHERE Amount > 0;
        END
        
        -- Process Documents if provided
        IF @DocumentComponnents IS NOT NULL AND @DocumentComponnents != ''
        BEGIN
            DECLARE @DocumentTable TABLE (
                DocumentType NVARCHAR(100),
                FilesName NVARCHAR(255),
                FileExtension NVARCHAR(10),
                FileContent NVARCHAR(MAX)
            );
            
            INSERT INTO @DocumentTable (DocumentType, FilesName, FileExtension, FileContent)
            SELECT 
                JSON_VALUE(value, '$.DocumentType') AS DocumentType,
                JSON_VALUE(value, '$.FilesName') AS FilesName,
                JSON_VALUE(value, '$.FileExtension') AS FileExtension,
                JSON_VALUE(value, '$.FileContent') AS FileContent
            FROM OPENJSON(@DocumentComponnents);
            
            -- Insert document records
            INSERT INTO EmployeeDocuments (
                EmployeeID, DocumentType, DocumentName, DocumentData, UploadDate, CreatedBy, CreatedAt, IsDeleted
            )
            SELECT 
                @EmployeeID,
                DocumentType,
                FilesName,
                CAST('' AS VARBINARY(MAX)) + CAST(FileContent AS VARBINARY(MAX)), -- Convert base64 to binary
                GETDATE(),
                @CreatedBy,
                GETDATE(),
                0
            FROM @DocumentTable;
        END
        
        -- Set output values
        SET @UserCode = @EmployeeCode;
        SET @Status = 'SUCCESS';
        SET @Message = 'Employee added successfully';
        SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + @Message + '","EmployeeID":' + CAST(@EmployeeID AS NVARCHAR) + ',"EmployeeCode":"' + @EmployeeCode + '"}';
        
        COMMIT TRANSACTION;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SET @Status = 'FAILED';
        SET @Message = ERROR_MESSAGE();
        SET @ResultJson = '{"Status":"' + @Status + '","Message":"' + REPLACE(@Message, '"', '\"') + '"}';
    END CATCH
END
GO
