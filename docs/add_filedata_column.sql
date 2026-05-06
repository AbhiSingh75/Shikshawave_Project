-- Add FileData column to TicketAttachments table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TicketAttachments') AND name = 'FileData')
BEGIN
    ALTER TABLE TicketAttachments
    ADD FileData VARBINARY(MAX) NULL;
    
    PRINT 'FileData column added successfully';
END
ELSE
BEGIN
    PRINT 'FileData column already exists';
END
