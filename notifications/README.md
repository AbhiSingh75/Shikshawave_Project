# ShikshaWave Notifications Module

Universal in-app notification system for ShikshaWave ERP.

## Features

✓ **Universal** - Works across all modules (Tickets, Fees, Timetable, Attendance, Exams)  
✓ **Real-time Badge** - Shows unread count with 30s polling  
✓ **Dropdown Panel** - Clean UI with pagination  
✓ **Click Actions** - Navigate to target pages on click  
✓ **Extensible** - Easy to add new notification types  
✓ **Multi-recipient** - Send to multiple users  
✓ **Read Tracking** - Per-user read/unread status  
✓ **Dark Mode** - Full dark mode support  
✓ **Responsive** - Mobile-friendly design

## Quick Start

### 1. Install Database
```sql
-- Run in SQL Server
USE ShikshaWaveDB;
GO
-- Execute: database/INSTALL_NOTIFICATION_SYSTEM.sql
```

### 2. Configure Django
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'notifications',
]

# urls.py
urlpatterns = [
    # ...
    path('notifications/', include('notifications.urls')),
]
```

### 3. Use in Code
```python
from notifications.services import NotificationHelper

# Send notification
NotificationHelper.notify_ticket_created(
    ticket_id=123,
    ticket_number='TKT-2024-001',
    subject='Login Issue',
    school_id=3,
    created_by=1,
    assigned_to=5
)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/api/list/` | GET | Get notifications |
| `/notifications/api/unread-count/` | GET | Get unread count |
| `/notifications/api/mark-read/<id>/` | POST | Mark as read |
| `/notifications/api/mark-all-read/` | POST | Mark all as read |

## Notification Types

### Ticket
- TicketCreated
- TicketUpdated
- TicketAssigned
- TicketChatMessage
- TicketStatusChanged

### Fee
- FeeReminder
- FeePaymentConfirmed
- FeeDueDate

### Timetable
- TimetableReleased
- TimetableUpdated

### Attendance
- AttendanceSummary
- AttendanceLow

### Exam
- ExamScheduled
- ExamResultPublished

### General
- GeneralAnnouncement
- SystemAlert

## Architecture

```
notifications/
├── models.py           # Django models
├── services.py         # Business logic
├── views.py            # API endpoints
├── urls.py             # URL routing
└── apps.py             # App config

database/
├── tables/NotificationSystem.sql
├── procedures/Proc_Notification_*.sql
└── INSTALL_NOTIFICATION_SYSTEM.sql

staticfiles/
├── js/notifications.js
└── css/notifications.css
```

## Documentation

- **Complete Guide**: `docs/NOTIFICATION_SYSTEM_COMPLETE_GUIDE.md`
- **Quick Start**: `docs/NOTIFICATION_QUICK_START.md`
- **Integration**: `tickets/notification_integration.py`

## Support

Check documentation or review code comments for detailed information.
