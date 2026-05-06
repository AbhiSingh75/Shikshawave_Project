# School Views Refactoring Guide

## Current Status: ✅ URLS Updated - ⚠️ Code Extraction Needed

### What's Been Done:
1. ✅ Created `core/school_views.py` with `schools_create` function
2. ✅ Updated `core/urls.py` to import from `school_views`
3. ✅ All school URL patterns now point to `school_views`

### What Still Needs to Be Done:

The following functions need to be copied from `core/views.py` to `core/school_views.py`:

#### Functions to Extract (with approximate line numbers):

1. **schools_list** (lines ~1819-2037)
   - Main school list view with search, filters, and pagination
   
2. **school_soft_delete** (lines ~2041-2062)
   - Soft delete school endpoint
   
3. **school_restore** (lines ~2066-2086)
   - Restore deleted school endpoint
   
4. **school_update** (lines ~2091-2132)
   - Display school update form
   
5. **school_update_submit** (lines ~2135-2413)
   - Handle school update form submission
   
6. **load_more_schools** (lines ~2416-2551)
   - AJAX endpoint for loading more schools
   
7. **export_schools** (lines ~2554-2711)
   - Export schools to CSV

### Required Imports for school_views.py:

```python
import base64
import re
import time
import logging
import json
import csv
from datetime import datetime
from urllib.parse import urlparse

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db import connection
from django.urls import reverse
from django.core.paginator import Paginator

from .decorators import custom_login_required
from .utils import (
    get_context, safe_int, safe_strptime, validate_uploaded_file,
    ALLOWED_IMAGE_TYPES
)
```

### Manual Steps to Complete:

1. **Open `core/views.py`** and locate the functions listed above
2. **Copy each function** (including decorators and docstrings)
3. **Paste into `core/school_views.py`** after the existing `schools_create` function
4. **Add missing imports** to the top of `school_views.py` (Paginator, csv, json, etc.)
5. **Remove the functions** from `core/views.py` (lines 1816-2711 approx)
6. **Add a comment** in `core/views.py` where they were removed:
   ```python
   # School views moved to core/school_views.py
   # See school_views.py for: schools_list, school_update, school_soft_delete, etc.
   ```

### Testing After Refactoring:

Run these URLs to verify everything works:
- http://127.0.0.1:8000/schools/create/
- http://127.0.0.1:8000/schools/list/
- Try updating a school
- Try deleting and restoring a school

### Benefits of This Refactoring:

✅ Better code organization
✅ Easier maintenance
✅ Reduced file size for `core/views.py`
✅ Follows same pattern as `user_views.py`
✅ Clear separation of concerns

### Quick Copy-Paste Method:

Since manually copying ~900 lines is tedious, here's a Python script approach:

```python
# extract_school_views.py
with open('core/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end
start = next(i for i, l in enumerate(lines) if 'def schools_list' in l) - 2
end = next(i for i, l in enumerate(lines[2500:], 2500) if 'def export_schools' in l) + 60

school_functions = ''.join(lines[start:end])

# Append to school_views.py
with open('core/school_views.py', 'a', encoding='utf-8') as f:
    f.write('\n\n' + school_functions)

print(f'Extracted lines {start+1} to {end+1}')
print('Now review school_views.py and add any missing imports!')
```

Run this script to automatically extract the functions, then just review and clean up imports.
