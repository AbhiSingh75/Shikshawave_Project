# ShikshaWave Universal Notification System - Complete Guide

## Overview
A centralized, extensible notification system that works across all ShikshaWave modules (Tickets, Fees, Timetable, Attendance, Exams, etc.).

---

## 1. DATABASE SCHEMA

### Tables Created

#### NotificationTypeMaster
Stores notification type definitions.
```sql
- TypeID (PK, INT, IDENTITY)
- TypeName (NVARCHAR(50), UNIQUE)
- TypeCategory (NVARCHAR(50)) -- Ticket, Fee, Timetable, Attendance, Exam, General
- IconClass (NVARCHAR(50)) -- Font Awesome icon class
- ColorCode (NVARCHAR(20)) -- Hex color code
- IsActive (BIT)
- CreatedAt (DATETIME)
```

#### NotificationMaster
Stores notification content.
```sql
- NotificationID (PK, BIGINT, IDENTITY)
- SchoolID (INT, FK)
- TypeID (INT, FK)
- Title (NVARCHAR(255))
- Message (NVARCHAR(MAX))
- TargetURL (NVARCHAR(500)) -- Where to navigate on click
- TargetModule (NVARCHAR(50)) -- tickets, fees, timetable, etc.
- TargetRecordID (BIGINT) -- Related record ID
- CreatedByUserID (INT, FK)
- CreatedAt (DATETIME)
- ExpiresAt (DATETIME, NULL)
- IsDeleted (BIT)
```

#### NotificationRecipients
Tracks notification delivery and read status per user.
```sql
- RecipientID (PK, BIGINT, IDENTITY)
- NotificationID (BIGINT, FK)
- UserID (INT, FK)
- IsRead (BIT)
- ReadAt (DATETIME, NULL)
- IsDeleted (BIT)
- CreatedAt (DATETIME)
```

### Pre-populated Notification Types
- **Ticket**: TicketCreated, TicketUpdated, TicketAssigned, TicketChatMessage, TicketStatusChanged
- **Fee**: FeeReminder, FeePaymentConfirmed, FeeDueDate
- **Timetable**: TimetableReleased, TimetableUpdated
- **Attendance**: AttendanceSummary, AttendanceLow
- **Exam**: ExamScheduled, ExamResultPublished
- **General**: GeneralAnnouncement, SystemAlert

---

## 2. STORED PROCEDURES

### Proc_Notification_Create
Creates a notification and assigns to recipients.

**Parameters:**
```sql
@SchoolID INT
@TypeName NVARCHAR(50)
@Title NVARCHAR(255)
@Message NVARCHAR(MAX)
@TargetURL NVARCHAR(500) = NULL
@TargetModule NVARCHAR(50) = NULL
@TargetRecordID BIGINT = NULL
@CreatedByUserID INT
@RecipientUserIDs NVARCHAR(MAX) -- Comma-separated
@ExpiresAt DATETIME = NULL
```

**Returns:** NotificationID, Status

### Proc_Notification_GetList
Retrieves paginated notifications for a user.

**Parameters:**
```sql
@UserID INT
@SchoolID INT
@PageNumber INT = 1
@PageSize INT = 20
@UnreadOnly BIT = 0
```

**Returns:** Notification list with metadata

### Proc_Notification_MarkRead
Marks a single notification as read.

**Parameters:**
```sql
@NotificationID BIGINT
@UserID INT
```

### Proc_Notification_MarkAllRead
Marks all notifications as read for a user.

**Parameters:**
```sql
@UserID INT
@SchoolID INT
```

### Proc_Notification_GetUnreadCount
Gets unread notification count.

**Parameters:**
```sql
@UserID INT
@SchoolID INT
```

**Returns:** UnreadCount

---

## 3. BACKEND IMPLEMENTATION

### Django Models
Location: `notifications/models.py`

- `NotificationTypeMaster`
- `NotificationMaster`
- `NotificationRecipients`

### Service Layer
Location: `notifications/services.py`

