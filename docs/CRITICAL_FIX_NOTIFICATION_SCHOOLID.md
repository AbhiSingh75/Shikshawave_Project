# CRITICAL FIX: Notification SchoolID Issue

## Problem
Notifications were not being created because:
1. **NotificationMaster table** has `SchoolID INT NOT NULL` constraint
2. Code was passing `school_id=None` for Super Admin notifications
3. Database rejected NULL values causing insertion failure

## Root Cause
The database table schema requires SchoolID, but Super Admin and Support Executive notifications should work without SchoolID filtering.

## Solution

### STEP 1: Run Database Fix Script (REQUIRED)
**File**: `database/FIX_NOTIFICATION_SCHOOLID.sql`

This script does TWO things:
1. **Alters NotificationMaster table** - Makes SchoolID column nullable
2. **Updates stored procedure** - Makes @SchoolID parameter nullable

**Run this script in SQL Server Management Studio:**
```sql
-- Execute the script
USE ShikshaWaveDB;
GO
-- Then run: database/FIX_NOTIFICATION_SCHOOLID.sql
```

### STEP 2: Code Changes (Already Done)

#### Backend Files Modified:
1. **notifications/services.py** - Made school_id Optional[int]
2. **notifications/notification_helper.py** - Made school_id Optional[int]
3. **tickets/services.py** - All notifications pass school_id=None
4. **database/procedures/Proc_Notification_Create.sql** - Made @SchoolID nullable

## Verification Steps

### 1. Check Database Schema
```sql
-- Verify SchoolID is nullable
SELECT COLUMN_NAME, IS_NULLABLE, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'NotificationMaster' AND COLUMN_NAME = 'SchoolID';
-- Should show: IS_NULLABLE = 'YES'
```

### 2. Test Notification Creation
```sql
-- Test creating notification with NULL SchoolID
DECLARE @Result TABLE (NotificationID BIGINT, Status NVARCHAR(500));

INSERT INTO @Result
EXEC Proc_Notification_Create
    @SchoolID = NULL,
    @TypeName = 'TicketCreated',
    @Title = 'Test Notification',
    @Message = 'Test message',
    @TargetURL = '/test/',
    @TargetModule = 'tickets',
    @TargetRecordID = 1,
    @CreatedByUserID = 1,
    @RecipientUserIDs = '1',
    @ExpiresAt = NULL;

SELECT * FROM @Result;
-- Should return: NotificationID > 0, Status = 'Success'
```

### 3. Test Ticket Creation
1. Login as School Admin
2. Create a new ticket
3. Check browser console - should NOT show errors
4. Login as Super Admin
5. Check notifications - should see the new ticket notification

### 4. Check Database Tables
```sql
-- Check if notification was created
SELECT TOP 5 * FROM NotificationMaster ORDER BY CreatedAt DESC;

-- Check if recipients were added
SELECT TOP 5 nr.*, u.UserName 
FROM NotificationRecipients nr
JOIN UserMaster u ON nr.UserID = u.UserID
ORDER BY nr.CreatedAt DESC;
```

## Expected Behavior After Fix

### Ticket Creation Flow:
1. **School Admin creates ticket** → Notification sent to Super Admin (SchoolID = NULL)
2. **Super Admin assigns ticket** → Notification sent to assigned user (SchoolID = NULL)
3. **User updates status** → Notification sent to participants (SchoolID = NULL)
4. **User adds comment** → Notification sent to participants (SchoolID = NULL)

### Notification Visibility:
- **Super Admin**: Sees ALL notifications (SchoolID filter = NULL)
- **Support Executive**: Sees ALL notifications (SchoolID filter = NULL)
- **School Admin**: Sees only their school's notifications (SchoolID filter = their school)
- **Other Roles**: Sees only their school's notifications (SchoolID filter = their school)

## Troubleshooting

### If notifications still don't work:

1. **Check if script ran successfully:**
```sql
-- Verify column is nullable
SELECT COLUMN_NAME, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'NotificationMaster' AND COLUMN_NAME = 'SchoolID';
```

2. **Check browser console for errors:**
- Open Developer Tools (F12)
- Go to Console tab
- Look for red errors when creating ticket

3. **Check Django logs:**
- Look for error messages in console where Django is running
- Check for "Notification error:" messages

4. **Verify Super Admin exists:**
```sql
SELECT u.UserID, u.UserName, p.ProfileName 
FROM UserMaster u
JOIN ProfileMaster p ON u.ProfileID = p.ProfileID
WHERE p.ProfileName = 'Super Admin' AND u.IsActive = 1;
```

5. **Check notification type exists:**
```sql
SELECT * FROM NotificationTypeMaster WHERE TypeName = 'TicketCreated';
```

## Files Changed

### Database:
- `database/FIX_NOTIFICATION_SCHOOLID.sql` - **RUN THIS FIRST**
- `database/FIX_NOTIFICATION_SCHOOLID_COLUMN.sql` - Standalone column fix
- `database/procedures/Proc_Notification_Create.sql` - Updated procedure

### Backend:
- `notifications/services.py` - Made school_id optional
- `notifications/notification_helper.py` - Made school_id optional
- `tickets/services.py` - Pass school_id=None for all notifications

### Documentation:
- `NOTIFICATION_SCHOOLID_FIX_SUMMARY.md` - Detailed summary
- `CRITICAL_FIX_NOTIFICATION_SCHOOLID.md` - This file

## IMPORTANT NOTES

⚠️ **MUST RUN DATABASE SCRIPT FIRST** ⚠️

The code changes are already done, but they will NOT work until you run the database script to make SchoolID nullable in the NotificationMaster table.

Without running the script:
- ❌ Notifications will fail to insert
- ❌ No error will show to user
- ❌ Console will show database constraint errors

After running the script:
- ✅ Notifications will be created successfully
- ✅ Super Admin will receive notifications
- ✅ All ticket events will trigger notifications
