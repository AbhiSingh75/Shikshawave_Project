# Session Timeout User Preference Implementation

## Overview
Users can now configure their auto-logout timeout. By default, all users have a 1-hour (60 minutes) session timeout.

## Database Changes

### SQL Script
Run: `database/add_session_timeout_column.sql`

Adds `SessionTimeoutMinutes INT NULL` column to UserMaster table:
- Default: 60 minutes (1 hour) for all users
- NULL = No auto-logout (stay logged in indefinitely)
- Integer value = Timeout in minutes (e.g., 30 = 30 minutes)

### user_sessions Table
- `expires_at` column stores the exact expiry datetime
- Calculated as: `current_time + (SessionTimeoutMinutes * 60 seconds)`
- Updated on login based on user's SessionTimeoutMinutes setting

## Code Changes

### 1. Decorator (`core/decorators.py`)
- Checks `expires_at` from `user_sessions` table
- If current time > expires_at, session is expired
- Updates `last_activity` on each request
- No longer calculates timeout - uses database expiry

### 2. Login Views (`core/views.py`)
- Loads `SessionTimeoutMinutes` from UserMaster during login
- Passes timeout to `_create_custom_session()` function
- Calculates `expires_at` = current_time + (timeout_minutes * 60)
- Stores in both session and user_sessions table
- Works for both password and OTP login
- Default: 60 minutes if not set

### 3. Session Creation (`_create_custom_session`)
- Accepts `timeout_minutes` parameter
- Defaults to 60 minutes if not provided
- Calculates `expires_at` and stores in user_sessions table
- Sets cookie max_age based on timeout

### 4. Settings Page
- URL: `/settings/`
- Template: `core/templates/core/user_settings.html`
- View: `core/user_settings_view.py`
- Users can:
  - Disable auto-logout (set to NULL)
  - Set custom timeout (5-1440 minutes)
  - Default shown: 60 minutes

## Usage

1. **Run SQL Script**:
   ```sql
   -- Execute database/add_session_timeout_column.sql
   -- This will:
   -- 1. Add SessionTimeoutMinutes column if not exists
   -- 2. Set default 60 minutes for all existing users
   ```

2. **User Access Settings**:
   - Navigate to `/settings/`
   - Choose timeout option
   - Save settings
   - New expiry will apply on next login

3. **Default Behavior**:
   - New users: 60 minutes (1 hour)
   - Existing users: 60 minutes (1 hour) after running SQL script
   - Can be changed per user via settings page
   - NULL = no timeout (stay logged in indefinitely)

## How It Works

1. **Login Process**:
   - User logs in (password or OTP)
   - System reads SessionTimeoutMinutes from UserMaster (default 60)
   - Creates session in user_sessions with expires_at = now + timeout
   - Stores timeout in Django session

2. **Request Validation**:
   - Decorator checks user_sessions.expires_at
   - If expires_at > current_time: session valid
   - If expires_at <= current_time: session expired, redirect to login
   - Updates last_activity on each valid request

3. **Timeout Update**:
   - User changes timeout in settings
   - New timeout saved to UserMaster.SessionTimeoutMinutes
   - Takes effect on next login (current session unaffected)

## Security Recommendation
For security, recommend users set timeout between 30-120 minutes rather than disabling it completely.