#### NotificationService
Core service with methods:
- `create_notification()` - Create and send notification
- `get_notifications()` - Get paginated notifications
- `mark_as_read()` - Mark single as read
- `mark_all_as_read()` - Mark all as read
- `get_unread_count()` - Get unread count

#### NotificationHelper
Helper functions for specific notification types:
- `notify_ticket_created()`
- `notify_ticket_chat_message()`
- `notify_fee_reminder()`
- `notify_attendance_low()`

**Example Usage:**
```python
from notifications.services import NotificationHelper

# Ticket created notification
NotificationHelper.notify_ticket_created(
    ticket_id=123,
    ticket_number='TKT-2024-001',
    subject='Login Issue',
    school_id=3,
    created_by=1,
    assigned_to=5
)

# Chat message notification
NotificationHelper.notify_ticket_chat_message(
    ticket_id=123,
    ticket_number='TKT-2024-001',
    message='I have resolved the issue',
    school_id=3,
    sender_id=5,
    recipient_ids=[1, 2]
)
```

---

## 4. API ENDPOINTS

### GET /notifications/api/list/
Get notifications for logged-in user.

**Query Parameters:**
- `page` (int, default=1)
- `page_size` (int, default=20)
- `unread_only` (bool, default=false)

**Response:**
```json
{
  "notifications": [
    {
      "NotificationID": 1,
      "Title": "New Ticket: TKT-2024-001",
      "Message": "Ticket 'Login Issue' has been created...",
      "TargetURL": "/tickets/view/123/",
      "TypeName": "TicketCreated",
      "TypeCategory": "Ticket",
      "IconClass": "fa-ticket",
      "ColorCode": "#3b82f6",
      "IsRead": false,
      "CreatedAt": "2024-01-15T10:30:00"
    }
  ],
  "total_count": 45,
  "page_number": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### GET /notifications/api/unread-count/
Get unread notification count.

**Response:**
```json
{
  "unread_count": 5
}
```

### POST /notifications/api/mark-read/<notification_id>/
Mark notification as read.

**Response:**
```json
{
  "success": true
}
```

### POST /notifications/api/mark-all-read/
Mark all notifications as read.

**Response:**
```json
{
  "success": true
}
```

---

## 5. FRONTEND COMPONENTS

### UI Components
Location: `staticfiles/js/notifications.js`, `staticfiles/css/notifications.css`

#### NotificationSystem Class
JavaScript class that manages:
- Bell icon with badge
- Dropdown panel
- Polling for new notifications (30s interval)
- Click handlers and navigation

#### Features
- Real-time unread count badge
- Dropdown with notification list
- Pagination (Load More)
- Mark as read on click
- Mark all as read
- Auto-navigation to target page
- Responsive design
- Dark mode support

### UI Elements
1. **Bell Icon** - Shows in header with unread badge
2. **Dropdown Panel** - Opens on bell click
3. **Notification Items** - Clickable with icon, title, message, timestamp
4. **Load More Button** - Pagination support
5. **Mark All Read Button** - Bulk action

---

## 6. INSTALLATION STEPS

### Step 1: Run Database Scripts
```sql
-- Execute in SQL Server Management Studio
-- 1. Create tables
USE ShikshaWaveDB;
GO
-- Run: database/tables/NotificationSystem.sql

-- 2. Create stored procedures
-- Run: database/procedures/Proc_Notification_Create.sql
-- Run: database/procedures/Proc_Notification_GetList.sql
-- Run: database/procedures/Proc_Notification_MarkRead.sql
```

### Step 2: Update Django Settings
Add to `ShikshaWave/settings.py`:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'notifications',
]
```

### Step 3: Update Main URLs
Add to `ShikshaWave/urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('notifications/', include('notifications.urls')),
]
```

### Step 4: Verify Static Files
Ensure these files exist:
- `staticfiles/js/notifications.js`
- `staticfiles/css/notifications.css`

### Step 5: Test Installation
```python
# Test in Django shell
python manage.py shell

from notifications.services import NotificationService

# Test unread count
count = NotificationService.get_unread_count(user_id=1, school_id=3)
print(f"Unread count: {count}")
```

