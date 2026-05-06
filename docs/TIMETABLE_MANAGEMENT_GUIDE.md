# Class Timetable Management System - Installation Guide

## Overview
This system provides comprehensive class timetable management for Indian schools following standard practices:
- Period-based scheduling (typically 6-8 periods per day)
- Monday to Saturday schedule
- Support for breaks, assembly, and activity periods
- Subject and teacher assignment
- Room allocation
- Print-friendly timetable view

## Installation Steps

### 1. Create Database Tables
Run the following SQL script to create the required tables:
```bash
sqlcmd -S YOUR_SERVER -d ShikshaWave -i database/tables/ClassTimetable.sql
```

Or execute in SQL Server Management Studio:
```sql
-- Run: database/tables/ClassTimetable.sql
```

### 2. Create Stored Procedures
Run the stored procedures script:
```bash
sqlcmd -S YOUR_SERVER -d ShikshaWave -i database/procedures/Proc_Timetable_Management.sql
```

### 3. Add Menu Items
Run the menu installation script:
```bash
sqlcmd -S YOUR_SERVER -d ShikshaWave -i database/add_timetable_menu.sql
```

### 4. Restart Django Server
After all database changes, restart your Django development server:
```bash
python manage.py runserver
```

## Features

### 1. Period Setup
- Define school periods with start and end times
- Support for different period types:
  - **Class**: Regular teaching periods
  - **Break**: Recess/lunch breaks
  - **Assembly**: Morning assembly
  - **Activity**: Sports/extra-curricular activities
- Flexible display order

### 2. Timetable Creation
- Create timetables for specific classes and sections
- Academic year tracking
- Effective date ranges
- Multiple timetables for different terms

### 3. Interactive Timetable Grid
- Visual weekly schedule (Monday to Saturday)
- Drag-and-drop style slot assignment
- Subject and teacher allocation
- Room number assignment
- Notes for special instructions

### 4. Print Support
- Clean, print-friendly layout
- Professional formatting
- School branding support

## Usage Guide

### Setting Up Periods (First Time)
1. Navigate to **Class → Timetable Management**
2. Click on **Period Setup** tab
3. Add periods in order:
   - Period 1: 08:00 - 08:45 (Class)
   - Period 2: 08:45 - 09:30 (Class)
   - Break: 09:30 - 09:45 (Break)
   - Period 3: 09:45 - 10:30 (Class)
   - ... and so on

### Creating a Timetable
1. Go to **Timetables** tab
2. Click **+ Create Timetable**
3. Select:
   - Class (e.g., Class 10)
   - Section (e.g., A)
   - Academic Year (e.g., 2024-25)
   - Effective dates
4. Click **Create**

### Filling the Timetable
1. Go to **View Timetable** tab
2. Select the timetable from dropdown
3. Click on any empty slot to add:
   - Subject
   - Teacher
   - Room number (optional)
   - Notes (optional)
4. Click **Save**

### Printing Timetable
1. View the timetable
2. Click **🖨️ Print** button
3. Use browser print dialog

## Indian School Standards

This system follows typical Indian school patterns:

### Standard School Day
- **Assembly**: 08:00 - 08:15
- **Period 1**: 08:15 - 09:00
- **Period 2**: 09:00 - 09:45
- **Short Break**: 09:45 - 10:00
- **Period 3**: 10:00 - 10:45
- **Period 4**: 10:45 - 11:30
- **Lunch Break**: 11:30 - 12:15
- **Period 5**: 12:15 - 13:00
- **Period 6**: 13:00 - 13:45
- **Period 7**: 13:45 - 14:30

### Working Days
- Monday to Saturday (6-day week)
- Sunday off

### Common Subjects
- Mathematics
- Science (Physics, Chemistry, Biology)
- Social Studies (History, Geography, Civics)
- Languages (English, Hindi, Regional)
- Computer Science
- Physical Education
- Arts/Music

## Permissions

### Super Admin & School Admin
- Full access: Create, view, edit, delete timetables
- Manage periods
- Assign teachers and subjects

### Teachers
- View only access
- Can see their assigned periods
- Cannot modify timetables

### Students
- No direct access (view through class teacher)

## API Endpoints

- `GET /timetable/management/` - Main management page
- `GET /timetable/periods/` - List all periods
- `POST /timetable/period/save/` - Save period
- `POST /timetable/period/delete/` - Delete period
- `GET /timetable/list/` - List all timetables
- `POST /timetable/create/` - Create new timetable
- `GET /timetable/view/<id>/` - View specific timetable
- `POST /timetable/slot/save/` - Save timetable slot
- `POST /timetable/delete/` - Delete timetable

## Troubleshooting

### Menu not appearing
1. Check if menu was added: `SELECT * FROM MenuMaster WHERE MenuName = 'Timetable Management'`
2. Check permissions: `SELECT * FROM ProfileMenuMapping WHERE MenuID = (SELECT MenuID FROM MenuMaster WHERE MenuName = 'Timetable Management')`
3. Clear browser cache and refresh

### Cannot save slots
1. Ensure subjects are created for the class
2. Ensure teachers exist in the system
3. Check that timetable is active

### Print layout issues
1. Use Chrome/Edge for best results
2. Set margins to "Default" in print dialog
3. Enable "Background graphics" option

## Future Enhancements
- Teacher workload analysis
- Conflict detection (same teacher, multiple classes)
- Automatic timetable generation
- Mobile app for teachers
- Student-specific timetable view
- Substitution management

## Support
For issues or questions, contact the development team.
