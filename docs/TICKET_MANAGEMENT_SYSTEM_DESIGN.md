# Ticket Management System - Technical Design Document
## ShikshaWave ERP Platform

---

## 1. OVERVIEW

The Ticket Management System is a comprehensive support module for ShikshaWave ERP platform that enables users to create, track, and resolve support tickets with role-based access control, SLA management, and complete audit trails.

### Technology Stack
- **Backend**: Django (Python)
- **Database**: Microsoft SQL Server
- **Architecture**: Multi-tenant SaaS
- **Authentication**: Session-based with ProfileMaster roles

---

## 2. DATABASE SCHEMA

### 2.1 Entity-Relationship Model

```
TicketMaster (Core Entity)
├── SchoolID (FK → SchoolMaster)
├── CategoryID (FK → TicketCategory)
├── PriorityID (FK → TicketPriority)
├── StatusID (FK → TicketStatus)
├── CreatedByUserID (FK → UserMaster)
├── AssignedToUserID (FK → UserMaster)
└── Related Tables:
    ├── TicketAttachments (1:N)
    ├── TicketComments (1:N)
    ├── TicketStatusHistory (1:N)
    ├── TicketAssignment (1:N)
    └── TicketNotificationLog (1:N)
```

### 2.2 Table Definitions

#### TicketMaster
Primary table storing all ticket information.

**Columns:**
- `TicketID` (PK, INT, IDENTITY)
- `TicketNumber` (VARCHAR(50), UNIQUE) - Auto-generated: TKT{YYYYMM}{Sequence}
- `SchoolID` (INT, FK) - Multi-tenancy isolation
- `Title` (NVARCHAR(200))
- `Description` (NVARCHAR(MAX))
- `CategoryID` (INT, FK)
- `PriorityID` (INT, FK)
- `StatusID` (INT, FK)
- `CreatedByUserID` (INT, FK)
- `AssignedToUserID` (INT, FK, NULL)
- `ResolutionNotes` (NVARCHAR(MAX), NULL)
- `ResolvedAt` (DATETIME, NULL)
- `ClosedAt` (DATETIME, NULL)
- `ReopenedCount` (INT, DEFAULT 0)
- `LastReopenedAt` (DATETIME, NULL)
- `LastReopenedBy` (INT, FK, NULL)
- Audit fields: CreatedAt, UpdatedAt, CreatedBy, UpdatedBy, IsDeleted, DeletedAt, DeletedBy

**Indexes:**
- IX_TicketMaster_SchoolID (SchoolID) INCLUDE (StatusID, PriorityID, CategoryID)
- IX_TicketMaster_StatusID (StatusID) INCLUDE (SchoolID, AssignedToUserID)
- IX_TicketMaster_AssignedToUserID (AssignedToUserID) WHERE AssignedToUserID IS NOT NULL
- IX_TicketMaster_CreatedByUserID (CreatedByUserID)
- IX_TicketMaster_CreatedAt (CreatedAt DESC)
- IX_TicketMaster_IsDeleted (IsDeleted) WHERE IsDeleted = 0

#### TicketCategory
Categorizes tickets (Technical, Academic, Administrative, etc.)

**Default Categories:**
1. Technical Support (TECH)
2. Academic Query (ACAD)
3. Administrative (ADMIN)
4. Fee Related (FEE)
5. Admission (ADMN)
6. Attendance (ATTN)
7. Exam (EXAM)
8. Other (OTHER)

#### TicketPriority
Priority levels with SLA implications.

