# Next Steps - Employee Attendance Implementation

## ✅ Completed
- [x] Updated menu structure in database
- [x] Renamed student attendance menus
- [x] Added employee/staff attendance menus
- [x] Added new profile types (Accountant, Driver, Librarian)
- [x] Configured profile permissions
- [x] Updated Django models

## 🔨 To Do - Backend Implementation

### 1. Create Database Table for Employee Attendance
Create migration file: `core/migrations/0051_create_employee_attendance.py`

```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0050_update_attendance_menu'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE EmployeeAttendance (
                AttendanceID INT PRIMARY KEY IDENTITY(1,1),
                EmployeeID INT NOT NULL,
                SchoolID INT NOT NULL,
                AttendanceDate DATE NOT NULL,
                Status VARCHAR(20) NOT NULL,
                CheckInTime TIME,
                CheckOutTime TIME,
                Remarks VARCHAR(500),
                CreatedBy INT,
                CreatedAt DATETIME DEFAULT GETDATE(),
                UpdatedBy INT,
                UpdatedAt DATETIME,
                IsDeleted BIT DEFAULT 0,
                FOREIGN KEY (EmployeeID) REFERENCES UserMaster(UserID),
                FOREIGN KEY (SchoolID) REFERENCES SchoolMaster(SchoolID),
                FOREIGN KEY (CreatedBy) REFERENCES UserMaster(UserID),
                FOREIGN KEY (UpdatedBy) REFERENCES UserMaster(UserID)
            );
            
            CREATE INDEX IX_EmployeeAttendance_Employee ON EmployeeAttendance(EmployeeID);
            CREATE INDEX IX_EmployeeAttendance_Date ON EmployeeAttendance(AttendanceDate);
            CREATE INDEX IX_EmployeeAttendance_School ON EmployeeAttendance(SchoolID);
            """,
            reverse_sql="DROP TABLE EmployeeAttendance;"
        ),
    ]
```

### 2. Create Django Model
Add to `core/models.py`:

```python
class EmployeeAttendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
        ('Half Day', 'Half Day'),
        ('Late', 'Late'),
    ]
    
    attendance_id = models.AutoField(primary_key=True, db_column='AttendanceID')
    employee = models.ForeignKey(UserMaster, on_delete=models.CASCADE, db_column='EmployeeID', related_name='employee_attendance')
    school = models.ForeignKey(SchoolMaster, on_delete=models.CASCADE, db_column='SchoolID')
    attendance_date = models.DateField(db_column='AttendanceDate')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_column='Status')
    check_in_time = models.TimeField(null=True, blank=True, db_column='CheckInTime')
    check_out_time = models.TimeField(null=True, blank=True, db_column='CheckOutTime')
    remarks = models.CharField(max_length=500, null=True, blank=True, db_column='Remarks')
    created_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='CreatedBy', related_name='emp_attendance_created_by')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, db_column='UpdatedBy', related_name='emp_attendance_updated_by')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='UpdatedAt')
    is_deleted = models.BooleanField(default=False, db_column='IsDeleted')

    class Meta:
        db_table = 'EmployeeAttendance'
        managed = False
        unique_together = ('employee', 'attendance_date', 'school')

    def __str__(self):
        return f"{self.employee.user_name} - {self.attendance_date} - {self.status}"
```

### 3. Create Views
Add to `core/views.py` or create `core/attendance_views.py`:

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

@login_required
def mark_employee_attendance_view(request):
    """View to mark employee/staff attendance"""
    user = request.user
    school_id = user.school_id
    
    if request.method == 'POST':
        # Handle attendance marking logic
        pass
    
    # Get list of employees for the school
    employees = UserMaster.objects.filter(
        school_id=school_id,
        profile_id__in=[3, 5, 6, 7],  # Teacher, Accountant, Driver, Librarian
        is_deleted=False,
        is_active=True
    )
    
    context = {
        'employees': employees,
        'today': date.today(),
    }
    return render(request, 'core/mark_employee_attendance.html', context)

@login_required
def view_employee_attendance_view(request):
    """View to display employee/staff attendance records"""
    user = request.user
    school_id = user.school_id
    
    # Get attendance records
    attendance_records = EmployeeAttendance.objects.filter(
        school_id=school_id,
        is_deleted=False
    ).select_related('employee').order_by('-attendance_date')
    
    context = {
        'attendance_records': attendance_records,
    }
    return render(request, 'core/view_employee_attendance.html', context)
```

### 4. Update URLs
Add to `core/urls.py`:

```python
from core import attendance_views

