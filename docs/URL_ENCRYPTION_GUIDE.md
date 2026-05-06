# URL Encryption Implementation Guide

## Overview
Automatic encryption/decryption of sensitive URL parameters across all pages using middleware.

## How It Works

### 1. Middleware (Automatic)
- **URLEncryptionMiddleware**: Decrypts incoming GET parameters
- **EncryptContextMiddleware**: Provides `encrypt_id` function to all templates

### 2. Protected Parameters
```python
user_id, employee_id, student_id, school_id, class_id, 
section_id, teacher_id, staff_id, exam_id, subject_id,
payment_id, receipt_id, attendance_id, fee_id
```

### 3. Usage in Templates

#### Load Template Tags
```django
{% load core_extras %}
```

#### Encrypt IDs in URLs
```django
<a href="?employee_id={{ employee.EmployeeID|encrypt }}">View</a>
<option value="{{ student.StudentID|encrypt }}">{{ student.Name }}</option>
```

### 4. Usage in Views

#### Reading Parameters (Automatic)
```python
# Middleware auto-decrypts, use normally
employee_id = request.GET.get('employee_id', '')
```

#### Passing to Context
```python
context = {
    'encrypt_id': encrypt_id  # Available for manual encryption
}
```

## Example: Complete Flow

### Template
```django
{% load core_extras %}
<select name="student_id">
    {% for student in students %}
    <option value="{{ student.StudentID|encrypt }}">{{ student.Name }}</option>
    {% endfor %}
</select>
```

### URL Generated
```
?student_id=gAAAAABm8xK3...encrypted_value...
```

### View Receives
```python
student_id = request.GET.get('student_id')  # Already decrypted to "123"
```

## Security Benefits
✅ IDs never exposed in URLs
✅ Prevents enumeration attacks
✅ Cryptographically secure (Fernet)
✅ Works across all pages automatically
