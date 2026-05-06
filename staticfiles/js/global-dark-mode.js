/**
 * Global Dark Mode Management
 * Ensures consistent dark mode behavior across all pages
 */

class GlobalDarkMode {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupDarkModeToggle();
                this.applySavedPreference();
                this.setupCrossTabSync();
            });
        } else {
            this.setupDarkModeToggle();
            this.applySavedPreference();
            this.setupCrossTabSync();
        }
    }

    setupDarkModeToggle() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        
        if (darkModeToggle) {
            // Remove any existing event listeners
            darkModeToggle.replaceWith(darkModeToggle.cloneNode(true));
            const newToggle = document.getElementById('darkModeToggle');
            
            newToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDarkMode();
            });
        }
    }

    toggleDarkMode() {
        const isDarkMode = document.body.classList.contains('dark-mode');
        const newDarkMode = !isDarkMode;
        
        // Update UI immediately for instant feedback
        this.updateUI(newDarkMode);
        
        // Save preference to server
        this.savePreference(newDarkMode);
    }

    updateUI(isDarkMode) {
        // Toggle body class
        document.body.classList.toggle('dark-mode', isDarkMode);
        
        // Update toggle button icon
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (darkModeToggle) {
            const icon = darkModeToggle.querySelector('i');
            if (icon) {
                icon.className = `fas ${isDarkMode ? 'fa-sun' : 'fa-moon'}`;
            }
            
            // Update tooltip
            darkModeToggle.title = isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode';
            
            // Add animation class
            darkModeToggle.classList.add('animating');
            setTimeout(() => {
                darkModeToggle.classList.remove('animating');
            }, 600);
        }
    }

    savePreference(isDarkMode) {
        // Get CSRF token
        const csrfToken = this.getCSRFToken();
        
        if (!csrfToken) {
            console.error('CSRF token not found');
            return;
        }

        fetch('/toggle-dark-mode/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dark_mode: isDarkMode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Dark mode preference saved successfully');
                // Update session for immediate consistency
                this.updateSession(isDarkMode);
                // Broadcast change to other tabs
                this.broadcastChange(isDarkMode);
            } else {
                console.error('Failed to save dark mode preference:', data.error);
                // Revert UI changes on failure
                this.updateUI(!isDarkMode);
            }
        })
        .catch(error => {
            console.error('Error saving dark mode preference:', error);
            // Revert UI changes on error
            this.updateUI(!isDarkMode);
        });
    }

    getCSRFToken() {
        // Try to get CSRF token from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Try to get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try to get from form
        const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return null;
    }

    updateSession(isDarkMode) {
        // This is handled by the server response, but we can add local storage as backup
        try {
            localStorage.setItem('dark_mode_preference', isDarkMode.toString());
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
    }

    // Method to check and apply saved preference on page load
    applySavedPreference() {
        // Priority 1: Check server-rendered state (most reliable)
        const serverDarkMode = document.body.classList.contains('dark-mode');
        
        // Update localStorage to match server state
        try {
            localStorage.setItem('dark_mode_preference', serverDarkMode.toString());
        } catch (e) {
            console.warn('Could not save to localStorage:', e);
        }
        
        // Ensure UI matches server state
        this.updateUI(serverDarkMode);
        console.log('Dark mode synced with server:', serverDarkMode);
    }

    // Setup cross-tab synchronization
    setupCrossTabSync() {
        // Listen for storage changes from other tabs
        window.addEventListener('storage', (e) => {
            if (e.key === 'dark_mode_preference') {
                const isDarkMode = e.newValue === 'true';
                this.updateUI(isDarkMode);
            }
        });

        // Listen for custom events for same-tab communication
        window.addEventListener('darkModeChanged', (e) => {
            this.updateUI(e.detail.isDarkMode);
        });
    }

    // Broadcast dark mode change to other tabs
    broadcastChange(isDarkMode) {
        try {
            localStorage.setItem('dark_mode_preference', isDarkMode.toString());
            // Dispatch custom event for same-tab communication
            window.dispatchEvent(new CustomEvent('darkModeChanged', {
                detail: { isDarkMode }
            }));
        } catch (e) {
            console.warn('Could not broadcast dark mode change:', e);
        }
    }
}

// Initialize global dark mode
const globalDarkMode = new GlobalDarkMode();

// Export for potential use in other scripts
window.GlobalDarkMode = GlobalDarkMode;
