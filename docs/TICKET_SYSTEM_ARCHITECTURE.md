# Ticket Management System - Architecture Diagrams

## 1. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    ShikshaWave ERP Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Frontend   │─────▶│   Django     │─────▶│ SQL Server│ │
│  │   (Web UI)   │◀─────│   Backend    │◀─────│ Database  │ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│         │                      │                     │       │
│         │                      │                     │       │
│    User Actions          API Endpoints         Stored       │
│    - Create Ticket       - /tickets/create/    Procedures   │
│    - View Tickets        - /tickets/list/      - Create     │
│    - Assign              - /tickets/{id}/      - Assign     │
│    - Comment             - /tickets/assign/    - Reopen     │
│    - Reopen              - /tickets/reopen/    - Status     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 2. DATABASE SCHEMA DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                      TICKET MANAGEMENT SCHEMA                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  SchoolMaster    │
│  (Existing)      │
│──────────────────│
│ SchoolID (PK)    │◀──────────┐
│ SchoolName       │            │
│ ...              │            │
└──────────────────┘            │
                                │
┌──────────────────┐            │
│  UserMaster      │            │
│  (Existing)      │            │
│──────────────────│            │
│ UserID (PK)      │◀───────┐  │
│ UserName         │        │  │
│ ProfileID (FK)   │        │  │
│ SchoolID (FK)    │        │  │
└──────────────────┘        │  │
        ▲                   │  │
        │                   │  │
┌──────────────────┐        │  │
│  ProfileMaster   │        │  │
│  (Extended)      │        │  │
│──────────────────│        │  │
│ ProfileID (PK)   │        │  │
│ 1=Super Admin    │        │  │
│ 2=School Admin   │        │  │
│ 3=Teacher        │        │  │
│ 4=Student        │        │  │
│ 5=Support Exec   │◀NEW    │  │
└──────────────────┘        │  │
                            │  │
┌──────────────────┐        │  │
│ TicketCategory   │        │  │
│──────────────────│        │  │
│ CategoryID (PK)  │◀───┐   │  │
│ CategoryName     │    │   │  │
│ CategoryCode     │    │   │  │
└──────────────────┘    │   │  │
                        │   │  │
┌──────────────────┐    │   │  │
│ TicketPriority   │    │   │  │
│──────────────────│    │   │  │
│ PriorityID (PK)  │◀─┐ │   │  │
│ PriorityName     │  │ │   │  │
│ PriorityLevel    │  │ │   │  │
│ ColorCode        │  │ │   │  │
└──────────────────┘  │ │   │  │
        ▲             │ │   │  │
        │             │ │   │  │
┌──────────────────┐  │ │   │  │
│   SLAMaster      │  │ │   │  │
│──────────────────│  │ │   │  │
│ SLAID (PK)       │  │ │   │  │
│ PriorityID (FK)  │──┘ │   │  │
│ ResponseTimeHrs  │    │   │  │
│ ResolutionTimeHrs│    │   │  │
└──────────────────┘    │   │  │
                        │   │  │
┌──────────────────┐    │   │  │
│  TicketStatus    │    │   │  │
│──────────────────│    │   │  │
│ StatusID (PK)    │◀─┐ │   │  │
│ StatusName       │  │ │   │  │
│ StatusCode       │  │ │   │  │
│ StatusOrder      │  │ │   │  │
└──────────────────┘  │ │   │  │
                      │ │   │  │
┌────────────────────────────────────────┐
│         TicketMaster (CORE)            │
│────────────────────────────────────────│
│ TicketID (PK)                          │
│ TicketNumber (UNIQUE)                  │
│ SchoolID (FK) ─────────────────────────┘
│ Title                                  │
│ Description                            │
│ CategoryID (FK) ───────────────────────┘
│ PriorityID (FK) ─────────────────────────┘
│ StatusID (FK) ─────────────────────────────┘
│ CreatedByUserID (FK) ──────────────────────────┘
│ AssignedToUserID (FK) ─────────────────────────┐
│ ResolutionNotes                                │
│ ResolvedAt                                     │
│ ClosedAt                                       │
│ ReopenedCount                                  │
│ LastReopenedAt                                 │
│ LastReopenedBy (FK) ───────────────────────────┤
│ CreatedAt, UpdatedAt                           │
│ CreatedBy, UpdatedBy                           │
│ IsDeleted, DeletedAt, DeletedBy                │
└────────────────────────────────────────────────┘
        │           │           │           │
        │           │           │           │
        ▼           ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│TicketAttach  │ │TicketComments│ │TicketStatus  │ │TicketAssign  │
