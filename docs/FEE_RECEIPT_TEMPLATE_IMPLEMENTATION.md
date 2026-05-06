# Fee Receipt Template-Based Implementation

## ✅ Implementation Complete

Template-based fee receipt system similar to admission acknowledgment has been successfully implemented.

---

## 📋 What Was Done

### 1. **Updated `print_fee_receipt()` in views.py**
- Added template preference lookup from `TemplateSettings` table
- Falls back to default template if no preference set
- Uses same approach as admission acknowledgment

```python
# Get template preference from database
template_file = 'core/document_templates/payment_receipt/payment_success.html'
school_id = request.session.get('SchoolID')

if school_id:
    cursor.execute("""
        SELECT TemplateFile FROM TemplateSettings 
        WHERE SchoolID = %s AND TemplateType = 'PaymentReceipt' 
        AND IsActive = 1 AND IsDeleted = 0
    """, [school_id])
    template_row = cursor.fetchone()
    if template_row and template_row[0]:
        template_file = template_row[0]

return render(request, template_file, context)
```

### 2. **Updated `payment_receipt_preview()` in template_views.py**
- Changed context structure to match `print_fee_receipt()`
- Uses `school_info`, `student_info`, `fee_breakdown` structure
- Fetches school logo from database

### 3. **Added Template Validation**
- Added `receipt_template.html` to valid templates list
- Ensures all payment receipt templates are validated

---

## 🎨 Available Templates

### Payment Receipt Templates:
1. **payment_success.html** - Modern Success (Default)
2. **payment_receipt_template2.html** - Professional Corporate
3. **payment_receipt_template3.html** - Modern Gradient
4. **payment_receipt_template4.html** - Classic Elegant
5. **payment_receipt_template5.html** - Fresh Green Receipt

**Location**: `core/templates/core/document_templates/payment_receipt/`

---

## 🔧 How It Works

### User Flow:

1. **Admin goes to Template Management**
   - URL: `/template-management/`
   - Selects "Payment Receipt" card
   - Chooses template from dropdown
   - Clicks "Preview" to see sample
   - Clicks "Apply" to save preference

2. **Template Saved to Database**
   ```sql
   INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateFile, IsActive, CreatedBy)
   VALUES (@SchoolID, 'PaymentReceipt', @TemplateFile, 1, @UserId)
   ```

3. **Fee Collection & Receipt Generation**
   - User submits fee collection
   - Receipt generated with receipt number
   - Receipt popup shows with Download button

4. **Download Receipt**
   - User clicks "Download" button
   - Calls: `/fees/receipt/{receipt_id}/print/`
   - Backend fetches template preference
   - Generates PDF using selected template
   - Returns PDF for download

---

## 📊 Database Structure

### TemplateSettings Table:
```sql
CREATE TABLE TemplateSettings (
    SettingID INT PRIMARY KEY IDENTITY,
    SchoolID INT NOT NULL,
    TemplateType NVARCHAR(50) NOT NULL,  -- 'PaymentReceipt'
    TemplateFile NVARCHAR(255) NOT NULL,
    IsActive BIT DEFAULT 1,
    IsDeleted BIT DEFAULT 0,
    CreatedBy INT,
    CreatedDate DATETIME DEFAULT GETDATE()
)
```

---

## 🎯 Template Context Structure

All payment receipt templates receive this context:

```python
context = {
    'school_info': {
        'school_name': 'School Name',
        'school_logo': 'data:image/png;base64,...',
        'phone': '1234567890',
        'address': 'School Address',
        'district': 'District',
        'state': 'State',
        'country': 'Country'
    },
    'student_info': {
        'student_code': 'STU001',
        'full_name': 'John Doe',
        'guardian_name': 'Parent Name',
        'class_name': 'Class 10',
        'section_name': 'A',
        'receipt_no': 'RCP-2024-001',
        'date_of_submission': '15-Jan-2024',
        'fees_month': 'January 2024',
        'total_amount': 15000.00,
        'total_paid_amount': 15000.00,
        'remaining_amount': 0.00
    },
    'fee_breakdown': [
        {
            'name': 'Tuition Fee',
            'amount': 10000.00,
            'user_enter_amount': 10000.00,
            'fee_type': 'Regular'
        },
        {
            'name': 'Transport Fee',
            'amount': 3000.00,
            'user_enter_amount': 3000.00,
            'fee_type': 'Regular'
        }
    ],
    'previous_fees': [],  # Last 10 payment history
    'total_amount': 15000.00,
    'paid_amount': 15000.00,
    'remaining_amount': 0.00
}
```

