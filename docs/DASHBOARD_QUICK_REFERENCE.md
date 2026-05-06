# Dashboard Views - Quick Reference

## File Location
`core/dashboard_views.py`

## Functions

### 1. dashboard_view(request)
**Purpose:** Main dashboard page rendering  
**URL:** `/dashboard/`  
**Authentication:** Required  
**Returns:** Rendered dashboard.html with statistics

**What it does:**
- Fetches user menus
- Gets active student statistics
- Renders dashboard template

### 2. api_dashboard_students(request)
**Purpose:** API endpoint for filtered student data  
**URL:** `/api/dashboard/students/`  
**Method:** GET  
**Authentication:** Required

**Query Parameters:**
- `from_date` - Filter by creation date (from)
- `to_date` - Filter by creation date (to)
- `class_id` - Filter by class
- `section_id` - Filter by section
- `gender` - Filter by gender (Male/Female)
- `category` - Filter by category (General/OBC/SC/ST)
- `academic_year` - Filter by academic year
- `show_active_only` - Show only active students (default: 1)

**Response:**
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
  "class_breakdown": [...]
}
```

## Visibility Rules

**Student Cards Visible To:**
- School Admin (Profile ID = 2)
- Teacher (Profile ID = 3)

**Hidden From:**
- Super Admin (Profile ID = 1)
- Student (Profile ID = 4)
- Other profiles

## Default Behavior

- Shows **only active students** by default
- No date filters applied initially
- All filters optional
- Reset button clears all filters

## Usage Examples

### Example 1: Get all active students
```javascript
fetch('/api/dashboard/students/')
  .then(res => res.json())
  .then(data => console.log(data.stats.active_students));
```

### Example 2: Filter by date range
```javascript
fetch('/api/dashboard/students/?from_date=2024-01-01&to_date=2024-12-31')
  .then(res => res.json())
  .then(data => console.log(data));
```

### Example 3: Filter by class and gender
```javascript
fetch('/api/dashboard/students/?class_id=5&gender=Male')
  .then(res => res.json())
  .then(data => console.log(data));
```

## Testing

```bash
# Test dashboard page
curl -b cookies.txt http://localhost:8000/dashboard/

# Test API endpoint
curl -b cookies.txt http://localhost:8000/api/dashboard/students/

# Test with filters
curl -b cookies.txt "http://localhost:8000/api/dashboard/students/?class_id=5&gender=Male"
```

## Troubleshooting

**Issue:** Dashboard not loading  
**Solution:** Check if user is logged in and has valid session

**Issue:** No statistics showing  
**Solution:** Verify Student table has data with IsDeleted=0 and IsActive=1

**Issue:** Filters not working  
**Solution:** Check browser console for JavaScript errors

**Issue:** Cards not visible  
**Solution:** Verify user profile_id is 2 or 3

## Related Files

- **Template:** `core/templates/core/dashboard.html`
- **Stored Procedure:** `database/procedures/Proc_Dashboard_Students_Get.sql`
- **URLs:** `core/urls.py`
- **Main Views:** `core/views.py` (helper functions)

## Notes

- All dashboard code is now in `dashboard_views.py`
- Main `views.py` only contains comments pointing to new file
- No functionality changed - only code organization improved
- Follows minimal code principles
