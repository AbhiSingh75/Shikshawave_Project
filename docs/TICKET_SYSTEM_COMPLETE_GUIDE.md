# Ticket Management System - Complete Implementation Guide

## Overview
Production-grade Ticket Management System for ShikshaWave with strict role-based permissions enforced at database and API levels.

## Architecture

### Tech Stack
- **Backend**: Django (following ShikshaWave conventions)
- **Database**: Microsoft SQL Server with stored procedures
- **Frontend**: Django Templates + jQuery/HTMX
- **Styling**: Bootstrap (ShikshaWave theme)

### Role Mapping
- **Role 1**: Super Admin - Full access, can assign tickets, close tickets
- **Role 2**: School Admin - Create tickets for their school, reopen resolved tickets
- **Role 3**: Teacher - No ticket access
- **Role 4**: Support Executive - View assigned tickets, update status (Open → In Progress → Resolved)

## Database Schema

### Tables Created
1. **TicketCategory** - Ticket categories with seed data
2. **TicketPriority** - Priority levels (Low, Medium, High, Critical)
3. **TicketMaster** - Main ticket table with computed TicketNumber
4. **TicketActivityLog** - Audit trail of all ticket actions
5. **TicketComments** - Comments on tickets (internal/external)
6. **TicketAttachments** - File attachments

### Indexes
- IX_Ticket_SchoolID
- IX_Ticket_AssignedTo
- IX_Ticket_Status
- IX_Ticket_CreatedAt
- IX_Activity_Ticket
- IX_Comment_Ticket
- IX_Attachment_Ticket

## Stored Procedures

### 1. Proc_Ticket_Insert
**Purpose**: Create new ticket with role validation

**Parameters**:
- @UserID INT
- @RoleID INT
- @SchoolID INT (optional, auto-bound for School Admin)
- @CategoryID INT
- @Priority INT (1-4)
- @Subject NVARCHAR(255)
- @Description NVARCHAR(MAX)
- @AttachmentPath NVARCHAR(500)
- @TicketID BIGINT OUTPUT
- @ErrorMessage NVARCHAR(500) OUTPUT

**Validation**:
- School Admin: SchoolID auto-bound from user profile
- Super Admin: Must provide SchoolID
- Support Executive: Cannot create tickets (403)
- Validates category, priority, and school existence

**Returns**: 0 on success, error code on failure

### 2. Proc_Ticket_Assign
**Purpose**: Assign ticket to Support Executive (Super Admin only)

**Parameters**:
- @UserID INT
- @RoleID INT
- @TicketID BIGINT
- @AssignToUserID INT
- @Comment NVARCHAR(MAX)
- @ErrorMessage NVARCHAR(500) OUTPUT

**Validation**:
- Only Super Admin (Role 1) can assign
- Can only assign Open or Reopened tickets
- Assignee must be Support Executive (Role 4)
- Logs assignment in activity log

**Returns**: 0 on success, 403 if not Super Admin, 422 if invalid status

### 3. Proc_Ticket_UpdateStatus
**Purpose**: Update ticket status with role-based transition validation

**Parameters**:
- @UserID INT
- @RoleID INT
- @TicketID BIGINT
- @NewStatus VARCHAR(20)
- @Comment NVARCHAR(MAX)
- @ErrorMessage NVARCHAR(500) OUTPUT

**Allowed Transitions**:
- Support Executive (Role 4):
  - Open → In Progress
  - In Progress → Resolved
  - Must be assigned to user
- Super Admin (Role 1):
  - Resolved → Closed
- School Admin (Role 2):
  - Resolved → Reopened
  - Must be from same school

**Returns**: 0 on success, 403 if unauthorized, 422 if invalid transition

### 4. Proc_Tickets_GetByRole
**Purpose**: Get tickets with role-based filtering and pagination

**Parameters**:
- @UserID INT
- @RoleID INT
- @SchoolIDFilter INT (optional)
- @AssignedToFilter INT (optional)
- @StatusFilter VARCHAR(20) (optional)
- @CategoryFilter INT (optional)
- @PriorityFilter INT (optional)
- @SearchTerm NVARCHAR(255) (optional)
- @PageNumber INT (default 1)
- @PageSize INT (default 10)
- @SortColumn VARCHAR(50) (default 'CreatedAt')
- @SortDirection VARCHAR(4) (default 'DESC')

**Role-Based Filtering**:
- Super Admin: See all tickets (can filter by school)
- School Admin: Only their school's tickets
- Support Executive: Only tickets assigned to them

**Returns**: Paginated ticket list with total count

### 5. Proc_Ticket_GetDetails
**Purpose**: Get ticket details with activity log, comments, and attachments

**Parameters**:
- @UserID INT
- @RoleID INT
- @TicketID BIGINT
- @ErrorMessage NVARCHAR(500) OUTPUT

**Validation**:
- School Admin: Can only view tickets from their school
- Support Executive: Can only view tickets assigned to them
- Super Admin: Can view all tickets

**Returns**: 4 result sets:
1. Ticket details
2. Activity log
3. Comments
4. Attachments