│──────────────│ │──────────────│ │History       │ │──────────────│
│AttachmentID  │ │CommentID (PK)│ │──────────────│ │AssignmentID  │
│TicketID (FK) │ │TicketID (FK) │ │HistoryID (PK)│ │TicketID (FK) │
│SchoolID (FK) │ │SchoolID (FK) │ │TicketID (FK) │ │SchoolID (FK) │
│FileName     │ │CommentText   │ │SchoolID (FK) │ │AssignedTo    │
│FileSize      │ │IsInternal    │ │FromStatusID  │ │AssignedBy    │
│FilePath      │ │CreatedAt     │ │ToStatusID    │ │IsActive      │
│FileData      │ │CreatedBy     │ │ChangeReason  │ │AssignedAt    │
│UploadedAt    │ │UpdatedAt     │ │IsReopenAction│ │UnassignedAt  │
│UploadedBy    │ │UpdatedBy     │ │ChangedAt     │ │UnassignedBy  │
└──────────────┘ └──────────────┘ │ChangedBy     │ └──────────────┘
                                  └──────────────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │TicketNotif   │
                                  │Log           │
                                  │──────────────│
                                  │NotificationID│
                                  │TicketID (FK) │
                                  │SchoolID (FK) │
                                  │RecipientUser │
                                  │NotifType     │
                                  │NotifEvent    │
                                  │IsSent        │
                                  │SentAt        │
                                  └──────────────┘
```

## 3. TICKET LIFECYCLE FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    TICKET LIFECYCLE                          │
└─────────────────────────────────────────────────────────────┘

    [User Creates Ticket]
            │
            ▼
    ┌───────────────┐
    │   NEW (1)     │ ◀── Initial State
    │   Status      │     Auto-assigned on creation
    └───────────────┘
            │
            │ [Admin/School Admin Assigns]
            ▼
    ┌───────────────┐
    │ ASSIGNED (2)  │
    │   Status      │
    └───────────────┘
            │
            │ [Support Executive Starts Work]
            ▼
    ┌───────────────┐
    │ IN PROGRESS   │ ◀──┐
    │     (3)       │    │ [Resume from On Hold]
    └───────────────┘    │
            │            │
            │ [Temporary Pause]
            ▼            │
    ┌───────────────┐    │
    │  ON HOLD (4)  │────┘
    │   Status      │
    └───────────────┘
            │
            │ [Solution Provided]
            ▼
    ┌───────────────┐
    │ RESOLVED (5)  │
    │   Status      │
    └───────────────┘
            │
            │ [Admin Closes]
            ▼
    ┌───────────────┐
    │  CLOSED (6)   │ ◀── Terminal State
    │   Status      │
    └───────────────┘
            │
            │ [Creator/Admin Reopens]
            ▼
    ┌───────────────┐
    │ RE-OPENED (7) │
    │   Status      │
    └───────────────┘
            │
            │ [Reassign and Continue]
            ▼
    [Back to ASSIGNED (2)]
```

## 4. ROLE-BASED ACCESS FLOW

