# Session Timeout - Quick Reference Guide

## Quick Summary
✅ Default timeout: **60 minutes (1 hour)**  
✅ Stored in: **UserMaster.SessionTimeoutMinutes**  
✅ Expiry stored in: **user_sessions.expires_at**  
✅ User configurable: **Yes, via /settings/**  

## Database Schema

### UserMaster Table
```sql
SessionTimeoutMinutes INT NULL
-- NULL = no timeout (stay logged in)
-- 60 = 1 hour (default)
-- Any integer = timeout in minutes
```

### user_sessions Table
```sql
expires_at DATETIME
-- Calculated as: GETDATE() + (SessionTimeoutMinutes * 60 seconds)
-- Checked on every request
```

## Key Files Modified

1. **database/add_session_timeout_column.sql**
   - Adds SessionTimeoutMinutes column
   - Sets default 60 minutes for all users

2. **core/views.py**
   - `_create_custom_session()`: Accepts timeout_minutes, calculates expires_at
   - `login_view()`: Reads timeout from DB, passes to session creation
   - `verify_otp_view()`: Same as login_view for OTP flow

3. **core/decorators.py**
   - `login_required()`: Checks expires_at from user_sessions table

4. **core/user_settings_view.py**
   - `user_settings()`: Allows users to change timeout

## Code Flow

### Login
```python
# 1. Read timeout from UserMaster
timeout_minutes = row[10]  # SessionTimeoutMinutes from query

# 2. Store in session (default 60 if NULL)
request.session['session_timeout_minutes'] = timeout_minutes if timeout_minutes is not None else 60

# 3. Create session with expiry
token = _create_custom_session(resp, row, request, timeout_minutes=timeout_minutes)
```

### Session Creation
```python
# Calculate expiry
if timeout_minutes is None:
    timeout_minutes = 60  # Default 1 hour
lifetime_seconds = timeout_minutes * 60

# Store in user_sessions
expires_at = GETDATE() + DATEADD(SECOND, lifetime_seconds, GETDATE())
```

### Request Validation
```python
# Check expiry from database
cursor.execute(
    "SELECT expires_at FROM user_sessions WHERE user_id = %s AND expires_at > GETDATE()",
    [user_id]
)
if not result:
    # Session expired, redirect to login
```

## User Settings

### URL
`/settings/`

### Options
- **Disabled**: Set SessionTimeoutMinutes = NULL (no timeout)
- **Custom**: Set SessionTimeoutMinutes = user's choice (5-1440 minutes)
- **Default**: 60 minutes shown if not set

### Update Flow
```python
# User changes timeout
new_timeout = 30  # or NULL for disabled

# Update database
UPDATE UserMaster SET SessionTimeoutMinutes = new_timeout WHERE UserID = user_id

# Update session
request.session['session_timeout_minutes'] = new_timeout

# Takes effect on next login
```

## SQL Queries

### Check User's Timeout
```sql
SELECT SessionTimeoutMinutes FROM UserMaster WHERE UserID = 123;
```

### Check Session Expiry
```sql
SELECT expires_at FROM user_sessions WHERE user_id = 123;
```

### Set Default for All Users
```sql
UPDATE UserMaster SET SessionTimeoutMinutes = 60 WHERE SessionTimeoutMinutes IS NULL;
```

### Disable Timeout for User
```sql
UPDATE UserMaster SET SessionTimeoutMinutes = NULL WHERE UserID = 123;
```

### Set Custom Timeout
```sql
UPDATE UserMaster SET SessionTimeoutMinutes = 30 WHERE UserID = 123;
```

## Testing Commands

### Test Default Timeout
```python
# Login and check session
user = UserMaster.objects.get(UserID=123)
print(user.SessionTimeoutMinutes)  # Should be 60

# Check user_sessions
cursor.execute("SELECT expires_at FROM user_sessions WHERE user_id = 123")
expires_at = cursor.fetchone()[0]
print(expires_at)  # Should be ~60 minutes from now
```

### Test Custom Timeout
```python
# Set custom timeout
cursor.execute("UPDATE UserMaster SET SessionTimeoutMinutes = 30 WHERE UserID = 123")

# Login again
# Check expires_at should be ~30 minutes from now
```

### Test No Timeout
```python
# Set NULL timeout
cursor.execute("UPDATE UserMaster SET SessionTimeoutMinutes = NULL WHERE UserID = 123")

# Login again
# Session should not expire
```

## Common Issues & Solutions

### Issue: Session expires immediately
**Solution**: Check if SessionTimeoutMinutes is 0 or very small
```sql
SELECT UserID, SessionTimeoutMinutes FROM UserMaster WHERE SessionTimeoutMinutes < 5;
```

### Issue: Session never expires
**Solution**: Check if SessionTimeoutMinutes is NULL
```sql
SELECT UserID, SessionTimeoutMinutes FROM UserMaster WHERE SessionTimeoutMinutes IS NULL;
```

### Issue: Different timeout than expected
**Solution**: Check user_sessions.expires_at
```sql
SELECT user_id, expires_at, DATEDIFF(MINUTE, GETDATE(), expires_at) as minutes_remaining
FROM user_sessions
WHERE user_id = 123;
```

### Issue: Timeout not updating
**Solution**: User needs to logout and login again for new timeout to take effect

## Best Practices

1. **Default Timeout**: Keep at 60 minutes for good security/usability balance
2. **Minimum Timeout**: Don't allow less than 5 minutes
3. **Maximum Timeout**: Don't allow more than 1440 minutes (24 hours)
4. **NULL Timeout**: Only for trusted users or development
5. **Session Cleanup**: Regularly clean expired sessions from user_sessions table

## Monitoring

### Check Active Sessions
```sql
SELECT COUNT(*) as active_sessions
FROM user_sessions
WHERE expires_at > GETDATE();
```

### Check Expired Sessions
```sql
SELECT COUNT(*) as expired_sessions
FROM user_sessions
WHERE expires_at <= GETDATE();
```

### Check User Timeout Settings
```sql
SELECT 
    SessionTimeoutMinutes,
    COUNT(*) as user_count
FROM UserMaster
WHERE IsDeleted = 0
GROUP BY SessionTimeoutMinutes
ORDER BY SessionTimeoutMinutes;
```

## Security Notes

- Session expiry is enforced by database, not client
- No clock skew issues between client and server
- Timeout is per-user, not global
- Users can't extend their own session without re-login
- Expired sessions are automatically rejected
