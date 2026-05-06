-- Class Timetable Management System for Indian Schools
-- Drop existing tables if they exist
IF OBJECT_ID('TimetableSlot', 'U') IS NOT NULL DROP TABLE TimetableSlot;
IF OBJECT_ID('TimetableMaster', 'U') IS NOT NULL DROP TABLE TimetableMaster;
IF OBJECT_ID('PeriodMaster', 'U') IS NOT NULL DROP TABLE PeriodMaster;

-- Period Master: Defines time slots for periods
CREATE TABLE PeriodMaster (
    PeriodID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL FOREIGN KEY REFERENCES SchoolMaster(SchoolID),
    PeriodName NVARCHAR(50) NOT NULL, -- e.g., 'Period 1', 'Lunch Break', 'Assembly'
    PeriodType NVARCHAR(20) NOT NULL DEFAULT 'Class', -- 'Class', 'Break', 'Assembly', 'Activity'
    StartTime TIME NOT NULL,
    EndTime TIME NOT NULL,
    DisplayOrder INT NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

-- Timetable Master: Main timetable configuration
CREATE TABLE TimetableMaster (
    TimetableID INT IDENTITY(1,1) PRIMARY KEY,
    SchoolID INT NOT NULL FOREIGN KEY REFERENCES SchoolMaster(SchoolID),
    ClassID INT NOT NULL FOREIGN KEY REFERENCES ClassMaster(ClassID),
    SectionID INT FOREIGN KEY REFERENCES SectionMaster(SectionID),
    AcademicYear NVARCHAR(20) NOT NULL, -- e.g., '2024-25'
    EffectiveFrom DATE NOT NULL,
    EffectiveTo DATE,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

-- Timetable Slot: Individual period assignments
CREATE TABLE TimetableSlot (
    SlotID INT IDENTITY(1,1) PRIMARY KEY,
    TimetableID INT NOT NULL FOREIGN KEY REFERENCES TimetableMaster(TimetableID),
    DayOfWeek INT NOT NULL, -- 1=Monday, 2=Tuesday, ..., 6=Saturday
    PeriodID INT NOT NULL FOREIGN KEY REFERENCES PeriodMaster(PeriodID),
    SubjectID INT FOREIGN KEY REFERENCES SubjectMaster(SubjectID),
    TeacherID INT FOREIGN KEY REFERENCES UserMaster(UserID),
    RoomNumber NVARCHAR(20),
    Notes NVARCHAR(255),
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    CreatedAt DATETIME DEFAULT GETDATE(),
    UpdatedBy INT FOREIGN KEY REFERENCES UserMaster(UserID),
    UpdatedAt DATETIME,
    IsDeleted BIT NOT NULL DEFAULT 0
);

-- Create indexes for better performance
CREATE INDEX IX_PeriodMaster_School ON PeriodMaster(SchoolID, IsDeleted, IsActive);
CREATE INDEX IX_TimetableMaster_Class ON TimetableMaster(ClassID, SectionID, IsActive, IsDeleted);
CREATE INDEX IX_TimetableSlot_Timetable ON TimetableSlot(TimetableID, DayOfWeek, IsDeleted);
CREATE INDEX IX_TimetableSlot_Teacher ON TimetableSlot(TeacherID, DayOfWeek, IsDeleted);
