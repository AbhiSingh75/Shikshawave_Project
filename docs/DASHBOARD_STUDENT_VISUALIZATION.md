# Dashboard Student Data Visualization

## Overview
This document describes the implementation of the Total Students Card data visualization on the Dashboard page with India standard school filters.

## Features Implemented

### 1. Stored Procedure: `Proc_Dashboard_Students_Get`
**Location:** `database/procedures/Proc_Dashboard_Students_Get.sql`

**Purpose:** Retrieve student statistics with flexible filtering options

**Parameters:**
- `@SchoolID` - Filter by school (required for multi-school systems)
- `@ClassID` - Filter by class
- `@SectionID` - Filter by section
- `@AcademicYear` - Filter by academic year
- `@Gender` - Filter by gender (Male/Female)
- `@Category` - Filter by category (General/OBC/SC/ST)

**Returns Two Result Sets:**

**Result Set 1 - Summary Statistics:**
- `TotalStudents` - Total count of students
- `MaleStudents` - Count of male students
- `FemaleStudents` - Count of female students
- `GeneralCategory` - Count of General category students
- `OBCCategory` - Count of OBC category students
- `SCCategory` - Count of SC category students
- `STCategory` - Count of ST category students
- `ActiveStudents` - Count of active students
- `InactiveStudents` - Count of inactive students

**Result Set 2 - Class-wise Breakdown:**
- `ClassID` - Class identifier
- `ClassName` - Class name
- `StudentCount` - Total students in class
- `MaleCount` - Male students in class
- `FemaleCount` - Female students in class

### 2. Backend Implementation

**View Function:** `dashboard_view` in `core/views.py`
- Fetches initial dashboard statistics on page load
- Passes data to template context

**API Endpoint:** `api_dashboard_students` in `core/views.py`
- URL: `/api/dashboard/students/`
- Method: GET
- Authentication: Required (custom_login_required)
- Returns JSON with filtered statistics

**URL Route:** Added to `core/urls.py`
```python
path('api/dashboard/students/', views.api_dashboard_students, name='api_dashboard_students')
```

### 3. Frontend Implementation

**Dashboard Template:** `core/templates/core/dashboard.html`

**Filter Section:**
- Class dropdown (populated from `/api/classes/`)
- Section dropdown (populated dynamically based on class selection)
- Gender dropdown (Male/Female/All)
- Category dropdown (General/OBC/SC/ST/All)
- Academic Year dropdown (populated from `/api/academic-years/`)
- Apply Filters button

**Dashboard Cards:**
1. **Total Students** - Shows total student count
2. **Male Students** - Shows male student count
3. **Female Students** - Shows female student count
4. **Active Students** - Shows active student count
5. **Category Breakdown** - Shows category-wise distribution

**JavaScript Features:**
- Async filter loading on page load
- Dynamic section loading based on class selection
- AJAX call to update statistics without page reload
- Real-time card updates based on filter selection

## India Standard School Filters

The implementation follows India's standard school categorization:

### Gender Classification
- Male
- Female

### Category Classification (Reservation System)
- **General** - General category students
- **OBC** - Other Backward Classes
- **SC** - Scheduled Castes
- **ST** - Scheduled Tribes

### Academic Structure
- Class-based organization (1st to 12th standard)
- Section-based division (A, B, C, etc.)
- Academic year tracking

## Usage

### Installation

1. **Execute the stored procedure:**
```sql
-- Run the SQL file
sqlcmd -S your_server -d your_database -i database/procedures/Proc_Dashboard_Students_Get.sql
```

2. **Restart Django server:**
```bash
python manage.py runserver
```

### Using the Dashboard

1. **Navigate to Dashboard:**
   - Login to the system
   - You'll be redirected to the dashboard automatically

2. **View Default Statistics:**
   - Initial load shows all students for your school
   - Cards display total counts

3. **Apply Filters:**
   - Select desired filters (Class, Section, Gender, Category, Academic Year)
   - Click "Apply Filters" button
   - Cards update automatically with filtered data

4. **Reset Filters:**
   - Select "All" options in dropdowns
   - Click "Apply Filters" to see all students again

## API Usage

### Get Filtered Student Statistics

**Endpoint:** `GET /api/dashboard/students/`

**Query Parameters:**
- `class_id` (optional) - Filter by class ID
- `section_id` (optional) - Filter by section ID
- `gender` (optional) - Filter by gender (Male/Female)
- `category` (optional) - Filter by category (General/OBC/SC/ST)
- `academic_year` (optional) - Filter by academic year

**Example Request:**
```javascript
fetch('/api/dashboard/students/?class_id=5&gender=Male&category=General')
  .then(response => response.json())
  .then(data => {
    console.log(data.stats.total_students);
    console.log(data.class_breakdown);
  });
```

**Example Response:**
```json
{
  "success": true,
  "stats": {
    "total_students": 150,
    "male_students": 80,
    "female_students": 70,
    "general_category": 90,
    "obc_category": 40,
    "sc_category": 15,
    "st_category": 5,
    "active_students": 145,
    "inactive_students": 5
  },
  "class_breakdown": [
    {
      "class_id": 1,
      "class_name": "Class 1",
      "student_count": 30,
      "male_count": 16,
      "female_count": 14
    }
  ]
}
```

## Database Schema Requirements

### Required Tables
- `Student` - Main student table
- `ClassMaster` - Class information
- `SectionMaster` - Section information

### Required Columns in Student Table
- `StudentID` - Primary key
- `SchoolID` - School reference
- `ClassID` - Class reference
- `SectionID` - Section reference
- `Gender` - Student gender (Male/Female)
- `Category` - Student category (General/OBC/SC/ST)
- `AcademicYear` - Academic year
- `IsActive` - Active status
- `IsDeleted` - Soft delete flag

## Performance Considerations

1. **Indexing:**
   - Ensure indexes on `SchoolID`, `ClassID`, `SectionID` in Student table
   - Index on `Gender` and `Category` for faster filtering

2. **Caching:**
   - Filter dropdowns (classes, academic years) are loaded once on page load
   - Consider implementing Redis caching for frequently accessed data

3. **Query Optimization:**
   - Stored procedure uses efficient COUNT with CASE statements
   - Single query for all statistics reduces database round trips

## Future Enhancements

1. **Additional Filters:**
   - Religion-based filtering
   - Age group filtering
   - Admission date range filtering

2. **Visualizations:**
   - Add charts (pie chart for category distribution)
   - Bar chart for class-wise comparison
   - Trend analysis over academic years

3. **Export Features:**
   - Export filtered data to Excel
   - Generate PDF reports
   - Email scheduled reports

4. **Real-time Updates:**
   - WebSocket integration for live updates
   - Auto-refresh on data changes

## Troubleshooting

### Issue: Filters not loading
**Solution:** Check if API endpoints are accessible and returning data

### Issue: Statistics showing zero
**Solution:** Verify Student table has data and IsDeleted = 0

### Issue: Section dropdown not populating
**Solution:** Ensure class is selected first and sections exist for that class

## Support

For issues or questions, contact the development team or refer to the main project documentation.

## Version History

- **v1.0** (2024) - Initial implementation with basic filters and statistics
