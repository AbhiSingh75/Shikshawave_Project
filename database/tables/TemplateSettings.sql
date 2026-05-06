-- Table to store template settings for schools
CREATE TABLE TemplateSettings (
    TemplateSettingID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL,
    TemplateType NVARCHAR(50) NOT NULL, -- 'AdmissionAcknowledgment', 'FeeReceipt', etc.
    TemplateName NVARCHAR(100) NOT NULL,
    TemplateFile NVARCHAR(200) NOT NULL, -- Template file name
    IsActive BIT DEFAULT 1,
    CreatedBy INT,
    CreatedAt DATETIME DEFAULT GETDATE(),
    ModifiedBy INT,
    ModifiedAt DATETIME,
    IsDeleted BIT DEFAULT 0,
    FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
    UNIQUE(SchoolID, TemplateType, IsDeleted)
);
GO

-- Insert default templates
INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateName, TemplateFile, IsActive, CreatedAt)
SELECT SchoolID, 'AdmissionAcknowledgment', 'Modern Gradient', 'admission_acknowledgment.html', 1, GETDATE()
FROM SchoolMaster WHERE IsDeleted = 0;
GO