---

## 7. MODULE INTEGRATION GUIDE

### Integrating with Ticket Module

#### Step 1: Import Helper
```python
from notifications.services import NotificationHelper
```

#### Step 2: Add to Ticket Creation
In `tickets/services.py`, after successful ticket creation:
```python
if result['success'] and assigned_to_user_id:
    NotificationHelper.notify_ticket_created(
        ticket_id=ticket_id,
        ticket_number=ticket_number,
        subject=subject,
        school_id=school_id,
        created_by=user_id,
        assigned_to=assigned_to_user_id
    )
```

#### Step 3: Add to Chat Comments
In `tickets/services.py`, after adding comment:
```python
if result['success']:
    # Get ticket participants
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT TicketNumber, SchoolID, CreatedByUserID, AssignedToUserID
            FROM TicketMaster WHERE TicketID = %s
        ''', [ticket_id])
        ticket_row = cursor.fetchone()
        
        if ticket_row:
            ticket_number, school_id, creator_id, assigned_id = ticket_row
            recipients = [uid for uid in [creator_id, assigned_id] if uid and uid != user_id]
            
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

### Integrating with Fee Module

```python
from notifications.services import NotificationHelper

# Fee reminder
NotificationHelper.notify_fee_reminder(
    student_id=student_id,
    fee_type='Tuition Fee',
    amount=5000.00,
    due_date='2024-02-15',
    school_id=school_id,
    recipient_ids=[parent_user_id]
)
```

### Integrating with Attendance Module

```python
from notifications.services import NotificationHelper

# Low attendance alert
NotificationHelper.notify_attendance_low(
    student_id=student_id,
    attendance_percentage=65.5,
    school_id=school_id,
    recipient_ids=[parent_user_id, class_teacher_id]
)
```

### Creating Custom Notification Types

#### Step 1: Add to Database
```sql
INSERT INTO NotificationTypeMaster (TypeName, TypeCategory, IconClass, ColorCode)
VALUES ('CustomEvent', 'General', 'fa-star', '#f59e0b');
```

#### Step 2: Create Helper Function
```python
# In notifications/services.py - NotificationHelper class
@staticmethod
def notify_custom_event(event_id, event_name, school_id, recipient_ids):
    return NotificationService.create_notification(
        school_id=school_id,
        type_name='CustomEvent',
        title=f'New Event: {event_name}',
        message=f'A new event "{event_name}" has been scheduled.',
        recipient_user_ids=recipient_ids,
        created_by_user_id=1,
        target_url=f'/events/view/{event_id}/',
        target_module='events',
        target_record_id=event_id
    )
```

---

## 8. ROUTING BEHAVIOR

### Notification Click Actions

Each notification has a `TargetURL` that determines navigation:

| Module | TargetURL Pattern | Behavior |
|--------|------------------|----------|
| Tickets | `/tickets/view/{id}/` | Opens ticket detail |
| Ticket Chat | `/tickets/view/{id}/#chat` | Opens ticket + scrolls to chat |
| Fees | `/fees/` | Opens fee page |
| Timetable | `/timetable/` | Opens timetable page |
| Attendance | `/attendance/` | Opens attendance page |
| Exams | `/exams/` | Opens exam page |

### Auto-scroll to Chat Section
For ticket chat notifications, the URL includes `#chat` anchor:
```javascript
// In notifications.js
if (targetUrl && targetUrl !== '#') {
    window.location.href = targetUrl; // Navigates and auto-scrolls
}
```

---

## 9. POLLING STRATEGY

### Current Implementation: Polling
- Interval: 30 seconds
- Endpoint: `/notifications/api/unread-count/`
- Updates badge only (lightweight)

### Advantages
- Simple implementation
- No additional infrastructure
- Works with existing Django setup

### Future Enhancement: WebSockets (Optional)
For real-time notifications, consider:
- Django Channels
- Redis for pub/sub
- WebSocket connection per user

---

## 10. SAMPLE PAYLOADS

