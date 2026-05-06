# User Session Settings Guide

## How to Change Your Session Timeout

### Access Settings Page
1. Login to your account
2. Navigate to `/settings/` URL
3. Or click on "Settings" from your profile menu (if available)

### Available Options

#### Option 1: Never Auto-Logout
- **What it does**: You stay logged in indefinitely
- **When to use**: If you're on a private/secure device
- **Security note**: Not recommended for shared computers

#### Option 2: Auto-Logout After X Minutes
- **What it does**: Automatically logs you out after specified time of inactivity
- **Default**: 60 minutes (1 hour)
- **Range**: 5 to 1440 minutes (24 hours)
- **Recommended**: 30-120 minutes for good security

### How to Update

1. **Select your preference**:
   - Choose "Never auto-logout" for no timeout
   - OR choose "Auto-logout after" and enter minutes

2. **Click "Save Settings"**

3. **Important**: Logout and login again for changes to take effect

### Examples

**Example 1: Set 30 minutes timeout**
- Select "Auto-logout after"
- Enter `30` in the minutes field
- Click "Save Settings"
- Logout and login again
- You'll be auto-logged out after 30 minutes of inactivity

**Example 2: Disable timeout**
- Select "Never auto-logout"
- Click "Save Settings"
- Logout and login again
- You'll stay logged in until you manually logout

**Example 3: Set 2 hours timeout**
- Select "Auto-logout after"
- Enter `120` in the minutes field (2 hours = 120 minutes)
- Click "Save Settings"
- Logout and login again
- You'll be auto-logged out after 2 hours of inactivity

### Common Questions

**Q: When does the timeout take effect?**
A: After you logout and login again. Your current session is not affected.

**Q: What counts as "activity"?**
A: Any page request, click, or action in the system resets the timer.

**Q: What happens when I'm logged out?**
A: You'll be redirected to the login page. Your work is saved up to that point.

**Q: Can I change it multiple times?**
A: Yes, you can change it as many times as you want.

**Q: What's the recommended setting?**
A: 60 minutes (1 hour) is the default and recommended for most users.

**Q: Is my setting saved permanently?**
A: Yes, it's saved in the database and applies to all your future logins.

### Security Recommendations

✅ **Do:**
- Use 30-120 minutes timeout for shared computers
- Use 60 minutes (default) for regular use
- Disable timeout only on private devices

❌ **Don't:**
- Set very long timeouts on shared computers
- Set very short timeouts (less than 15 minutes) - it's inconvenient
- Forget to logout manually on shared computers

### Troubleshooting

**Problem**: Settings not taking effect
**Solution**: Make sure you logout and login again after changing settings

**Problem**: Getting logged out too quickly
**Solution**: Check your timeout setting - it might be set too low

**Problem**: Never getting logged out
**Solution**: Check if timeout is disabled (set to "Never auto-logout")

**Problem**: Can't access settings page
**Solution**: Make sure you're logged in and have permission to access settings
