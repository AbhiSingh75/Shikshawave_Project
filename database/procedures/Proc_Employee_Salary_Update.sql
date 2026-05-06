CREATE OR ALTER PROCEDURE Proc_Employee_Salary_Update
    @EmployeeCode NVARCHAR(50),
    @SchoolID INT,
    @SalaryData NVARCHAR(MAX), -- JSON array of {ComponentID, Amount}
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
        
        -- Parse JSON and update/insert salary components
        DECLARE @ComponentID INT, @Amount DECIMAL(18,2);
        
        DECLARE salary_cursor CURSOR FOR
        SELECT ComponentID, Amount
        FROM OPENJSON(@SalaryData)
        WITH (
            ComponentID INT '$.ComponentID',
            Amount DECIMAL(18,2) '$.Amount'
        );
        
        OPEN salary_cursor;
        FETCH NEXT FROM salary_cursor INTO @ComponentID, @Amount;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            IF EXISTS (SELECT 1 FROM EmployeeSalaryBreakup WHERE EmployeeID = @EmployeeID AND ComponentID = @ComponentID)
            BEGIN
                UPDATE EmployeeSalaryBreakup
                SET Amount = @Amount,
                    UpdatedBy = @UpdatedBy,
                    UpdatedAt = GETDATE()
                WHERE EmployeeID = @EmployeeID AND ComponentID = @ComponentID;
            END
            ELSE
            BEGIN
                INSERT INTO EmployeeSalaryBreakup (EmployeeID, ComponentID, Amount, CreatedBy, CreatedAt)
                VALUES (@EmployeeID, @ComponentID, @Amount, @UpdatedBy, GETDATE());
            END
            
            FETCH NEXT FROM salary_cursor INTO @ComponentID, @Amount;
        END
        
        CLOSE salary_cursor;
        DEALLOCATE salary_cursor;
        
        COMMIT TRANSACTION;
        SELECT 'success' AS status, 'Salary breakup updated successfully' AS message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 'error' AS status, ERROR_MESSAGE() AS message;
    END CATCH
END