## Django Implementation

### Models (tickets/models.py)
- TicketCategory
- TicketPriority
- TicketMaster (with TicketManager for role-aware queries)
- TicketActivityLog
- TicketComments
- TicketAttachments

### Service Layer (tickets/services.py)
- TicketService.create_ticket()
- TicketService.assign_ticket()
- TicketService.update_status()
- TicketService.get_tickets()
- TicketService.get_ticket_details()
- TicketService.add_comment()
- TicketService.get_support_executives()

### Views (tickets/views.py)
- ticket_list() - Display tickets with filters
- ticket_create() - Create new ticket
- ticket_detail() - View ticket details
- ticket_assign() - Assign ticket (POST)
- ticket_update_status() - Update status (POST)
- ticket_add_comment() - Add comment (POST)
- api_tickets_list() - AJAX endpoint
- api_support_executives() - AJAX endpoint

### URLs (tickets/urls.py)
```python
/tickets/ - List tickets
/tickets/create/ - Create ticket
/tickets/<id>/ - View ticket details
/tickets/assign/ - Assign ticket (POST)
/tickets/update-status/ - Update status (POST)
/tickets/add-comment/ - Add comment (POST)
/tickets/api/list/ - AJAX list
/tickets/api/support-executives/ - AJAX executives
```

## Frontend Templates

### ticket_list.html
- KPI cards (Open, In Progress, Resolved, Closed, Reopened)
- Filter form (search, school, status, priority, category)
- Tickets table with color-coded status and priority badges
- Pagination
- Role-based UI (hide/show create button, school column)

### ticket_create.html
- Category dropdown
- Priority dropdown (Low, Medium, High, Critical)
- School dropdown (Super Admin only, auto-filled for School Admin)
- Subject and description fields
- Attachment upload
- Form validation

### ticket_detail.html
- Ticket metadata (number, school, creator, assignee, category, priority, status)
- Description
- Assignment panel (Super Admin only, searchable list of Support Executives)
- Status action buttons (role-based, only show valid transitions)
- Activity timeline with timestamps
- Comments section with internal note toggle
- Attachments list with download links

## Installation Steps

### 1. Database Setup
```sql
-- Run in order:
1. database/tables/TicketSystem.sql
2. database/procedures/Proc_Ticket_Insert.sql
3. database/procedures/Proc_Ticket_Assign.sql
4. database/procedures/Proc_Ticket_UpdateStatus.sql
5. database/procedures/Proc_Tickets_GetByRole.sql
6. database/procedures/Proc_Ticket_GetDetails.sql
```

### 2. Django Setup
```python
# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    ...
    'tickets',
]

# Add to core/urls.py
from django.urls import path, include

urlpatterns = [
    ...
    path('tickets/', include('tickets.urls')),
]
```

### 3. Menu Setup
```sql
-- Add ticket menu items
INSERT INTO MenuMaster (MenuName, DisplayOrder, ParentMenuID, MenuURL, Icon, IsActive, CreatedAt, IsDeleted)
VALUES ('Tickets', 50, NULL, '/tickets/', 'fas fa-ticket-alt', 1, GETDATE(), 0);

DECLARE @TicketMenuID INT = SCOPE_IDENTITY();

-- Grant permissions
INSERT INTO ProfileMenuMapping (ProfileID, MenuID, CanView, CanAdd, CanEdit, CanDelete, CreatedAt, IsDeleted)
VALUES 
(1, @TicketMenuID, 1, 1, 1, 1, GETDATE(), 0), -- Super Admin
(2, @TicketMenuID, 1, 1, 0, 0, GETDATE(), 0), -- School Admin
(4, @TicketMenuID, 1, 0, 1, 0, GETDATE(), 0); -- Support Executive
```

### 4. Create Support Executive Users
```sql
-- Example: Create a support executive
INSERT INTO UserMaster (UserCode, UserName, PasswordHash, Email, Phone, ProfileID, SchoolID, IsActive, CreatedAt, IsDeleted)
VALUES ('SUPPORT001', 'Support Executive', '<hashed_password>', 'support@example.com', '1234567890', 4, NULL, 1, GETDATE(), 0);
```

## Testing Guide

### Test Case 1: School Admin Creates Ticket
```
1. Login as School Admin (Role 2)
2. Navigate to /tickets/create/
3. Fill form (school auto-filled, cannot change)
4. Submit
5. Verify ticket created with correct SchoolID
6. Verify activity log entry
```

### Test Case 2: Super Admin Assigns Ticket
```
1. Login as Super Admin (Role 1)
2. Navigate to ticket detail
3. Click "Assign" button
4. Select Support Executive from list
5. Submit
6. Verify ticket assigned
7. Verify activity log entry
8. Verify Support Executive can now see ticket
```

### Test Case 3: Support Executive Updates Status
```
1. Login as Support Executive (Role 4)
2. Navigate to assigned ticket
3. Click "Start Working" (Open → In Progress)
4. Verify status updated
5. Click "Mark Resolved" (In Progress → Resolved)
6. Verify status updated
7. Verify activity log entries
```

