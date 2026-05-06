# OTP Email Template Setup Guide

## Problem
You were not receiving OTP emails during login because the `LOGIN_OTP` email template was missing from the database.

## Solution
A global email template has been created for OTP emails that works across all schools.

## Installation Steps

### Step 1: Run the SQL Script
Execute the following SQL script to create the LOGIN_OTP template:

```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\create_login_otp_template.sql"
```

**OR** manually run the SQL file in SQL Server Management Studio:
- Open: `database\create_login_otp_template.sql`
- Execute against the `ShikshaWave` database

### Step 2: Verify Template Creation
Run this query to verify the template was created:

```sql
SELECT 
    Code,
    SchoolId,
    Language,
    SubjectTemplate,
    IsActive,
    CreatedAt
FROM EmailTemplate
WHERE Code = 'LOGIN_OTP';
```

Expected result:
- Code: `LOGIN_OTP`
- SchoolId: `NULL` (Global template)
- Language: `en`
- IsActive: `1`

### Step 3: Test OTP Login
1. Go to login page
2. Enter your username/email
3. Select "Login with OTP"
4. Click "Send OTP"
5. Check your email inbox (and spam folder)

## Email Template Features

### Visual Design
✅ **Modern gradient header** with purple/blue colors
✅ **Large, bold OTP display** in a highlighted box
✅ **Security warnings** with colored alert boxes
✅ **Login details** showing IP address and time
✅ **Mobile-responsive** design
✅ **Professional footer** with branding

### Template Details
- **Code**: `LOGIN_OTP`
- **Type**: Global (SchoolId = NULL)
- **Language**: English (en)
- **From**: ShikshaWave <shikshawaves@gmail.com>
- **Validity**: 15 minutes

### Placeholders Used
- `{{ user_name }}` - User's full name
- `{{ otp }}` - 6-digit OTP code
- `{{ valid_minutes }}` - OTP validity (15 minutes)
- `{{ ip_address }}` - Login IP address

## How It Works

### 1. OTP Generation Flow
```
User clicks "Login with OTP"
    ↓
System generates 6-digit OTP
    ↓
OTP stored in OTPRecords table
    ↓
Email sent using LOGIN_OTP template
    ↓
User receives email with OTP
    ↓
User enters OTP to login
```

### 2. Code Flow
**File**: `core/auth_utils.py`
- Function: `generate_and_store_otp()`
- Generates random 6-digit OTP
- Stores in database with 15-minute expiry
- Calls `send_email_by_code()` with template code `LOGIN_OTP`

**File**: `mail/utils.py`
- Function: `send_email_by_code()`
- Fetches template from EmailTemplate table
- Renders placeholders
- Sends email via SMTP

### 3. Email Settings
**File**: `ShikshaWave/settings.py`
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'shikshawaves@gmail.com'
EMAIL_HOST_PASSWORD = 'deon bwdb wwum imhj'  # App password
DEFAULT_FROM_EMAIL = 'ShikshaWave <shikshawaves@gmail.com>'
```

## Troubleshooting

### Issue: Still not receiving emails
**Check 1**: Verify template exists
```sql
SELECT * FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND IsActive = 1;
```

**Check 2**: Check email tracking
```sql
SELECT TOP 10 
    EmailCode,
    ToEmail,
    Status,
    LastError,
    CreatedAt
FROM EmailTracking
WHERE EmailCode = 'LOGIN_OTP'
ORDER BY CreatedAt DESC;
```

**Check 3**: Check application logs
- Look for errors in console output
- Search for: "Failed to send OTP email"

**Check 4**: Verify SMTP settings
- Test email credentials
- Check if Gmail app password is valid
- Ensure "Less secure app access" is enabled (if using regular password)

### Issue: Template not found error
**Error**: `No active email template found for code 'LOGIN_OTP'`

**Solution**: 
1. Run the SQL script again
2. Verify SchoolId is NULL (global template)
3. Verify IsActive = 1

### Issue: Email goes to spam
**Solution**:
1. Add shikshawaves@gmail.com to contacts
2. Mark email as "Not Spam"
3. Check spam folder during testing

## Database Tables

### EmailTemplate Table
Stores email templates with HTML/text content
```sql
CREATE TABLE EmailTemplate (
    Id INT PRIMARY KEY IDENTITY,
    Code NVARCHAR(100),
    SchoolId INT NULL,  -- NULL = Global template
    Language NVARCHAR(10),
    SubjectTemplate NVARCHAR(MAX),
    BodyTextTemplate NVARCHAR(MAX),
    BodyHtmlTemplate NVARCHAR(MAX),
    DefaultFrom NVARCHAR(255),
    IsActive BIT,
    CreatedAt DATETIME,
    UpdatedAt DATETIME
);
```

### EmailTracking Table
Tracks all sent emails for debugging
```sql
CREATE TABLE EmailTracking (
    EmailTrackingID INT PRIMARY KEY IDENTITY,
    EmailCode NVARCHAR(100),
    ToEmail NVARCHAR(500),
    Status NVARCHAR(50),  -- Pending, Sent, Failed
    LastError NVARCHAR(MAX),
    CreatedAt DATETIME,
    CompletedAt DATETIME
);
```

### OTPRecords Table
Stores generated OTPs
```sql
CREATE TABLE OTPRecords (
    Id INT PRIMARY KEY IDENTITY,
    Identifier NVARCHAR(255),
    OTP NVARCHAR(10),
    Purpose NVARCHAR(50),
    CreatedAt DATETIME,
    ExpiresAt DATETIME,
    IsUsed BIT,
    IPAddress NVARCHAR(45),
    DeviceInfo NVARCHAR(MAX)
);
```

## Testing Checklist

- [ ] SQL script executed successfully
- [ ] Template exists in EmailTemplate table
- [ ] Template is active (IsActive = 1)
- [ ] Template is global (SchoolId = NULL)
- [ ] SMTP settings are correct
- [ ] Test user has valid email address
- [ ] OTP email received in inbox
- [ ] Email displays correctly (HTML rendering)
- [ ] OTP code is visible and readable
- [ ] Can successfully login with OTP

## Support

If you continue to face issues:
1. Check EmailTracking table for error messages
2. Review application logs for exceptions
3. Verify email credentials in settings.py
4. Test with different email addresses
5. Check if firewall is blocking SMTP port 587

## Next Steps

After successful OTP email setup, you may want to:
1. Create similar templates for other email types
2. Add email templates for password reset
3. Implement email verification for new users
4. Add SMS OTP as backup option
5. Monitor email delivery rates

---
**Last Updated**: 2024
**Version**: 1.0
**Status**: Ready for Production