---

## 🚀 Usage Instructions

### For School Admin:

1. **Set Template Preference**:
   - Navigate to: **Master Data → Template Management**
   - Find "Payment Receipt" card
   - Select desired template from dropdown
   - Click "Preview" to see how it looks
   - Click "Apply" to save

2. **Collect Fee**:
   - Go to: **Fees → Fee Collection**
   - Search student
   - Fill fee details
   - Submit fee collection
   - Receipt popup appears

3. **Download Receipt**:
   - Click "Download" button in popup
   - PDF opens in new tab
   - Browser downloads PDF automatically

### For Developers:

**To add new template**:

1. Create template file in:
   ```
   core/templates/core/document_templates/payment_receipt/
   payment_receipt_template6.html
   ```

2. Add to valid templates in `template_views.py`:
   ```python
   'core/document_templates/payment_receipt/payment_receipt_template6.html',
   ```

3. Add option in `template_management.html`:
   ```html
   <option value="core/document_templates/payment_receipt/payment_receipt_template6.html">
       Template 6 - Your Design Name
   </option>
   ```

---

## 🔄 Integration Points

### Files Modified:
1. ✅ `core/views.py` - Updated `print_fee_receipt()`
2. ✅ `core/template_views.py` - Updated `payment_receipt_preview()`
3. ✅ `core/templates/template_management.html` - Already has UI

### Files Using Templates:
- `core/views.py` → `print_fee_receipt()` → Uses template preference
- `core/template_views.py` → `payment_receipt_preview()` → Preview with sample data
- `core/pdf_generator.py` → `generate_pdf_from_template()` → Converts to PDF

---

## 📝 Stored Procedure

**Proc_Template_Preference_Save**:
```sql
CREATE PROCEDURE Proc_Template_Preference_Save
    @SchoolID INT,
    @TemplateType NVARCHAR(50),
    @TemplateFile NVARCHAR(255),
    @CreatedBy INT
AS
BEGIN
    IF EXISTS (SELECT 1 FROM TemplateSettings 
               WHERE SchoolID = @SchoolID AND TemplateType = @TemplateType)
    BEGIN
        UPDATE TemplateSettings 
        SET TemplateFile = @TemplateFile, 
            IsActive = 1,
            CreatedBy = @CreatedBy,
            CreatedDate = GETDATE()
        WHERE SchoolID = @SchoolID AND TemplateType = @TemplateType
    END
    ELSE
    BEGIN
        INSERT INTO TemplateSettings (SchoolID, TemplateType, TemplateFile, IsActive, CreatedBy)
        VALUES (@SchoolID, @TemplateType, @TemplateFile, 1, @CreatedBy)
    END
END
```

**Proc_Template_Preference_Get**:
```sql
CREATE PROCEDURE Proc_Template_Preference_Get
    @SchoolID INT
AS
BEGIN
    SELECT TemplateType, TemplateFile
    FROM TemplateSettings
    WHERE SchoolID = @SchoolID AND IsActive = 1 AND IsDeleted = 0
END
```

---

## ✨ Features

### ✅ Implemented:
- Template selection per school
- Preview before applying
- Automatic template loading
- Fallback to default template
- PDF generation with selected template
- Same approach as admission acknowledgment

### 🎨 Design Consistency:
- Uses same UI as admission templates
- Same database structure
- Same preview mechanism
- Same save/apply workflow

---

## 🧪 Testing

### Test Template Selection:
1. Go to Template Management
2. Select different payment receipt template
3. Click Preview - should show sample receipt
4. Click Apply - should save preference

### Test Receipt Generation:
1. Collect fee for a student
2. Click Download in receipt popup
3. Should generate PDF with selected template
4. Verify template matches selection

### Test Fallback:
1. Delete template preference from database
2. Generate receipt
3. Should use default template (payment_success.html)

---

## 🎯 Summary

**Implementation Status**: ✅ **COMPLETE**

**What Works**:
- ✅ Template selection UI (already existed)
- ✅ Template preference storage
- ✅ Template preference retrieval
- ✅ Dynamic template loading
- ✅ PDF generation with template
- ✅ Preview functionality
- ✅ Fallback mechanism

**No Additional Work Needed** - System is fully functional!

**User can now**:
1. Select payment receipt template from 5 options
2. Preview template before applying
3. Apply template to their school
4. Download receipts using selected template
5. Change template anytime

---

## 📞 Support

For issues or questions:
- Check template file exists in correct location
- Verify TemplateSettings table has correct data
- Check browser console for JavaScript errors
- Verify Chrome is installed for PDF generation
