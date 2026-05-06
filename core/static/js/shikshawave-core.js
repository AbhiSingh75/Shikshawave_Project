/**
 * ShikshaWave Core UI Logic
 * Standardized initialization for theme, session, and components
 */

const ShikshaWave = {
    config: {
        themeApi: '/toggle-dark-mode/',
        notificationApi: '/notifications/api/list/',
        sessionTimerDuration: 60 // Default fallback
    },

    init: function () {
        console.log("🚀 ShikshaWave Standardized Core Initializing...");

        this.Theme.init();

        // Load session data from DOM
        const sessionData = document.getElementById('sessionExpiresData');
        if (sessionData && sessionData.dataset.expires) {
            window.SHIKSHAWAVE_EXPIRES_AT = parseInt(sessionData.dataset.expires);
        }

        this.Session.init();
        if (this.Notifications) this.Notifications.init();
        this.Notification.init();
        this.UI.init();
        this.UI.setupSidebarToggle();
        this.UI.setupDownloadDelegates(); // Global download delegator

        // Auto-initialize components on content change (Htmx support etc)
        document.body.addEventListener('htmx:afterSettle', () => this.UI.init());
    },

    /**
     * Theme Management (Dark/Light)
     */
    Theme: {
        init: function () {
            const toggle = document.getElementById('themeToggle');
            if (!toggle) return;

            toggle.addEventListener('click', () => this.toggle());
        },

        toggle: async function () {
            const isDark = document.body.classList.contains('dark-mode');
            const newMode = !isDark;

            try {
                const response = await ShikshaWave.Utils.fetch(ShikshaWave.config.themeApi, {
                    method: 'POST',
                    body: JSON.stringify({ dark_mode: newMode })
                });

                if (response.ok) {
                    document.body.classList.toggle('dark-mode');
                    this.updateUI(newMode);
                }
            } catch (err) {
                console.error("Theme toggle failed:", err);
            }
        },

        updateUI: function (isDark) {
            const toggle = document.getElementById('themeToggle');
            if (!toggle) return;

            const icon = toggle.querySelector('i');
            const text = toggle.querySelector('span');

            if (isDark) {
                icon.className = 'fas fa-sun';
                if (text) text.textContent = 'Light Mode';
            } else {
                icon.className = 'fas fa-moon';
                if (text) text.textContent = 'Dark Mode';
            }
        }
    },

    /**
     * Session and Timer Logic
     */
    Session: {
        init: function () {
            // Initialize timeout modal settings logic if the modal exists in DOM
            this.setupTimeoutModal();

            const countdownEl = document.getElementById('sessionCountdown');
            if (countdownEl) {
                this.startTimer(countdownEl);
            }
        },

        setupTimeoutModal: function () {
            const modal = document.getElementById('timeoutModal');
            if (!modal) return;

            const cards = modal.querySelectorAll('.sw-timeout-card');
            cards.forEach(card => {
                card.addEventListener('click', function () {
                    cards.forEach(c => c.classList.remove('selected'));
                    this.classList.add('selected');
                    const radio = this.querySelector('input[type="radio"]');
                    if (radio) radio.checked = true;
                });
            });

            const saveBtn = document.getElementById('saveTimeoutBtn');
            const form = document.getElementById('timeoutSettingsForm');

            if (saveBtn && form) {
                saveBtn.addEventListener('click', async () => {
                    const formData = new FormData(form);
                    saveBtn.disabled = true;
                    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Saving...';

                    try {
                        const response = await ShikshaWave.Utils.fetch('/settings/', {
                            method: 'POST',
                            headers: { 'X-Requested-With': 'XMLHttpRequest' },
                            body: formData
                        });

                        const data = await response.json();
                        if (data.status === 'success') {
                            ShikshaWave.Dialog.success('Settings Saved', data.message);
                            ShikshaWave.UI.closeModal('timeoutModal');
                        } else {
                            ShikshaWave.Dialog.error('Update Failed', data.message || 'Unknown error');
                        }
                    } catch (err) {
                        console.error("Timeout save failed:", err);
                        ShikshaWave.Dialog.error('Connection Error', 'Failed to save settings. Please try again.');
                    } finally {
                        saveBtn.disabled = false;
                        saveBtn.innerHTML = '<i class="fas fa-save mr-1"></i> Save Changes';
                    }
                });
            }
        },

        startTimer: function (el) {
            // Check multiple sources for the expiry timestamp
            let expiresAt = window.SHIKSHAWAVE_EXPIRES_AT || (ShikshaWave.config && ShikshaWave.config.expiresAt) || (Date.now() + 3600 * 1000);

            const update = () => {
                const now = Date.now();
                const remaining = Math.floor((expiresAt - now) / 1000);

                if (remaining <= 0) {
                    el.textContent = "00:00";
                    el.style.background = 'var(--danger)';
                    // Only redirect if it was actually running and then expired
                    if (expiresAt > 0 && now > expiresAt + 2000) {
                        window.location.href = '/login/?expired=1';
                    }
                    return;
                }

                const mins = Math.floor(remaining / 60);
                const secs = remaining % 60;
                el.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;

                // Visual warnings
                if (remaining < 300) el.style.background = 'var(--danger)';
                else if (remaining < 600) el.style.background = 'var(--warning)';
                else el.style.background = 'var(--success)';
            };

            update();
            setInterval(update, 1000);
        }
    },

    /**
     * Standard UI Handlers (Modals, Dropdowns)
     */
    
    /**
     * Global Notification System (Toasts)
     */
    Notification: {
        init: function() {
            // Check for Django messages to show as toasts
            const messagesEl = document.getElementById('django-messages');
            if (messagesEl) {
                try {
                    const messages = JSON.parse(messagesEl.textContent);
                    messages.forEach(m => {
                        if (m.tags.includes('modal')) {
                            const type = m.tags.includes('success') ? 'success' : 
                                         (m.tags.includes('error') ? 'error' : 
                                         (m.tags.includes('warning') ? 'warning' : 'info'));
                            ShikshaWave.Dialog[type](type.charAt(0).toUpperCase() + type.slice(1), m.content);
                        } else {
                            this.showToast(m.tags, m.content);
                        }
                    });
                } catch (e) {
                    console.error('Error parsing Django messages:', e);
                }
            }
        },

        showToast: function(type, message, title = '') {
            const container = document.getElementById('toastContainer');
            if (!container) return;

            const baseTitle = title || (type.charAt(0).toUpperCase() + type.slice(1));
            const iconClass = {
                'success': 'fas fa-check-circle',
                'error': 'fas fa-exclamation-circle',
                'warning': 'fas fa-exclamation-triangle',
                'info': 'fas fa-info-circle'
            }[type] || 'fas fa-info-circle';

            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="toast-content">
                    <div class="toast-title">${baseTitle}</div>
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close">
                    <i class="fas fa-times"></i>
                </button>
            `;

            container.appendChild(toast);

            // Trigger animation
            setTimeout(() => toast.classList.add('show'), 10);

            // Auto-hide
            const hideTimeout = setTimeout(() => this.hideToast(toast), 5000);

            // Manual hide
            toast.querySelector('.toast-close').addEventListener('click', () => {
                clearTimeout(hideTimeout);
                this.hideToast(toast);
            });
        },

        hideToast: function(toast) {
            toast.classList.add('hide');
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        }
    },
    UI: {
        init: function () {
            this.setupDropdowns();
            this.setupModals();
            this.setupFullscreen();
            this.restoreFullscreen();
            this.setupThemeModal();
            this.setupDownloadDelegates();
        },
        
        /**
         * Global Download Delegator
         * Any element with [data-sw-download] will trigger standardized download
         */
        setupDownloadDelegates: function () {
            document.addEventListener('click', (e) => {
                const trigger = e.target.closest('[data-sw-download]');
                if (trigger) {
                    e.preventDefault();
                    
                    const url = trigger.getAttribute('data-sw-download');
                    if (!url) return;

                    const btnSelector = trigger.getAttribute('data-sw-btn');
                    const btn = btnSelector ? document.querySelector(btnSelector) : trigger;
                    const method = trigger.getAttribute('data-sw-method') || 'GET';
                    
                    // Close open dropdowns if this was a dropdown item
                    if (trigger.classList.contains('export-item') || trigger.closest('.sw-dropdown')) {
                        document.querySelectorAll('.sw-dropdown.show, .export-menu').forEach(d => {
                             d.style.display = 'none';
                             d.classList.remove('show');
                        });
                    }

                    ShikshaWave.Utils.downloadFile(url, {
                        btn: btn,
                        method: method,
                        filename: trigger.getAttribute('data-sw-filename'),
                        successMsg: trigger.getAttribute('data-sw-success-msg'),
                        errorMsg: trigger.getAttribute('data-sw-error-msg'),
                        loadingText: trigger.getAttribute('data-sw-loading-text')
                    });
                }
            });
        },

        restoreFullscreen: function () {
            const isZen = localStorage.getItem('sw-fullscreen-active') === 'true';
            if (isZen) {
                document.body.classList.add('sw-fullscreen-active');

                // Native fullscreen requires a click, so we'll wait for the first click on the document
                const retriggerHandler = () => {
                    if (localStorage.getItem('sw-fullscreen-active') === 'true' && !document.fullscreenElement) {
                        this.toggleFullscreen(true, 'on');
                    }
                    document.removeEventListener('mousedown', retriggerHandler);
                };
                document.addEventListener('mousedown', retriggerHandler);
            }
        },

        setupFullscreen: function () {
            const btn = document.getElementById('fullscreenToggle');
            const exitBtn = document.getElementById('exitFullscreenBtn');
            if (btn) btn.addEventListener('click', () => this.toggleFullscreen());
            if (exitBtn) exitBtn.addEventListener('click', () => this.toggleFullscreen());

            // Sync state if user exits via ESC key or other browser controls
            document.addEventListener('fullscreenchange', () => {
                if (!document.fullscreenElement) {
                    document.body.classList.remove('sw-fullscreen-active');
                    localStorage.setItem('sw-fullscreen-active', 'false');
                } else {
                    document.body.classList.add('sw-fullscreen-active');
                    localStorage.setItem('sw-fullscreen-active', 'true');
                }
            });
        },

        toggleFullscreen: function (silent = false, forceState = null) {
            const isActiveAlready = document.body.classList.contains('sw-fullscreen-active');

            // If forceState is 'on', we want to be active. If 'off', inactive. Otherwise toggle.
            const targetActive = forceState === 'on' ? true : (forceState === 'off' ? false : !isActiveAlready);

            if (targetActive) {
                // Enter Fullscreen Mode
                document.body.classList.add('sw-fullscreen-active');
                localStorage.setItem('sw-fullscreen-active', 'true');

                // Try native browser fullscreen
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(err => {
                        if (!silent) console.error(`Error attempting to enable full-screen mode: ${err.message}`);
                    });
                }
            } else {
                // Exit Fullscreen Mode
                document.body.classList.remove('sw-fullscreen-active');
                localStorage.setItem('sw-fullscreen-active', 'false');

                // Exit native browser fullscreen
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                }
            }
        },

        setupDropdowns: function () {
            document.querySelectorAll('[data-sw-dropdown]').forEach(trigger => {
                const targetId = trigger.getAttribute('data-sw-dropdown');
                const target = document.getElementById(targetId);

                if (target) {
                    trigger.addEventListener('click', (e) => {
                        e.stopPropagation(); // Stop click from bubbling up
                        // Close any other open dropdowns first
                        document.querySelectorAll('.sw-dropdown.show').forEach(d => {
                            if (d !== target) d.classList.remove('show');
                        });
                        target.classList.toggle('show');
                    });
                }
            });

            // Close dropdowns when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.sw-dropdown') && !e.target.closest('[data-sw-dropdown]')) {
                    document.querySelectorAll('.sw-dropdown.show').forEach(d => d.classList.remove('show'));
                }
            });
        },

        setupModals: function () {
            // Use event delegation for modal triggers to be more robust
            document.addEventListener('click', (e) => {
                const trigger = e.target.closest('[data-sw-modal]');
                if (trigger) {
                    e.preventDefault();
                    const modalId = trigger.getAttribute('data-sw-modal');
                    this.openModal(modalId);
                }
            });

            // Standardize closing behavior for all modals using delegation too
            document.addEventListener('click', (e) => {
                // Backdrop click
                if (e.target.classList.contains('sw-modal-container')) {
                    this.closeModal(e.target.id);
                }
                // Close button click
                const closeBtn = e.target.closest('.sw-modal-close');
                if (closeBtn) {
                    const container = closeBtn.closest('.sw-modal-container');
                    if (container) this.closeModal(container.id);
                }
            });
        },

        openModal: function (id) {
            const modal = document.getElementById(id);
            if (modal) {
                modal.style.display = 'flex';
                // Trigger reflow for animation
                modal.offsetHeight;
                modal.classList.add('show');
                document.body.style.overflow = 'hidden';
            }
        },

        closeModal: function (id) {
            const modal = document.getElementById(id);
            if (modal) {
                modal.classList.remove('show');
                setTimeout(() => {
                    modal.style.display = 'none';
                    if (!document.querySelector('.sw-modal-container.show')) {
                        document.body.style.overflow = '';
                    }
                }, 300);
            }
        },

        setupThemeModal: function () {
            const themeModal = document.getElementById('themeModal');
            if (!themeModal) return;

            const themeGrid = document.getElementById('themeGrid');
            const saveBtn = document.getElementById('saveThemeBtn');
            const applyToSchoolCheckbox = document.getElementById('applyToSchool');
            this.selectedThemeId = null;

            // Load themes when modal opens
            document.querySelectorAll('[data-sw-modal="themeModal"]').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.loadThemes();
                });
            });

            if (saveBtn) {
                saveBtn.addEventListener('click', async () => {
                    if (!this.selectedThemeId) {
                        ShikshaWave.Dialog.error('Selection Required', 'Please select a theme first.');
                        return;
                    }

                    saveBtn.disabled = true;
                    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

                    try {
                        const response = await ShikshaWave.Utils.fetch('/api/set-theme/', {
                            method: 'POST',
                            body: JSON.stringify({
                                theme_id: this.selectedThemeId,
                                apply_to_school: applyToSchoolCheckbox ? applyToSchoolCheckbox.checked : false
                            })
                        });

                        const data = await response.json();
                        if (data.success) {
                            location.reload();
                        } else {
                            ShikshaWave.Dialog.error('Theme Update Failed', data.error || 'Failed to update theme.');
                            saveBtn.disabled = false;
                            saveBtn.textContent = 'Save Selection';
                        }
                    } catch (err) {
                        console.error(err);
                        saveBtn.disabled = false;
                        saveBtn.textContent = 'Save Selection';
                    }
                });
            }

            // Delegate click for theme cards
            if (themeGrid) {
                themeGrid.addEventListener('click', (e) => {
                    const card = e.target.closest('.sw-theme-card');
                    if (card) {
                        document.querySelectorAll('.sw-theme-card').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');
                        this.selectedThemeId = card.dataset.id;
                    }
                });
            }
        },

        loadThemes: async function () {
            const themeGrid = document.getElementById('themeGrid');
            const saveBtn = document.getElementById('saveThemeBtn');
            if (!themeGrid) return;

            themeGrid.innerHTML = '<div class="sw-theme-loading"><i class="fas fa-spinner fa-spin"></i> Loading themes...</div>';
            if (saveBtn) saveBtn.disabled = true;

            try {
                const response = await ShikshaWave.Utils.fetch('/api/themes/');
                const data = await response.json();
                if (data.success) {
                    themeGrid.innerHTML = '';
                    data.themes.forEach(theme => {
                        const isActive = theme.id == data.current_theme_id;
                        if (isActive) this.selectedThemeId = theme.id;

                        const card = document.createElement('div');
                        card.className = `sw-theme-card ${isActive ? 'active' : ''}`;
                        card.dataset.id = theme.id;
                        card.innerHTML = `
                            <div class="sw-color-preview" style="background: ${theme.primary_color}"></div>
                            <div class="sw-theme-info">
                                <span class="sw-theme-name">${theme.name}</span>
                            </div>
                        `;
                        themeGrid.appendChild(card);
                    });
                    if (saveBtn) saveBtn.disabled = false;
                }
            } catch (err) {
                console.error("Theme Load Error:", err);
                themeGrid.innerHTML = '<div class="sw-theme-error">Failed to load themes.</div>';
            }
        },

        setupSidebarToggle: function () {
            const toggle = document.getElementById('sidebarToggle');
            const mobileTrigger = document.getElementById('mobileTrigger');
            const sidebar = document.getElementById('swSidebar');
            const layout = document.querySelector('.sw-layout');
            const resizer = document.getElementById('sidebarResizer');
            const overlay = document.getElementById('mobileOverlay');
            if (!sidebar) return;

            // Load saved width from localStorage
            const savedWidth = localStorage.getItem('sw-sidebar-width');
            if (savedWidth) {
                document.documentElement.style.setProperty('--sidebar-width', savedWidth);
            }

            const isMobile = () => window.innerWidth <= 768;

            const toggleSidebar = () => {
                const isOpenMobile = sidebar.classList.toggle('open-mobile');
                if (overlay) overlay.classList.toggle('active', isOpenMobile);
            };

            const closeSidebarOnMobile = () => {
                if (isMobile() && sidebar.classList.contains('open-mobile')) {
                    sidebar.classList.remove('open-mobile');
                    if (overlay) overlay.classList.remove('active');
                }
            };

            // Desktop toggle (inside sidebar)
            if (toggle) {
                toggle.addEventListener('click', () => {
                    const isCollapsed = sidebar.classList.toggle('collapsed');
                    if (layout) layout.classList.toggle('sidebar-collapsed', isCollapsed);
                    // Optional: persist state in localStorage
                    localStorage.setItem('sw-sidebar-collapsed', isCollapsed);
                });
            }

            // Mobile Specific Floating Trigger Logic
            if (mobileTrigger) {
                // Restore saved vertical position
                const savedTop = localStorage.getItem('sw-mobile-trigger-top');
                if (savedTop) {
                    mobileTrigger.style.top = savedTop;
                    mobileTrigger.style.transform = 'none'; // Clear the automatic -50% translateY to map 1:1 with pixels
                }

                let isDraggingTrigger = false;
                let dragStartPosY = 0;
                let triggerStartTop = 0;
                let hasMoved = false;

                const onDragStart = (e) => {
                    isDraggingTrigger = true;
                    hasMoved = false;
                    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                    dragStartPosY = clientY;

                    const rect = mobileTrigger.getBoundingClientRect();
                    // Calculate current top. If transform is still -50%, it compensates for that natively
                    triggerStartTop = rect.top;

                    // Wipe transform once manual dragging starts so top Maps 1:1
                    mobileTrigger.style.transform = 'none';

                    document.body.style.userSelect = 'none';
                };

                const onDragMove = (e) => {
                    if (!isDraggingTrigger) return;

                    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                    const deltaY = clientY - dragStartPosY;

                    if (Math.abs(deltaY) > 10) {
                        hasMoved = true;
                    }

                    // Calculate new top, clamp between 0 and window height minus button height
                    let newTop = triggerStartTop + deltaY;
                    const maxTop = window.innerHeight - mobileTrigger.offsetHeight;
                    newTop = Math.max(0, Math.min(newTop, maxTop));

                    // Use requestAnimationFrame for smooth dragged painting
                    requestAnimationFrame(() => {
                        mobileTrigger.style.top = `${newTop}px`;
                    });
                };

                const onDragEnd = (e) => {
                    if (!isDraggingTrigger) return;
                    isDraggingTrigger = false;
                    document.body.style.userSelect = '';

                    // Save final position ONLY if a drag actually happened
                    if (hasMoved) {
                        localStorage.setItem('sw-mobile-trigger-top', mobileTrigger.style.top);
                    }
                };

                // Use the native click listener to determine whether to open the drawer
                mobileTrigger.addEventListener('click', (e) => {
                    if (hasMoved) {
                        // User was just dragging the button to position it, block the opening!
                        e.preventDefault();
                        e.stopPropagation();
                        // Reset flag slightly later to ensure click bubble is fully blocked
                        setTimeout(() => hasMoved = false, 50);
                    } else {
                        // Clean tap! Open the sidebar!
                        toggleSidebar();
                    }
                });

                // Touch Events
                mobileTrigger.addEventListener('touchstart', onDragStart, { passive: true });
                document.addEventListener('touchmove', onDragMove, { passive: true });
                document.addEventListener('touchend', onDragEnd);

                // Mouse Events (Fallback for testing on desktop simulators)
                mobileTrigger.addEventListener('mousedown', onDragStart);
                document.addEventListener('mousemove', onDragMove);
                document.addEventListener('mouseup', onDragEnd);
            }

            // Close on overlay tap
            if (overlay) {
                overlay.addEventListener('click', closeSidebarOnMobile);
            }

            // Restore state on load
            if (localStorage.getItem('sw-sidebar-collapsed') === 'true') {
                sidebar.classList.add('collapsed');
                if (layout) layout.classList.add('sidebar-collapsed');
            }

            // Resizer logic
            if (resizer) {
                let isResizing = false;
                let startX;
                let startWidth;

                resizer.addEventListener('mousedown', (e) => {
                    if (sidebar.classList.contains('collapsed')) return;
                    isResizing = true;
                    sidebar.classList.add('resizing');
                    startX = e.clientX;
                    startWidth = parseInt(document.defaultView.getComputedStyle(sidebar).width, 10);

                    document.body.style.cursor = 'col-resize';
                    document.body.style.userSelect = 'none'; // Prevent text selection
                });

                document.addEventListener('mousemove', (e) => {
                    if (!isResizing) return;

                    const newWidth = startWidth + (e.clientX - startX);
                    // Constrain width between min and max values
                    if (newWidth >= 200 && newWidth <= 500) {
                        document.documentElement.style.setProperty('--sidebar-width', `${newWidth}px`);
                    }
                });

                document.addEventListener('mouseup', () => {
                    if (isResizing) {
                        isResizing = false;
                        sidebar.classList.remove('resizing');
                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';

                        // Save the new width to localStorage
                        const finalWidth = document.documentElement.style.getPropertyValue('--sidebar-width');
                        localStorage.setItem('sw-sidebar-width', finalWidth);
                    }
                });
            }

            // Auto-expand minimized sidebar on menu click
            sidebar.addEventListener('click', (e) => {
                if (sidebar.classList.contains('collapsed')) {
                    // Only expand if they clicked a menu item/link, not just empty space
                    const clickedItem = e.target.closest('.sw-menu-item');
                    if (clickedItem) {
                        sidebar.classList.remove('collapsed');
                        if (layout) layout.classList.remove('sidebar-collapsed');
                        localStorage.setItem('sw-sidebar-collapsed', 'false');
                    }
                }
            });
        }
    },

    /**
     * Global Dialog System (SweetAlert2 wrapper)
     * Provides standardized, theme-aware, and compact popups
     */
    Dialog: {
        confirm: function(options) {
            if (typeof Swal === 'undefined') {
                console.error('SweetAlert2 not loaded!');
                return Promise.resolve({ isConfirmed: confirm(options.text || 'Are you sure?') });
            }

            return Swal.fire({
                title: options.title || 'Are you sure?',
                text: options.text || '',
                icon: options.icon || 'warning',
                showCancelButton: true,
                confirmButtonText: options.confirmText || 'Confirm',
                cancelButtonText: options.cancelText || 'Cancel',
                reverseButtons: options.reverse || true,
                // These will use our CSS overrides automatically
                customClass: {
                    popup: 'sw-swal-popup',
                    confirmButton: 'sw-swal-confirm',
                    cancelButton: 'sw-swal-cancel'
                }
            });
        },

        success: function(title, text = '', timer = 2000) {
            if (typeof Swal === 'undefined') {
                return alert(title + '\n' + text);
            }

            return Swal.fire({
                icon: 'success',
                title: title,
                text: text,
                timer: timer,
                showConfirmButton: false
            });
        },

        error: function(title, text = '') {
            if (typeof Swal === 'undefined') {
                return alert('Error: ' + title + '\n' + text);
            }

            return Swal.fire({
                icon: 'error',
                title: title,
                text: text
            });
        }
    },

    /**
     * Utility functions
     */
    Utils: {
        fetch: function (url, options = {}) {
            const method = (options.method || 'GET').toUpperCase();
            const defaults = {
                headers: {
                    'X-CSRFToken': this.getCsrf()
                }
            };
            
            // Only set Content-Type if not GET and NO custom content-type provided
            // AND the body is NOT FormData (browser needs to set multipart/form-data with boundary)
            const isFormData = options.body instanceof FormData;
            if (method !== 'GET' && (!options.headers || !options.headers['Content-Type']) && !isFormData) {
                defaults.headers['Content-Type'] = 'application/json';
            }
            
            const headers = { ...defaults.headers, ...(options.headers || {}) };
            return fetch(url, { ...defaults, ...options, headers: headers });
        },

        getCsrf: function () {
            return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        },

        /**
         * Global Download Utility with Loading State
         * @param {string} url - The URL to fetch the file from
         * @param {Object} options - Configuration options
         * @param {HTMLElement} options.btn - The button element that triggered the download (for loading state)
         * @param {string} options.filename - The default filename for the download
         * @param {string} options.successMsg - Success message for toast
         * @param {string} options.errorMsg - Error message for toast
         */
        downloadFile: async function(url, options = {}) {
            const btn = options.btn;
            const originalContent = btn ? btn.innerHTML : null;
            const loadingText = options.loadingText || '<i class="fas fa-spinner fa-spin"></i>';
            
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = loadingText;
                btn.classList.add('loading');
            }
            
            try {
                // Use the existing fetch utility which handles CSRF
                const response = await this.fetch(url, {
                    method: options.method || 'GET',
                    body: options.body || null
                });

                if (!response.ok) {
                    let errorText = "Download failed (" + response.status + ")";
                    try {
                        errorText = await response.text();
                    } catch (e) {
                        console.warn("Could not read error body", e);
                    }
                    throw new Error(errorText || 'Download failed');
                }
                
                const blob = await response.blob();
                
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                
                // Try to get filename from content-disposition header if not provided
                let filename = options.filename;
                if (!filename) {
                    try {
                        const disposition = response.headers.get('Content-Disposition');
                        if (disposition && disposition.indexOf('attachment') !== -1) {
                            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                            const matches = filenameRegex.exec(disposition);
                            if (matches != null && matches[1]) {
                                filename = matches[1].replace(/['"]/g, '');
                            }
                        }
                    } catch (e) { console.warn("Could not parse filename from headers", e); }
                }
                
                a.download = filename || 'downloaded_file';
                a.style.display = 'none';
                document.body.appendChild(a);
                
                a.click();
                
                // Cleanup
                setTimeout(() => {
                    if (document.body.contains(a)) document.body.removeChild(a);
                    window.URL.revokeObjectURL(downloadUrl);
                }, 500); // Increased timeout for safety
                
                if (options.successMsg) {
                    ShikshaWave.Notification.showToast('success', options.successMsg);
                }
            } catch (err) {
                console.error('Download Error:', err);
                ShikshaWave.Notification.showToast('error', options.errorMsg || 'Failed to download file: ' + err.message);
                
                // Final fallback if everything fails
                if (btn && !btn.classList.contains('download-fallback-tried')) {
                    btn.classList.add('download-fallback-tried');
                    window.location.href = url;
                }
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = originalContent;
                    btn.classList.remove('loading');
                }
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => ShikshaWave.init());
window.ShikshaWave = ShikshaWave;

window.showToast = (type, message, title) => ShikshaWave.Notification.showToast(type, message, title);
window.openModal = (id) => ShikshaWave.UI.openModal(id);
window.closeModal = (id) => ShikshaWave.UI.closeModal(id);
