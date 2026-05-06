# Exam Timetable Templates - Implementation Guide

## Overview
This document describes the implementation of 10 modern and classic templates for the Exam Timetable print page with Template Management integration.

## Features Implemented

### 1. **10 Professional Templates**
Created 10 unique, modern, and classic templates for exam timetable printing:

1. **Template 1 - Purple Gradient**: Modern gradient design with purple and violet colors
2. **Template 2 - Professional Blue**: Clean blue header with professional layout
3. **Template 3 - Classic Formal**: Traditional black and white formal design with serif fonts
4. **Template 4 - Cyan Modern**: Fresh cyan/turquoise gradient design
5. **Template 5 - Green Fresh**: Vibrant green theme with modern styling
6. **Template 6 - Orange Warm**: Warm orange tones with elegant borders
7. **Template 7 - Pink Vibrant**: Eye-catching pink gradient design
8. **Template 8 - Dark Professional**: Sophisticated dark slate theme
9. **Template 9 - Violet Elegant**: Elegant violet with decorative elements
10. **Template 10 - Red Classic**: Bold red theme with classic styling

### 2. **Template Management Integration**
- Added "Exam Timetable" card to Template Management page
- Users can select from 10 templates via dropdown
- Preview functionality to see templates before applying
- Apply button to save template preference per school

### 3. **Database Integration**
- Templates are stored in `TemplateSettings` table
- Template type: `ExamTimetable`
- Uses stored procedure: `Proc_Template_Preference_Get` and `Proc_Template_Preference_Save`
- School-specific template preferences

## File Structure

```
core/
├── templates/
│   ├── core/
│   │   └── document_templates/
│   │       └── exam_timetable/
│   │           ├── exam_timetable_template1.html
│   │           ├── exam_timetable_template2.html
│   │           ├── exam_timetable_template3.html
│   │           ├── exam_timetable_template4.html
│   │           ├── exam_timetable_template5.html
│   │           ├── exam_timetable_template6.html
│   │           ├── exam_timetable_template7.html
│   │           ├── exam_timetable_template8.html
│   │           ├── exam_timetable_template9.html
│   │           └── exam_timetable_template10.html
│   └── template_management.html (updated)
├── exam_timetable_views.py (updated)
├── template_views.py (updated)
└── urls.py (updated)
```

## Template Features

Each template includes:
- **Responsive Design**: Optimized for A4 landscape printing
- **School Logo Support**: Displays school logo if available
- **Print & Close Buttons**: User-friendly controls (hidden in print)
- **Complete Information Display**:
  - School name
  - Exam name and type
  - Class information
  - Exam duration (start and end dates)
  - Subject-wise schedule with:
    - Serial number
    - Subject name
    - Exam date and day
    - Time (start and end)
    - Room number
    - Maximum marks (Theory, Practical, Viva)
- **Authorized Signature Section**: Space for official signature
- **Print-Optimized Styling**: Clean output when printed

## Usage

### For School Administrators:

1. **Navigate to Template Management**:
   - Go to Template Management page
   - Find "Exam Timetable" card

2. **Select Template**:
   - Choose from 10 available templates in dropdown
   - Click "Preview" to see how it looks
   - Click "Apply" to save your preference

3. **Print Timetable**:
   - Go to Exam Management
   - Select an exam
   - Click on a class to view timetable
   - Click "Print" button
   - The selected template will be used automatically

### For Developers:

#### Adding New Templates:
1. Create new HTML file in `core/templates/core/document_templates/exam_timetable/`
2. Follow the existing template structure
3. Add template option in `template_management.html`
4. Add template path to validation list in `template_views.py`

#### Template Context Variables:
```python
{
    'school_name': str,           # School name
    'school_logo_src': str,       # School logo URL/base64
    'exam': {
        'ExamName': str,          # Exam name
        'ExamType': str,          # Exam type
        'StartDate': date,        # Exam start date
        'EndDate': date           # Exam end date
    },
    'class_name': str,            # Class name
    'timetable': [                # List of exam schedules
        {
            'SubjectName': str,
            'ExamDate': date,
            'StartTime': time,
            'EndTime': time,
            'RoomNo': str,
            'MaxTheoryMarks': int,
            'MaxPracticalMarks': int,
            'MaxVivaMarks': int
        }
    ]
}
```

## Technical Implementation

### 1. View Updates (`exam_timetable_views.py`)
```python
@custom_login_required
def exam_timetable_print(request, exam_id, class_id):
    # ... existing code ...
    
    # Get template preference
    template_file = 'core/exam_timetable_print.html'
    template_param = request.GET.get('template')
    if template_param:
        template_file = template_param
    else:
        cursor.execute("EXEC Proc_Template_Preference_Get @SchoolID = %s", [school_id])
        for row in cursor.fetchall():
            if row[0] == 'ExamTimetable':
                template_file = row[1]
                break
    
    return render(request, template_file, context)
```

### 2. Preview Function (`template_views.py`)
```python
@custom_login_required
@xframe_options_exempt
def exam_timetable_preview(request):
    template = request.GET.get('template', 'core/document_templates/exam_timetable/exam_timetable_template1.html')
    # Generate sample data for preview
    # Render template with sample data
```

### 3. URL Configuration (`urls.py`)
```python
path('exam/timetable/preview/', template_views.exam_timetable_preview, name='exam_timetable_preview'),
```

## Database Schema

The templates use the existing `TemplateSettings` table:

```sql
CREATE TABLE TemplateSettings (
    TemplateSettingID INT PRIMARY KEY IDENTITY(1,1),
    SchoolID INT NOT NULL,
    TemplateType VARCHAR(50) NOT NULL,  -- 'ExamTimetable'
    TemplateFile VARCHAR(255) NOT NULL,
    CreatedBy INT,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedBy INT,
    UpdatedDate DATETIME,
    IsDeleted BIT DEFAULT 0
);
```

## Testing

### Manual Testing Steps:
1. Login as school administrator
2. Navigate to Template Management
3. Select "Exam Timetable" section
4. Try each template preview
5. Apply a template
6. Go to Exam Management
7. Create/select an exam with timetable
8. Print timetable and verify selected template is used

### Test Cases:
- ✅ Template selection and preview
- ✅ Template preference saving
- ✅ Template preference retrieval
- ✅ Print with selected template
- ✅ Print with default template (if no preference set)
- ✅ All 10 templates render correctly
- ✅ Print optimization (buttons hidden, proper page breaks)

## Browser Compatibility
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Print preview works in all modern browsers

## Print Settings Recommendation
- **Page Size**: A4 Landscape
- **Margins**: 10mm (default)
- **Background Graphics**: Enabled (for gradient templates)

## Future Enhancements
1. Add more template variations
2. Allow custom CSS injection for advanced users
3. Template preview with actual exam data
4. Bulk print for multiple classes
5. PDF export functionality
6. Email timetable to students/parents

## Support
For issues or questions, contact the development team or refer to the main project documentation.

## Version History
- **v1.0** (Current): Initial implementation with 10 templates
  - Purple Gradient
  - Professional Blue
  - Classic Formal
  - Cyan Modern
  - Green Fresh
  - Orange Warm
  - Pink Vibrant
  - Dark Professional
  - Violet Elegant
  - Red Classic

---
**Last Updated**: 2024
**Author**: ShikshaWave Development Team
