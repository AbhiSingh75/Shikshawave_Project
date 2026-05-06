# Notification System Fix - Deployment Checklist

## Pre-Deployment

### 1. Backup ✅
- [ ] Backup database
  ```sql
  BACKUP DATABASE [YourDatabase] TO DISK = 'C:\Backups\YourDatabase_BeforeNotificationFix.bak'
  ```
- [ ] Backup application code (Git commit)
  ```bash
  git add .
  git commit -m "Before notification system fix"
  git push
  ```

### 2. Review Changes ✅
- [ ] Review SQL script: `database/FIX_NOTIFICATION_SYSTEM.sql`
- [ ] Review Python changes: `tickets/services.py`
- [ ] Review new helper: `notifications/notification_helper.py`
- [ ] Review documentation: `NOTIFICATION_FIX_README.md`

### 3. Environment Check ✅
- [ ] Verify database connection
- [ ] Verify Django version compatibility
- [ ] Check disk space (minimal required)
- [ ] Verify user permissions (need CREATE PROCEDURE rights)

## Deployment Steps

### Step 1: Database Changes (2 minutes)

#### Option A: SQL Server Management Studio
- [ ] Open SSMS
- [ ] Connect to your database
- [ ] Open file: `database/FIX_NOTIFICATION_SYSTEM.sql`
- [ ] Execute script (F5)
- [ ] Verify success messages in output

#### Option B: Command Line
```bash
sqlcmd -S your_server -d your_database -i database/FIX_NOTIFICATION_SYSTEM.sql
```
- [ ] Execute command
- [ ] Check for errors in output

### Step 2: Verify Database Changes (1 minute)

Run these verification queries:

```sql
-- Check notification procedures
SELECT name FROM sys.procedures 
WHERE name LIKE 'Proc_Notification%'
ORDER BY name;
-- Expected: 5 procedures

-- Check ticket procedures
SELECT name FROM sys.procedures 
WHERE name LIKE 'Proc_Ticket%'
ORDER BY name;
-- Expected: Multiple procedures including Insert, Assign, UpdateStatus

-- Check notification types
SELECT COUNT(*) FROM NotificationTypeMaster WHERE IsActive = 1;
-- Expected: 16 types

-- Check tables exist
SELECT name FROM sys.tables 
WHERE name IN ('NotificationMaster', 'NotificationRecipients', 'NotificationTypeMaster');
-- Expected: 3 tables
```

- [ ] All procedures created
- [ ] All tables exist
- [ ] Notification types populated

### Step 3: Application Restart (30 seconds)

```bash
# Stop Django server
Ctrl+C

# Restart Django server
python manage.py runserver
```

- [ ] Server stopped cleanly
- [ ] Server restarted successfully
- [ ] No errors in console

### Step 4: Automated Testing (2 minutes)

```bash
python test_notification_fix.py
```

Expected output:
```
========================================
TEST 1: Checking Database Procedures
========================================
✅ All required procedures exist!

========================================
TEST 2: Checking Notification Types
========================================
✅ Ticket notification types configured!

========================================
TEST 3: Testing Unread Count
========================================
✅ Unread count: X

========================================
TEST 4: Testing Notification Creation
========================================
✅ Notification created! ID: X
✅ Notification recipient record created!

========================================
TEST 5: Testing Universal Notification Helper
========================================
✅ Universal helper working! Notification ID: X

========================================
TEST SUMMARY
========================================
✅ PASS - Database Procedures
✅ PASS - Notification Types
✅ PASS - Unread Count
✅ PASS - Notification Creation
✅ PASS - Universal Helper

Total: 5/5 tests passed

🎉 All tests passed! Notification system is working correctly!
```

- [ ] All 5 tests passed
- [ ] No errors in output

## Manual Testing

### Test 1: Ticket Creation Notification (2 minutes)

**As School Admin:**
1. [ ] Login as School Admin
2. [ ] Navigate to Tickets → Create Ticket
3. [ ] Fill in ticket details:
   - Category: Technical
   - Priority: High
   - Subject: Test Notification
   - Description: Testing notification system
4. [ ] Submit ticket
5. [ ] Note the ticket number (e.g., TKT-001)

**As Super Admin:**
1. [ ] Login as Super Admin
2. [ ] Check notification bell icon
3. [ ] Should see: "New Ticket: TKT-001"
4. [ ] Click notification
5. [ ] Should navigate to ticket detail page