urlpatterns = [
    # ... existing patterns ...
    path('attendance/mark-employee/', attendance_views.mark_employee_attendance_view, name='mark_employee_attendance'),
    path('attendance/view-employee/', attendance_views.view_employee_attendance_view, name='view_employee_attendance'),
]
```

### 5. Create Templates

#### Template 1: `core/templates/core/mark_employee_attendance.html`
```html
{% extends 'base.html' %}
{% block content %}
<div class="container mt-4">
    <h2><i class="fas fa-user-tie"></i> Mark Employee/Staff Attendance</h2>
    
    <form method="post">
        {% csrf_token %}
        <div class="row mb-3">
            <div class="col-md-4">
                <label>Date</label>
                <input type="date" name="attendance_date" class="form-control" value="{{ today }}" required>
            </div>
        </div>
        
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>Employee Name</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Remarks</th>
                </tr>
            </thead>
            <tbody>
                {% for employee in employees %}
                <tr>
                    <td>{{ employee.user_name }}</td>
                    <td>{{ employee.profile.profile_name }}</td>
                    <td>
                        <select name="status_{{ employee.user_id }}" class="form-control">
                            <option value="Present">Present</option>
                            <option value="Absent">Absent</option>
                            <option value="Leave">Leave</option>
                            <option value="Half Day">Half Day</option>
                            <option value="Late">Late</option>
                        </select>
                    </td>
                    <td><input type="time" name="checkin_{{ employee.user_id }}" class="form-control"></td>
                    <td><input type="time" name="checkout_{{ employee.user_id }}" class="form-control"></td>
                    <td><input type="text" name="remarks_{{ employee.user_id }}" class="form-control"></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <button type="submit" class="btn btn-primary">
            <i class="fas fa-save"></i> Save Attendance
        </button>
    </form>
</div>
{% endblock %}
```

#### Template 2: `core/templates/core/view_employee_attendance.html`
```html
{% extends 'base.html' %}
{% block content %}
<div class="container mt-4">
    <h2><i class="fas fa-users"></i> View Employee/Staff Attendance</h2>
    
    <div class="row mb-3">
        <div class="col-md-3">
            <input type="date" id="filterDate" class="form-control" placeholder="Filter by date">
        </div>
        <div class="col-md-3">
            <select id="filterStatus" class="form-control">
                <option value="">All Status</option>
                <option value="Present">Present</option>
                <option value="Absent">Absent</option>
                <option value="Leave">Leave</option>
            </select>
        </div>
    </div>
    
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Date</th>
                <th>Employee Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Check In</th>
                <th>Check Out</th>
                <th>Remarks</th>
            </tr>
        </thead>
        <tbody>
            {% for record in attendance_records %}
            <tr>
                <td>{{ record.attendance_date }}</td>
                <td>{{ record.employee.user_name }}</td>
                <td>{{ record.employee.profile.profile_name }}</td>
                <td>
                    <span class="badge badge-{% if record.status == 'Present' %}success{% elif record.status == 'Absent' %}danger{% else %}warning{% endif %}">
                        {{ record.status }}
                    </span>
                </td>
                <td>{{ record.check_in_time|default:"-" }}</td>
                <td>{{ record.check_out_time|default:"-" }}</td>
                <td>{{ record.remarks|default:"-" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

### 6. Create Stored Procedures (Optional but Recommended)

Create `database/procedures/Proc_EmployeeAttendance_Mark.sql`:
```sql
CREATE PROCEDURE Proc_EmployeeAttendance_Mark
    @SchoolID INT,
    @EmployeeID INT,
    @AttendanceDate DATE,
    @Status VARCHAR(20),
    @CheckInTime TIME = NULL,
    @CheckOutTime TIME = NULL,
    @Remarks VARCHAR(500) = NULL,
    @CreatedBy INT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM EmployeeAttendance 
               WHERE EmployeeID = @EmployeeID 
               AND AttendanceDate = @AttendanceDate 
               AND IsDeleted = 0)
    BEGIN
        UPDATE EmployeeAttendance
        SET Status = @Status,
            CheckInTime = @CheckInTime,
            CheckOutTime = @CheckOutTime,
            Remarks = @Remarks,
            UpdatedBy = @CreatedBy,
            UpdatedAt = GETDATE()
        WHERE EmployeeID = @EmployeeID 
        AND AttendanceDate = @AttendanceDate 
        AND IsDeleted = 0;
    END
    ELSE
    BEGIN
        INSERT INTO EmployeeAttendance (SchoolID, EmployeeID, AttendanceDate, Status, CheckInTime, CheckOutTime, Remarks, CreatedBy)
        VALUES (@SchoolID, @EmployeeID, @AttendanceDate, @Status, @CheckInTime, @CheckOutTime, @Remarks, @CreatedBy);
    END
END
```

## 📋 Testing Checklist

- [ ] Run migrations successfully
- [ ] Verify menu appears for correct profiles
- [ ] Test marking employee attendance
- [ ] Test viewing employee attendance
- [ ] Test filtering and searching
- [ ] Verify permissions work correctly
- [ ] Test with different user roles

## 🎯 Priority Order

1. **High Priority**: Database table and model creation
2. **High Priority**: Basic mark attendance functionality
3. **Medium Priority**: View attendance with filters
4. **Low Priority**: Reports and analytics
5. **Low Priority**: Bulk import/export

## 📞 Need Help?

Refer to existing student attendance implementation for reference:
- `core/templates/core/student_attendance.html`
- `core/templates/core/view_attendance.html`

Good luck! 🚀