**Default Priorities:**
1. Low (Priority Level 1, Color: #28a745)
2. Medium (Priority Level 2, Color: #ffc107)
3. High (Priority Level 3, Color: #fd7e14)
4. Critical (Priority Level 4, Color: #dc3545)

#### TicketStatus
Workflow states for ticket lifecycle.

**Status Flow:**
1. New (NEW) → Initial state
2. Assigned (ASSIGNED) → Assigned to support executive
3. In Progress (IN_PROGRESS) → Work started
4. On Hold (ON_HOLD) → Temporarily paused
5. Resolved (RESOLVED) → Solution provided
6. Closed (CLOSED) → Ticket completed
7. Re-Opened (REOPENED) → Reopened after closure

#### TicketAttachments
Stores file attachments for tickets.

**Columns:**
- `AttachmentID` (PK)
- `TicketID` (FK)
- `SchoolID` (FK)
- `FileName`, `FileSize`, `FileType`, `FilePath`
- `FileData` (VARBINARY(MAX)) - Binary storage
- `UploadedAt`, `UploadedBy`
- Soft delete fields

#### TicketComments
Communication thread for tickets.

**Columns:**
- `CommentID` (PK)
- `TicketID` (FK)
- `SchoolID` (FK)
- `CommentText` (NVARCHAR(MAX))
- `IsInternal` (BIT) - Internal notes vs public comments
- Audit fields

#### TicketStatusHistory
Complete audit trail of status changes.

**Columns:**
- `HistoryID` (PK)
- `TicketID` (FK)
- `SchoolID` (FK)
- `FromStatusID` (FK, NULL)
- `ToStatusID` (FK)
- `ChangeReason` (NVARCHAR(500))
- `IsReopenAction` (BIT) - Flags reopen events
- `ChangedAt`, `ChangedBy`

#### SLAMaster
Service Level Agreement definitions.

**Default SLAs:**
- Critical: 1hr response, 4hr resolution
- High: 2hr response, 8hr resolution
- Medium: 4hr response, 24hr resolution
- Low: 8hr response, 48hr resolution

#### TicketAssignment
Tracks assignment history.

**Columns:**
- `AssignmentID` (PK)
- `TicketID` (FK)
- `SchoolID` (FK)
- `AssignedToUserID` (FK)
- `AssignedByUserID` (FK)
- `AssignmentNotes`
- `IsActive` (BIT)
- `AssignedAt`, `UnassignedAt`, `UnassignedBy`

#### TicketNotificationLog
Logs all notifications sent.

**Notification Events:**
- CREATED, ASSIGNED, STATUS_CHANGED, COMMENT_ADDED, REOPENED, SLA_BREACH

**Notification Types:**
- EMAIL, IN_APP

#### ProfileMaster Extension
Added new role:
- **ProfileID = 5**: Support Executive

---

## 3. ROLE-BASED ACCESS CONTROL

### 3.1 Role Definitions

| Role ID | Role Name | Access Level |
|---------|-----------|--------------|
| 1 | Super Admin | Full access to all tickets across all schools |
| 2 | School Admin | Manage all tickets within their school |
| 3 | Teacher | Create and view own tickets |
| 4 | Student | Create and view own tickets |
| 5 | Support Executive | View and work on assigned tickets only |

### 3.2 Permission Matrix

| Action | Super Admin | School Admin | Teacher | Student | Support Exec |
|--------|-------------|--------------|---------|---------|--------------|
| Create Ticket | ✓ | ✓ | ✓ | ✓ | ✗ |
| View All Tickets | ✓ | ✓ (School) | ✗ | ✗ | ✗ |
| View Own Tickets | ✓ | ✓ | ✓ | ✓ | ✗ |
| View Assigned Tickets | ✓ | ✓ | ✗ | ✗ | ✓ |
| Assign Ticket | ✓ | ✓ | ✗ | ✗ | ✗ |
| Change Status | ✓ | ✓ | ✗ | ✗ | ✓ (Assigned) |
| Add Comment | ✓ | ✓ | ✓ (Own) | ✓ (Own) | ✓ (Assigned) |
| Reopen Ticket | ✓ | ✓ | ✓ (Own) | ✓ (Own) | ✗ |
| Delete Ticket | ✓ | ✓ | ✗ | ✗ | ✗ |

### 3.3 Reopen Logic
- Only **Closed** tickets can be reopened
- Only **ticket creator** or **School Admin** can reopen
- Reopening sets status to **Re-Opened** (StatusID = 7)
- `ReopenedCount` increments
- `LastReopenedAt` and `LastReopenedBy` updated
- Status history logs with `IsReopenAction = 1`

---

## 4. TICKET LIFECYCLE

### 4.1 Status Workflow

```
New (1)
  ↓
Assigned (2)
  ↓
In Progress (3)
  ↓ ↔ On Hold (4)
  ↓
Resolved (5)
  ↓
Closed (6)
  ↓ (Reopen by creator/admin)
Re-Opened (7)
  ↓
Assigned (2) → [cycle continues]
```

### 4.2 State Transitions

**Valid Transitions:**
- New → Assigned (on assignment)
- Assigned → In Progress (support executive starts work)
- In Progress → On Hold (temporary pause)
- On Hold → In Progress (resume work)
- In Progress → Resolved (solution provided)
- Resolved → Closed (ticket completion)
- Closed → Re-Opened (reopen action)
- Re-Opened → Assigned (reassignment)

---

## 5. API ENDPOINTS

### 5.1 Ticket Management

#### Create Ticket
```
POST /tickets/create/
Body: {
  "title": "string",
  "description": "string",
  "category_id": int,
  "priority_id": int
}
Response: {
  "status": "success",
  "ticket_id": int,
  "ticket_number": "TKT202401000001"
}
```

#### Get Ticket List
```
GET /tickets/list/?status_id=1&priority_id=3&category_id=2&search=text&page=1&page_size=20
Response: {
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 150,
    "total_pages": 8
  }
}
```

#### Get Ticket Detail
```
GET /tickets/{ticket_id}/
Response: {
  "status": "success",
  "data": {
    "ticket_id": int,
    "ticket_number": "string",
    "title": "string",
    "description": "string",
    "category": {...},
    "priority": {...},
    "status": {...},
    "attachments": [...],
    "comments": [...],
    "status_history": [...]
  }
}
```

#### Assign Ticket
```
POST /tickets/{ticket_id}/assign/
Body: {
  "assigned_to_user_id": int,
  "assignment_notes": "string"
}
```

#### Change Status
```
POST /tickets/{ticket_id}/status/
Body: {
  "new_status_id": int,
  "change_reason": "string",
  "resolution_notes": "string" (if resolving)
}
```

#### Reopen Ticket
```
POST /tickets/{ticket_id}/reopen/
Body: {
  "reopen_reason": "string"
}
```

#### Add Comment
```
POST /tickets/{ticket_id}/comment/
Body: {
  "comment_text": "string",
  "is_internal": boolean
}
```

### 5.2 Metadata Endpoints

```
GET /tickets/categories/
GET /tickets/priorities/
GET /tickets/statuses/
GET /tickets/dashboard/
```

---

## 6. STORED PROCEDURES

### 6.1 Proc_Ticket_Create
Creates new ticket with auto-generated ticket number.

**Parameters:**
- @SchoolID, @Title, @Description, @CategoryID, @PriorityID, @CreatedByUserID
- @TicketID OUTPUT, @TicketNumber OUTPUT

**Logic:**
- Generate unique ticket number: TKT{YYYYMM}{6-digit sequence}
- Insert into TicketMaster with StatusID = 1 (New)
- Log initial status in TicketStatusHistory

### 6.2 Proc_Ticket_Assign
Assigns ticket to support executive.

**Parameters:**
- @TicketID, @AssignedToUserID, @AssignedByUserID, @AssignmentNotes

**Logic:**
- Deactivate previous assignments
- Create new assignment record
- Update ticket status to Assigned (StatusID = 2)
- Log status change

### 6.3 Proc_Ticket_Reopen
Reopens closed ticket with validation.

**Parameters:**
- @TicketID, @ReopenedByUserID, @ReopenReason

**Logic:**
- Validate ticket is closed (StatusID = 6)
- Validate user is creator or School Admin
- Update status to Re-Opened (StatusID = 7)
- Increment ReopenedCount
- Log with IsReopenAction = 1

### 6.4 Proc_Ticket_StatusChange
Updates ticket status.

**Parameters:**
- @TicketID, @NewStatusID, @ChangedByUserID, @ChangeReason, @ResolutionNotes

**Logic:**
- Update ticket status
- Set ResolvedAt if status = 5
- Set ClosedAt if status = 6
- Log status change

### 6.5 Proc_Ticket_GetList
Retrieves filtered ticket list with role-based access.

**Parameters:**
- @UserID, @SchoolID, @StatusID, @PriorityID, @CategoryID, @SearchText, @PageNumber, @PageSize

**Logic:**
- Apply role-based filtering
- Apply additional filters
- Return paginated results

### 6.6 Proc_Ticket_Dashboard
Returns dashboard statistics.

**Returns:**
- NewTickets, AssignedTickets, InProgressTickets, OnHoldTickets
- ResolvedTickets, ClosedTickets, ReopenedTickets
- TotalTickets, MyAssignedTickets, MyCreatedTickets

---

## 7. DJANGO IMPLEMENTATION

### 7.1 Models
Location: `core/ticket_system/models.py`

All models use `managed = False` to prevent Django migrations from altering SQL Server schema.

### 7.2 Serializers
Location: `core/ticket_system/serializers.py`

- TicketListSerializer - List view
- TicketDetailSerializer - Detail view with nested relations
- TicketCreateSerializer - Create validation
- TicketUpdateSerializer - Update validation
- TicketAssignSerializer - Assignment validation
- TicketStatusChangeSerializer - Status change validation
- TicketReopenSerializer - Reopen validation
- TicketCommentCreateSerializer - Comment validation

### 7.3 Views
Location: `core/ticket_system/views.py`

All views use `@login_required_custom` decorator for authentication.

### 7.4 Permissions
Location: `core/ticket_system/permissions.py`

- TicketPermission - General access control
- CanReopenTicket - Reopen-specific permission
- CanAssignTicket - Assignment permission

### 7.5 URL Routing
Location: `core/ticket_system/urls.py`

Integrated into main URLs via:
```python
# In core/urls.py
path('tickets/', include('core.ticket_system.urls')),
```

---

## 8. FRONTEND REQUIREMENTS

### 8.1 Ticket Creation Form
**Fields:**
- Title (required, max 200 chars)
- Description (required, rich text editor)
- Category (dropdown)
- Priority (dropdown)
- Attachments (file upload, multiple)

**Validation:**
- All required fields must be filled
- File size limit: 10MB per file
- Allowed file types: pdf, doc, docx, jpg, png, xlsx

### 8.2 Ticket Detail Page

**Sections:**
1. **Header**
   - Ticket number, title, status badge, priority badge
   - Created by, created date
   - Assigned to (if assigned)

2. **Status Timeline**
   - Visual timeline showing status progression
   - Timestamps for each status change
   - User who made the change
   - Highlight reopen events

3. **Description**
   - Full ticket description
   - Resolution notes (if resolved)

4. **Attachments Section**
   - List of uploaded files
   - Download links
   - Upload new attachment button

5. **Comment Thread**
   - Chronological list of comments
   - User avatar, name, timestamp
   - Internal/public indicator
   - Add comment form

6. **Action Buttons**
   - Change Status (dropdown with valid transitions)
   - Assign to Support Executive (for admins)
   - Reopen Ticket (visible only when closed, for creator/admin)
   - Add Comment

### 8.3 Ticket List Page

**Features:**
- Tabular view with columns: Ticket#, Title, Category, Priority, Status, Created Date, Assigned To
- Color-coded priority and status badges
- Search bar (searches ticket#, title, description)
- Filters: Status, Priority, Category, School (for Super Admin)
- Pagination (20 records per page)
- Click row to view detail

### 8.4 Support Executive Console

**Dashboard Widgets:**
- My Assigned Tickets count
- Tickets by Status (pie chart)
- Tickets by Priority (bar chart)
- SLA breach alerts

**Filters:**
- Priority (multi-select)
- Category (multi-select)
- School (for Super Admin)
- Status (multi-select)
- Date range

**Quick Actions:**
- Bulk status update
- Reassign tickets
- Export to Excel

### 8.5 Dashboard

**Metrics:**
- Total Tickets
- New Tickets
- In Progress Tickets
- Resolved Today
- Closed This Week
- Reopened Tickets
- Average Resolution Time
- SLA Compliance %

**Charts:**
- Tickets by Category (pie chart)
- Tickets by Priority (donut chart)
- Ticket Trend (line chart - last 30 days)
- Resolution Time by Priority (bar chart)

---

## 9. NOTIFICATION WORKFLOW

### 9.1 Email Notifications

**Triggers:**
1. **Ticket Created**
   - To: School Admin, Support Team
   - Subject: "New Ticket Created - {TicketNumber}"

2. **Ticket Assigned**
   - To: Assigned Support Executive
   - Subject: "Ticket Assigned to You - {TicketNumber}"

3. **Status Changed**
   - To: Ticket Creator, Assigned Support Executive
   - Subject: "Ticket Status Updated - {TicketNumber}"

4. **Comment Added**
   - To: Ticket Creator, Assigned Support Executive (if not commenter)
   - Subject: "New Comment on Ticket - {TicketNumber}"

5. **Ticket Reopened**
   - To: School Admin, Previously Assigned Support Executive
   - Subject: "Ticket Reopened - {TicketNumber}"

6. **SLA Breach**
   - To: School Admin, Support Team Lead
   - Subject: "SLA Breach Alert - {TicketNumber}"

### 9.2 In-App Notifications

**Display:**
- Bell icon with unread count
- Notification dropdown with recent 10 notifications
- Link to full notification center

**Persistence:**
- Store in TicketNotificationLog
- Mark as read/unread
- Auto-expire after 30 days

---

## 10. AUDIT LOGGING

### 10.1 Logged Actions

All actions logged in TicketStatusHistory and application logs:
- Ticket creation
- Ticket update (title, description, category, priority)
- Status changes
- Assignment/reassignment
- Comment addition
- Attachment upload
- Reopen action
- Soft delete

### 10.2 Audit Fields

Every table includes:
- CreatedAt, CreatedBy
- UpdatedAt, UpdatedBy
- DeletedAt, DeletedBy, IsDeleted

### 10.3 Audit Reports

**Available Reports:**
- Ticket Activity Log (by ticket)
- User Activity Log (by user)
- Status Change Report
- Reopen Frequency Report
- SLA Compliance Report

---

## 11. SCALABILITY CONSIDERATIONS

### 11.1 Indexing Strategy

**Composite Indexes:**
- (SchoolID, StatusID, PriorityID) - Most common filter combination
- (AssignedToUserID, StatusID) - Support executive workload
- (CreatedAt DESC) - Recent tickets

**Filtered Indexes:**
- WHERE IsDeleted = 0 - Active records only
- WHERE AssignedToUserID IS NOT NULL - Assigned tickets
- WHERE IsReopenAction = 1 - Reopen events

### 11.2 Pagination

- Default page size: 20 records
- Maximum page size: 100 records
- Use OFFSET-FETCH for SQL Server pagination
- Return total count for UI pagination controls

### 11.3 Table Partitioning

**Partition Strategy:**
- Partition TicketMaster by CreatedAt (monthly partitions)
- Partition TicketStatusHistory by ChangedAt (monthly partitions)
- Partition TicketNotificationLog by CreatedAt (monthly partitions)

**Benefits:**
- Faster queries on recent data
- Easier archival of old data
- Improved maintenance operations

### 11.4 Ticket Archiving

**Archive Policy:**
- Archive closed tickets older than 2 years
- Move to TicketMaster_Archive table
- Maintain same schema
- Keep indexes for historical queries

**Archive Process:**
```sql
-- Monthly job
INSERT INTO TicketMaster_Archive
SELECT * FROM TicketMaster
WHERE StatusID = 6 
  AND ClosedAt < DATEADD(YEAR, -2, GETDATE());

DELETE FROM TicketMaster
WHERE StatusID = 6 
  AND ClosedAt < DATEADD(YEAR, -2, GETDATE());
```

### 11.5 School-Level Isolation

**Query Optimization:**
- Always filter by SchoolID first
- Use SchoolID in all composite indexes
- Partition by SchoolID for large deployments

**Connection Pooling:**
- Configure Django connection pool
- Set MAX_CONNECTIONS based on concurrent users
- Use read replicas for reporting queries

### 11.6 Caching Strategy

**Cache Layers:**
1. **Metadata Cache** (Redis)
   - Categories, Priorities, Statuses
   - TTL: 1 hour

2. **Dashboard Cache**
   - Dashboard counts
   - TTL: 5 minutes

3. **User Permission Cache**
   - Role-based permissions
   - TTL: 30 minutes

---

## 12. MENU INTEGRATION

### 12.1 MenuMaster Structure

```
Ticket Management (MenuID: Auto, ParentMenuID: NULL)
├── My Tickets (URL: /tickets/my-tickets/)
├── Create Ticket (URL: /tickets/create/)
├── All Tickets (URL: /tickets/all/)
├── Assigned Tickets (URL: /tickets/assigned/)
└── Ticket Dashboard (URL: /tickets/dashboard/)
```

### 12.2 ProfileMenuMapping

**Super Admin (ProfileID = 1):**
- All menus: CanView=1, CanAdd=1, CanEdit=1, CanDelete=1

**School Admin (ProfileID = 2):**
- All menus: CanView=1, CanAdd=1, CanEdit=1, CanDelete=1

**Teacher (ProfileID = 3):**
- My Tickets: CanView=1
- Create Ticket: CanView=1, CanAdd=1

**Student (ProfileID = 4):**
- My Tickets: CanView=1
- Create Ticket: CanView=1, CanAdd=1

**Support Executive (ProfileID = 5):**
- Assigned Tickets: CanView=1, CanEdit=1

### 12.3 Installation Script

Location: `database/ticket_system/add_ticket_menus.sql`

Run after table creation to add menus and permissions.

---

## 13. INSTALLATION GUIDE

### 13.1 Database Setup

**Step 1: Create Tables**
```bash
# Execute in order:
01_TicketMaster.sql
02_TicketCategory.sql
03_TicketPriority.sql
04_TicketStatus.sql
05_TicketAttachments.sql
06_TicketComments.sql
07_TicketStatusHistory.sql
08_SLAMaster.sql
09_TicketAssignment.sql
10_ProfileMaster_SupportExecutive.sql
11_TicketNotificationLog.sql
```

**Step 2: Create Stored Procedures**
```bash
Proc_Ticket_Create.sql
Proc_Ticket_Assign.sql
Proc_Ticket_Reopen.sql
Proc_Ticket_StatusChange.sql
Proc_Ticket_GetList.sql
Proc_Ticket_Dashboard.sql
```

**Step 3: Add Menus**
```bash
add_ticket_menus.sql
```

### 13.2 Django Setup

**Step 1: Update core/urls.py**
```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('tickets/', include('core.ticket_system.urls')),
]
```

**Step 2: No migrations needed**
All models use `managed = False`

### 13.3 Verification

**Test Queries:**
```sql
-- Verify tables
SELECT COUNT(*) FROM TicketMaster;
SELECT COUNT(*) FROM TicketCategory;

-- Verify procedures
EXEC Proc_Ticket_Dashboard @UserID=1, @SchoolID=NULL;

-- Verify menus
SELECT * FROM MenuMaster WHERE MenuName LIKE '%Ticket%';
```

---

## 14. TESTING CHECKLIST

### 14.1 Functional Testing

- [ ] Create ticket as Teacher
- [ ] Create ticket as Student
- [ ] Assign ticket as School Admin
- [ ] Change status as Support Executive
- [ ] Add comment to ticket
- [ ] Upload attachment
- [ ] Reopen closed ticket as creator
- [ ] Reopen closed ticket as School Admin
- [ ] Verify reopen denied for non-creator/non-admin
- [ ] Filter tickets by status, priority, category
- [ ] Search tickets by keyword
- [ ] View dashboard statistics

### 14.2 Permission Testing

- [ ] Super Admin sees all tickets
- [ ] School Admin sees only school tickets
- [ ] Teacher sees only own tickets
- [ ] Student sees only own tickets
- [ ] Support Executive sees only assigned tickets
- [ ] Verify assignment permission (Admin only)
- [ ] Verify reopen permission (Creator/Admin only)

### 14.3 Performance Testing

- [ ] Create 10,000 tickets
- [ ] Query with filters (< 2 seconds)
- [ ] Dashboard load (< 1 second)
- [ ] Pagination performance
- [ ] Concurrent user load (50+ users)

---

## 15. MAINTENANCE

### 15.1 Regular Tasks

**Daily:**
- Monitor SLA breaches
- Check notification queue
- Review error logs

**Weekly:**
- Analyze ticket trends
- Review resolution times
- Check disk space (attachments)

**Monthly:**
- Archive old tickets
- Rebuild indexes
- Update statistics

### 15.2 Monitoring Queries

```sql
-- SLA Breach Check
SELECT t.TicketID, t.TicketNumber, t.CreatedAt, 
       s.ResolutionTimeHours,
       DATEDIFF(HOUR, t.CreatedAt, GETDATE()) AS HoursOpen
FROM TicketMaster t
INNER JOIN SLAMaster s ON t.PriorityID = s.PriorityID
WHERE t.StatusID NOT IN (5, 6)
  AND DATEDIFF(HOUR, t.CreatedAt, GETDATE()) > s.ResolutionTimeHours;

-- Reopen Frequency
SELECT t.TicketNumber, t.ReopenedCount, t.LastReopenedAt
FROM TicketMaster t
WHERE t.ReopenedCount > 2
ORDER BY t.ReopenedCount DESC;
```

---

## 16. FUTURE ENHANCEMENTS

1. **AI-Powered Categorization**: Auto-categorize tickets using ML
2. **Chatbot Integration**: First-level support via chatbot
3. **Knowledge Base**: Link tickets to KB articles
4. **Customer Satisfaction**: Post-resolution surveys
5. **Mobile App**: Native mobile app for ticket management
6. **WhatsApp Integration**: Create tickets via WhatsApp
7. **Advanced Analytics**: Predictive analytics for ticket volume
8. **Multi-Language Support**: Localization for regional schools

---

## DOCUMENT VERSION

- **Version**: 1.0
- **Date**: 2024
- **Author**: ShikshaWave Development Team
- **Status**: Production Ready

