# Notification System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NOTIFICATION SYSTEM ARCHITECTURE                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Tickets    │  │     Fees     │  │  Attendance  │              │
│  │   Module     │  │    Module    │  │    Module    │   ... more   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                  │                  │                       │
│         └──────────────────┼──────────────────┘                      │
│                            │                                          │
│                            ▼                                          │
│              ┌─────────────────────────────┐                         │
│              │ UniversalNotificationHelper │                         │
│              │  (notification_helper.py)   │                         │
│              └─────────────┬───────────────┘                         │
│                            │                                          │
│                            ▼                                          │
│              ┌─────────────────────────────┐                         │
│              │   NotificationService       │                         │
│              │     (services.py)           │                         │
│              └─────────────┬───────────────┘                         │
│                            │                                          │
└────────────────────────────┼───────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATABASE LAYER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              STORED PROCEDURES                                 │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │  • Proc_Notification_Create                                   │  │
│  │  • Proc_Notification_GetList                                  │  │
│  │  • Proc_Notification_GetUnreadCount                           │  │
│  │  • Proc_Notification_MarkRead                                 │  │
│  │  • Proc_Notification_MarkAllRead                              │  │
│  │  • Proc_Ticket_Insert (with notification)                     │  │
│  │  • Proc_Ticket_Assign (with notification)                     │  │
│  │  • Proc_Ticket_UpdateStatus (with notification)               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              DATABASE TABLES                                   │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │  NotificationTypeMaster                                        │  │
│  │  ├─ TypeID, TypeName, TypeCategory, IconClass, ColorCode      │  │
│  │  └─ 16 predefined types (Ticket, Fee, Attendance, etc.)       │  │
│  │                                                                 │  │
│  │  NotificationMaster                                            │  │
│  │  ├─ NotificationID, SchoolID, TypeID, Title, Message          │  │
│  │  └─ TargetURL, TargetModule, TargetRecordID, CreatedByUserID │  │
│  │                                                                 │  │
│  │  NotificationRecipients                                        │  │
│  │  ├─ RecipientID, NotificationID, UserID                       │  │
│  │  └─ IsRead, ReadAt, IsDeleted                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Ticket Creation Flow

```
┌──────────────┐
│ School Admin │
│ Creates      │
│ Ticket       │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ tickets/views.py: ticket_create()                       │
│ ├─ Validates input                                      │
│ └─ Calls TicketService.create_ticket()                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ tickets/services.py: TicketService.create_ticket()      │
│ ├─ Calls Proc_Ticket_Insert                            │
│ ├─ Gets ticket_id                                       │
│ └─ Calls NotificationService.create_notification()      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Database: Proc_Ticket_Insert                            │
│ ├─ Validates role and permissions                       │
│ ├─ Inserts into TicketMaster                           │
│ ├─ Logs activity                                        │
│ └─ Returns ticket_id                                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ notifications/services.py: create_notification()        │
│ ├─ Gets Super Admin user IDs                           │
│ └─ Calls Proc_Notification_Create                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Database: Proc_Notification_Create                      │
│ ├─ Gets TypeID for 'TicketCreated'                     │
│ ├─ Inserts into NotificationMaster                     │
│ ├─ Inserts into NotificationRecipients (Super Admins)  │
│ └─ Returns notification_id                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Super Admins see notification in their bell icon       │
│ "New Ticket: TKT-001"                                   │
└─────────────────────────────────────────────────────────┘
```

### 2. Ticket Assignment Flow

```
┌──────────────┐
│ Super Admin  │
│ Assigns      │
│ Ticket       │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ tickets/views.py: ticket_assign()                       │
│ └─ Calls TicketService.assign_ticket()                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Database: Proc_Ticket_Assign                            │
│ ├─ Validates role (must be Super Admin)                │
│ ├─ Updates TicketMaster.AssignedToUserID               │
│ ├─ Logs activity                                        │
│ ├─ Creates notification                                 │
│ └─ Inserts into NotificationRecipients (assigned user) │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Support Executive sees notification                     │
│ "Ticket Assigned: TKT-001"                              │
└─────────────────────────────────────────────────────────┘
```

