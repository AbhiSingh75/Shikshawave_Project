-- =============================================
-- ShikshaWave Universal Notification System
-- Database Schema for SQL Server
-- =============================================

-- Notification Type Master
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationTypeMaster')
BEGIN
    CREATE TABLE NotificationTypeMaster (
        TypeID INT PRIMARY KEY IDENTITY(1,1),
        TypeName NVARCHAR(50) NOT NULL UNIQUE,
        TypeCategory NVARCHAR(50) NOT NULL, -- Ticket, Fee, Timetable, Attendance, Exam, General
        IconClass NVARCHAR(50) NULL,
        ColorCode NVARCHAR(20) NULL,
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE()
    );
END
GO

-- Notification Master
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationMaster')
BEGIN
    CREATE TABLE NotificationMaster (
        NotificationID BIGINT PRIMARY KEY IDENTITY(1,1),
        SchoolID INT NOT NULL,
        TypeID INT NOT NULL,
        Title NVARCHAR(255) NOT NULL,
        Message NVARCHAR(MAX) NOT NULL,
        TargetURL NVARCHAR(500) NULL,
        TargetModule NVARCHAR(50) NULL, -- tickets, fees, timetable, attendance, exams
        TargetRecordID BIGINT NULL,
        CreatedByUserID INT NOT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        ExpiresAt DATETIME NULL,
        IsDeleted BIT DEFAULT 0,
        CONSTRAINT FK_Notification_School FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
        CONSTRAINT FK_Notification_Type FOREIGN KEY (TypeID) REFERENCES NotificationTypeMaster(TypeID),
        CONSTRAINT FK_Notification_CreatedBy FOREIGN KEY (CreatedByUserID) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_Notification_School ON NotificationMaster(SchoolID);
    CREATE INDEX IX_Notification_Type ON NotificationMaster(TypeID);
    CREATE INDEX IX_Notification_CreatedAt ON NotificationMaster(CreatedAt DESC);
END
GO

-- Notification Recipients (User-specific notifications)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'NotificationRecipients')
BEGIN
    CREATE TABLE NotificationRecipients (
        RecipientID BIGINT PRIMARY KEY IDENTITY(1,1),
        NotificationID BIGINT NOT NULL,
        UserID INT NOT NULL,
        IsRead BIT DEFAULT 0,
        ReadAt DATETIME NULL,
        IsDeleted BIT DEFAULT 0,
        CreatedAt DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_Recipient_Notification FOREIGN KEY (NotificationID) REFERENCES NotificationMaster(NotificationID),
        CONSTRAINT FK_Recipient_User FOREIGN KEY (UserID) REFERENCES UserMaster(UserID)
    );
    
    CREATE INDEX IX_Recipient_User ON NotificationRecipients(UserID, IsRead);
    CREATE INDEX IX_Recipient_Notification ON NotificationRecipients(NotificationID);
    CREATE UNIQUE INDEX UX_Recipient_User_Notification ON NotificationRecipients(NotificationID, UserID);
END
GO

-- Insert Default Notification Types
IF NOT EXISTS (SELECT * FROM NotificationTypeMaster WHERE TypeName = 'TicketCreated')
BEGIN
    INSERT INTO NotificationTypeMaster (TypeName, TypeCategory, IconClass, ColorCode) VALUES
    ('TicketCreated', 'Ticket', 'fa-ticket', '#3b82f6'),
    ('TicketUpdated', 'Ticket', 'fa-ticket', '#f59e0b'),
    ('TicketAssigned', 'Ticket', 'fa-user-check', '#8b5cf6'),
    ('TicketChatMessage', 'Ticket', 'fa-comment', '#10b981'),
    ('TicketStatusChanged', 'Ticket', 'fa-exchange-alt', '#6366f1'),
    ('FeeReminder', 'Fee', 'fa-money-bill-wave', '#ef4444'),
    ('FeePaymentConfirmed', 'Fee', 'fa-check-circle', '#10b981'),
    ('FeeDueDate', 'Fee', 'fa-calendar-exclamation', '#f59e0b'),
    ('TimetableReleased', 'Timetable', 'fa-calendar-alt', '#3b82f6'),
    ('TimetableUpdated', 'Timetable', 'fa-calendar-edit', '#f59e0b'),
    ('AttendanceSummary', 'Attendance', 'fa-clipboard-check', '#10b981'),
    ('AttendanceLow', 'Attendance', 'fa-exclamation-triangle', '#ef4444'),
    ('ExamScheduled', 'Exam', 'fa-file-alt', '#8b5cf6'),
    ('ExamResultPublished', 'Exam', 'fa-trophy', '#10b981'),
    ('GeneralAnnouncement', 'General', 'fa-bullhorn', '#6366f1'),
    ('SystemAlert', 'General', 'fa-bell', '#ef4444');
END
GO

PRINT 'Notification System Tables Created Successfully';
