-- PostgreSQL Schema for ShikshaWave Home Page Modules

-- 1. SubscriptionPlan Table
CREATE TABLE IF NOT EXISTS SubscriptionPlan (
    PlanID SERIAL PRIMARY KEY,
    PlanName VARCHAR(100) NOT NULL,
    PlanCode VARCHAR(50) NOT NULL,
    PlanType VARCHAR(50),
    DurationMonths INT,
    Price DECIMAL(10, 2),
    DiscountPercent DECIMAL(5, 2),
    FinalPrice DECIMAL(10, 2) GENERATED ALWAYS AS (Price * (1 - DiscountPercent / 100)) STORED,
    MaxStudents INT,
    MaxTeachers INT,
    StorageLimitMB INT,
    IncludeReports BOOLEAN DEFAULT TRUE,
    IsTrialPlan BOOLEAN DEFAULT FALSE,
    GracePeriodDays INT DEFAULT 0,
    CreatedBy INT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedBy INT,
    UpdatedAt TIMESTAMP,
    DeletedBy INT,
    DeletedAt TIMESTAMP,
    IsDeleted BOOLEAN DEFAULT FALSE
);

-- 2. RegistrationDraft Table
CREATE TABLE IF NOT EXISTS RegistrationDraft (
    DraftID SERIAL PRIMARY KEY,
    SchoolName VARCHAR(200),
    RegistrationNumber VARCHAR(100),
    Address TEXT,
    CountryID INT,
    StateID INT,
    DistrictID INT,
    Pincode VARCHAR(10),
    Phone VARCHAR(20),
    Email VARCHAR(100),
    Website VARCHAR(200),
    BoardID INT,
    MediumID INT,
    EstablishDate DATE,
    PrincipalName VARCHAR(100),
    PrincipalEmail VARCHAR(100),
    PrincipalPhone VARCHAR(20),
    DirectorName VARCHAR(100),
    DirectorEmail VARCHAR(100),
    DirectorPhone VARCHAR(20),
    PlanID INT,
    SubscriptionStartDate DATE,
    Status VARCHAR(20) DEFAULT 'Pending',
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    IsProcessed BOOLEAN DEFAULT FALSE
);

