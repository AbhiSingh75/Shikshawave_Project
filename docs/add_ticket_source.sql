-- Add Sources column to TicketMaster table
-- Sources: Website (default), Email, Call

ALTER TABLE TicketMaster
ADD Sources NVARCHAR(20) DEFAULT 'Website' NOT NULL;

-- Add check constraint to ensure valid values
ALTER TABLE TicketMaster
ADD CONSTRAINT CK_TicketMaster_Source CHECK (Sources IN ('Website', 'Email', 'Call'));