```
┌─────────────────────────────────────────────────────────────┐
│              ROLE-BASED ACCESS CONTROL FLOW                  │
└─────────────────────────────────────────────────────────────┘

User Login
    │
    ▼
┌─────────────────┐
│ Get ProfileID   │
│ from UserMaster │
└─────────────────┘
    │
    ├──────────────────────────────────────────────────┐
    │                                                   │
    ▼                                                   ▼
ProfileID = 1                                    ProfileID = 2
┌─────────────────┐                            ┌─────────────────┐
│  SUPER ADMIN    │                            │  SCHOOL ADMIN   │
│─────────────────│                            │─────────────────│
│ ✓ All Tickets   │                            │ ✓ School Tickets│
│ ✓ All Schools   │                            │ ✓ Assign        │
│ ✓ Assign        │                            │ ✓ Reopen Any    │
│ ✓ Full Control  │                            │ ✓ Manage        │
└─────────────────┘                            └─────────────────┘
    │                                                   │
    ├──────────────────────────────────────────────────┤
    │                                                   │
    ▼                                                   ▼
ProfileID = 3                                    ProfileID = 4
┌─────────────────┐                            ┌─────────────────┐
│    TEACHER      │                            │    STUDENT      │
│─────────────────│                            │─────────────────│
│ ✓ Create Ticket │                            │ ✓ Create Ticket │
│ ✓ View Own      │                            │ ✓ View Own      │
│ ✓ Comment Own   │                            │ ✓ Comment Own   │
│ ✓ Reopen Own    │                            │ ✓ Reopen Own    │
│ ✗ Assign        │                            │ ✗ Assign        │
└─────────────────┘                            └─────────────────┘
    │
    ▼
ProfileID = 5
┌─────────────────┐
│SUPPORT EXECUTIVE│
│─────────────────│
│ ✓ View Assigned │
│ ✓ Change Status │
│ ✓ Comment       │
│ ✗ Create        │
│ ✗ Reopen        │
└─────────────────┘
```

## 5. API REQUEST FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    API REQUEST FLOW                          │
└─────────────────────────────────────────────────────────────┘

Client Request
    │
    ▼
