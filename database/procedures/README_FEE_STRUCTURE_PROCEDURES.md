# Fee Structure Stored Procedures

## Overview
This document describes the stored procedures created for retrieving fee structure details on the admission form.

## Stored Procedures

### 1. Proc_Admission_Fee_Types_Get
**Purpose**: Retrieve admission fee types that are not class-specific

**Parameters**:
- `@SchoolID INT` - School identifier

**Returns**: List of admission fee types with columns:
- FeeTypeId
- SchoolId
- FeeTypeName
- DefaultAmount

**Usage**:
```sql
EXEC Proc_Admission_Fee_Types_Get @SchoolID = 3
```

### 2. Proc_Monthly_Fee_Types_Get
**Purpose**: Retrieve monthly fee types based on class selection

**Parameters**:
- `@SchoolID INT` - School identifier
- `@ClassID INT` - Class identifier

**Returns**: List of monthly fee types with columns:
- FeeTypeId
- SchoolId
- FeeTypeName
- DefaultAmount
- ClassId

**Usage**:
```sql
EXEC Proc_Monthly_Fee_Types_Get @SchoolID = 3, @ClassID = 5
```

## Implementation Changes

### Code Updates
1. **Admission Form Load**: Uses `Proc_Admission_Fee_Types_Get` to load admission fees
2. **Class Selection AJAX**: Uses `Proc_Monthly_Fee_Types_Get` to load class-specific fees
3. **Fee Assignment**: All fees (admission + monthly) are saved to `Student_Fee_Assignment` table
4. **Payment Record**: Complete fee breakdown is saved to `Payment.FeeBreakdown` column as JSON

### Data Flow
1. User loads admission form → Admission fees loaded via procedure
2. User selects class → Monthly fees loaded via AJAX procedure call
3. User submits form → All fees saved to `Student_Fee_Assignment`
4. User completes payment → Fee breakdown saved to `Payment.FeeBreakdown`

## Database Setup

Run these procedures in order:
```sql
-- 1. Create admission fee types procedure
-- Run: Proc_Admission_Fee_Types_Get.sql

-- 2. Create monthly fee types procedure
-- Run: Proc_Monthly_Fee_Types_Get.sql
```

## Verification

### Test Admission Fees
```sql
EXEC Proc_Admission_Fee_Types_Get @SchoolID = 3
```

### Test Monthly Fees
```sql
EXEC Proc_Monthly_Fee_Types_Get @SchoolID = 3, @ClassID = 5
```

### Verify Fee Assignments
```sql
SELECT * FROM Student_Fee_Assignment 
WHERE StudentID = [STUDENT_ID] 
ORDER BY FeeTypeId
```

### Verify Payment Breakdown
```sql
SELECT ReceiptNumber, FeeBreakdown 
FROM Payment 
WHERE EntityID = [STUDENT_ID] AND EntityType = 'Student'
```

## Receipt Number Format

Admission payment receipt numbers are generated in the format:
```
ADM-{SCHOOL_ID}-{STUDENT_CODE}-{YYYYMMDD}-{SEQUENCE}
```

Example: `ADM-3-STU001-20240115-001`

Where:
- `ADM` = Admission payment identifier
- `SCHOOL_ID` = School identifier
- `STUDENT_CODE` = Student code
- `YYYYMMDD` = Payment date
- `SEQUENCE` = Daily sequence number (001, 002, etc.)

## Benefits
- Centralized fee structure logic in database
- Consistent fee retrieval across application
- All fees properly saved to both assignment and payment tables
- Complete audit trail of fee structure at time of admission
- Unique, meaningful receipt numbers for every admission payment
