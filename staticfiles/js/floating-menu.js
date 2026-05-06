// Floating Menu JavaScript - Desktop Only
(function() {
    'use strict';
    
    // Only run on desktop
    if (window.innerWidth <= 768) return;
    
    document.addEventListener('DOMContentLoaded', function() {
        const floatingBtn = document.getElementById('floatingMenuBtn');
        const sidebar = document.getElementById('floatingSidebar');
        const overlay = document.getElementById('menuOverlay');
        const closeBtn = document.getElementById('closeSidebarBtn');
        
        if (!floatingBtn || !sidebar || !overlay || !closeBtn) return;
        
        // Draggable functionality
        let isDragging = false;
        let startY = 0;
        let startTop = 0;
        
        floatingBtn.addEventListener('mousedown', function(e) {
            isDragging = true;
            startY = e.clientY;
            const rect = floatingBtn.getBoundingClientRect();
            startTop = rect.top;
            floatingBtn.classList.add('dragging');
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            const deltaY = e.clientY - startY;
            const newTop = startTop + deltaY;
            const maxTop = window.innerHeight - floatingBtn.offsetHeight - 20;
            const clampedTop = Math.max(100, Math.min(newTop, maxTop));
            floatingBtn.style.top = clampedTop + 'px';
            floatingBtn.style.transform = 'none';
        });
        
        document.addEventListener('mouseup', function(e) {
            if (isDragging) {
                isDragging = false;
                floatingBtn.classList.remove('dragging');
                const moveDistance = Math.abs(e.clientY - startY);
                if (moveDistance < 5) {
                    sidebar.classList.add('open');
                    overlay.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
            }
        });
        
        // Close sidebar
        function closeSidebar() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        
        closeBtn.addEventListener('click', closeSidebar);
        overlay.addEventListener('click', closeSidebar);
        
        // Handle submenu toggles - delegate to dynamically loaded menu
        sidebar.addEventListener('click', function(e) {
            const link = e.target.closest('.has-submenu > .menu-link');
            if (link) {
                e.preventDefault();
                const parent = link.parentElement;
                
                // Close other open submenus
                sidebar.querySelectorAll('.menu-item.open').forEach(item => {
                    if (item !== parent) {
                        item.classList.remove('open');
                    }
                });
                
                // Toggle current submenu
                parent.classList.toggle('open');
            }
        });
        
        // Close sidebar on window resize to mobile
        window.addEventListener('resize', function() {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });
})();
