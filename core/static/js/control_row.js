/**
 * Control Row Controller Module
 * Handles filters, columns, export, and search row actions globally
 */

window.App.ControlRowController = {
    init: function () {
        console.log("Initializing Control Row Controller...");
        this.bindEvents();
    },

    /**
     * Use event delegation to handle clicks on control row elements
     */
    bindEvents: function () {
        document.addEventListener('click', (e) => {
            const target = e.target;

            // Filter Button
            const filterBtn = target.closest('#filterBtn, #filter-btn, .filter-trigger');
            if (filterBtn) {
                this.toggleFilterModal();
                return;
            }

            // Export Button Toggle
            const exportBtn = target.closest('#exportBtn');
            if (exportBtn) {
                const menu = document.getElementById('exportMenu');
                if (menu) menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
                return;
            }

            // Columns Button
            const columnsBtn = target.closest('#columnsBtn, #columns-btn, #column-toggle');
            if (columnsBtn) {
                this.toggleColumnSelector();
                return;
            }

            // Close dropdowns when clicking elsewhere
            const exportMenu = document.getElementById('exportMenu');
            if (exportMenu && !target.closest('.export-dropdown-container')) {
                exportMenu.style.display = 'none';
            }
        });

        // Handle Search Input (Debounced)
        const searchInput = document.getElementById('searchInput') || document.getElementById('search-input');
        if (searchInput) {
            let timeout = null;
            searchInput.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (window.performSearch) window.performSearch(searchInput.value);
                    else if (typeof applyFilters === 'function') applyFilters(); // Fallback to user_list style
                }, 500);
            });
        }
    },

    toggleFilterModal: function () {
        const modal = document.getElementById('filterModal') || document.getElementById('filter-modal');
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('show');
            // Trigger any page-specific init if needed
            if (window.initFilterModal) window.initFilterModal();
        }
    },

    toggleColumnSelector: function () {
        const modal = document.getElementById('columnSelectorModal') || document.getElementById('column-menu');
        if (modal) {
            modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
            modal.classList.add('show');
        }
    }
};