### Create Notification
```python
NotificationService.create_notification(
    school_id=3,
    type_name='TicketCreated',
    title='New Ticket: TKT-2024-001',
    message='Ticket "Login Issue" has been created and assigned to you.',
    recipient_user_ids=[5, 6],
    created_by_user_id=1,
    target_url='/tickets/view/123/',
    target_module='tickets',
    target_record_id=123,
    expires_at=None
)
```

### Get Notifications Response
```json
{
  "notifications": [
    {
      "NotificationID": 1,
      "Title": "New Ticket: TKT-2024-001",
      "Message": "Ticket 'Login Issue' has been created...",
      "TargetURL": "/tickets/view/123/",
      "TargetModule": "tickets",
      "TargetRecordID": 123,
      "TypeName": "TicketCreated",
      "TypeCategory": "Ticket",
      "IconClass": "fa-ticket",
      "ColorCode": "#3b82f6",
      "IsRead": false,
      "ReadAt": null,
      "CreatedAt": "2024-01-15T10:30:00",
      "CreatedByUserName": "Admin User",
      "TotalCount": 45
    }
  ],
  "total_count": 45,
  "page_number": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

## 11. TESTING CHECKLIST

### Database
- [ ] Tables created successfully
- [ ] Stored procedures created
- [ ] Default notification types inserted
- [ ] Test procedure execution

### Backend
- [ ] Django app registered in settings
- [ ] URLs configured
- [ ] Models accessible
- [ ] Service methods work
- [ ] APIs return correct responses

### Frontend
- [ ] Bell icon appears in header
- [ ] Badge shows unread count
- [ ] Dropdown opens on click
- [ ] Notifications load correctly
- [ ] Mark as read works
- [ ] Navigation works
- [ ] Polling updates badge
- [ ] Responsive on mobile
- [ ] Dark mode compatible

### Integration
- [ ] Ticket creation sends notification
- [ ] Chat message sends notification
- [ ] Notification click opens correct page
- [ ] Multiple recipients receive notification

---

## 12. TROUBLESHOOTING

### Bell Icon Not Showing
- Check `notifications.css` is loaded
- Check `notifications.js` is loaded
- Verify `.actions` div exists in header

### Notifications Not Loading
- Check database connection
- Verify stored procedures exist
- Check user has SchoolID
- Check browser console for errors

### Badge Not Updating
- Check polling is running (console logs)
- Verify API endpoint returns data
- Check CSRF token is present

### Click Navigation Not Working
- Verify TargetURL is correct
- Check URL encryption/decryption
- Verify target page exists

---

## 13. PERFORMANCE CONSIDERATIONS

### Database Optimization
- Indexes on UserID, SchoolID, CreatedAt
- Pagination to limit result sets
- Soft delete instead of hard delete

### Frontend Optimization
- Polling interval: 30s (adjustable)
- Lazy load notifications on dropdown open
- Cache unread count

### Scalability
- Notification expiry for cleanup
- Archive old notifications
- Batch notification creation

---

## 14. SECURITY

### Access Control
- Users only see their own notifications
- School-level isolation
- Login required for all endpoints

### Data Protection
- CSRF protection on POST requests
- SQL injection prevention (parameterized queries)
- XSS prevention (HTML escaping)

---

## 15. FUTURE ENHANCEMENTS

### Phase 2 Features
- [ ] Email notifications
- [ ] SMS notifications
- [ ] Push notifications (PWA)
- [ ] Notification preferences per user
- [ ] Notification categories filter
- [ ] Search notifications
- [ ] Notification templates
- [ ] Scheduled notifications
- [ ] Bulk notification sending
- [ ] Notification analytics

### Real-time Implementation
- [ ] WebSocket support
- [ ] Django Channels integration
- [ ] Redis pub/sub
- [ ] Instant delivery

---

## 16. SUPPORT

For issues or questions:
1. Check this documentation
2. Review code comments
3. Check browser console for errors
4. Review Django logs
5. Test stored procedures directly in SQL Server

---

**Version:** 1.0  
**Last Updated:** 2024  
**Author:** Amazon Q  
**Status:** Production Ready
