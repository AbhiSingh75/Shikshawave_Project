# Staff Attendance - Quick Start Guide

## 🚀 3-Step Installation

### Step 1: Install Menu Updates
```bash
cd c:\Users\AbhishekKumar\Desktop\ShikshaWave_Project
python manage.py migrate
```

### Step 2: Install Database Procedures
Execute this SQL file:
```
database/install_staff_attendance_procedures.sql
```

### Step 3: Restart Server
```bash
python manage.py runserver
```

## ✅ Done! Access the Pages

- **Mark Attendance**: http://localhost:8000/attendance/mark-employee/
- **View Attendance**: http://localhost:8000/attendance/view-employee/

## 📋 What You Can Do

### Mark Attendance
1. Select date
2. Mark status for each staff member (Present/Absent/Leave/Half Day/Late)
3. Add remarks (optional)
4. Click Save

### View Attendance
1. Filter by date range
2. Filter by employee
3. Filter by status
4. View all records with color-coded status badges

## 👥 Who Can Access?

- School Admin ✓
- Teacher ✓
- Accountant ✓
- Driver ✓
- Librarian ✓

## 📁 Files Created

✅ 3 Database Procedures
✅ 1 Views File (staff_attendance_views.py)
✅ 2 HTML Templates
✅ URLs Updated

**Total: 7 files created, 1 file modified**

## 🎉 Ready to Use!
