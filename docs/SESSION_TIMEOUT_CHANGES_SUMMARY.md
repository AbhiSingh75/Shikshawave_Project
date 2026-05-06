# Session Timeout Implementation - Changes Summary

## Overview
Implemented configurable user session timeout with default 1-hour expiry. Users can customize their timeout via settings page, and the system uses database-stored expiry dates for accurate session management.

## Changes Made

### 1. Database Changes (`database/add_session_timeout_column.sql`)
**What Changed:**
- Added `SessionTimeoutMinutes INT NULL` column to UserMaster table
- Set default value of 60 minutes for all existing users
- Set default value of 60 minutes for any users without a timeout value

**Impact:**
- All users now have a 1-hour default session timeout
- Existing users automatically get the default timeout
- New users will get 60 minutes by default

### 2. Session Creation (`core/views.py` - `_create_custom_session`)
**What Changed:**
- Changed function signature to accept `timeout_minutes` parameter
- Removed hardcoded `lifetime_seconds` parameter
- Now calculates `expires_at` based on user's SessionTimeoutMinutes
- Defaults to 60 minutes if timeout_minutes is None

**Impact:**
- Session expiry is now based on user preference
- Each user can have different session timeout
- Expiry date is stored in user_sessions table

### 3. Login Process (`core/views.py` - `login_view`)
**What Changed:**
- Password login now reads SessionTimeoutMinutes from database
- Passes timeout_minutes to `_create_custom_session()`
- Stores timeout in session with default of 60 if NULL
- Logs timeout value for debugging

**Impact:**
- User's timeout preference is applied on login
- Session expiry is calculated correctly
- Default 60 minutes if user hasn't set a preference

### 4. OTP Verification (`core/views.py` - `verify_otp_view`)
**What Changed:**
- Both OTP verification paths now read SessionTimeoutMinutes
- Pass timeout_minutes to `_create_custom_session()`
- Store timeout in session with default of 60 if NULL

**Impact:**
- OTP login also respects user's timeout preference
- Consistent behavior between password and OTP login

### 5. Session Validation (`core/decorators.py` - `login_required`)
**What Changed:**
- Removed client-side timeout calculation
- Now checks `expires_at` from user_sessions table
- Compares expires_at with current database time
- Updates last_activity on each valid request
- Better error handling with try-catch

**Impact:**
- More accurate session expiry checking
- No clock skew issues between client and server
- Session expiry is enforced by database
- Automatic logout when session expires

### 6. User Settings (`core/user_settings_view.py`)
**What Changed:**
- Default timeout_minutes to 60 if not set
- Store timeout with default of 60 in session
- Display 60 minutes as default in UI

**Impact:**
- Users see 60 minutes as default
- Consistent default across the application

## How It Works Now

### Login Flow:
1. User logs in (password or OTP)
2. System reads SessionTimeoutMinutes from UserMaster (default: 60)
3. Calculates expires_at = current_time + (timeout_minutes * 60 seconds)
4. Stores expires_at in user_sessions table
5. Sets session cookie with appropriate max_age

### Request Validation:
1. User makes a request
2. Decorator checks user_sessions.expires_at
3. If expires_at > current_time: session valid, update last_activity
4. If expires_at <= current_time: session expired, redirect to login

### Timeout Update:
1. User changes timeout in settings page
2. New timeout saved to UserMaster.SessionTimeoutMinutes
3. Takes effect on next login (current session unaffected)

## Default Behavior

- **New Users**: 60 minutes (1 hour)
- **Existing Users**: 60 minutes (1 hour) after running SQL script
- **NULL Value**: No timeout (stay logged in indefinitely)
- **Custom Values**: User can set any value between 5-1440 minutes

## Testing Checklist

- [ ] Run SQL script to add column and set defaults
- [ ] Test password login with default timeout
- [ ] Test OTP login with default timeout
- [ ] Test session expiry after 60 minutes
- [ ] Test changing timeout in settings
- [ ] Test NULL timeout (no expiry)
- [ ] Test custom timeout values
- [ ] Verify expires_at is stored correctly in user_sessions
- [ ] Verify last_activity is updated on requests
- [ ] Test automatic logout on expiry

## Deployment Steps

1. **Backup Database**
   ```sql
   -- Backup UserMaster and user_sessions tables
   ```

2. **Run SQL Script**
   ```sql
   -- Execute: database/add_session_timeout_column.sql
   ```

3. **Deploy Code Changes**
   - Deploy updated views.py
   - Deploy updated decorators.py
   - Deploy updated user_settings_view.py

4. **Verify Deployment**
   - Check all users have SessionTimeoutMinutes = 60
   - Test login and verify expires_at in user_sessions
   - Test session expiry after 60 minutes

5. **Monitor**
   - Check logs for any session-related errors
   - Monitor user feedback on timeout behavior

## Rollback Plan

If issues occur:

1. **Database Rollback**
   ```sql
   -- Set all users back to NULL (no timeout)
   UPDATE UserMaster SET SessionTimeoutMinutes = NULL;
   ```

2. **Code Rollback**
   - Revert to previous version of views.py
   - Revert to previous version of decorators.py
   - Revert to previous version of user_settings_view.py

## Notes

- Session timeout is enforced by database, not client-side calculation
- More accurate and secure than previous implementation
- Users can customize their timeout via settings page
- Default 60 minutes provides good balance between security and usability
- NULL value allows users to stay logged in indefinitely if needed
