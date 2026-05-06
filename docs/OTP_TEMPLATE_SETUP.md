# OTP Template Management Setup

## Quick Installation

### Step 1: Create OTP Templates
```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\create_otp_templates.sql"
```

### Step 2: Add Menu
```bash
sqlcmd -S "Laptop-CHI-047\UAT_CURITICS" -d ShikshaWave -U ShikshaWave_Dev -P ShikshaWave_Dev_123 -i "database\add_otp_template_menu.sql"
```

### Step 3: Access Template Management
Navigate to: **Master Data → OTP Template Management**

## Features

### 3 Pre-built Templates
1. **Modern Gradient** (Default) - Purple/blue gradient with large OTP display
2. **Minimal Clean** - Simple, clean design with minimal styling
3. **Professional Blue** - Corporate blue theme

### School Name Integration
- Templates automatically show school name in subject if user belongs to a school
- Subject format: `{School Name} - Your Login OTP Code`
- Falls back to "ShikshaWave" for users without school

### Template Management UI
- Preview templates before activation
- One-click template switching
- Visual indication of active template

## Usage

1. Login as Super Admin or School Admin
2. Go to **Master Data → OTP Template Management**
3. Click **Preview** to see template design
4. Click **Activate** to set as active template
5. Test OTP login to see new template

## Template Placeholders

All templates support:
- `{{ user_name }}` - User's full name
- `{{ otp }}` - 6-digit OTP code
- `{{ valid_minutes }}` - Validity period (15 minutes)
- `{{ ip_address }}` - Login IP address
- `{{ school_name }}` - School name (if user has school)

## Files Created

1. `database/create_otp_templates.sql` - Creates 3 templates
2. `database/add_otp_template_menu.sql` - Adds menu item
3. `core/otp_template_views.py` - Template management views
4. `core/templates/core/otp_template_management.html` - UI
5. Updated `core/auth_utils.py` - School name support
6. Updated `core/urls.py` - Routes

## Verification

Check templates:
```sql
SELECT Code, SubjectTemplate, IsActive FROM EmailTemplate WHERE Code LIKE 'LOGIN_OTP%';
```

Expected: 3 templates, 1 active
