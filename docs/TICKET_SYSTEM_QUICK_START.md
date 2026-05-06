# Ticket Management System - Quick Start Guide

## Installation (5 Minutes)

### Step 1: Database Installation

Open SQL Server Management Studio and execute:

```sql
-- Option A: Run master script (recommended)
:r database\ticket_system\INSTALL_TICKET_SYSTEM.sql

-- Option B: Run individual scripts in order
-- 1. Tables (01-11)
-- 2. Procedures
-- 3. Menus
```

### Step 2: Django Integration

Add to `core/urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('tickets/', include('core.ticket_system.urls')),
]
```

### Step 3: Restart Django

```bash
python manage.py runserver
```

## Usage Examples

### Create Ticket (API)

```bash
curl -X POST http://localhost:8000/tickets/create/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cannot access fee payment module",
    "description": "Getting 500 error when trying to collect fees",
    "category_id": 1,
    "priority_id": 3
  }'
```

### Get Ticket List

```bash
curl http://localhost:8000/tickets/list/?status_id=1&page=1&page_size=20
```

### Assign Ticket

```bash
curl -X POST http://localhost:8000/tickets/123/assign/ \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to_user_id": 45,
    "assignment_notes": "Assigning to senior support executive"
  }'
```

### Change Status

```bash
curl -X POST http://localhost:8000/tickets/123/status/ \
  -H "Content-Type: application/json" \
  -d '{
    "new_status_id": 3,
    "change_reason": "Started investigating the issue"
  }'
```

### Reopen Ticket

```bash
curl -X POST http://localhost:8000/tickets/123/reopen/ \
  -H "Content-Type: application/json" \
  -d '{
    "reopen_reason": "Issue not fully resolved, still getting errors"
  }'
```

### Add Comment

```bash
curl -X POST http://localhost:8000/tickets/123/comment/ \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "Checked the logs, found database connection timeout",
    "is_internal": false
  }'
```

## Role-Based Access

### Super Admin (ProfileID = 1)
- Full access to all tickets
- Can assign tickets
- Can manage all schools

### School Admin (ProfileID = 2)
- Manage tickets for their school
- Can assign tickets
- Can reopen any school ticket

### Teacher (ProfileID = 3)
- Create tickets
- View own tickets
- Add comments to own tickets
- Reopen own tickets

### Student (ProfileID = 4)
- Create tickets
- View own tickets
- Add comments to own tickets
- Reopen own tickets

### Support Executive (ProfileID = 5)
- View assigned tickets
- Change status of assigned tickets
- Add comments to assigned tickets
- Cannot create or reopen tickets

## Common Workflows

### Workflow 1: Student Reports Issue

1. Student creates ticket (Status: New)
2. School Admin assigns to Support Executive (Status: Assigned)
3. Support Executive starts work (Status: In Progress)
4. Support Executive resolves issue (Status: Resolved)
5. School Admin closes ticket (Status: Closed)

### Workflow 2: Ticket Reopened

1. Ticket is Closed
2. Student reopens (Status: Re-Opened)
3. School Admin reassigns (Status: Assigned)
4. Support Executive works again (Status: In Progress)
5. Issue resolved and closed

### Workflow 3: Ticket On Hold

1. Ticket is In Progress
2. Support Executive puts on hold (Status: On Hold)
3. Later resumes work (Status: In Progress)
4. Resolves and closes

## Database Queries

### Get All Open Tickets for a School

```sql
SELECT t.TicketNumber, t.Title, s.StatusName, p.PriorityName
FROM TicketMaster t
INNER JOIN TicketStatus s ON t.StatusID = s.StatusID
INNER JOIN TicketPriority p ON t.PriorityID = p.PriorityID
WHERE t.SchoolID = 1
  AND t.StatusID NOT IN (6) -- Not Closed
  AND t.IsDeleted = 0
ORDER BY p.PriorityLevel DESC, t.CreatedAt ASC;
```

### Get Tickets Breaching SLA

```sql
SELECT t.TicketNumber, t.Title, 
       DATEDIFF(HOUR, t.CreatedAt, GETDATE()) AS HoursOpen,
       s.ResolutionTimeHours AS SLAHours
FROM TicketMaster t
INNER JOIN SLAMaster s ON t.PriorityID = s.PriorityID
WHERE t.StatusID NOT IN (5, 6)
  AND DATEDIFF(HOUR, t.CreatedAt, GETDATE()) > s.ResolutionTimeHours;
```

### Get Reopen Statistics

```sql
SELECT 
    COUNT(*) AS TotalReopened,
    AVG(ReopenedCount) AS AvgReopenCount,
    MAX(ReopenedCount) AS MaxReopenCount
FROM TicketMaster
WHERE ReopenedCount > 0;
```

## Testing Checklist

- [ ] Create ticket as Teacher
- [ ] Create ticket as Student
- [ ] View ticket list (filtered by role)
- [ ] Assign ticket as School Admin
- [ ] Change status as Support Executive
- [ ] Add comment to ticket
- [ ] Reopen closed ticket
- [ ] Verify reopen permission denied for non-creator
- [ ] Check dashboard statistics
- [ ] Test search and filters

## Troubleshooting

### Issue: Cannot create ticket

**Check:**
- User is authenticated
- User has valid ProfileID (1-5)
- SchoolID is set for user
- Category and Priority IDs are valid

### Issue: Cannot assign ticket

**Check:**
- User is Super Admin or School Admin
- Assigned user has ProfileID = 5 (Support Executive)
- Ticket exists and is not deleted

### Issue: Cannot reopen ticket

**Check:**
- Ticket status is Closed (StatusID = 6)
- User is ticket creator OR School Admin
- Ticket is not deleted

### Issue: Stored procedure not found

**Solution:**
```sql
-- Re-run procedure creation scripts
:r database\ticket_system\procedures\Proc_Ticket_Create.sql
:r database\ticket_system\procedures\Proc_Ticket_Assign.sql
-- etc.
```

## Performance Tips

1. **Use Pagination**: Always use page_size parameter (default: 20)
2. **Filter Early**: Apply status/priority filters to reduce result set
3. **Index Usage**: Queries automatically use optimized indexes
4. **Cache Metadata**: Cache categories, priorities, statuses (change rarely)
5. **Archive Old Tickets**: Run monthly archival for tickets > 2 years old

## Support

For detailed technical documentation, see:
- `docs/TICKET_MANAGEMENT_SYSTEM_DESIGN.md`

For database schema, see:
- `database/ticket_system/tables/`

For stored procedures, see:
- `database/ticket_system/procedures/`

---

**Version**: 1.0  
**Last Updated**: 2024  
**ShikshaWave Development Team**
