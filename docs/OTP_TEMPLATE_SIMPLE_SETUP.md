# OTP Template Management - Simple Setup

## Installation (1 Command)

```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\setup_otp_templates.sql"
```

## How It Works

**No EmailTemplate table needed!** Uses direct HTML template files like salary/timetable.

### Template Files
- `core/templates/emails/otp_modern_gradient.html` - Default
- `core/templates/emails/otp_minimal_clean.html`
- `core/templates/emails/otp_professional_blue.html`

### Storage
Uses `TemplateSettings` table:
- TemplateType: `OTP_EMAIL`
- TemplateFile: `modern_gradient` / `minimal_clean` / `professional_blue`

### School Name
Automatically shows school name in subject and body if user has school.

## Access
**Master Data → OTP Templates**

## Features
✅ 3 pre-built designs
✅ Preview before activation
✅ School name in subject
✅ No database templates needed
✅ Same approach as salary/timetable
