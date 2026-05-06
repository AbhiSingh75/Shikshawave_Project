# Fee Receipt Download Procedure

## Overview
This document explains the complete flow of downloading fee receipts in the Fee Collection page.

## Architecture Components

### 1. Frontend (JavaScript)
- **File**: `core/templates/core/fee_collection_new.html`
- **Function**: `downloadReceipt()`

### 2. Backend (Python)
- **File**: `core/views.py`
- **Functions**: 
  - `submit_fee_collection()` - Saves payment and generates receipt
  - `print_fee_receipt()` - Generates PDF for download
  - `fee_receipt_view()` - Displays receipt in browser

### 3. Database
- **Procedure**: `Proc_Payment_Receipt_Get`
- **Table**: `Payment`

### 4. PDF Generation
- **File**: `core/pdf_generator.py`
- **Function**: `generate_pdf_from_template()`

---

## Complete Flow

### Step 1: Fee Collection Submission
```
User fills fee form → Clicks "Submit Fee Collection" → submitFeeCollection() called
```

**JavaScript Function**: `submitFeeCollection()`
- Validates payment month, mode, transaction reference
- Validates deposit amount (minimum 50%)
- Collects fee breakdown from form
- Sends POST request to `/fees/submit-fee-collection/`

### Step 2: Backend Processing
```
POST /fees/submit-fee-collection/ → submit_fee_collection() in views.py
```

**Process**:
1. Generates unique receipt number: `RCP-{school_id}-{student_id}-{uuid}`
2. Inserts payment record into `Payment` table with:
   - ReceiptNumber
   - TotalAmount
   - PaidAmount
   - PaymentMode
   - TransactionRef
   - FeeBreakdown (JSON)
   - PaymentMonth
3. Stores receipt data in session: `request.session['fee_collection_receipt']`
4. Returns JSON response with receipt number

### Step 3: Receipt Popup Display
```
Success response → showReceiptPopup() called
```

**JavaScript Function**: `showReceiptPopup(receiptNumber, studentName, totalAmount, depositAmount)`
- Displays receipt popup with:
  - Receipt number
  - Student details
  - Payment date
  - Payment mode
  - Fee breakdown table
  - Total amount
- Shows 3 action buttons:
  - **Download** (calls `downloadReceipt()`)
  - **Dashboard** (redirects to dashboard)
  - **Close** (closes popup)

### Step 4: Download Receipt (Current Implementation)
```
User clicks "Download" button → downloadReceipt() called
```

**Current JavaScript Function**:
```javascript
function downloadReceipt() {
    // Currently NOT IMPLEMENTED
    // Need to add implementation
}
```

---

## Implementation Required

### Option 1: Direct PDF Download (Recommended)

**Frontend (JavaScript)**:
```javascript
function downloadReceipt() {
    const receiptNumber = document.getElementById('receipt-number').textContent;
    
    if (!receiptNumber || receiptNumber === '-') {
        alert('Receipt number not found');
        return;
    }
    
    // Open PDF in new tab for download
    window.open(`/fees/receipt/${receiptNumber}/print/`, '_blank');
}
```

**Backend Route** (Already exists):
```
URL: /fees/receipt/<receipt_id>/print/
View: print_fee_receipt(request, receipt_id)
```

**Backend Function** (Already exists in views.py):
```python
def print_fee_receipt(request, receipt_id):
    # 1. Fetch receipt data using Proc_Payment_Receipt_Get
    # 2. Render receipt_template.html with data
    # 3. Generate PDF using pdf_generator.py
    # 4. Return PDF as HTTP response
```

### Option 2: AJAX Download with Progress

**Frontend (JavaScript)**:
```javascript
function downloadReceipt() {
    const receiptNumber = document.getElementById('receipt-number').textContent;
    const downloadBtn = document.querySelector('.btn-download');
    
    // Show loading state
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    downloadBtn.disabled = true;
    
    fetch(`/fees/receipt/${receiptNumber}/print/`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Receipt-${receiptNumber}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        })
        .finally(() => {
            downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download';
            downloadBtn.disabled = false;
        });
}
```

---

## Database Procedure

**Proc_Payment_Receipt_Get.sql**:
```sql
CREATE OR ALTER PROCEDURE Proc_Payment_Receipt_Get
    @ReceiptNumber NVARCHAR(50) = NULL,
    @StudentCode NVARCHAR(20) = NULL
AS
BEGIN
    -- Fetches complete payment and student details
    -- Returns: Payment info, Student info, School info
END
```

