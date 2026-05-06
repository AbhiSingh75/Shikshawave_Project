-- Add AttachmentID column to TicketComments table
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('TicketComments') AND name = 'AttachmentID')
BEGIN
    ALTER TABLE TicketComments
    ADD AttachmentID BIGINT NULL;
    
    ALTER TABLE TicketComments
    ADD CONSTRAINT FK_Comment_Attachment FOREIGN KEY (AttachmentID) REFERENCES TicketAttachments(AttachmentID);
    
    PRINT 'AttachmentID column added to TicketComments successfully';
END
ELSE
BEGIN
    PRINT 'AttachmentID column already exists in TicketComments';
END