**Verification:**
- [ ] Super Admin received notification
- [ ] Notification shows correct ticket number
- [ ] Clicking notification navigates correctly
- [ ] Unread count updated

### Test 2: Ticket Assignment Notification (2 minutes)

**As Super Admin:**
1. [ ] Open the test ticket (TKT-001)
2. [ ] Click "Assign" button
3. [ ] Select a Support Executive
4. [ ] Add comment (optional)
5. [ ] Submit assignment

**As Support Executive:**
1. [ ] Login as the assigned Support Executive
2. [ ] Check notification bell icon
3. [ ] Should see: "Ticket Assigned: TKT-001"
4. [ ] Click notification
5. [ ] Should navigate to ticket detail page

**Verification:**
- [ ] Support Executive received notification
- [ ] Notification shows correct ticket number
- [ ] Clicking notification navigates correctly
- [ ] Unread count updated

### Test 3: Ticket Status Change Notification (2 minutes)

**As Support Executive:**
1. [ ] Open the assigned ticket
2. [ ] Change status: Open → In Progress
3. [ ] Add comment (optional)
4. [ ] Submit status change

**As School Admin (ticket creator):**
1. [ ] Login as School Admin
2. [ ] Check notification bell icon
3. [ ] Should see: "Ticket Status Updated: TKT-001"
4. [ ] Click notification
5. [ ] Should navigate to ticket detail page

**Verification:**
- [ ] School Admin received notification
- [ ] Notification shows correct status
- [ ] Clicking notification navigates correctly
- [ ] Unread count updated

### Test 4: Ticket Message Notification (2 minutes)

**As Support Executive:**
1. [ ] Open the ticket
2. [ ] Scroll to chat section
3. [ ] Type a message: "I'm working on this issue"
4. [ ] Send message

**As School Admin:**
1. [ ] Check notification bell icon
2. [ ] Should see: "New message on TKT-001"
3. [ ] Click notification
4. [ ] Should navigate to ticket chat section

**Verification:**
- [ ] School Admin received notification
- [ ] Notification shows message preview
- [ ] Clicking notification navigates to chat
- [ ] Unread count updated

### Test 5: Multiple Notifications (1 minute)

1. [ ] Create 2-3 more test tickets
2. [ ] Check notification list
3. [ ] Verify all notifications appear
4. [ ] Check unread count is correct
5. [ ] Mark one as read
6. [ ] Verify unread count decreases
7. [ ] Click "Mark all as read"
8. [ ] Verify all marked as read

**Verification:**
- [ ] Multiple notifications display correctly
- [ ] Unread count accurate
- [ ] Mark as read works
- [ ] Mark all as read works

## Post-Deployment Verification

### 1. Database Health Check

```sql
-- Check notification creation rate
SELECT 
    CAST(CreatedAt AS DATE) as Date,
    COUNT(*) as NotificationCount
FROM NotificationMaster
WHERE CreatedAt >= DATEADD(DAY, -7, GETDATE())
GROUP BY CAST(CreatedAt AS DATE)
ORDER BY Date DESC;

-- Check unread notifications
SELECT 
    u.UserName,
    COUNT(*) as UnreadCount
FROM NotificationRecipients nr
INNER JOIN UserMaster u ON nr.UserID = u.UserID
WHERE nr.IsRead = 0 AND nr.IsDeleted = 0
GROUP BY u.UserName
ORDER BY UnreadCount DESC;

-- Check notification types usage
SELECT 
    nt.TypeName,
    COUNT(*) as UsageCount
FROM NotificationMaster nm
INNER JOIN NotificationTypeMaster nt ON nm.TypeID = nt.TypeID
WHERE nm.CreatedAt >= DATEADD(DAY, -7, GETDATE())
GROUP BY nt.TypeName
ORDER BY UsageCount DESC;
```

- [ ] Notifications being created
- [ ] Users receiving notifications
- [ ] All notification types working

### 2. Application Health Check

```bash
# Check Django logs for errors
tail -f logs/django.log | grep -i "notification"

# Check for any errors
tail -f logs/django.log | grep -i "error"
```

- [ ] No notification-related errors
- [ ] No database connection errors
- [ ] Application running smoothly

### 3. Performance Check

