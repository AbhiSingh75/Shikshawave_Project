-- Verification Script for OTP Email Setup
-- Run this script to verify that LOGIN_OTP template is properly configured

PRINT '========================================';
PRINT 'OTP EMAIL SETUP VERIFICATION';
PRINT '========================================';
PRINT '';

-- Check 1: Verify LOGIN_OTP template exists
PRINT '1. Checking if LOGIN_OTP template exists...';
IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP')
BEGIN
    PRINT '   ✓ LOGIN_OTP template found';
    
    SELECT 
        'Template Details' AS CheckType,
        Code,
        CASE WHEN SchoolId IS NULL THEN 'Global (All Schools)' ELSE CAST(SchoolId AS NVARCHAR) END AS Scope,
        Language,
        SubjectTemplate,
        CASE WHEN IsActive = 1 THEN 'Active' ELSE 'Inactive' END AS Status,
        DefaultFrom,
        CreatedAt,
        UpdatedAt
    FROM EmailTemplate
    WHERE Code = 'LOGIN_OTP';
    
    -- Check if it's a global template
    IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND SchoolId IS NULL)
    BEGIN
        PRINT '   ✓ Template is GLOBAL (works for all schools)';
    END
    ELSE
    BEGIN
        PRINT '   ⚠ WARNING: Template is school-specific, not global!';
    END
    
    -- Check if it's active
    IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND IsActive = 1)
    BEGIN
        PRINT '   ✓ Template is ACTIVE';
    END
    ELSE
    BEGIN
        PRINT '   ✗ ERROR: Template is INACTIVE!';
    END
END
ELSE
BEGIN
    PRINT '   ✗ ERROR: LOGIN_OTP template NOT FOUND!';
    PRINT '   → Run create_login_otp_template.sql to create it';
END
PRINT '';

-- Check 2: Verify email settings in template
PRINT '2. Checking email configuration...';
SELECT 
    'Email Config' AS CheckType,
    DefaultFrom AS FromEmail,
    CASE WHEN Cc IS NULL THEN 'None' ELSE Cc END AS CC,
    CASE WHEN Bcc IS NULL THEN 'None' ELSE Bcc END AS BCC,
    Placeholders
FROM EmailTemplate
WHERE Code = 'LOGIN_OTP';
PRINT '';

-- Check 3: Check recent OTP records
PRINT '3. Checking recent OTP generation (last 10)...';
IF EXISTS (SELECT 1 FROM OTPRecords)
BEGIN
    SELECT TOP 10
        'Recent OTPs' AS CheckType,
        Identifier,
        Purpose,
        CASE WHEN IsUsed = 1 THEN 'Used' ELSE 'Unused' END AS Status,
        CASE 
            WHEN ExpiresAt < GETDATE() THEN 'Expired'
            ELSE 'Valid'
        END AS Validity,
        CreatedAt,
        ExpiresAt,
        IPAddress
    FROM OTPRecords
    ORDER BY CreatedAt DESC;
END
ELSE
BEGIN
    PRINT '   ℹ No OTP records found yet (this is normal for new setup)';
END
PRINT '';

-- Check 4: Check recent email tracking
PRINT '4. Checking recent email attempts (last 10)...';
IF EXISTS (SELECT 1 FROM EmailTracking WHERE EmailCode = 'LOGIN_OTP')
BEGIN
    SELECT TOP 10
        'Email Tracking' AS CheckType,
        ToEmail,
        Status,
        CASE WHEN LastError IS NULL THEN 'No errors' ELSE LastError END AS ErrorMessage,
        AttemptCount,
        CreatedAt,
        CompletedAt
    FROM EmailTracking
    WHERE EmailCode = 'LOGIN_OTP'
    ORDER BY CreatedAt DESC;
END
ELSE
BEGIN
    PRINT '   ℹ No LOGIN_OTP emails sent yet (this is normal for new setup)';
END
PRINT '';

-- Check 5: Verify users with email addresses
PRINT '5. Checking users with email addresses (for testing)...';
SELECT TOP 5
    'Test Users' AS CheckType,
    UserCode,
    UserName,
    Email,
    CASE WHEN IsActive = 1 THEN 'Active' ELSE 'Inactive' END AS Status
FROM UserMaster
WHERE Email IS NOT NULL 
  AND Email != ''
  AND IsDeleted = 0
ORDER BY CreatedAt DESC;
PRINT '';

-- Summary
PRINT '========================================';
PRINT 'VERIFICATION SUMMARY';
PRINT '========================================';

DECLARE @TemplateExists BIT = 0;
DECLARE @TemplateActive BIT = 0;
DECLARE @TemplateGlobal BIT = 0;

IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP')
    SET @TemplateExists = 1;

IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND IsActive = 1)
    SET @TemplateActive = 1;

IF EXISTS (SELECT 1 FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND SchoolId IS NULL)
    SET @TemplateGlobal = 1;

IF @TemplateExists = 1 AND @TemplateActive = 1 AND @TemplateGlobal = 1
BEGIN
    PRINT '✓ ALL CHECKS PASSED!';
    PRINT '✓ LOGIN_OTP template is properly configured';
    PRINT '✓ Ready to send OTP emails';
    PRINT '';
    PRINT 'Next Steps:';
    PRINT '1. Test OTP login from the application';
    PRINT '2. Check your email inbox (and spam folder)';
    PRINT '3. Monitor EmailTracking table for any errors';
END
ELSE
BEGIN
    PRINT '⚠ SETUP INCOMPLETE!';
    IF @TemplateExists = 0
        PRINT '✗ Template does not exist - Run create_login_otp_template.sql';
    IF @TemplateActive = 0
        PRINT '✗ Template is inactive - Update IsActive = 1';
    IF @TemplateGlobal = 0
        PRINT '✗ Template is not global - Set SchoolId = NULL';
END

PRINT '========================================';
GO
