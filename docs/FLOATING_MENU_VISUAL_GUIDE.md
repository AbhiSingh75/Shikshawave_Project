# Floating Menu - Visual Guide

## Desktop View (Width > 768px)

### Initial State
```
┌─────────────────────────────────────────────────┐
│  Header (ShikshaWave Logo, School, User)       │
└─────────────────────────────────────────────────┘
│                                                 │
│  ●  ← Floating Menu Button (Left side)         │
│  ⚫                                              │
│                                                 │
│           Page Content Here                     │
│                                                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

### When Floating Button is Clicked
```
┌─────────────────────────────────────────────────┐
│  Header (ShikshaWave Logo, School, User)       │
└─────────────────────────────────────────────────┘
┌──────────┐                                      │
│  Menu  ✕ │  ← Sidebar Opens                     │
│──────────│                                      │
│ 📊 Dash  │     [Dark Overlay]                   │
│ 👥 Users │                                      │
│ 📚 Class │        Page Content                  │
│   ▼ Sub  │        (Dimmed)                      │
│    • Sub1│                                      │
│    • Sub2│                                      │
│ 💰 Fees  │                                      │
└──────────┘                                      │
```

### Hover Effects

#### Floating Button Hover
```
Before:  ●  (50px circle)
         ⚫

After:   ●  (55px circle, rotated icon)
         ⚫  Shadow enhanced
```

#### Menu Item Hover
```
Before:  │ 📊 Dashboard        │
         
After:   │  📊 Dashboard       │  (Indented + highlighted)
```

## Mobile View (Width ≤ 768px)

```
┌─────────────────────────────────────────────────┐
│  Header (ShikshaWave Logo, School, User)       │
└─────────────────────────────────────────────────┘
│                                                 │
│  [No Floating Button - Hidden]                 │
│                                                 │
│           Page Content Here                     │
│                                                 │
│  (Use existing mobile menu)                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Color Scheme

### Light Mode
- **Floating Button**: 
  - Background: Linear gradient (#004aad → #0077ff)
  - Icon: White
  - Shadow: rgba(0, 74, 173, 0.4)

- **Sidebar**:
  - Background: Linear gradient (#004aad → #0077ff)
  - Text: White
  - Hover: rgba(255, 255, 255, 0.1)

- **Overlay**: rgba(0, 0, 0, 0.5)

### Dark Mode
- **Floating Button**: 
  - Background: Linear gradient (#6366f1 → #818cf8)
  - Icon: White
  - Shadow: rgba(99, 102, 241, 0.4)

- **Sidebar**:
  - Background: Linear gradient (#1f2937 → #374151)
  - Text: White
  - Hover: rgba(255, 255, 255, 0.1)

- **Overlay**: rgba(0, 0, 0, 0.5)

## Interaction Flow

```
User Action                    System Response
───────────────────────────────────────────────────
1. Click Floating Button   →   Sidebar slides in from left
                                Overlay appears
                                Body scroll disabled

2. Click Menu Item         →   Navigate to page
   (without submenu)           Sidebar closes

3. Click Menu Item         →   Submenu expands
   (with submenu)              Other submenus collapse

4. Click Submenu Item      →   Navigate to page
                                Sidebar closes

5. Click Close Button (✕)  →   Sidebar slides out
                                Overlay fades out
                                Body scroll enabled

6. Click Overlay           →   Same as Close Button
```

## Dimensions

### Floating Button
- Width: 50px
- Height: 50px
- Border Radius: 50% (perfect circle)
- Position: left: 20px, top: 50%
- Z-index: 999

### Sidebar
- Width: 280px
- Height: 100vh (full viewport height)
- Position: Fixed, left: -280px (hidden) → 0 (visible)
- Z-index: 1001

### Overlay
- Width: 100%
- Height: 100%
- Position: Fixed, covers entire viewport
- Z-index: 1000

## Animation Timings

- Sidebar slide: 0.3s ease
- Overlay fade: 0.3s ease
- Button hover: 0.3s ease
- Menu item hover: 0.3s ease
- Submenu expand: 0.3s ease
- Icon rotation: 0.3s ease

## Accessibility Features

1. **Keyboard Navigation**: All menu items are focusable
2. **Screen Readers**: Proper ARIA labels and semantic HTML
3. **Visual Feedback**: Clear hover and active states
4. **Close Options**: Multiple ways to close (button, overlay, ESC key)
5. **Contrast**: High contrast ratios for text and icons

## Responsive Breakpoint

```
Desktop:  min-width: 769px  → Floating menu visible
Mobile:   max-width: 768px  → Floating menu hidden
```

## Z-Index Hierarchy

```
Layer 5: Sidebar (1001)         ← Top layer
Layer 4: Overlay (1000)         ← Blocks interaction
Layer 3: Floating Button (999)  ← Always accessible
Layer 2: Header (100)           ← Fixed header
Layer 1: Content (auto)         ← Page content
```

## Example Menu Structure

```
📊 Dashboard
👥 Students
   ├─ 📝 Add Student
   ├─ 👀 View Students
   └─ 📋 Student Reports
📚 Classes
   ├─ ➕ Add Class
   └─ 📖 View Classes
👨‍🏫 Teachers
💰 Fees
   ├─ 💵 Collect Fee
   ├─ 📊 Fee Reports
   └─ ⚙️ Fee Settings
📅 Attendance
⚙️ Settings
🚪 Logout
```

## Browser Support

✅ Chrome 90+
✅ Firefox 88+
✅ Safari 14+
✅ Edge 90+
✅ Opera 76+

## Performance Notes

- CSS transitions for smooth animations
- No JavaScript animations (better performance)
- Minimal DOM manipulation
- Event delegation for menu items
- Debounced resize handler
