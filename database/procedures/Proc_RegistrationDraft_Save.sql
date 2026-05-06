CREATE PROCEDURE Proc_RegistrationDraft_Save
    @SchoolName NVARCHAR(200),
    @RegistrationNumber NVARCHAR(100),
    @Address NVARCHAR(500),
    @CountryID INT,
    @StateID INT,
    @DistrictID INT,
    @Pincode NVARCHAR(10),
    @Phone NVARCHAR(20),
    @Email NVARCHAR(100),
    @Website NVARCHAR(200),
    @BoardID INT,
    @MediumID INT,
    @EstablishDate DATE,
    @PrincipalName NVARCHAR(100),
    @PrincipalEmail NVARCHAR(100),
    @PrincipalPhone NVARCHAR(20),
    @DirectorName NVARCHAR(100),
    @DirectorEmail NVARCHAR(100),
    @DirectorPhone NVARCHAR(20),
    @PlanID INT,
    @SubscriptionStartDate DATE
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO RegistrationDraft (
        SchoolName, RegistrationNumber, Address, CountryID, StateID, DistrictID,
        Pincode, Phone, Email, Website, BoardID, MediumID, EstablishDate,
        PrincipalName, PrincipalEmail, PrincipalPhone,
        DirectorName, DirectorEmail, DirectorPhone,
        PlanID, SubscriptionStartDate
    )
    VALUES (
        @SchoolName, @RegistrationNumber, @Address, @CountryID, @StateID, @DistrictID,
        @Pincode, @Phone, @Email, @Website, @BoardID, @MediumID, @EstablishDate,
        @PrincipalName, @PrincipalEmail, @PrincipalPhone,
        @DirectorName, @DirectorEmail, @DirectorPhone,
        @PlanID, @SubscriptionStartDate
    );
    
    SELECT 'SUCCESS' AS Status, SCOPE_IDENTITY() AS DraftID, 'Registration draft saved successfully' AS Message;
END