### 3. Ticket Message Flow

```
┌──────────────┐
│ Any User     │
│ Sends        │
│ Message      │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ tickets/views.py: ticket_add_comment()                  │
│ └─ Calls TicketService.add_comment()                    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ tickets/services.py: TicketService.add_comment()        │
│ ├─ Inserts into TicketComments                         │
│ ├─ Gets ticket participants                            │
│ └─ Calls NotificationHelper.notify_ticket_chat_message()│
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ notifications/services.py: create_notification()        │
│ ├─ Filters recipients (exclude sender)                 │
│ └─ Calls Proc_Notification_Create                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ All participants (except sender) see notification       │
│ "New message on TKT-001"                                │
└─────────────────────────────────────────────────────────┘
```

## Notification Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION TYPE HIERARCHY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TICKET NOTIFICATIONS                                            │
│  ├─ TicketCreated         → New ticket created                  │
│  ├─ TicketAssigned        → Ticket assigned to user             │
│  ├─ TicketStatusChanged   → Status updated                      │
│  ├─ TicketChatMessage     → New message on ticket               │
│  └─ TicketUpdated         → Ticket details updated              │
│                                                                   │
│  FEE NOTIFICATIONS                                               │
│  ├─ FeeReminder           → Payment reminder                    │
│  ├─ FeePaymentConfirmed   → Payment received                    │
│  └─ FeeDueDate            → Fee overdue alert                   │
│                                                                   │
│  ATTENDANCE NOTIFICATIONS                                        │
│  ├─ AttendanceSummary     → Daily summary                       │
│  └─ AttendanceLow         → Low attendance alert                │
│                                                                   │
│  EXAM NOTIFICATIONS                                              │
│  ├─ ExamScheduled         → Exam scheduled                      │
│  └─ ExamResultPublished   → Results published                   │
│                                                                   │
│  TIMETABLE NOTIFICATIONS                                         │
│  ├─ TimetableReleased     → New timetable                       │
│  └─ TimetableUpdated      → Timetable changed                   │
│                                                                   │
│  GENERAL NOTIFICATIONS                                           │
│  ├─ GeneralAnnouncement   → School announcements                │
│  └─ SystemAlert           → System alerts                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Universal Helper API