**Returns**:
- Receipt details (number, amount, mode, date)
- Student details (code, name, class, section)
- School details (name, logo)
- Fee breakdown (JSON)

---

## PDF Generation Process

**pdf_generator.py → generate_pdf_from_template()**:

1. Renders HTML template with context data
2. Creates temporary HTML file
3. Uses headless Chrome to convert HTML to PDF:
   ```
   chrome.exe --headless --print-to-pdf=output.pdf input.html
   ```
4. Reads PDF bytes
5. Returns PDF content
6. Cleans up temporary files

**Fallback**: If Chrome fails, generates simple PDF with basic content

---

## Receipt Templates

**Available Templates**:
1. `payment_success.html` (Default)
2. `payment_receipt_template2.html`
3. `payment_receipt_template3.html`
4. `payment_receipt_template4.html`
5. `payment_receipt_template5.html`

**Template Selection**:
- Stored in `TemplateSettings` table
- Per school configuration
- Falls back to default if not configured

---

## URL Routes

```python
# Fee Collection
path('fees/submit-fee-collection/', views.submit_fee_collection)

# Receipt Display
path('fees/receipt/<str:receipt_id>/', views.fee_receipt_view)

# Receipt Print/Download
path('fees/receipt/<str:receipt_id>/print/', views.print_fee_receipt)

# Receipt Data API
path('api/get-receipt-data/', views.get_receipt_data)
```

---

## Session Data Structure

**After successful payment**:
```python
request.session['fee_collection_receipt'] = {
    'receipt_number': 'RCP-1-123-ABC123',
    'student_code': 'STU001',
    'student_name': 'John Doe',
    'total_amount': 5000.00,
    'amount_paid': 5000.00,
    'payment_mode': 'Cash',
    'transaction_ref': '',
    'payment_date': '2024-01-15',
    'fee_breakdown': [
        {'feeTypeName': 'Tuition Fee', 'amount': 3000},
        {'feeTypeName': 'Transport', 'amount': 2000}
    ]
}
```

---

## Error Handling

### Frontend Validation:
- Receipt number exists
- Valid receipt format
- Network connectivity

### Backend Validation:
- Receipt exists in database
- Not deleted (IsDeleted = 0)
- Belongs to current school
- Student data available

### PDF Generation:
- Chrome executable found
- Template exists
- Sufficient disk space
- Timeout handling (60 seconds)
- Fallback to simple PDF if Chrome fails

---

## Security Considerations

1. **Session-based**: Receipt data stored in session
2. **School isolation**: Only receipts from user's school
3. **Soft delete check**: Excludes deleted records
4. **CSRF protection**: All POST requests require CSRF token
5. **Login required**: All views require authentication

---

## Performance Optimization

1. **Session caching**: Receipt data cached in session
2. **Async PDF generation**: Can be moved to background task
3. **Template caching**: Django template caching enabled
4. **Chrome reuse**: Headless Chrome process optimization

---

## Testing Endpoints

```
# Test receipt procedure
GET /fees/test-procedure/?receipt_id=RCP-1-123-ABC123

# Test with session data
GET /fees/test-session-receipt/

# View receipt in browser
GET /fees/receipt/RCP-1-123-ABC123/

# Download receipt PDF
GET /fees/receipt/RCP-1-123-ABC123/print/
```

---

## Minimal Implementation (Add to fee_collection_new.html)

```javascript
// Add this function after showReceiptPopup()
function downloadReceipt() {
    const receiptNumber = document.getElementById('receipt-number').textContent;
    if (!receiptNumber || receiptNumber === '-') {
        alert('Receipt number not available');
        return;
    }
    window.open(`/fees/receipt/${receiptNumber}/print/`, '_blank');
}
```

**That's it!** The backend is already implemented. Just add this 7-line function.

---

## Summary

**Current Status**: ✅ Backend fully implemented, ❌ Frontend function empty

**Required Action**: Add `downloadReceipt()` function implementation (7 lines)

**Flow**: 
1. User submits fee → Receipt generated → Popup shown
2. User clicks Download → `downloadReceipt()` called
3. Opens `/fees/receipt/{id}/print/` in new tab
4. Backend generates PDF using Chrome
5. Browser downloads PDF file

**Dependencies**: 
- Chrome browser installed on server
- Session data available
- Receipt exists in database
