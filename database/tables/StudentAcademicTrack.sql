-- Student Academic Track Table
-- Tracks complete academic history: class, section, performance, promotions, transfers

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[StudentAcademicTrack]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[StudentAcademicTrack] (
        [TrackID] INT IDENTITY(1,1) PRIMARY KEY,
        [SchoolID] INT NOT NULL,
        [StudentID] INT NOT NULL,
        [AcademicYearID] INT NOT NULL,
        [ClassID] INT NOT NULL,
        [SectionID] INT NOT NULL,
        [RollNumber] NVARCHAR(20) NULL,
        [Status] NVARCHAR(20) NOT NULL DEFAULT 'Active', -- Active, Promoted, Detained, Transferred, Dropout, Completed
        [AttendancePercentage] DECIMAL(5,2) NULL,
        [OverallGrade] NVARCHAR(5) NULL,
        [OverallPercentage] DECIMAL(5,2) NULL,
        [Rank] INT NULL,
        [Remarks] NVARCHAR(500) NULL,
        [PromotedToClassID] INT NULL,
        [PromotedToSectionID] INT NULL,
        [PromotionDate] DATE NULL,
        [IsCurrent] BIT NOT NULL DEFAULT 1,
        [StartDate] DATE NOT NULL,
        [EndDate] DATE NULL,
        [CreatedBy] INT NULL,
        [CreatedAt] DATETIME DEFAULT GETDATE(),
        [UpdatedBy] INT NULL,
        [UpdatedAt] DATETIME NULL,
        [IsDeleted] BIT DEFAULT 0,
        
        CONSTRAINT FK_StudentAcademicTrack_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_StudentAcademicTrack_Student FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
        CONSTRAINT FK_StudentAcademicTrack_AcademicYear FOREIGN KEY (AcademicYearID) REFERENCES AcademicYear(AcademicYearID),
        CONSTRAINT FK_StudentAcademicTrack_Class FOREIGN KEY (ClassID) REFERENCES ClassMaster(ClassID),
        CONSTRAINT FK_StudentAcademicTrack_Section FOREIGN KEY (SectionID) REFERENCES SectionMaster(SectionID),
        CONSTRAINT FK_StudentAcademicTrack_PromotedClass FOREIGN KEY (PromotedToClassID) REFERENCES ClassMaster(ClassID),
        CONSTRAINT FK_StudentAcademicTrack_PromotedSection FOREIGN KEY (PromotedToSectionID) REFERENCES SectionMaster(SectionID),
        CONSTRAINT FK_StudentAcademicTrack_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID),
        CONSTRAINT FK_StudentAcademicTrack_UpdatedBy FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID)
    );

    CREATE INDEX IX_StudentAcademicTrack_Student ON StudentAcademicTrack(StudentID, IsCurrent);
    CREATE INDEX IX_StudentAcademicTrack_School_Year ON StudentAcademicTrack(SchoolID, AcademicYearID);
    CREATE INDEX IX_StudentAcademicTrack_Class_Section ON StudentAcademicTrack(ClassID, SectionID, IsCurrent);
    CREATE INDEX IX_StudentAcademicTrack_Status ON StudentAcademicTrack(Status, IsCurrent);

    PRINT 'StudentAcademicTrack table created successfully';
END
ELSE
BEGIN
    PRINT 'StudentAcademicTrack table already exists';
END
GO
