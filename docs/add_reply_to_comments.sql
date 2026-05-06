-- Add ReplyToCommentID column to TicketComments table for WhatsApp-style replies

ALTER TABLE TicketComments
ADD ReplyToCommentID BIGINT NULL;

-- Add foreign key constraint
ALTER TABLE TicketComments
ADD CONSTRAINT FK_TicketComments_ReplyTo FOREIGN KEY (ReplyToCommentID) 
REFERENCES TicketComments(CommentID);
