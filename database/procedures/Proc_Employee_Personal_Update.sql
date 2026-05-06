CREATE OR ALTER PROCEDURE Proc_Employee_Personal_Update
    @EmployeeCode NVARCHAR(50),
    @SchoolID INT,
    @EmployeeName NVARCHAR(255) = NULL,
    @Gender NVARCHAR(10) = NULL,
    @DateOfBirth DATE = NULL,
    @DateOfJoining DATE = NULL,
    @FatherOrHusbandName NVARCHAR(255) = NULL,
    @NationalID NVARCHAR(50) = NULL,
    @Religion NVARCHAR(50) = NULL,
    @Education NVARCHAR(255) = NULL,
    @BloodGroup NVARCHAR(10) = NULL,
    @Experience NVARCHAR(50) = NULL,
    @EmploymentType NVARCHAR(50) = NULL,
    @UpdatedBy INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @EmployeeID INT;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        SELECT @EmployeeID = EmployeeID 
        FROM EmployeeMaster 
        WHERE EmployeeCode = @EmployeeCode AND SchoolID = @SchoolID;
        
        IF @EmployeeID IS NULL
        BEGIN
            SELECT 'error' AS status, 'Employee not found' AS message;
            ROLLBACK TRANSACTION;
            RETURN;
        END
        
        UPDATE EmployeeMaster
        SET 
            EmployeeName = ISNULL(@EmployeeName, EmployeeName),
            Gender = ISNULL(@Gender, Gender),
            DateOfBirth = ISNULL(@DateOfBirth, DateOfBirth),
            DateOfJoining = ISNULL(@DateOfJoining, DateOfJoining),
            FatherOrHusbandName = ISNULL(@FatherOrHusbandName, FatherOrHusbandName),
            NationalID = ISNULL(@NationalID, NationalID),
            Religion = ISNULL(@Religion, Religion),
            Education = ISNULL(@Education, Education),
            BloodGroup = ISNULL(@BloodGroup, BloodGroup),
            Experience = ISNULL(@Experience, Experience),
            EmploymentType = ISNULL(@EmploymentType, EmploymentType),
            UpdatedBy = @UpdatedBy,
            UpdatedAt = GETDATE()
        WHERE EmployeeID = @EmployeeID;
        
        COMMIT TRANSACTION;
        SELECT 'success' AS status, 'Personal information updated successfully' AS message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'error' AS status, ERROR_MESSAGE() AS message;
    END CATCH
END
