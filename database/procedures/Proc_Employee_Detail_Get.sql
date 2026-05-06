CREATE OR ALTER PROCEDURE Proc_Employee_Detail_Get
    @EmployeeCode NVARCHAR(50),
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @EmployeeId INT
    SELECT @EmployeeId=EmployeeID FROM EmployeeMaster WHERE EmployeeCode=@EmployeeCode

----Table 0 get Employee info    
    SELECT 
        e.EmployeeID,
        e.EmployeeCode,
        e.EmployeeName,
        e.Gender,
        e.DateOfBirth,
        e.DateOfJoining,
        e.MobileNo,
        e.Email,
        e.FatherOrHusbandName,
        e.NationalID,
        e.Religion,
        e.Education,
        e.BloodGroup,
        e.Experience,
        p.ProfileName,
        e.HomeAddress,
        e.Country,
        e.State,
        e.District,
        e.Pincode,
        e.EmploymentType,
        u.UserName AS CreatedBy,
        e.CreatedAt,
        CASE WHEN ISNULL(e.IsDeleted, 0) = 0 THEN 'Active' ELSE 'Inactive' END AS Status
    FROM EmployeeMaster e
    LEFT JOIN ProfileMaster p ON e.ProfileID = p.ProfileID
    LEFT JOIN UserMaster AS U ON U.UserID=e.CreatedBy
    WHERE e.EmployeeCode = @EmployeeCode 
        AND e.SchoolID = @SchoolID;

----Table 1 get salary breakup
    SELECT esb.EmployeeID, esb.ComponentID, sc.ComponentType, sc.ComponentName, esb.Amount 
    FROM EmployeeSalaryBreakup AS esb
    INNER JOIN SalaryComponentMaster AS SC ON ESB.ComponentID=sc.ComponentID
    WHERE esb.EmployeeID = @EmployeeId;

----Table 2 get Document upload
    SELECT DocumentID, EmployeeID, DocumentType, FilesName, FileExtension, FileContent 
    FROM EmployeeDocument
    WHERE EmployeeID = @EmployeeId;

END
