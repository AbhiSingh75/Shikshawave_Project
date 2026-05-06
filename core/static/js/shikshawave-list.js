/**
 * ShikshaWave Global List Management Script
 * Handles sorting, filtering, pagination, column visibility, and exports for all list pages.
 */
document.addEventListener("DOMContentLoaded", function () {

    // --- TOAST NOTIFICATIONS ---
    window.showToast = function (type, message, duration = 5000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} show`;
        const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle');
        toast.innerHTML = `
            <div class="toast-icon"><i class="fas ${icon}"></i></div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close"><i class="fas fa-times"></i></button>
        `;
        container.appendChild(toast);
        toast.querySelector('.toast-close').onclick = () => toast.remove();
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };

    // Parse messages from Django if present
    const messagesEl = document.getElementById('django-messages');
    if (messagesEl) {
        try {
            const messages = JSON.parse(messagesEl.textContent);
            messages.forEach(m => window.showToast(m.tags, m.content));
        } catch (e) {
            console.error('Error parsing messages:', e);
        }
    }

    // --- SORTING LOGIC ---
    document.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', function () {
            const column = this.dataset.sort;
            if (!column) return;

            const currentUrl = new URL(window.location.href);
            const currentSort = currentUrl.searchParams.get('order_by');
            const currentDir = currentUrl.searchParams.get('order_direction') || 'ASC';

            let newDir = 'ASC';
            if (currentSort === column && currentDir === 'ASC') {
                newDir = 'DESC';
            }

            currentUrl.searchParams.set('order_by', column);
            currentUrl.searchParams.set('order_direction', newDir);
            window.location.replace(currentUrl.toString());
        });
    });

    // Update Sort Icons on Load
    const urlParams = new URLSearchParams(window.location.search);
    const activeSort = urlParams.get('order_by');
    const activeDir = urlParams.get('order_direction') || 'ASC';

    if (activeSort) {
        const th = document.querySelector(`th[data-sort="${activeSort}"]`);
        if (th) {
            const icon = th.querySelector('.sort-icon');
            if (icon) {
                icon.className = `fas fa-sort-${activeDir === 'DESC' ? 'down' : 'up'} sort-icon active`;
            }
        }
    }

    // --- FILTERS & SEARCH ---
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(applyGlobalFilters, 600);
        });
    }

    const filterModal = document.getElementById("filter-modal");
    const filterBtn = document.getElementById("filterBtn") || document.getElementById("filter-btn");
    const closeFilterBtn = document.getElementById("close-filter-modal") || document.getElementById("close-filter") || document.querySelector(".sw-modal-close");
    const applyFiltersBtn = document.getElementById("apply-filters");
    const resetFiltersBtn = document.getElementById("reset-filters");

    if (filterBtn && filterModal) {
        filterBtn.addEventListener("click", () => {
            filterModal.classList.add("show");
            // Also ensure display: flex if CSS doesn't handle it
            filterModal.style.display = "flex"; 
        });
    }

    if (closeFilterBtn && filterModal) {
        closeFilterBtn.addEventListener("click", () => {
            filterModal.classList.remove("show");
            setTimeout(() => {
                if (!filterModal.classList.contains('show')) {
                    filterModal.style.display = "none";
                }
            }, 300);
        });
    }

    // Close on window click
    window.addEventListener("click", (e) => {
        if (filterModal && e.target === filterModal) {
            filterModal.classList.remove("show");
            setTimeout(() => {
                if (!filterModal.classList.contains('show')) {
                    filterModal.style.display = "none";
                }
            }, 300);
        }
    });

    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener("click", () => {
            applyGlobalFilters();
            if (filterModal) {
                filterModal.classList.remove("show");
                setTimeout(() => {
                    if (!filterModal.classList.contains('show')) {
                        filterModal.style.display = "none";
                    }
                }, 300);
            }
        });
    }

    // Handle Enter key in filter modal
    if (filterModal) {
        filterModal.addEventListener("keypress", (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (applyFiltersBtn) applyFiltersBtn.click();
            }
        });
    }

    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener("click", () => {
            window.location.href = window.location.pathname; // Clear all query params
        });
    }

    function applyGlobalFilters() {
        const params = new URLSearchParams(window.location.search);

        // Search Input Handling
        if (searchInput) {
            const val = searchInput.value.trim();
            const searchParamName = searchInput.name || 'search';
            if (val) {
                params.set(searchParamName, val);
            } else {
                params.delete(searchParamName);
            }
        }

        // Modal Filter Handling
        if (filterModal) {
            const filterElements = filterModal.querySelectorAll('input[name], select[name], textarea[name]');
            filterElements.forEach(el => {
                const val = el.value.trim();
                if (val) {
                    params.set(el.name, val);
                } else {
                    params.delete(el.name);
                }
            });
        }

        // Pagination Handling
        const perPageSelector = document.getElementById("per-page-selector");
        if (perPageSelector) {
            params.set('per_page', perPageSelector.value);
        }
        params.delete('page'); // Reset to page 1 on new filter
        window.location.search = params.toString();
    }

    // --- CUSTOM DROPDOWNS ---
    window.initCustomDropdowns = function () {
        const dropdowns = document.querySelectorAll('.custom-dropdown');

        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.custom-dropdown-toggle');
            const menu = dropdown.querySelector('.custom-dropdown-menu');
            const targetId = dropdown.dataset.target;
            const nativeSelect = document.getElementById(targetId);

            if (!toggle || !menu || !nativeSelect) return;

            // Initialize toggle text and state from native select
            dropdown.updateToggleText = () => {
                const selectedOption = nativeSelect.options[nativeSelect.selectedIndex];
                const textSpan = toggle.querySelector('.custom-dropdown-text');
                if (textSpan && selectedOption) {
                    textSpan.textContent = selectedOption.textContent.trim();
                }

                // Update selected class in custom menu
                menu.querySelectorAll('.custom-dropdown-option').forEach(opt => {
                    opt.classList.toggle('selected', opt.dataset.value === nativeSelect.value);
                });

                // Update disabled state
                if (nativeSelect.disabled) {
                    dropdown.classList.add('disabled');
                } else {
                    dropdown.classList.remove('disabled');
                }
            };

            // Rebuild options from native select
            dropdown.rebuildOptions = () => {
                const searchDiv = menu.querySelector('.dropdown-search');
                menu.innerHTML = '';
                if (searchDiv) menu.appendChild(searchDiv);
                
                Array.from(nativeSelect.options).forEach(opt => {
                    if (opt.style.display === 'none' || opt.hidden) return;
                    const item = document.createElement('div');
                    item.className = 'custom-dropdown-option';
                    item.dataset.value = opt.value;
                    item.textContent = opt.textContent.trim();
                    if (opt.value === nativeSelect.value) item.classList.add('selected');
                    menu.appendChild(item);
                });
            };

            if (dropdown.dataset.initialized === 'true') {
                dropdown.updateToggleText();
                return;
            }
            dropdown.dataset.initialized = 'true';
            
            // Initial population of options and toggle text
            dropdown.rebuildOptions();
            dropdown.updateToggleText();

            // Toggle menu visibility
            toggle.addEventListener('click', (e) => {
                if (dropdown.classList.contains('disabled')) return;
                e.stopPropagation();
                const isActive = dropdown.classList.contains('active') || dropdown.classList.contains('open');

                // Close all other dropdowns
                document.querySelectorAll('.custom-dropdown.active, .custom-dropdown.open').forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('active', 'open', 'open-up');
                    }
                });

                if (!isActive) {
                    // Smart Positioning
                    const rect = toggle.getBoundingClientRect();
                    const windowHeight = window.innerHeight;
                    const spaceBelow = windowHeight - rect.bottom;
                    const spaceAbove = rect.top;
                    const menuMaxHeight = 250; 

                    if (rect.bottom > (windowHeight * 0.6) && spaceBelow < menuMaxHeight && spaceAbove > spaceBelow) {
                        dropdown.classList.add('open-up');
                    } else {
                        dropdown.classList.remove('open-up');
                    }
                    dropdown.classList.add('active', 'open');
                } else {
                    dropdown.classList.remove('active', 'open', 'open-up');
                }
            });

            // Handle option selection
            menu.addEventListener('click', (e) => {
                const option = e.target.closest('.custom-dropdown-option');
                if (!option) return;

                e.stopPropagation();
                const value = option.dataset.value;
                nativeSelect.value = value;
                
                // Update hidden input if it exists
                const hiddenInput = document.getElementById(`${targetId}-id-input`);
                if (hiddenInput) {
                    hiddenInput.value = value;
                    hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                nativeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                dropdown.updateToggleText();
                dropdown.classList.remove('active', 'open', 'open-up');
            });
        });
    };

    window.refreshCustomDropdowns = () => {
        document.querySelectorAll('.custom-dropdown').forEach(d => {
            if (d.rebuildOptions) d.rebuildOptions();
            if (d.updateToggleText) d.updateToggleText();
        });
    };

    initCustomDropdowns();

    // --- PAGINATION ---
    document.querySelectorAll(".pagination-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            if (this.disabled) return;
            const params = new URLSearchParams(window.location.search);
            params.set("page", this.dataset.page);
            window.location.search = params.toString();
        });
    });

    const perPageSelector = document.getElementById("per-page-selector");
    if (perPageSelector) {
        perPageSelector.addEventListener("change", function () {
            const params = new URLSearchParams(window.location.search);
            params.set("per_page", this.value);
            params.delete("page");
            window.location.search = params.toString();
        });
    }

    // --- GLOBAL CLICK HANDLER (Consolidated) ---
    const columnMenu = document.getElementById("column-menu");
    const exportMenu = document.getElementById("exportMenu");

    window.addEventListener("click", function (e) {
        // Modal Backdrop
        if (filterModal && e.target === filterModal) {
            filterModal.classList.remove('show');
            setTimeout(() => { filterModal.style.display = 'none'; }, 300);
        }
        // Column Menu
        if (columnMenu && !e.target.closest(".column-visibility")) {
            columnMenu.style.display = "none";
        }
        // Export Menu
        if (exportMenu && !e.target.closest(".export-dropdown-container")) {
            exportMenu.style.display = "none";
        }
        // Custom Dropdowns
        if (!e.target.closest('.custom-dropdown')) {
            document.querySelectorAll('.custom-dropdown.active, .custom-dropdown.open').forEach(d => {
                d.classList.remove('active', 'open', 'open-up');
            });
        }
    });

    // --- COLUMN VISIBILITY ---
    function initializeColumnMenu() {
        if (!columnMenu) return;

        const tableHeaders = document.querySelectorAll("table th[data-column]");
        // Namespace local storage by pathname so each list page has its own config
        const storageKey = `shikshawave_columns_${window.location.pathname}`;
        const preferences = JSON.parse(localStorage.getItem(storageKey) || "{}");

        columnMenu.innerHTML = `
            <div class="column-menu-header">
                <button id="cols-select-all" style="padding:4px 8px; font-size:12px;">Select All</button>
                <button id="cols-reset" style="padding:4px 8px; font-size:12px;">Reset</button>
            </div>
            <div class="column-menu-list"></div>
        `;

        const listContainer = columnMenu.querySelector(".column-menu-list");
        tableHeaders.forEach(th => {
            const colId = th.getAttribute("data-column");
            const colName = th.textContent.replace(/<[^>]*>/g, '').trim() || colId;
            const isVisible = preferences[colId] !== false;

            const item = document.createElement("div");
            item.className = "column-item";
            item.innerHTML = `
                <input type="checkbox" id="col-${colId}" ${isVisible ? 'checked' : ''} data-column="${colId}">
                <label for="col-${colId}">${colName}</label>
            `;
            listContainer.appendChild(item);
            toggleColumn(colId, isVisible);
        });

        // Event Delegation for toggles
        listContainer.addEventListener("change", (e) => {
            if (e.target.tagName === 'INPUT') {
                const colId = e.target.getAttribute("data-column");
                const isVisible = e.target.checked;
                toggleColumn(colId, isVisible);
                savePreferences();
            }
        });

        document.getElementById("cols-select-all").addEventListener("click", () => {
            listContainer.querySelectorAll("input").forEach(i => {
                i.checked = true;
                toggleColumn(i.dataset.column, true);
            });
            savePreferences();
        });

        document.getElementById("cols-reset").addEventListener("click", () => {
            listContainer.querySelectorAll("input").forEach(i => {
                i.checked = true;
                toggleColumn(i.dataset.column, true);
            });
            localStorage.removeItem(storageKey);
        });

        function savePreferences() {
            const prefs = {};
            listContainer.querySelectorAll("input").forEach(i => {
                prefs[i.dataset.column] = i.checked;
            });
            localStorage.setItem(storageKey, JSON.stringify(prefs));
        }
    }

    function toggleColumn(colId, isVisible) {
        const cells = document.querySelectorAll(`[data-column="${colId}"]`);
        cells.forEach(c => c.style.display = isVisible ? "" : "none");
    }
    const columnToggle = document.getElementById("columnsBtn") || document.getElementById("column-toggle");
    if (columnToggle && columnMenu) {
        columnToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            columnMenu.style.display = (columnMenu.style.display === "flex") ? "none" : "flex";
        });
        initializeColumnMenu();
    }

    // --- EXPORT MENU ---
    const exportBtn = document.getElementById("exportBtn") || document.getElementById("export-btn");
    if (exportBtn && exportMenu) {
        exportBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            exportMenu.style.display = exportMenu.style.display === "block" || exportMenu.style.display === "flex" ? "none" : "block";
        });
    }

    document.querySelectorAll(".export-item").forEach(item => {
        item.addEventListener("click", function (e) {
            e.preventDefault();
            console.log("💾 Export item clicked:", this.dataset.format);
            
            const format = this.dataset.format;
            const delimiter = this.dataset.delimiter;
            const params = new URLSearchParams(window.location.search);
            params.set("format", format);
            if (delimiter) params.set("delimiter", delimiter);

            const menu = document.getElementById("exportMenu");
            const exportUrlBase = menu ? menu.dataset.exportUrl : null;
            
            if (exportUrlBase) {
                const fullUrl = `${exportUrlBase}${exportUrlBase.includes('?') ? '&' : '?'}${params.toString()}`;
                const filename = `Export_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`;
                
                console.log("🔗 Export URL:", fullUrl);

                if (window.ShikshaWave && ShikshaWave.Utils && ShikshaWave.Utils.downloadFile) {
                    console.log("🚀 Using ShikshaWave.Utils.downloadFile");
                    ShikshaWave.Utils.downloadFile(fullUrl, {
                        getCsrf: true,
                        btn: exportBtn,
                        filename: filename,
                        successMsg: 'Export started...'
                    });
                } else {
                    console.warn("⚠️ ShikshaWave utility not found, falling back to location.href");
                    window.location.href = fullUrl;
                }
            } else {
                console.log("📄 Exporting via frontend table scrape");
                exportFrontendTable(format, delimiter);
            }
            
            if (menu) menu.style.display = 'none';
        });
    });

    function exportFrontendTable(format, delimiterName) {
        const table = document.querySelector("table");
        if (!table) return showToast("error", "No table found to export.");

        let delimiter = ",";
        if (delimiterName === "pipe") delimiter = "|";
        if (delimiterName === "tab") delimiter = "\t";

        let csvContent = "";

        // Helper to format CSV values
        const formatValue = (text) => {
            text = text.replace(/(\r\n|\n|\r)/gm, " ").trim();
            if (text.includes(delimiter) || text.includes('"') || text.includes(',')) {
                return `"${text.replace(/"/g, '""')}"`;
            }
            return text;
        };

        // Get headers (only visible ones, exclude 'actions' or 'photo' usually, but let's just use visible content)
        const headers = Array.from(table.querySelectorAll('th'))
            .filter(th => th.style.display !== 'none' && th.dataset.column !== 'actions' && th.dataset.column !== 'photo')
            .map(th => formatValue(th.textContent.trim().replace(/▼|▲/g, '')));

        csvContent += headers.join(delimiter) + "\n";

        // Get rows
        const tbody = table.querySelector('tbody');
        if (tbody) {
            const rows = Array.from(tbody.querySelectorAll('tr')).filter(tr => tr.style.display !== 'none');
            rows.forEach(row => {
                const rowData = Array.from(table.querySelectorAll('th'))
                    .filter(th => th.style.display !== 'none' && th.dataset.column !== 'actions' && th.dataset.column !== 'photo')
                    .map((th, index) => {
                        // find corresponding td by index in the row.
                        // However, some columns might be hidden, so we map by calculating actual index.
                        // Actually, it's safer to map by data-column if we can, but let's just find the corresponding td
                        const thElements = Array.from(table.querySelectorAll('th'));
                        const originalIndex = thElements.indexOf(th);
                        const td = row.querySelectorAll('td')[originalIndex];
                        if (td) {
                            // Extract text, being careful with status labels/badges
                            let text = td.textContent.trim();
                            return formatValue(text);
                        }
                        return "";
                    });
                csvContent += rowData.join(delimiter) + "\n";
            });
        }

        const addBOM = format === 'excel' || format === 'csv';
        const bom = addBOM ? "\uFEFF" : "";
        const blob = new Blob([bom + csvContent], { type: format === 'excel' ? 'application/vnd.ms-excel;charset=utf-8;' : 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const filename = `export_${new Date().toISOString().slice(0, 10)}.${format === 'excel' ? 'csv' : 'csv'}`;
        // Note: For actual xlsx we would need a library like SheetJS, so we output UTF-8 CSV which Excel handles well.
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

});

// Global CSRF Token Helper
window.getCSRFToken = function () {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
};
