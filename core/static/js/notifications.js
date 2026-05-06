/**
 * ShikshaWave Universal Notification System
 * Frontend Component
 */

class NotificationSystem {
    constructor() {
        this.unreadCount = 0;
        this.notifications = [];
        this.currentPage = 1;
        this.pageSize = 20;
        this.isOpen = false;
        this.pollInterval = 30000; // 30 seconds
        this.pollTimer = null;
        
        this.init();
    }
    
    init() {
        console.log('[Notification] Initializing...');
        const bell = document.getElementById('notificationBell');
        const badge = document.getElementById('notificationBadge');
        console.log('[Notification] Bell element:', bell);
        console.log('[Notification] Badge element:', badge);
        
        this.attachEventListeners();
        this.loadUnreadCount();
        this.startPolling();
    }
    
    attachEventListeners() {
        const bell = document.getElementById('notificationBell');
        const dropdown = document.getElementById('notificationDropdown');
        const markAllBtn = document.getElementById('markAllReadBtn');
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        
        bell?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });
        
        markAllBtn?.addEventListener('click', () => this.markAllAsRead());
        loadMoreBtn?.addEventListener('click', () => this.loadMore());
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!dropdown?.contains(e.target) && !bell?.contains(e.target)) {
                this.closeDropdown();
            }
        });
    }
    
    async loadUnreadCount() {
        try {
            const response = await fetch('/notifications/api/unread-count/');
            const data = await response.json();
            console.log('[Notification] Unread count:', data.unread_count);
            this.updateBadge(data.unread_count);
        } catch (error) {
            console.error('Error loading unread count:', error);
        }
    }
    
    async loadNotifications(page = 1) {
        try {
            const response = await fetch(`/notifications/api/list/?page=${page}&page_size=${this.pageSize}`);
            const data = await response.json();
            
            if (page === 1) {
                this.notifications = data.notifications;
            } else {
                this.notifications = [...this.notifications, ...data.notifications];
            }
            
            this.currentPage = page;
            this.renderNotifications(data);
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError();
        }
    }
    
    renderNotifications(data) {
        const listEl = document.getElementById('notificationList');
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        
        if (!listEl) return;
        
        if (this.notifications.length === 0) {
            if (listEl) listEl.innerHTML = '<div class="notification-empty" style="padding: 30px; text-align: center; color: var(--text-muted);"><i class="fas fa-bell-slash" style="font-size: 2rem; opacity: 0.3; display: block; margin-bottom: 10px;"></i><p>No new notifications</p></div>';
            if (loadMoreBtn) loadMoreBtn.style.display = 'none';
            return;
        }
        
        listEl.innerHTML = this.notifications.map(n => this.renderNotificationItem(n)).join('');
        
        // Show/hide load more button
        if (loadMoreBtn) {
            if (data.page_number < data.total_pages) {
                loadMoreBtn.style.display = 'block';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
        
        // Attach click handlers
        listEl.querySelectorAll('.sw-notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = item.dataset.notificationId;
                const targetUrl = item.dataset.targetUrl;
                this.handleNotificationClick(notificationId, targetUrl);
            });
        });
    }
    
    renderNotificationItem(notification) {
        const isUnread = !notification.IsRead;
        const timeAgo = this.getTimeAgo(notification.CreatedAt);
        const iconClass = notification.IconClass || 'fa-bell';
        const colorCode = notification.ColorCode || '#6366f1';
        const actorName = notification.CreatedByUserName || 'System';
        
        // Extract Ticket Code if present in Title (e.g. "Action on TKT-12345")
        let title = this.escapeHtml(notification.Title);
        let ticketCode = '';
        const codeMatch = title.match(/TKT-\d+/);
        if (codeMatch) {
            ticketCode = codeMatch[0];
            title = title.replace(ticketCode, '').replace('on ', '').trim();
        }

        return `
            <div class="sw-notification-item ${isUnread ? 'unread' : ''}" 
                 data-notification-id="${notification.NotificationID}"
                 data-target-url="${notification.TargetURL || '#'}">
                <div class="sw-notification-icon-mini" style="background-color: ${colorCode}20; color: ${colorCode};">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="sw-notification-content">
                    <div class="sw-notification-header">
                        <div class="sw-notification-title">${title || 'Notification'}</div>
                        <div class="sw-notification-time">${timeAgo}</div>
                    </div>
                    ${ticketCode ? `<div class="sw-notification-code">${ticketCode}</div>` : ''}
                    <div class="sw-notification-message">${this.escapeHtml(notification.Message)}</div>
                    <div class="sw-notification-meta">
                        by <span class="sw-notification-actor">${this.escapeHtml(actorName)}</span>
                    </div>
                </div>
                ${isUnread ? '<div class="sw-notification-unread-dot"></div>' : ''}
            </div>
        `;
    }
    
    async handleNotificationClick(notificationId, targetUrl) {
        await this.markAsRead(notificationId);
        this.closeDropdown();
        
        if (targetUrl && targetUrl !== '#') {
            window.location.href = targetUrl;
        }
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/notifications/api/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                // Update local state
                const notification = this.notifications.find(n => n.NotificationID == notificationId);
                if (notification) {
                    notification.IsRead = true;
                }
                this.loadUnreadCount();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/notifications/api/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                this.notifications.forEach(n => n.IsRead = true);
                this.updateBadge(0);
                this.loadNotifications(1);
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }
    
    toggleDropdown() {
        this.isOpen = !this.isOpen;
        const dropdown = document.getElementById('notificationDropdown');
        
        if (this.isOpen) {
            dropdown.style.display = 'block';
            this.loadNotifications(1);
        } else {
            dropdown.style.display = 'none';
        }
    }
    
    closeDropdown() {
        this.isOpen = false;
        const dropdown = document.getElementById('notificationDropdown');
        if (dropdown) dropdown.style.display = 'none';
    }
    
    loadMore() {
        this.loadNotifications(this.currentPage + 1);
    }
    
    updateBadge(count) {
        this.unreadCount = count;
        const badge = document.getElementById('notificationBadge');
        
        console.log('[Notification] Updating badge, count:', count, 'badge element:', badge);
        
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'flex';
                console.log('[Notification] Badge updated to:', badge.textContent);
            } else {
                badge.style.display = 'none';
            }
        } else {
            console.error('[Notification] Badge element not found!');
        }
    }
    
    startPolling() {
        this.pollTimer = setInterval(() => {
            this.loadUnreadCount();
        }, this.pollInterval);
    }
    
    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }
    
    showError() {
        const listEl = document.getElementById('notificationList');
        if (listEl) {
            listEl.innerHTML = '<div class="notification-error"><i class="fas fa-exclamation-triangle"></i><p>Error loading notifications</p></div>';
        }
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return date.toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (token) return token;
        
        // Get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        return '';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
});
