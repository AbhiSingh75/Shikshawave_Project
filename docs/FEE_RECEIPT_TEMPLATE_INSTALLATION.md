# Fee Receipt Template Management - Quick Installation Guide

## What Was Added

A new "Fee Receipt" section in Template Management with 5 professional templates for schools to choose from.

## Files Added

### New Templates Directory
```
core/templates/core/document_templates/fee_receipt/
├── fee_receipt_template1.html (Modern Purple Gradient)
├── fee_receipt_template2.html (Professional Red)
├── fee_receipt_template3.html (Classic Blue)
├── fee_receipt_template4.html (Fresh Green)
└── fee_receipt_template5.html (Elegant Pink)
```

### Documentation
```
FEE_RECEIPT_TEMPLATE_MANAGEMENT.md
FEE_RECEIPT_TEMPLATE_INSTALLATION.md (this file)
```

## Files Modified

1. **core/template_views.py**
   - Added 5 fee receipt templates to valid_templates list
   - Added fee_receipt_preview() function

2. **core/templates/template_management.html**
   - Added Fee Receipt card with template selector
   - Added preview functionality

3. **core/urls.py**
   - Added fee receipt preview URL route

## Installation Steps

### Step 1: Verify Files
Ensure all files are in place:
```bash
# Check templates directory
dir core\templates\core\document_templates\fee_receipt

# Should show 5 HTML files
```

### Step 2: No Database Changes Required
The existing TemplateSettings table and stored procedures already support the new template type.

### Step 3: Test the Feature

1. **Login to the system**
   - Use your admin credentials

2. **Navigate to Template Management**
   - Go to: `/template-management/`

3. **Find Fee Receipt Section**
   - Look for the card with 💵 icon
   - Should be between "Payment Receipt" and "Salary Slip"

4. **Test Preview**
   - Select any template from dropdown
   - Click "Preview" button
   - Modal should open showing the template with sample data

5. **Test Apply**
   - Select a template
   - Click "Apply" button
   - Should see success message
   - Refresh page - selected template should remain selected

## Verification Checklist

- [ ] Fee Receipt card appears in Template Management
- [ ] Dropdown shows 5 template options
- [ ] Preview button opens modal with template
- [ ] Apply button saves selection
- [ ] Selected template persists after page refresh
- [ ] All 5 templates preview correctly
- [ ] School logo appears in preview (if set)
- [ ] No console errors

## Template Selection

The templates are stored in the database with:
- **Template Type**: `FeeReceipt`
- **Template File**: Full path to selected template
- **School ID**: Current school's ID

## Integration with Fee Collection

To use these templates in your fee collection system:

```python
# In your fee receipt view
from django.db import connection

def get_fee_receipt_template(school_id):
    with connection.cursor() as cursor:
        cursor.execute("EXEC Proc_Template_Preference_Get @SchoolID = %s", [school_id])
        templates = {}
        for row in cursor.fetchall():
            templates[row[0]] = row[1]
    
    # Get FeeReceipt template or use default
    return templates.get('FeeReceipt', 'core/document_templates/fee_receipt/fee_receipt_template1.html')

# Use in your view
def print_fee_receipt(request, receipt_id):
    school_id = request.session.get('SchoolID')
    template = get_fee_receipt_template(school_id)
    
    # Your receipt data
    context = {
        'receipt_no': receipt_data['receipt_no'],
        'student_name': receipt_data['student_name'],
        # ... other data
    }
    
    return render(request, template, context)
```

## Troubleshooting

### Issue: Templates not showing in dropdown
**Solution**: Clear browser cache and refresh

### Issue: Preview not working
**Solution**: 
1. Check browser console for errors
2. Verify URL pattern in urls.py
3. Check that fee_receipt_preview function exists in template_views.py

### Issue: Template not saving
**Solution**:
1. Verify database connection
2. Check that Proc_Template_Preference_Save exists
3. Verify user has SchoolID in session

### Issue: School logo not showing in preview
**Solution**:
1. Verify school has logo uploaded
2. Check SchoolMaster.get_school_logo() method
3. Ensure logo is in correct format (base64 or URL)

## Customization

### Adding More Templates

1. Create new template file in `core/templates/core/document_templates/fee_receipt/`
2. Add to valid_templates list in `template_views.py`
3. Add option to dropdown in `template_management.html`

### Modifying Existing Templates

1. Edit the HTML file directly
2. Keep the same variable names for compatibility
3. Test with preview before deploying

## Support

For issues or questions:
1. Check the main documentation: FEE_RECEIPT_TEMPLATE_MANAGEMENT.md
2. Review template variable names in any template file
3. Check console logs for JavaScript errors
4. Verify database stored procedures are working

## Rollback (If Needed)

To remove this feature:
1. Delete the fee_receipt directory
2. Remove fee receipt section from template_management.html
3. Remove fee_receipt_preview from template_views.py
4. Remove fee receipt URL from urls.py
5. Remove fee receipt entries from valid_templates list

## Success Indicators

✅ Feature is working correctly if:
- All 5 templates preview without errors
- Template selection saves and persists
- School logo appears in previews
- No console errors
- Templates are print-friendly
- Responsive on mobile devices

## Next Steps

After installation:
1. Test with real fee receipt data
2. Train staff on template selection
3. Let schools choose their preferred template
4. Collect feedback for improvements
5. Consider adding more templates based on feedback
