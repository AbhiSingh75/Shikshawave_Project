-- =============================================
-- Ticket Management System - Database Schema
-- =============================================

-- Drop existing tables if they exist
IF OBJECT_ID('TicketActivityLog', 'U') IS NOT NULL DROP TABLE TicketActivityLog;
IF OBJECT_ID('TicketAttachments', 'U') IS NOT NULL DROP TABLE TicketAttachments;
IF OBJECT_ID('TicketComments', 'U') IS NOT NULL DROP TABLE TicketComments;
IF OBJECT_ID('TicketMaster', 'U') IS NOT NULL DROP TABLE TicketMaster;
IF OBJECT_ID('TicketCategory', 'U') IS NOT NULL DROP TABLE TicketCategory;
IF OBJECT_ID('TicketPriority', 'U') IS NOT NULL DROP TABLE TicketPriority;

-- =============================================
-- TicketCategory Table
-- =============================================
CREATE TABLE TicketCategory (
    CategoryID INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(255) NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    CreatedBy INT NULL,
    IsDeleted BIT DEFAULT 0
);

-- =============================================
-- TicketPriority Table
-- =============================================
CREATE TABLE TicketPriority (
    PriorityID INT IDENTITY(1,1) PRIMARY KEY,
    PriorityName NVARCHAR(50) NOT NULL,
    PriorityLevel INT NOT NULL, -- 1=Low, 2=Medium, 3=High, 4=Critical
    ColorCode NVARCHAR(20) NULL,
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    IsDeleted BIT DEFAULT 0
);

-- =============================================
-- TicketMaster Table
-- =============================================
CREATE TABLE TicketMaster (
    TicketID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TicketNumber AS ('TKT-' + RIGHT('000000' + CAST(TicketID AS VARCHAR(10)), 6)) PERSISTED,
    SchoolID INT NOT NULL,
    CreatedByUserID INT NOT NULL,
    AssignedToUserID INT NULL,
    CategoryID INT NOT NULL,
    Priority INT NOT NULL DEFAULT 2, -- 1=Low, 2=Medium, 3=High, 4=Critical
    Subject NVARCHAR(255) NOT NULL,
    Description NVARCHAR(MAX) NOT NULL,
    CurrentStatus VARCHAR(20) NOT NULL DEFAULT 'Open', -- Open, In Progress, Resolved, Closed, Reopened
    AttachmentPath NVARCHAR(500) NULL,
    ReopenedCount INT DEFAULT 0,
    CreatedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    UpdatedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    ResolvedAt DATETIMEOFFSET NULL,
    ClosedAt DATETIMEOFFSET NULL,
    IsDeleted BIT DEFAULT 0,
    CONSTRAINT FK_Ticket_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
    CONSTRAINT FK_Ticket_CreatedBy FOREIGN KEY (CreatedByUserID) REFERENCES UserMaster(UserID),
    CONSTRAINT FK_Ticket_AssignedTo FOREIGN KEY (AssignedToUserID) REFERENCES UserMaster(UserID),
    CONSTRAINT FK_Ticket_Category FOREIGN KEY (CategoryID) REFERENCES TicketCategory(CategoryID),
    CONSTRAINT CHK_Ticket_Status CHECK (CurrentStatus IN ('Open', 'In Progress', 'Resolved', 'Closed', 'Reopened')),
    CONSTRAINT CHK_Ticket_Priority CHECK (Priority BETWEEN 1 AND 4)
);

-- =============================================
-- TicketActivityLog Table
-- =============================================
CREATE TABLE TicketActivityLog (
    ActivityID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TicketID BIGINT NOT NULL,
    ActionByUserID INT NOT NULL,
    ActionType VARCHAR(50) NOT NULL, -- Created, Assigned, StatusChanged, Commented, Reopened, Closed
    OldStatus VARCHAR(20) NULL,
    NewStatus VARCHAR(20) NULL,
    OldAssignee INT NULL,
    NewAssignee INT NULL,
    Comment NVARCHAR(MAX) NULL,
    Timestamp DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    CONSTRAINT FK_Activity_Ticket FOREIGN KEY (TicketID) REFERENCES TicketMaster(TicketID),
    CONSTRAINT FK_Activity_User FOREIGN KEY (ActionByUserID) REFERENCES UserMaster(UserID)
);

-- =============================================
-- TicketComments Table
-- =============================================
CREATE TABLE TicketComments (
    CommentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TicketID BIGINT NOT NULL,
    CommentByUserID INT NOT NULL,
    CommentText NVARCHAR(MAX) NOT NULL,
    IsInternal BIT DEFAULT 0, -- Internal notes visible only to support/admin
    CreatedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    IsDeleted BIT DEFAULT 0,
    CONSTRAINT FK_Comment_Ticket FOREIGN KEY (TicketID) REFERENCES TicketMaster(TicketID),
    CONSTRAINT FK_Comment_User FOREIGN KEY (CommentByUserID) REFERENCES UserMaster(UserID)
);

-- =============================================
-- TicketAttachments Table
-- =============================================
CREATE TABLE TicketAttachments (
    AttachmentID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TicketID BIGINT NOT NULL,
    FileName NVARCHAR(255) NOT NULL,
    FilePath NVARCHAR(500) NOT NULL,
    FileSize BIGINT NULL,
    ContentType NVARCHAR(100) NULL,
    UploadedByUserID INT NOT NULL,
    UploadedAt DATETIMEOFFSET DEFAULT SYSDATETIMEOFFSET(),
    IsDeleted BIT DEFAULT 0,
    CONSTRAINT FK_Attachment_Ticket FOREIGN KEY (TicketID) REFERENCES TicketMaster(TicketID),
    CONSTRAINT FK_Attachment_User FOREIGN KEY (UploadedByUserID) REFERENCES UserMaster(UserID)
);

-- =============================================
-- Indexes for Performance
-- =============================================
CREATE NONCLUSTERED INDEX IX_Ticket_SchoolID ON TicketMaster(SchoolID) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Ticket_AssignedTo ON TicketMaster(AssignedToUserID) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Ticket_Status ON TicketMaster(CurrentStatus) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Ticket_CreatedAt ON TicketMaster(CreatedAt DESC) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Ticket_CreatedBy ON TicketMaster(CreatedByUserID) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Activity_Ticket ON TicketActivityLog(TicketID, Timestamp DESC);
CREATE NONCLUSTERED INDEX IX_Comment_Ticket ON TicketComments(TicketID, CreatedAt DESC) WHERE IsDeleted = 0;
CREATE NONCLUSTERED INDEX IX_Attachment_Ticket ON TicketAttachments(TicketID) WHERE IsDeleted = 0;

-- =============================================
-- Seed Data - Categories
-- =============================================
INSERT INTO TicketCategory (CategoryName, Description, IsActive) VALUES
('Technical Issue', 'Software, hardware, or system-related problems', 1),
('Account Access', 'Login, password, or permission issues', 1),
('Feature Request', 'Request for new features or enhancements', 1),
('Data Issue', 'Problems with data accuracy or missing information', 1),
('Training', 'Questions about how to use the system', 1),
('Bug Report', 'Software bugs or unexpected behavior', 1),
('Other', 'General inquiries or other issues', 1);

-- =============================================
-- Seed Data - Priorities
-- =============================================
INSERT INTO TicketPriority (PriorityName, PriorityLevel, ColorCode, IsActive) VALUES
('Low', 1, '#10b981', 1),
('Medium', 2, '#f59e0b', 1),
('High', 3, '#ef4444', 1),
('Critical', 4, '#dc2626', 1);

PRINT 'Ticket Management System schema created successfully';
