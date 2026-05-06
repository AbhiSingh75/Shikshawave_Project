/**
 * ShikshaWave Global JS Module
 * Centralized application state and initialization
 */

window.App = {
    modules: {},

    /**
     * Initialize the application
     */
    init: function () {
        console.log("Initializing ShikshaWave App...");

        // Initialize theme
        this.initTheme();

        // Initialize other modules if they exist
        if (this.HeaderController) this.HeaderController.init();
        if (this.ControlRowController) this.ControlRowController.init();

        // Run page-specific initialization if defined
        if (typeof this.initPage === 'function') {
            this.initPage();
        }
    },

    /**
     * Handle theme (dark/light mode)
     */
    initTheme: function () {
        const themeBtn = document.getElementById('themeToggle');
        if (!themeBtn) return;

        themeBtn.addEventListener('click', () => {
            const isDarkMode = document.body.classList.toggle('dark-mode');
            const icon = themeBtn.querySelector('i');
            const text = themeBtn.querySelector('span');

            if (isDarkMode) {
                icon.className = 'fas fa-sun';
                text.textContent = 'Light Mode';
            } else {
                icon.className = 'fas fa-moon';
                text.textContent = 'Dark Mode';
            }

            // Persist preference via session
            fetch('/api/update-theme/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ dark_mode: isDarkMode })
            });
        });
    },

    /**
     * Helper to get CSRF token
     */
    getCsrfToken: function () {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
};

// Auto-initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    window.App.init();
});
