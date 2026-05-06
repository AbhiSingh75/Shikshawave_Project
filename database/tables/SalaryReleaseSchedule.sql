CREATE TABLE dbo.SalaryReleaseSchedule (
    ScheduleID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL,
    ReleaseDate DATE NOT NULL,
    SalaryMonth VARCHAR(7) NOT NULL,
    IsProcessed BIT DEFAULT 0,
    ProcessedAt DATETIME NULL,
    CreatedBy INT NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    IsDeleted BIT DEFAULT 0,
    FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
    FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID)
);
GO
