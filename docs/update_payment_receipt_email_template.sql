-- Update PAYMENT_RECEIPT email template to use full receipt HTML

UPDATE EmailTemplate
SET BodyHtmlTemplate = '{{ receipt_html }}',
    UpdatedAt = GETDATE()
WHERE Code = 'PAYMENT_RECEIPT' 
  AND SchoolId IS NULL;

PRINT 'PAYMENT_RECEIPT email template updated to use full receipt HTML';