```sql
-- Check query performance
SET STATISTICS TIME ON;
EXEC Proc_Notification_GetUnreadCount @UserID = 1, @SchoolID = 1;
SET STATISTICS TIME OFF;
-- Should complete in < 100ms

-- Check table sizes
SELECT 
    t.name AS TableName,
    p.rows AS RowCount,
    SUM(a.total_pages) * 8 AS TotalSpaceKB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.name IN ('NotificationMaster', 'NotificationRecipients')
GROUP BY t.name, p.rows
ORDER BY TotalSpaceKB DESC;
```

- [ ] Queries performing well
- [ ] Table sizes reasonable
- [ ] No performance degradation

## Rollback Plan (If Needed)

### If Issues Occur:

#### Option 1: Rollback Application Only
```bash
git revert HEAD
python manage.py runserver
```
- [ ] Application reverted
- [ ] Database changes remain (they don't break anything)

#### Option 2: Rollback Database Only
```sql
-- Drop new procedures (if causing issues)
DROP PROCEDURE IF EXISTS Proc_Notification_GetUnreadCount;
DROP PROCEDURE IF EXISTS Proc_Notification_MarkAllRead;

-- Restore old ticket procedures from backup
-- (You should have these backed up)
```
- [ ] Procedures dropped
- [ ] Old procedures restored

#### Option 3: Full Rollback
```sql
-- Restore database from backup
RESTORE DATABASE [YourDatabase] 
FROM DISK = 'C:\Backups\YourDatabase_BeforeNotificationFix.bak'
WITH REPLACE;
```
```bash
git revert HEAD
python manage.py runserver
```
- [ ] Database restored
- [ ] Application reverted

## Monitoring (First 24 Hours)

### Metrics to Monitor:

1. **Notification Creation Rate**
   - [ ] Check every 2 hours
   - [ ] Expected: Increases with ticket activity
   - [ ] Alert if: No notifications created

2. **Error Rate**
   - [ ] Check Django logs every hour
   - [ ] Expected: No notification-related errors
   - [ ] Alert if: Any errors appear

3. **User Feedback**
   - [ ] Ask users if they're receiving notifications
   - [ ] Expected: Positive feedback
   - [ ] Alert if: Users report not receiving notifications

4. **Performance**
   - [ ] Monitor page load times
   - [ ] Expected: No degradation
   - [ ] Alert if: Slowdown detected

### Monitoring Queries:

```sql
-- Hourly notification count
SELECT 
    DATEPART(HOUR, CreatedAt) as Hour,
    COUNT(*) as Count
FROM NotificationMaster
WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY DATEPART(HOUR, CreatedAt)
ORDER BY Hour;

-- Error check
SELECT TOP 10 *
FROM NotificationMaster
WHERE Title LIKE '%error%' OR Message LIKE '%error%'
ORDER BY CreatedAt DESC;

-- Undelivered notifications
SELECT COUNT(*)
FROM NotificationRecipients nr
INNER JOIN NotificationMaster nm ON nr.NotificationID = nm.NotificationID
WHERE nr.IsRead = 0 
  AND nm.CreatedAt < DATEADD(HOUR, -1, GETDATE());
```

## Success Criteria

### Immediate (Day 1):
- [x] All tests pass
- [x] No errors in logs
- [x] Users receive notifications
- [x] Unread count works
- [x] Navigation works

### Short Term (Week 1):
- [ ] Notification delivery rate > 95%
- [ ] No performance issues
- [ ] Positive user feedback
- [ ] No rollbacks needed

### Long Term (Month 1):
- [ ] System stable
- [ ] Ready to extend to other modules
- [ ] User adoption high
- [ ] No maintenance issues

## Sign-Off

### Deployment Team:
- [ ] Database Administrator: _________________ Date: _______
- [ ] Backend Developer: _________________ Date: _______
- [ ] QA Engineer: _________________ Date: _______
- [ ] Project Manager: _________________ Date: _______

### Approval:
- [ ] Technical Lead: _________________ Date: _______
- [ ] Product Owner: _________________ Date: _______

## Notes:

```
Deployment Date: _______________
Deployment Time: _______________
Deployed By: _______________

Issues Encountered:
_________________________________________________
_________________________________________________
_________________________________________________

Resolution:
_________________________________________________
_________________________________________________
_________________________________________________

Additional Comments:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**Status**: Ready for Deployment ✅
**Risk Level**: Low
**Estimated Time**: 10 minutes
**Rollback Time**: 5 minutes
