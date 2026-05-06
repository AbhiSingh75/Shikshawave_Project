# ShikshaWave Notification System - Quick Start Guide

## 5-Minute Setup

### Step 1: Database Installation (2 minutes)
```sql
-- Open SQL Server Management Studio
-- Connect to your ShikshaWave database
-- Execute this single script:
USE ShikshaWaveDB;
GO
-- Run: database/INSTALL_NOTIFICATION_SYSTEM.sql
```

### Step 2: Django Configuration (1 minute)

**Update `ShikshaWave/settings.py`:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps ...
    'core',
    'tickets',
    'mail',
    'notifications',  # ← Add this line
]
```

**Update `ShikshaWave/urls.py`:**
```python
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),
    path('tickets/', include('tickets.urls')),
    path('notifications/', include('notifications.urls')),  # ← Add this line
]
```

### Step 3: Verify Installation (1 minute)

**Test in Django shell:**
```bash
python manage.py shell
```

```python
from notifications.services import NotificationService

# Test unread count
count = NotificationService.get_unread_count(user_id=1, school_id=3)
print(f"Unread count: {count}")  # Should return 0

# Test create notification
result = NotificationService.create_notification(
    school_id=3,
    type_name='SystemAlert',
    title='Test Notification',
    message='This is a test notification',
    recipient_user_ids=[1],
    created_by_user_id=1
)
print(result)  # Should show success
```

### Step 4: Test in Browser (1 minute)

1. Login to ShikshaWave
2. Look for bell icon in header (next to dark mode toggle)
3. Click bell icon - dropdown should open
4. You should see the test notification created above

---

## Integration Examples

### Example 1: Ticket Created Notification

**In `tickets/services.py` - TicketService.create_ticket():**

```python
# After successful ticket creation
if result['success'] and assigned_to_user_id:
    from notifications.services import NotificationHelper
    
    NotificationHelper.notify_ticket_created(
        ticket_id=result['ticket_id'],
        ticket_number=ticket_number,
        subject=subject,
        school_id=school_id,
        created_by=user_id,
        assigned_to=assigned_to_user_id
    )
```

### Example 2: Ticket Chat Message

**In `tickets/services.py` - TicketService.add_comment():**

```python
# After successful comment
if result['success']:
    from notifications.services import NotificationHelper
    from django.db import connection
    
    # Get ticket details
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT TicketNumber, SchoolID, CreatedByUserID, AssignedToUserID
            FROM TicketMaster WHERE TicketID = %s
        ''', [ticket_id])
        ticket_row = cursor.fetchone()
        
        if ticket_row:
            ticket_number, school_id, creator_id, assigned_id = ticket_row
            
            # Build recipient list (exclude sender)
            recipients = []
            if creator_id and creator_id != user_id:
                recipients.append(creator_id)
            if assigned_id and assigned_id != user_id:
                recipients.append(assigned_id)
            
            if recipients:
                NotificationHelper.notify_ticket_chat_message(
                    ticket_id=ticket_id,
                    ticket_number=ticket_number,
                    message=comment_text,
                    school_id=school_id,
                    sender_id=user_id,
                    recipient_ids=recipients
                )
```

### Example 3: Custom Notification

```python
from notifications.services import NotificationService

# Send custom notification
NotificationService.create_notification(
    school_id=3,
    type_name='GeneralAnnouncement',
    title='School Holiday Announcement',
    message='School will remain closed on 26th January for Republic Day.',
    recipient_user_ids=[1, 2, 3, 4, 5],  # All staff
    created_by_user_id=1,
    target_url='/announcements/',
    target_module='announcements',
    target_record_id=None
)
```

---

## API Usage Examples

### Get Notifications
```javascript
fetch('/notifications/api/list/?page=1&page_size=20')
    .then(response => response.json())
    .then(data => {
        console.log('Notifications:', data.notifications);
        console.log('Total:', data.total_count);
    });
```

### Get Unread Count
```javascript
fetch('/notifications/api/unread-count/')
    .then(response => response.json())
    .then(data => {
        console.log('Unread:', data.unread_count);
    });
```

### Mark as Read
```javascript
fetch('/notifications/api/mark-read/123/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': getCsrfToken()
    }
})
.then(response => response.json())
.then(data => {
    console.log('Success:', data.success);
});
```

---

## Troubleshooting

### Bell Icon Not Showing
✓ Check `base_with_header.html` includes notification CSS/JS  
✓ Clear browser cache  
✓ Check browser console for errors

### Notifications Not Loading
✓ Verify database tables exist  
✓ Check stored procedures are created  
✓ Verify user has valid SchoolID  
✓ Check Django logs for errors

### Badge Not Updating
✓ Check polling is running (console.log in notifications.js)  
✓ Verify API endpoint returns data  
✓ Check network tab in browser dev tools

---

## File Checklist

Ensure these files exist:

**Database:**
- ✓ `database/tables/NotificationSystem.sql`
- ✓ `database/procedures/Proc_Notification_Create.sql`
- ✓ `database/procedures/Proc_Notification_GetList.sql`
- ✓ `database/procedures/Proc_Notification_MarkRead.sql`
- ✓ `database/INSTALL_NOTIFICATION_SYSTEM.sql`

**Backend:**
- ✓ `notifications/__init__.py`
- ✓ `notifications/models.py`
- ✓ `notifications/services.py`
- ✓ `notifications/views.py`
- ✓ `notifications/urls.py`
- ✓ `notifications/apps.py`

**Frontend:**
- ✓ `staticfiles/js/notifications.js`
- ✓ `staticfiles/css/notifications.css`

**Documentation:**
- ✓ `docs/NOTIFICATION_SYSTEM_COMPLETE_GUIDE.md`
- ✓ `docs/NOTIFICATION_QUICK_START.md`

---

## Next Steps

1. **Test the system** with the examples above
2. **Integrate with Ticket module** using provided code
3. **Add to other modules** (Fees, Attendance, etc.)
4. **Customize notification types** as needed
5. **Monitor performance** and adjust polling interval

---

## Support

For detailed documentation, see:
- `docs/NOTIFICATION_SYSTEM_COMPLETE_GUIDE.md`

For integration examples, see:
- `tickets/notification_integration.py`

---

**Ready to use!** The notification system is now fully functional across your ShikshaWave application.