```
┌─────────────────────────────────────────────────────────────────┐
│         UniversalNotificationHelper - Public Methods             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  CORE METHOD                                                     │
│  └─ send_notification(...)  → Generic notification sender       │
│                                                                   │
│  TICKET METHODS                                                  │
│  ├─ notify_ticket_created(...)                                  │
│  ├─ notify_ticket_assigned(...)                                 │
│  ├─ notify_ticket_status_changed(...)                           │
│  └─ notify_ticket_message(...)                                  │
│                                                                   │
│  FEE METHODS                                                     │
│  ├─ notify_fee_payment_received(...)                            │
│  ├─ notify_fee_reminder(...)                                    │
│  └─ notify_fee_overdue(...)                                     │
│                                                                   │
│  ATTENDANCE METHODS                                              │
│  ├─ notify_attendance_low(...)                                  │
│  └─ notify_attendance_summary(...)                              │
│                                                                   │
│  EXAM METHODS                                                    │
│  ├─ notify_exam_scheduled(...)                                  │
│  └─ notify_exam_result_published(...)                           │
│                                                                   │
│  TIMETABLE METHODS                                               │
│  ├─ notify_timetable_released(...)                              │
│  └─ notify_timetable_updated(...)                               │
│                                                                   │
│  GENERAL METHODS                                                 │
│  ├─ notify_announcement(...)                                    │
│  └─ notify_system_alert(...)                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                    MODULE INTEGRATION POINTS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TICKETS MODULE (✅ Integrated)                                  │
│  ├─ tickets/services.py                                         │
│  │   ├─ create_ticket() → notify_ticket_created()              │
│  │   ├─ assign_ticket() → [in stored procedure]                │
│  │   ├─ update_status() → [in stored procedure]                │
│  │   └─ add_comment() → notify_ticket_message()                │
│  │                                                               │
│  FEES MODULE (✅ Ready to integrate)                             │
│  ├─ fees/services.py                                            │
│  │   ├─ create_fee_reminder() → notify_fee_reminder()          │
│  │   ├─ process_payment() → notify_fee_payment_received()      │
│  │   └─ check_overdue() → notify_fee_overdue()                 │
│  │                                                               │
│  ATTENDANCE MODULE (✅ Ready to integrate)                       │
│  ├─ attendance/services.py                                      │
│  │   ├─ mark_attendance() → notify_attendance_summary()        │
│  │   └─ check_low_attendance() → notify_attendance_low()       │
│  │                                                               │
│  EXAM MODULE (✅ Ready to integrate)                             │
│  ├─ exam/services.py                                            │
│  │   ├─ schedule_exam() → notify_exam_scheduled()              │
│  │   └─ publish_results() → notify_exam_result_published()     │
│  │                                                               │
│  TIMETABLE MODULE (✅ Ready to integrate)                        │
│  ├─ timetable/services.py                                       │
│  │   ├─ release_timetable() → notify_timetable_released()      │
│  │   └─ update_timetable() → notify_timetable_updated()        │
│  │                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERROR HANDLING STRATEGY                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Module calls notification helper                                │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────────────────────────┐                       │
│  │ try:                                  │                       │
│  │   send_notification(...)              │                       │
│  │ except Exception as e:                │                       │
│  │   logger.warning(f"Notification       │                       │
│  │                   failed: {e}")       │                       │
│  │   # Continue with main workflow       │                       │
│  └──────────────────────────────────────┘                       │
│         │                                                         │
│         ▼                                                         │
│  Main workflow continues                                         │
│  (notification failure doesn't break app)                        │
│                                                                   │
│  Benefits:                                                       │
│  ✅ Graceful degradation                                         │
│  ✅ Main functionality not affected                              │
│  ✅ Errors logged for debugging                                  │
│  ✅ User experience not disrupted                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE OPTIMIZATIONS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. BATCH RECIPIENT HANDLING                                     │
│     ├─ Single notification for multiple recipients              │
│     ├─ Uses STRING_SPLIT in SQL                                 │
│     └─ Reduces database round trips                             │
│                                                                   │
│  2. INDEXED QUERIES                                              │
│     ├─ Index on NotificationRecipients(UserID, IsRead)          │
│     ├─ Index on NotificationMaster(SchoolID)                    │
│     └─ Fast unread count queries                                │
│                                                                   │
│  3. MINIMAL OVERHEAD                                             │
│     ├─ Notifications sent asynchronously (in try-catch)         │
│     ├─ Doesn't block main workflow                              │
│     └─ Failures don't impact user experience                    │
│                                                                   │
│  4. EFFICIENT FILTERING                                          │
│     ├─ Recipient filtering at application layer                 │
│     ├─ Excludes sender automatically                            │
│     └─ Validates recipient IDs before sending                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Security Considerations

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY FEATURES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. ROLE-BASED ACCESS                                            │
│     ├─ Notifications respect user roles                         │
│     ├─ Only authorized users receive notifications              │
│     └─ Stored procedures validate permissions                   │
│                                                                   │
│  2. DATA ISOLATION                                               │
│     ├─ School-level data isolation                              │
│     ├─ Users only see their school's notifications              │
│     └─ SchoolID filtering in all queries                        │
│                                                                   │
│  3. SOFT DELETE                                                  │
│     ├─ IsDeleted flag instead of hard delete                    │
│     ├─ Audit trail maintained                                   │
│     └─ Can recover deleted notifications                        │
│                                                                   │
│  4. INPUT VALIDATION                                             │
│     ├─ Recipient IDs validated                                  │
│     ├─ Notification types validated                             │
│     └─ SQL injection prevention                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

This architecture provides a robust, scalable, and maintainable notification system that can be easily extended to support all modules in the application.