### Test Case 4: Super Admin Closes Ticket
```
1. Login as Super Admin (Role 1)
2. Navigate to resolved ticket
3. Click "Close Ticket" (Resolved → Closed)
4. Verify status updated
5. Verify ClosedAt timestamp set
```

### Test Case 5: School Admin Reopens Ticket
```
1. Login as School Admin (Role 2)
2. Navigate to resolved ticket from their school
3. Click "Reopen Ticket" (Resolved → Reopened)
4. Verify status updated
5. Verify ReopenedCount incremented
```

### Test Case 6: Permission Violations
```
1. Support Executive tries to create ticket → 403
2. School Admin tries to assign ticket → 403
3. Support Executive tries to update unassigned ticket → 403
4. School Admin tries to view other school's ticket → 403
5. Support Executive tries invalid transition (Open → Resolved) → 422
```

## API Documentation

### POST /tickets/create/
**Request**:
```json
{
  "school_id": 1,  // Optional for School Admin
  "category_id": 1,
  "priority": 2,
  "subject": "Login issue",
  "description": "Cannot login to system"
}
```

**Response**:
```json
{
  "success": true,
  "ticket_id": 123
}
```

### POST /tickets/assign/
**Request**:
```json
{
  "ticket_id": 123,
  "assign_to_user_id": 45,
  "comment": "Assigning to support team"
}
```

**Response**:
```json
{
  "success": true
}
```

### POST /tickets/update-status/
**Request**:
```json
{
  "ticket_id": 123,
  "new_status": "In Progress",
  "comment": "Started working on this"
}
```

**Response**:
```json
{
  "success": true
}
```

### GET /tickets/api/list/
**Query Parameters**:
- page (default: 1)
- page_size (default: 10)
- school_id (Super Admin only)
- assigned_to
- status
- category
- priority
- search

**Response**:
```json
{
  "success": true,
  "tickets": [...],
  "total_count": 50,
  "page": 1,
  "page_size": 10
}
```

## Security Features

### Server-Side Enforcement
- All role checks in stored procedures
- No client-side trust
- SQL injection prevention via parameterized queries
- XSS prevention via Django template escaping

### Audit Trail
- Every action logged in TicketActivityLog
- Includes: who, what, when, old/new values
- Immutable log (no updates/deletes)

### Rate Limiting
- Implement rate limiting on critical endpoints:
  - /tickets/assign/ - 10 requests/minute
  - /tickets/update-status/ - 20 requests/minute

### Input Validation
- Subject: max 255 characters
- Description: required, max 4000 characters
- Priority: 1-4 only
- Status: enum validation
- File uploads: size limits, type validation

## Performance Optimization

### Database
- Indexes on frequently queried columns
- Pagination to avoid full table scans
- Computed column for TicketNumber (no joins needed)

### Caching
- Cache categories and priorities (rarely change)
- Cache support executive list (5 minutes)

### Query Optimization
- Single stored procedure call for ticket list (no N+1)
- Batch loading of related data (activities, comments, attachments)

## Deployment Checklist

- [ ] Run all SQL scripts in order
- [ ] Add tickets app to INSTALLED_APPS
- [ ] Add URL patterns
- [ ] Create menu items and permissions
- [ ] Create at least one Support Executive user
- [ ] Test all role-based scenarios
- [ ] Verify stored procedures exist
- [ ] Check indexes created
- [ ] Test pagination
- [ ] Test search functionality
- [ ] Verify activity logging
- [ ] Test file attachments
- [ ] Mobile responsive testing
- [ ] Load testing (100+ tickets)

## Troubleshooting

### Issue: "Only Super Admin can assign tickets"
**Solution**: Verify user's ProfileID is 1 in session

### Issue: "Invalid status transition"
**Solution**: Check current status and role, verify allowed transitions

### Issue: "Ticket not found"
**Solution**: Verify ticket exists and user has permission to view

### Issue: Stored procedure not found
**Solution**: Run SQL scripts in correct order, check database connection

### Issue: School Admin sees all tickets
**Solution**: Verify SchoolID in session matches user's school

## Future Enhancements

1. **Email Notifications**
   - Notify assignee when ticket assigned
   - Notify creator when status changes
   - Daily digest for pending tickets

2. **SLA Management**
   - Define SLA by priority
   - Track response time and resolution time
   - Escalation rules

3. **Ticket Templates**
   - Pre-defined templates for common issues
   - Auto-fill category and priority

4. **Knowledge Base**
   - Link tickets to KB articles
   - Suggest articles based on ticket content

5. **Reports & Analytics**
   - Ticket volume trends
   - Average resolution time
   - Support executive performance
   - Category distribution

6. **Mobile App**
   - React Native app for support executives
   - Push notifications
   - Offline support

## Support

For issues or questions:
- Check logs: `logs/ticket_system.log`
- Review activity log in database
- Contact: support@shikshawave.in

## License

Proprietary - ShikshaWave Project