┌─────────────────┐
│ Django Middleware│
│ - Session Check │
│ - CSRF Token    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ URL Routing     │
│ /tickets/*      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ View Function   │
│ @login_required │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Permission Check│
│ - Role-based    │
│ - Object-level  │
└─────────────────┘
    │
    ├─── DENIED ──▶ 403 Forbidden
    │
    ▼ ALLOWED
┌─────────────────┐
│ Business Logic  │
│ - Validation    │
│ - Processing    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Database Layer  │
│ - Stored Proc   │
│ - ORM Query     │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Serialization   │
│ - JSON Response │
└─────────────────┘
    │
    ▼
Client Response
```

## 6. REOPEN WORKFLOW

```
┌─────────────────────────────────────────────────────────────┐
│                    REOPEN WORKFLOW                           │
└─────────────────────────────────────────────────────────────┘

User Requests Reopen
    │
    ▼
┌─────────────────────────┐
│ Check Ticket Status     │
│ Must be CLOSED (6)      │
└─────────────────────────┘
    │
    ├─── NOT CLOSED ──▶ Error: "Only closed tickets can be reopened"
    │
    ▼ IS CLOSED
┌─────────────────────────┐
│ Check User Permission   │
│ - Is Ticket Creator?    │
│ - Is School Admin?      │
└─────────────────────────┘
    │
    ├─── NO ──▶ Error: "Access denied"
    │
    ▼ YES
┌─────────────────────────┐
│ Update TicketMaster     │
│ - StatusID = 7          │
│ - ReopenedCount++       │
│ - LastReopenedAt = NOW  │
│ - LastReopenedBy = User │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Log Status History      │
│ - FromStatusID = 6      │
│ - ToStatusID = 7        │
│ - IsReopenAction = 1    │
│ - ChangeReason          │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Send Notifications      │
│ - School Admin          │
│ - Previous Assignee     │
└─────────────────────────┘
    │
    ▼
Success Response
```

## 7. ASSIGNMENT WORKFLOW

```
┌─────────────────────────────────────────────────────────────┐
│                  ASSIGNMENT WORKFLOW                         │
└─────────────────────────────────────────────────────────────┘

Admin Assigns Ticket
    │
    ▼
┌─────────────────────────┐
│ Check User Permission   │
│ - Super Admin (1)?      │
│ - School Admin (2)?     │
└─────────────────────────┘
    │
    ├─── NO ──▶ Error: "Access denied"
    │
    ▼ YES
┌─────────────────────────┐
│ Validate Assignee       │
│ - ProfileID = 5?        │
│ - Is Active?            │
└─────────────────────────┘
    │
    ├─── INVALID ──▶ Error: "Invalid support executive"
    │
    ▼ VALID
┌─────────────────────────┐
│ Deactivate Previous     │
│ Assignments             │
│ - IsActive = 0          │
│ - UnassignedAt = NOW    │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Create New Assignment   │
│ - AssignedToUserID      │
│ - AssignedByUserID      │
│ - IsActive = 1          │
│ - AssignedAt = NOW      │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Update TicketMaster     │
│ - StatusID = 2          │
│ - AssignedToUserID      │
│ - UpdatedAt = NOW       │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Log Status History      │
│ - ToStatusID = 2        │
│ - ChangeReason          │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Send Notification       │
│ - To: Assignee          │
│ - Event: ASSIGNED       │
└─────────────────────────┘
    │
    ▼
Success Response
```

## 8. MULTI-TENANT ISOLATION

```
┌─────────────────────────────────────────────────────────────┐
│                MULTI-TENANT ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  School A    │  │  School B    │  │  School C    │
│  SchoolID=1  │  │  SchoolID=2  │  │  SchoolID=3  │
└──────────────┘  └──────────────┘  └──────────────┘
       │                 │                 │
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Shared Database │
              │  TicketMaster    │
              └──────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Tickets for  │  │ Tickets for  │  │ Tickets for  │
│ School A     │  │ School B     │  │ School C     │
│ SchoolID=1   │  │ SchoolID=2   │  │ SchoolID=3   │
└──────────────┘  └──────────────┘  └──────────────┘

Data Isolation:
- Every query filters by SchoolID
- Indexes include SchoolID
- Role-based access enforces school boundaries
- Super Admin can cross school boundaries
```

## 9. NOTIFICATION FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                   NOTIFICATION FLOW                          │
└─────────────────────────────────────────────────────────────┘

Ticket Event Occurs
    │
    ▼
┌─────────────────────────┐
│ Determine Event Type    │
│ - CREATED               │
│ - ASSIGNED              │
│ - STATUS_CHANGED        │
│ - COMMENT_ADDED         │
│ - REOPENED              │
│ - SLA_BREACH            │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Identify Recipients     │
│ - Ticket Creator        │
│ - Assigned User         │
│ - School Admin          │
│ - Support Team          │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Create Notification Log │
│ - TicketID              │
│ - RecipientUserID       │
│ - NotificationType      │
│ - NotificationEvent     │
│ - Subject & Body        │
└─────────────────────────┘
    │
    ├──────────────────────┐
    │                      │
    ▼                      ▼
┌──────────────┐    ┌──────────────┐
│ Email Queue  │    │ In-App Queue │
│ - SMTP Send  │    │ - Store in DB│
└──────────────┘    └──────────────┘
    │                      │
    ▼                      ▼
┌──────────────┐    ┌──────────────┐
│ Update Log   │    │ Update Log   │
│ - IsSent=1   │    │ - IsSent=1   │
│ - SentAt     │    │ - SentAt     │
└──────────────┘    └──────────────┘
```

## 10. DASHBOARD DATA FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                  DASHBOARD DATA FLOW                         │
└─────────────────────────────────────────────────────────────┘

User Requests Dashboard
    │
    ▼
┌─────────────────────────┐
│ Get User Profile        │
│ - ProfileID             │
│ - SchoolID              │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Execute Stored Proc     │
│ Proc_Ticket_Dashboard   │
│ - @UserID               │
│ - @SchoolID             │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Apply Role-Based Filter │
│ - Super Admin: All      │
│ - School Admin: School  │
│ - Teacher: Own          │
│ - Student: Own          │
│ - Support Exec: Assigned│
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Aggregate Statistics    │
│ - NewTickets            │
│ - AssignedTickets       │
│ - InProgressTickets     │
│ - OnHoldTickets         │
│ - ResolvedTickets       │
│ - ClosedTickets         │
│ - ReopenedTickets       │
│ - TotalTickets          │
│ - MyAssignedTickets     │
│ - MyCreatedTickets      │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│ Return JSON Response    │
│ - Status: success       │
│ - Data: {...}           │
└─────────────────────────┘
    │
    ▼
Frontend Renders Dashboard
```

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**ShikshaWave Development Team**
