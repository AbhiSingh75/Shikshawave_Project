-- Table to store admission instructions/next steps
CREATE TABLE AdmissionInstructions (
    InstructionID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL,
    InstructionTitle NVARCHAR(200) NOT NULL,
    InstructionText NVARCHAR(1000) NOT NULL,
    DisplayOrder INT DEFAULT 0,
    IsActive BIT DEFAULT 1,
    CreatedBy INT,
    CreatedAt DATETIME DEFAULT GETDATE(),
    ModifiedBy INT,
    ModifiedAt DATETIME,
    IsDeleted BIT DEFAULT 0,
    FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID)
);
GO
