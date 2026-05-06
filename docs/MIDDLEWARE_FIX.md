# Middleware Fix - User Authentication

## ✅ Issue Fixed

**Error**: `'WSGIRequest' object has no attribute 'user'`

**Cause**: Missing authentication middleware

## 🔧 Changes Made

### 1. Added CustomAuthenticationMiddleware
File: `core/middleware.py`
- Reads user_id from session
- Attaches UserMaster object to request.user
- Returns None if user not found

### 2. Updated Settings
File: `ShikshaWave/settings.py`
- Added `core.middleware.CustomAuthenticationMiddleware` to MIDDLEWARE list

## ✅ Fixed!

Restart the server and the error will be resolved.

```bash
python manage.py runserver
```
