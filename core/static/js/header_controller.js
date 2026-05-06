/**
 * Header Controller Module
 */

window.App.HeaderController = {
    timerInterval: null,

    init: function () {
        console.log("Initializing Header Controller...");
        this.initSettingsDropdown();
        this.initSessionTimer();
        this.initNotifications();
    },

    /**
     * Settings Dropdown Toggle
     */
    initSettingsDropdown: function () {
        const settingsBtn = document.getElementById('settingsBtn');
        const settingsDropdown = document.getElementById('settingsDropdown');

        if (settingsBtn && settingsDropdown) {
            settingsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                settingsDropdown.classList.toggle('show');
            });

            document.addEventListener('click', () => {
                settingsDropdown.classList.remove('show');
            });

            settingsDropdown.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    },

    /**
     * Session Timer Logic
     */
    initSessionTimer: function () {
        const countdownEl = document.getElementById('sessionCountdown');
        const expiresAt = window.SHIKSHAWAVE_EXPIRES_AT; // Normalized name

        if (!countdownEl || !expiresAt) {
            console.warn("Session timer elements or timestamp missing:", { countdownEl, expiresAt });
            return;
        }

        if (this.timerInterval) clearInterval(this.timerInterval);

        const updateTimer = () => {
            const now = new Date().getTime();
            const distance = expiresAt - now;

            if (distance < 0) {
                clearInterval(this.timerInterval);
                countdownEl.textContent = "Expired";
                window.location.href = '/login/?reason=timeout';
                return;
            }

            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            countdownEl.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

            // Visual warning
            if (minutes < 5) {
                countdownEl.style.background = '#ef4444'; // Red
            }
        };

        updateTimer();
        this.timerInterval = setInterval(updateTimer, 1000);
    },

    /**
     * Notifications Toggle
     */
    initNotifications: function () {
        const bell = document.getElementById('notificationBell');
        const dropdown = document.getElementById('notificationDropdown');

        if (bell && dropdown) {
            bell.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('show');

                // Trigger global notifications.js logic if available
                if (window.loadNotifications) window.loadNotifications();
            });

            document.addEventListener('click', () => {
                dropdown.classList.remove('show');
            });

            dropdown.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }
};
