# Clean & Secure URL System

## URL Format
**Before:** `?employee_id=12345` (exposed)
**After:** `?eid=a3f8b2c1` (8-char token)

## Parameters
```
uid → user_id      eid → employee_id   sid → student_id
cid → class_id     tid → teacher_id    xid → exam_id
```

## Usage

### Template
```django
{% load core_extras %}
<a href="?eid={{ emp.ID|token:'eid' }}">View</a>
```

### View
```python
employee_id = request.GET.get('employee_id')  # Auto-resolved
```

## Security
✅ IDs hidden ✅ 1-hour expiry ✅ SHA-256 hashed ✅ Clean URLs
