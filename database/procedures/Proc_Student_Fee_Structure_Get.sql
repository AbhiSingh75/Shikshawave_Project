-- Procedure to get student fee structure with discounts
CREATE OR ALTER PROCEDURE Proc_Student_Fee_Structure_Get
    @StudentID INT = NULL,
    @StudentCode NVARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ActualStudentID INT;
    
    -- Get StudentID if StudentCode is provided
    IF @StudentCode IS NOT NULL
    BEGIN
        SELECT @ActualStudentID = StudentID 
        FROM Student 
        WHERE StudentCode = @StudentCode 
          AND ISNULL(IsDeleted, 0) = 0;
    END
    ELSE
    BEGIN
        SET @ActualStudentID = @StudentID;
    END
    
    -- Return fee structure with all details
    SELECT 
        sfa.FeeAssignmentID,
        sfa.StudentID,
        s.StudentCode,
        s.FullName AS student_name,
        sfa.FeeTypeId,
        ft.FeeTypeName AS fee_name,
        sfa.FeeAmount AS default_amount,
        sfa.DiscountPercentage AS discount_percentage,
        sfa.FinalAmount AS amount,
        sfa.FeeMonth,
        sfa.AssignedDate,
        sfa.SchoolId,
        sch.SchoolName AS school_name
    FROM Student_Fee_Assignment sfa
    INNER JOIN Student s ON sfa.StudentID = s.StudentID
    INNER JOIN FeeType_Master ft ON sfa.FeeTypeId = ft.FeeTypeId
    LEFT JOIN SchoolMaster sch ON sfa.SchoolId = sch.SchoolID
    WHERE sfa.StudentID = @ActualStudentID
      AND ISNULL(sfa.IsDeleted, 0) = 0
    ORDER BY sfa.AssignedDate DESC, ft.FeeTypeName;
END
GO
