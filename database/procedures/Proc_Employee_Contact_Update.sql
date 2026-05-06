CREATE OR ALTER PROCEDURE Proc_Employee_Contact_Update
    @EmployeeCode NVARCHAR(50),
    @SchoolID INT,
    @MobileNo NVARCHAR(15) = NULL,
    @Email NVARCHAR(255) = NULL,
    @HomeAddress NVARCHAR(500) = NULL,
    @Country NVARCHAR(100) = NULL,
    @State NVARCHAR(100) = NULL,
    @District NVARCHAR(100) = NULL,
    @Pincode NVARCHAR(10) = NULL,
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
            MobileNo = ISNULL(@MobileNo, MobileNo),
            Email = ISNULL(@Email, Email),
            HomeAddress = ISNULL(@HomeAddress, HomeAddress),
            Country = ISNULL(@Country, Country),
            State = ISNULL(@State, State),
            District = ISNULL(@District, District),
            Pincode = ISNULL(@Pincode, Pincode),
            UpdatedBy = @UpdatedBy,
            UpdatedAt = GETDATE()
        WHERE EmployeeID = @EmployeeID;
        
        COMMIT TRANSACTION;
        SELECT 'success' AS status, 'Contact information updated successfully' AS message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'error' AS status, ERROR_MESSAGE() AS message;
    END CATCH
END
