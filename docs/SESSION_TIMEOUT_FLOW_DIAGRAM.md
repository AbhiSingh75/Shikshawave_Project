# Session Timeout - Complete Flow Diagram

## 🔄 Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LOGIN                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. User enters credentials (Password or OTP)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. System validates credentials                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Read SessionTimeoutMinutes from UserMaster                   │
│     - If NULL: No timeout                                        │
│     - If set: Use that value                                     │
│     - Default: 60 minutes                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Calculate expires_at                                         │
│     expires_at = GETDATE() + (timeout_minutes * 60 seconds)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Create session in user_sessions table                        │
│     - user_id                                                    │
│     - session_token                                              │
│     - expires_at                                                 │
│     - created_at                                                 │
│     - last_activity                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Set session cookie with token                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER LOGGED IN                                │
└─────────────────────────────────────────────────────────────────┘
```

## 🔍 Request Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER MAKES REQUEST                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Decorator: login_required                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Check if user_id exists in session                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
         ┌──────────┐              ┌──────────────┐
         │   NO     │              │     YES      │
         └──────────┘              └──────────────┘
                │                           │
                ▼                           ▼
    ┌──────────────────┐      ┌────────────────────────────┐
    │ Redirect to      │      │ 3. Query user_sessions:    │
    │ Login Page       │      │    SELECT expires_at       │
    └──────────────────┘      │    WHERE user_id = ?       │
                              │    AND expires_at > NOW    │
                              └────────────────────────────┘
                                          │
                        ┌─────────────────┴─────────────────┐
                        │                                   │
                        ▼                                   ▼
                 ┌──────────┐                      ┌──────────────┐
                 │  EXPIRED │                      │    VALID     │
                 └──────────┘                      └──────────────┘
                        │                                   │
                        ▼                                   ▼
            ┌──────────────────┐          ┌────────────────────────┐
            │ Flush session    │          │ 4. Update last_activity│
            │ Redirect to      │          │    in user_sessions    │
            │ Login Page       │          └────────────────────────┘
            └──────────────────┘                      │
                                                      ▼
                                          ┌────────────────────────┐
                                          │ 5. Process request     │
                                          └────────────────────────┘
```

## ⚙️ Settings Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              USER GOES TO /settings/                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Load current SessionTimeoutMinutes from UserMaster           │
│     - Display current setting                                    │
│     - Show default 60 if not set                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. User selects option:                                         │
│     ○ Never auto-logout (NULL)                                   │
│     ○ Auto-logout after X minutes (5-1440)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. User clicks "Save Settings"                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Update UserMaster:                                           │
│     UPDATE UserMaster                                            │
│     SET SessionTimeoutMinutes = new_value                        │
│     WHERE UserID = user_id                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Show success message:                                        │
│     "Settings saved. Please logout and login again"              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. User logs out and logs in again                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. New timeout applied to new session                           │
└─────────────────────────────────────────────────────────────────┘
```

## 🗄️ Database Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                        UserMaster                                │
├─────────────────────────────────────────────────────────────────┤
│ UserID (PK)                                                      │
│ UserName                                                         │
│ PasswordHash                                                     │
│ ...                                                              │
│ SessionTimeoutMinutes INT NULL  ← NEW COLUMN                    │
│   - NULL = No timeout                                            │
│   - 60 = Default (1 hour)                                        │
│   - 5-1440 = Custom timeout                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ (1:N)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      user_sessions                               │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)                                                          │
│ user_id (FK) → UserMaster.UserID                                │
│ session_token                                                    │
│ created_at                                                       │
│ last_activity                                                    │
│ expires_at  ← CALCULATED FROM SessionTimeoutMinutes             │
│   = created_at + (SessionTimeoutMinutes * 60 seconds)           │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 Timeout Calculation Examples

```
Example 1: Default Timeout (60 minutes)
┌────────────────────────────────────────────┐
│ SessionTimeoutMinutes = 60                 │
│ Login Time: 10:00 AM                       │
│ expires_at = 10:00 AM + 60 minutes         │
│ expires_at = 11:00 AM                      │
│                                            │
│ User will be logged out at 11:00 AM       │
└────────────────────────────────────────────┘

Example 2: Custom Timeout (30 minutes)
┌────────────────────────────────────────────┐
│ SessionTimeoutMinutes = 30                 │
│ Login Time: 2:00 PM                        │
│ expires_at = 2:00 PM + 30 minutes          │
│ expires_at = 2:30 PM                       │
│                                            │
│ User will be logged out at 2:30 PM        │
└────────────────────────────────────────────┘

Example 3: No Timeout
┌────────────────────────────────────────────┐
│ SessionTimeoutMinutes = NULL               │
│ Login Time: 9:00 AM                        │
│ expires_at = NULL or very far future       │
│                                            │
│ User will NEVER be logged out              │
└────────────────────────────────────────────┘
```

## 🎯 Key Decision Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION TREE                                 │
└─────────────────────────────────────────────────────────────────┘

Is SessionTimeoutMinutes NULL?
    │
    ├─ YES → No timeout, user stays logged in indefinitely
    │
    └─ NO → Is SessionTimeoutMinutes set?
            │
            ├─ YES → Use that value for timeout
            │
            └─ NO → Use default 60 minutes

Is expires_at > current_time?
    │
    ├─ YES → Session valid, allow request
    │
    └─ NO → Session expired, redirect to login

Did user change timeout in settings?
    │
    ├─ YES → Save to database, require re-login
    │
    └─ NO → Keep current setting
```

## 🔐 Security Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY CHECKS                               │
└─────────────────────────────────────────────────────────────────┘

1. Login
   ├─ Validate credentials
   ├─ Read timeout from database (server-side)
   ├─ Calculate expiry (server-side)
   └─ Store in database (server-side)

2. Every Request
   ├─ Check session exists
   ├─ Check expires_at from database (server-side)
   ├─ Compare with current time (server-side)
   └─ Update last_activity (server-side)

3. Settings Update
   ├─ Validate user is logged in
   ├─ Validate timeout value (5-1440 or NULL)
   ├─ Update database (server-side)
   └─ Require re-login for new timeout

✅ All checks are server-side
✅ No client-side manipulation possible
✅ Database is source of truth
```

## 📱 User Interface Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SETTINGS PAGE UI                              │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  Session Timeout Settings                                      │
│  Configure your auto-logout preferences                        │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ○ Never auto-logout (stay logged in indefinitely)            │
│                                                                │
│  ● Auto-logout after: [60] minutes                            │
│                                                                │
│  ℹ️ Current setting: Auto-logout after 60 minutes             │
│     Recommended: 30-120 minutes for security.                 │
│     Default is 60 minutes (1 hour).                           │
│                                                                │
│  [Cancel]  [Save Settings]                                    │
└────────────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `→` : Data flow
- `▼` : Next step
- `○` : Radio button (unselected)
- `●` : Radio button (selected)
- `[ ]` : Input field or button
- `ℹ️` : Information
- `✅` : Success/Valid
- `❌` : Error/Invalid
