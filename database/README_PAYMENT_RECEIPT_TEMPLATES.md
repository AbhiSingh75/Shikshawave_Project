# Payment Receipt Templates

## Overview
This document describes the 5 payment receipt templates available in ShikshaWave for printing and emailing payment receipts to students and parents.

## Templates

### Template 1: Modern Success (Default)
- **File**: `payment_success.html`
- **Style**: Modern with gradient buttons and success icon
- **Colors**: Green success theme with white background
- **Features**: 
  - Large success checkmark icon
  - Fee breakdown with discount display
  - Action buttons for print, acknowledgment, and dashboard
  - Responsive design
- **Best For**: General purpose, modern schools

### Template 2: Professional Corporate
- **File**: `payment_receipt_template2.html`
- **Style**: Professional corporate design
- **Colors**: Dark blue/gray header with white body
- **Features**:
  - Clean grid layout for student information
  - Professional table for fee breakdown
  - Bold header with school branding
  - Formal footer
- **Best For**: Corporate schools, professional institutions

### Template 3: Modern Gradient
- **File**: `payment_receipt_template3.html`
- **Style**: Modern with purple gradient
- **Colors**: Purple gradient (667eea to 764ba2)
- **Features**:
  - Curved header design
  - Badge-style receipt number
  - Colorful gradient sections
  - Modern card-style layout
- **Best For**: Modern schools, tech-focused institutions

### Template 4: Classic Elegant
- **File**: `payment_receipt_template4.html`
- **Style**: Classic formal with gold accents
- **Colors**: Gold borders with white background
- **Features**:
  - Ornamental decorations (❖ symbols)
  - Signature lines for authorization
  - Serif font (Georgia) for formal look
  - Gold accent borders
- **Best For**: Traditional schools, formal institutions

### Template 5: Fresh Green Receipt
- **File**: `payment_receipt_template5.html`
- **Style**: Receipt-style with green theme
- **Colors**: Green (#4caf50) with dashed borders
- **Features**:
  - Dashed border (receipt-style)
  - "PAID" watermark
  - Stamp-style receipt number
  - Monospace font (Courier New)
  - Checkmark decorations
- **Best For**: Casual schools, modern institutions

## Common Features (All Templates)

1. **Print/Close Buttons**: All templates include print and close buttons at the top (hidden during print)
2. **School Logo**: Display school logo if available
3. **Student Information**: 
   - Student Name
   - Student Code
   - Payment Date
   - Payment Mode
   - Transaction Reference (if available)
4. **Fee Breakdown**: 
   - Individual fee items
   - Discount display (strikethrough original amount)
   - Discount percentage
   - Total amount paid
5. **Print Optimization**: All templates are optimized for printing with proper page breaks and color preservation
6. **Responsive Design**: Mobile-friendly layouts

## Database Integration

### TemplateSettings Table
Templates are stored in the `TemplateSettings` table with:
- `TemplateType`: 'PaymentReceipt'
- `TemplateName`: Descriptive name
- `TemplateFile`: HTML filename
- `SchoolID`: School-specific template preference

### Stored Procedures
- **Proc_Template_Preference_Get**: Retrieves selected template for a school
- **Proc_Template_Preference_Save**: Saves template preference for a school

## Template Management UI

Schools can select their preferred payment receipt template from:
**Settings > Template Management > Payment Receipt**

Features:
- Dropdown to select from 5 templates
- Preview button to see template before applying
- Apply button to save preference

## Usage in Code

### Getting Template Preference
```python
with connection.cursor() as cursor:
    cursor.execute("EXEC Proc_Template_Preference_Get @SchoolID = %s", [school_id])
    templates = {}
    for row in cursor.fetchall():
        templates[row[0]] = row[1]
    
    receipt_template = templates.get('PaymentReceipt', 'payment_success.html')
```

### Rendering Receipt
```python
from django.shortcuts import render

def payment_receipt_view(request):
    # Get template preference
    receipt_template = get_template_preference(school_id, 'PaymentReceipt')
    
    # Prepare receipt data
    receipt_data = {
        'school_logo': school.get_school_logo(),
        'school_name': school.school_name,
        'receipt_number': receipt_number,
        'student_name': student_name,
        'student_code': student_code,
        'payment_date': payment_date,
        'payment_mode': payment_mode,
        'transaction_ref': transaction_ref,
        'fee_breakdown': fee_items,
        'amount_paid': total_amount
    }
    
    return render(request, receipt_template, {'payment_receipt': receipt_data})
```

## Installation

1. **Create Templates**: All 5 template files are in `core/templates/`
2. **Run SQL Script**: Execute `database/add_payment_receipt_templates.sql` to add default templates for all schools
3. **Update Template Management**: Template management UI already includes payment receipt selection
4. **Update Views**: Ensure payment receipt views use template preference

## Testing

Test each template by:
1. Going to Template Management
2. Selecting a payment receipt template
3. Clicking Preview to see the template
4. Making a test payment to see the actual receipt

## Customization

To add a new payment receipt template:
1. Create new HTML file in `core/templates/` (e.g., `payment_receipt_template6.html`)
2. Add template to `valid_templates` list in `core/template_views.py`
3. Add option to template management dropdown in `core/templates/template_management.html`
4. Update this README with template details

## Notes

- All templates support print functionality with `window.print()`
- Templates use `@media print` CSS for print optimization
- Color preservation is enabled with `print-color-adjust: exact`
- Templates are responsive and work on mobile devices
- Default template is `payment_success.html` if no preference is set
