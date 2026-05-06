# Exam Timetable Templates - Quick Installation Guide

## Installation Steps

### Step 1: Verify Files Created
Ensure all template files are in place:
```
core/templates/core/document_templates/exam_timetable/
├── exam_timetable_template1.html
├── exam_timetable_template2.html
├── exam_timetable_template3.html
├── exam_timetable_template4.html
├── exam_timetable_template5.html
├── exam_timetable_template6.html
├── exam_timetable_template7.html
├── exam_timetable_template8.html
├── exam_timetable_template9.html
└── exam_timetable_template10.html
```

### Step 2: Verify Code Updates
Check that the following files have been updated:
- ✅ `core/exam_timetable_views.py` - Template selection logic
- ✅ `core/template_views.py` - Preview function and validation
- ✅ `core/templates/template_management.html` - UI for template selection
- ✅ `core/urls.py` - Preview URL route

### Step 3: Database Setup (If Not Already Done)
The templates use the existing `TemplateSettings` table and stored procedures:
- `Proc_Template_Preference_Get`
- `Proc_Template_Preference_Save`

If these don't exist, run the SQL script from `database/tables/TemplateSettings.sql`

### Step 4: Test the Implementation

#### Test 1: Access Template Management
1. Login to the system
2. Navigate to Template Management page
3. Verify "Exam Timetable" card is visible with 10 template options

#### Test 2: Preview Templates
1. Select each template from dropdown
2. Click "Preview" button
3. Verify template displays correctly in modal
4. Close preview

#### Test 3: Apply Template
1. Select a template
2. Click "Apply" button
3. Verify success message appears
4. Refresh page and verify selected template is still selected

#### Test 4: Print with Template
1. Go to Exam Management
2. Create or select an exam
3. Add timetable entries for a class
4. Click "Print" button for that class
5. Verify the selected template is used
6. Test print functionality

### Step 5: Verify All Templates
Test each template individually:
- [ ] Template 1 - Purple Gradient
- [ ] Template 2 - Professional Blue
- [ ] Template 3 - Classic Formal
- [ ] Template 4 - Cyan Modern
- [ ] Template 5 - Green Fresh
- [ ] Template 6 - Orange Warm
- [ ] Template 7 - Pink Vibrant
- [ ] Template 8 - Dark Professional
- [ ] Template 9 - Violet Elegant
- [ ] Template 10 - Red Classic

## Troubleshooting

### Issue: Templates not showing in dropdown
**Solution**: 
- Clear browser cache
- Verify `template_management.html` was updated correctly
- Check browser console for JavaScript errors

### Issue: Preview not working
**Solution**:
- Verify URL route is added in `urls.py`
- Check `template_views.py` has `exam_timetable_preview` function
- Verify user is logged in

### Issue: Template not applied when printing
**Solution**:
- Check database connection
- Verify stored procedure `Proc_Template_Preference_Get` exists
- Check SchoolID is set in session
- Verify template path in database matches file path

### Issue: Print layout broken
**Solution**:
- Check CSS media queries for print
- Verify page size is set to A4 landscape
- Enable background graphics in print settings

## Configuration

### Default Template
If no template is selected, the system uses the original template:
```python
template_file = 'core/exam_timetable_print.html'
```

### Adding Custom Templates
1. Create new HTML file in `exam_timetable` folder
2. Add option in `template_management.html`:
```html
<option value="core/document_templates/exam_timetable/your_template.html">
    Your Template Name
</option>
```
3. Add path to validation list in `template_views.py`:
```python
'core/document_templates/exam_timetable/your_template.html',
```

## Rollback Instructions
If you need to rollback:

1. **Remove template files**:
```bash
rmdir /s core\templates\core\document_templates\exam_timetable
```

2. **Revert code changes**:
   - Restore original `exam_timetable_views.py`
   - Restore original `template_views.py`
   - Restore original `template_management.html`
   - Remove preview URL from `urls.py`

3. **Database cleanup** (optional):
```sql
DELETE FROM TemplateSettings WHERE TemplateType = 'ExamTimetable';
```

## Performance Considerations
- Templates are lightweight (inline CSS)
- No external dependencies
- Fast rendering
- Optimized for print

## Security Notes
- Template selection is validated against whitelist
- Only authenticated users can access
- School-specific template preferences
- XSS protection via Django template engine

## Browser Support
| Browser | Version | Status |
|---------|---------|--------|
| Chrome  | 90+     | ✅ Full Support |
| Firefox | 88+     | ✅ Full Support |
| Safari  | 14+     | ✅ Full Support |
| Edge    | 90+     | ✅ Full Support |

## Next Steps
1. ✅ Complete installation
2. ✅ Test all templates
3. ✅ Train users on template selection
4. ✅ Set default template for each school
5. ✅ Monitor usage and gather feedback

## Support
For technical support or questions:
- Check main documentation: `EXAM_TIMETABLE_TEMPLATES_README.md`
- Review code comments in updated files
- Contact development team

---
**Installation Date**: ___________
**Installed By**: ___________
**Version**: 1.0
