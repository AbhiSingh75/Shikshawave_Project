# Class Timetable Management System

## Quick Installation

### 1. Run the Installation Script
Execute this single SQL file to install everything:
```bash
sqlcmd -S YOUR_SERVER_NAME -d ShikshaWave -i database/INSTALL_TIMETABLE_SYSTEM.sql
```

Or in SQL Server Management Studio, open and execute:
`database/INSTALL_TIMETABLE_SYSTEM.sql`

### 2. Restart Django Server
```bash
# Stop the server (Ctrl+C)
# Then restart:
python manage.py runserver
```

### 3. Access the System
Navigate to: **Class → Timetable Management**

## Quick Start Guide

### Step 1: Setup Periods (One-time)
1. Go to **Period Setup** tab
2. Add your school's periods, for example:
   - Assembly: 08:00-08:15 (Assembly)
   - Period 1: 08:15-09:00 (Class)
   - Period 2: 09:00-09:45 (Class)
   - Short Break: 09:45-10:00 (Break)
   - Period 3: 10:00-10:45 (Class)
   - Period 4: 10:45-11:30 (Class)
   - Lunch: 11:30-12:15 (Break)
   - Period 5: 12:15-13:00 (Class)
   - Period 6: 13:00-13:45 (Class)
   - Period 7: 13:45-14:30 (Class)

### Step 2: Create Timetable
1. Go to **Timetables** tab
2. Click **+ Create Timetable**
3. Select Class and Section
4. Enter Academic Year (e.g., 2024-25)
5. Set effective dates
6. Click **Create**

### Step 3: Fill Timetable
1. Go to **View Timetable** tab
2. Select your timetable
3. Click on empty slots to add:
   - Subject
   - Teacher
   - Room number
4. Save each slot

### Step 4: Print
Click the **🖨️ Print** button to get a clean printout

## Features
✅ Period-based scheduling
✅ Monday to Saturday support
✅ Subject & teacher assignment
✅ Room allocation
✅ Break/Assembly periods
✅ Print-friendly view
✅ Multiple timetables per class
✅ Academic year tracking

## Files Created
- `core/timetable_views.py` - Backend logic
- `core/templates/core/timetable_management.html` - Main interface
- `core/templates/core/timetable_view.html` - Timetable display
- `database/tables/ClassTimetable.sql` - Database tables
- `database/procedures/Proc_Timetable_Management.sql` - Stored procedures
- `database/INSTALL_TIMETABLE_SYSTEM.sql` - Complete installation
- `docs/TIMETABLE_MANAGEMENT_GUIDE.md` - Detailed documentation

## Support
For detailed documentation, see: `docs/TIMETABLE_MANAGEMENT_GUIDE.md`
