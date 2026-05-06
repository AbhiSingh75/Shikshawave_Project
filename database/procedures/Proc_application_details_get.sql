-- Unified procedure for Application Details page
-- Replaces multiple queries with a single procedure call
CREATE PROCEDURE Proc_application_details_get
    @StudentCode NVARCHAR(50),
    @SchoolID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StudentID INT;
    
    -- Get StudentID first
    SELECT @StudentID = StudentID 
    FROM Student 
    WHERE StudentCode = @StudentCode 
      AND SchoolID = @SchoolID 
      AND ISNULL(IsDeleted, 0) = 0;
    
    IF @StudentID IS NULL
    BEGIN
        SELECT 'ERROR' AS Status, 'Student not found' AS Message;
        RETURN;
    END
    
    -- Result Set 1: Student Application Details
    SELECT 
        s.*,
        c.ClassName AS AdmissionClassName,
        sec.SectionName AS SectionName,
        country.Geog_Name AS CountryName,
        state.Geog_Name AS StateName,
        district.Geog_Name AS DistrictName
    FROM Student s
    LEFT JOIN ClassMaster c ON s.AdmissionClass = c.ClassID
    LEFT JOIN SectionMaster sec ON s.Section = sec.SectionID
    LEFT JOIN Geographical_Master country ON s.Country = country.Geog_Id
    LEFT JOIN Geographical_Master state ON s.State = state.Geog_Id
    LEFT JOIN Geographical_Master district ON s.District = district.Geog_Id
    WHERE s.StudentID = @StudentID;
    
    -- Result Set 2: Fee Structure
    SELECT 
        ft.FeeTypeName,
        sfa.FeeAmount,
        sfa.DiscountPercentage,
        sfa.FinalAmount
    FROM Student_Fee_Assignment sfa
    JOIN FeeType_Master ft ON sfa.FeeTypeId = ft.FeeTypeId
    WHERE sfa.StudentID = @StudentID 
      AND ISNULL(sfa.IsDeleted, 0) = 0
    ORDER BY ft.FeeTypeName;
    
    -- Result Set 3: Documents
    SELECT 
        DocumentID,
        DocumentType,
        DocumentName,
        DocumentData,
        UploadDate
    FROM StudentDocuments
    WHERE StudentID = @StudentID 
      AND ISNULL(IsDeleted, 0) = 0
    ORDER BY UploadDate DESC;
    
END