-- 3. Geographical_Master Table
CREATE TABLE IF NOT EXISTS Geographical_Master (
    Geog_Id SERIAL PRIMARY KEY,
    Geog_Name VARCHAR(200) NOT NULL,
    Geog_Type VARCHAR(50) NOT NULL, -- 'Country', 'State', 'District'
    Geog_Parent_Id INT,
    IsDeleted BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Board_Master Table
CREATE TABLE IF NOT EXISTS Board_Master (
    BoardID SERIAL PRIMARY KEY,
    BoardName VARCHAR(100) NOT NULL,
    IsDeleted BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Medium_Master Table
CREATE TABLE IF NOT EXISTS Medium_Master (
    MediumID SERIAL PRIMARY KEY,
    MediumName VARCHAR(100) NOT NULL,
    IsDeleted BOOLEAN DEFAULT FALSE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Proc_SubscriptionPlan_Get Function
CREATE OR REPLACE FUNCTION Proc_SubscriptionPlan_Get(
    p_PlanID INT DEFAULT NULL,
    p_PlanType VARCHAR DEFAULT NULL,
    p_IncludeDeleted BOOLEAN DEFAULT FALSE,
    p_Search VARCHAR DEFAULT NULL
) 
RETURNS TABLE (
    PlanID INT,
    PlanName VARCHAR,
    PlanCode VARCHAR,
    PlanType VARCHAR,
    DurationMonths INT,
    Price DECIMAL,
    DiscountPercent DECIMAL,
    FinalPrice DECIMAL,
    MaxStudents INT,
    MaxTeachers INT,
    StorageLimitMB INT,
    IncludeReports BOOLEAN,
    IsTrialPlan BOOLEAN,
    CreatedAt TIMESTAMP,
    IsDeleted BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.PlanID, s.PlanName, s.PlanCode, s.PlanType, s.DurationMonths, 
        s.Price, s.DiscountPercent, s.FinalPrice, s.MaxStudents, 
        s.MaxTeachers, s.StorageLimitMB, s.IncludeReports, 
        s.IsTrialPlan, s.CreatedAt, s.IsDeleted
    FROM SubscriptionPlan s
    WHERE (p_PlanID IS NULL OR s.PlanID = p_PlanID)
      AND (p_PlanType IS NULL OR s.PlanType = p_PlanType)
      AND (p_IncludeDeleted OR NOT s.IsDeleted)
      AND (p_Search IS NULL OR s.PlanName ILIKE '%' || p_Search || '%' OR s.PlanCode ILIKE '%' || p_Search || '%')
    ORDER BY s.CreatedAt DESC;
END;
$$ LANGUAGE plpgsql;

-- 4. Proc_RegistrationDraft_Save Function
CREATE OR REPLACE FUNCTION Proc_RegistrationDraft_Save(
    p_SchoolName VARCHAR,
    p_RegistrationNumber VARCHAR,
    p_Address TEXT,
    p_CountryID INT,
    p_StateID INT,
    p_DistrictID INT,
    p_Pincode VARCHAR,
    p_Phone VARCHAR,
    p_Email VARCHAR,
    p_Website VARCHAR,
    p_BoardID INT,
    p_MediumID INT,
    p_EstablishDate DATE,
    p_PrincipalName VARCHAR,
    p_PrincipalEmail VARCHAR,
    p_PrincipalPhone VARCHAR,
    p_DirectorName VARCHAR,
    p_DirectorEmail VARCHAR,
    p_DirectorPhone VARCHAR,
    p_PlanID INT,
    p_SubscriptionStartDate DATE
) RETURNS INT AS $$
DECLARE
    v_DraftID INT;
BEGIN
    INSERT INTO RegistrationDraft (
        SchoolName, RegistrationNumber, Address, CountryID, StateID, DistrictID,
        Pincode, Phone, Email, Website, BoardID, MediumID, EstablishDate,
        PrincipalName, PrincipalEmail, PrincipalPhone, DirectorName, DirectorEmail,
        DirectorPhone, PlanID, SubscriptionStartDate
    ) VALUES (
        p_SchoolName, p_RegistrationNumber, p_Address, p_CountryID, p_StateID, p_DistrictID,
        p_Pincode, p_Phone, p_Email, p_Website, p_BoardID, p_MediumID, p_EstablishDate,
        p_PrincipalName, p_PrincipalEmail, p_PrincipalPhone, p_DirectorName, p_DirectorEmail,
        p_DirectorPhone, p_PlanID, p_SubscriptionStartDate
    ) RETURNING DraftID INTO v_DraftID;
    
    RETURN v_DraftID;
END;
$$ LANGUAGE plpgsql;

-- 5. ContactUs Table
CREATE TABLE IF NOT EXISTS ContactUs (
    ContactID SERIAL PRIMARY KEY,
    Email VARCHAR(100),
    Message TEXT,
    IPAddress VARCHAR(45),
    BrowserInfo VARCHAR(500),
    Location VARCHAR(200),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. sp_InsertContactUs Function
CREATE OR REPLACE FUNCTION sp_InsertContactUs(
    p_Email VARCHAR,
    p_Message_of_Request TEXT,
    p_IPAddress VARCHAR,
    p_BrowserInfo VARCHAR,
    p_Location VARCHAR
) RETURNS TABLE (
    Status INT,
    Message VARCHAR
) AS $$
BEGIN
    INSERT INTO ContactUs (
        Email, Message, IPAddress, BrowserInfo, Location, CreatedAt
    ) VALUES (
        p_Email, p_Message_of_Request, p_IPAddress, p_BrowserInfo, p_Location, CURRENT_TIMESTAMP
    );
    
    RETURN QUERY SELECT 1, 'Message sent successfully'::VARCHAR;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 0, SQLERRM::VARCHAR;
END;
$$ LANGUAGE plpgsql;
