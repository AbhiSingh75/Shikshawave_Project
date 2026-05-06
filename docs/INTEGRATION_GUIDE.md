# Student ID Card Integration Guide

## Quick Integration Steps

### 1. Add ID Card Button to View Students Page

Update `view_students_cards.html` to add ID card view button in the action buttons section:

```html
<!-- In the card actions section -->
<div class="card-actions">
    <button class="action-btn view" onclick="viewIDCard('{{ student.StudentID }}')" title="View ID Card">
        <i class="fas fa-id-card"></i>
    </button>
    <button class="action-btn edit" data-student-id="{{ student.StudentID }}" data-action="edit" title="Edit Student">
        <i class="fas fa-edit"></i>
    </button>
    <button class="action-btn delete" data-student-id="{{ student.StudentID }}" data-action="delete" title="Delete Student">
        <i class="fas fa-trash"></i>
    </button>
</div>
```

Add JavaScript function:

```javascript
function viewIDCard(studentId) {
    window.open(`/student/idcard/${studentId}/`, '_blank');
}
```

### 2. Add ID Card Button to Student Profile Page

If you have a student profile page, add:

```html
<a href="{% url 'student_id_card' student.StudentID %}" class="btn btn-primary" target="_blank">
    <i class="fas fa-id-card"></i> View ID Card
</a>
```

### 3. Add to Table View Actions

In the table view section of `view_students_cards.html`:

```html
<td class="actions-cell">
    <button class="action-btn view" onclick="viewIDCard('{{ student.StudentID }}')" title="View ID Card">
        <i class="fas fa-id-card"></i>
    </button>
    <button class="action-btn edit" data-student-id="{{ student.StudentID }}" data-action="edit" title="Edit Student">
        <i class="fas fa-edit"></i>
    </button>
    <button class="action-btn delete" data-student-id="{{ student.StudentID }}" data-action="delete" title="Delete Student">
        <i class="fas fa-trash"></i>
    </button>
</td>
```

### 4. Add CSS for ID Card Button (Optional)

```css
.action-btn.id-card {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.action-btn.id-card:hover {
    background: linear-gradient(135deg, #059669, #047857);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
}
```

## Testing the Integration

### Test Checklist
1. ✅ Navigate to View Students page
2. ✅ Click ID Card button on any student
3. ✅ Verify ID card opens in new tab
4. ✅ Check all student details display correctly
5. ✅ Test print functionality
6. ✅ Test on mobile device
7. ✅ Verify template selection works from Template Management

### Test URLs
```
# Direct access
http://localhost:8000/student/idcard/1/

# With print mode
http://localhost:8000/student/idcard/1/?print=1

# Template Management
http://localhost:8000/template-management/
```

## Template Selection Flow

1. Admin goes to Template Management
2. Selects Student ID Card template (horizontal or vertical)
3. Clicks "Apply"
4. Template preference saved to database
5. All ID card views now use selected template

## Troubleshooting

### Issue: Student not found
**Solution:** Verify student ID exists and belongs to logged-in school

### Issue: Template not loading
**Solution:** Check TemplatePreference table has entry for school

### Issue: Photos not displaying
**Solution:** Verify Photo field in Student table contains valid image data

### Issue: Print not working
**Solution:** Check browser print settings and CSS @media print rules

## API Endpoints Used

```python
# View function
GET /student/idcard/<student_id>/

# Template preview
GET /student/card/preview/?template=<template_name>

# Template management
POST /template-management/save/
```

## Database Queries

```sql
-- Get student data
SELECT s.*, c.ClassName, sec.SectionName, sch.*
FROM Student s
LEFT JOIN ClassMaster c ON s.ClassID = c.ClassID
LEFT JOIN SectionMaster sec ON s.SectionID = sec.SectionID
LEFT JOIN SchoolMaster sch ON s.SchoolID = sch.SchoolID
WHERE s.StudentID = @StudentID AND s.SchoolID = @SchoolID

-- Get template preference
SELECT TemplateFile 
FROM TemplatePreference 
WHERE SchoolID = @SchoolID 
  AND TemplateType = 'StudentCard' 
  AND IsDeleted = 0
```

## Security Considerations

1. ✅ Login required for all ID card views
2. ✅ School ID validation from session
3. ✅ Student-school relationship verified
4. ✅ No direct database access from frontend
5. ✅ Base64 encoding for images (no file paths exposed)

## Performance Tips

1. Images converted to Base64 once per request
2. Template selection cached in context
3. Minimal database queries
4. No external API calls
5. Optimized CSS for fast rendering

## Mobile Optimization

- Responsive card dimensions
- Touch-friendly buttons
- Optimized font sizes
- Proper viewport settings
- Fast load times

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS/Android)

## Next Steps

1. Test integration on development server
2. Verify all templates display correctly
3. Test print functionality
4. Deploy to production
5. Train users on template selection
6. Monitor for any issues

---

**Integration Status:** Ready for implementation
**Estimated Time:** 15-30 minutes
**Difficulty:** Easy
