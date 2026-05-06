# 🔧 OTP Email Fix - Quick Start

## Problem
**You were not receiving OTP emails during login.**

## Root Cause
The `LOGIN_OTP` email template was missing from the `EmailTemplate` table in your database.

## Solution (3 Simple Steps)

### Step 1: Create the Email Template
Run this command in your terminal:

```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\create_login_otp_template.sql"
```

**Expected Output:**
```
LOGIN_OTP global email template created successfully
Template Code: LOGIN_OTP
SchoolId: NULL (Global template for all schools)
Status: Active
```

### Step 2: Verify Setup
Run this command to verify everything is configured correctly:

```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "verify_otp_setup.sql"
```

**Expected Output:**
```
✓ ALL CHECKS PASSED!
✓ LOGIN_OTP template is properly configured
✓ Ready to send OTP emails
```

### Step 3: Test OTP Login
1. Open your application: http://localhost:8000/login
2. Enter your username or email
3. Click "Login with OTP"
4. Check your email inbox (and spam folder)
5. Enter the 6-digit OTP code
6. Login successfully! 🎉

## What Was Created

### 1. Email Template (Global)
- **Code**: `LOGIN_OTP`
- **Type**: Global (works for all schools)
- **Design**: Modern, professional HTML email with gradient colors
- **Features**:
  - Large, bold OTP display
  - Security warnings
  - Login details (IP address, time)
  - Mobile-responsive design

### 2. Template Features
✅ Beautiful gradient header (purple/blue)
✅ Highlighted OTP box with large font
✅ Security alert boxes
✅ Login details section
✅ Professional footer
✅ Works on all email clients

## Files Created

1. **database/create_login_otp_template.sql** - Creates the email template
2. **verify_otp_setup.sql** - Verifies the setup
3. **OTP_EMAIL_SETUP_GUIDE.md** - Detailed documentation
4. **OTP_FIX_README.md** - This quick start guide

## Quick Verification

Run this SQL query to check if template exists:

```sql
SELECT Code, SchoolId, IsActive, SubjectTemplate 
FROM EmailTemplate 
WHERE Code = 'LOGIN_OTP';
```

**Expected Result:**
- Code: `LOGIN_OTP`
- SchoolId: `NULL` (Global)
- IsActive: `1` (Active)
- SubjectTemplate: `ShikshaWave - Your Login OTP Code`

## Troubleshooting

### ❌ Still not receiving emails?

**Check 1**: Verify template is active
```sql
SELECT * FROM EmailTemplate WHERE Code = 'LOGIN_OTP' AND IsActive = 1;
```

**Check 2**: Check email tracking for errors
```sql
SELECT TOP 5 * FROM EmailTracking 
WHERE EmailCode = 'LOGIN_OTP' 
ORDER BY CreatedAt DESC;
```

**Check 3**: Verify your email address in UserMaster
```sql
SELECT UserCode, UserName, Email FROM UserMaster WHERE UserCode = 'YOUR_USERNAME';
```

**Check 4**: Check spam folder
- OTP emails might go to spam initially
- Mark as "Not Spam" to receive future emails in inbox

### ❌ Template not found error?

**Solution**: Run the create script again
```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\create_login_otp_template.sql"
```

## Email Preview

Your OTP email will look like this:

```
┌─────────────────────────────────────┐
│   🔐 ShikshaWave                    │
│   Secure Login Verification         │
├─────────────────────────────────────┤
│                                     │
│ Hello Abhishek Kumar,               │
│                                     │
│ Your OTP is:                        │
│                                     │
│  ┌─────────────────┐                │
│  │   1 2 3 4 5 6   │                │
│  └─────────────────┘                │
│                                     │
│ ⏱️ Valid for 15 minutes             │
│                                     │
│ 📍 Login Details:                   │
│ • IP: 192.168.1.100                 │
│ • Time: Just now                    │
│                                     │
│ 🛡️ Security Alert:                  │
│ If you didn't request this,         │
│ contact support immediately.        │
│                                     │
├─────────────────────────────────────┤
│ © 2024 ShikshaWave                  │
│ This is an automated email          │
└─────────────────────────────────────┘
```

## How It Works

```
User clicks "Login with OTP"
         ↓
System generates 6-digit OTP
         ↓
OTP saved in OTPRecords table (15 min expiry)
         ↓
Email sent using LOGIN_OTP template
         ↓
User receives beautiful HTML email
         ↓
User enters OTP
         ↓
Login successful! ✅
```

## Support

If you need help:
1. Check `OTP_EMAIL_SETUP_GUIDE.md` for detailed documentation
2. Run `verify_otp_setup.sql` to diagnose issues
3. Check EmailTracking table for error messages
4. Verify SMTP settings in `ShikshaWave/settings.py`

## Success Checklist

- [ ] Ran `create_login_otp_template.sql`
- [ ] Ran `verify_otp_setup.sql` - All checks passed
- [ ] Template exists in database
- [ ] Template is active (IsActive = 1)
- [ ] Template is global (SchoolId = NULL)
- [ ] Tested OTP login
- [ ] Received OTP email
- [ ] Successfully logged in with OTP

---

**Status**: ✅ Ready to Use
**Last Updated**: 2024
**Version**: 1.0

🎉 **Congratulations!** Your OTP email system is now fully configured and ready to use!
