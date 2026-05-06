/**
 * Filter Modal Utility Functions
 * Provides enhanced functionality for filter modals across the application
 */

class FilterModal {
    constructor(modalId = 'filter-modal') {
        this.modal = document.getElementById(modalId);
        this.filterBtn = document.getElementById('filter-btn');
        this.closeBtn = document.getElementById('close-filter-modal');
        this.applyBtn = document.getElementById('apply-filters');
        this.resetBtn = document.getElementById('reset-filters');
        
        this.init();
    }
    
    init() {
        if (!this.modal) return;
        
        this.bindEvents();
        this.setupKeyboardNavigation();
        this.ensureMobileCompatibility();
    }
    
    bindEvents() {
        // Open modal
        if (this.filterBtn) {
            this.filterBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.open();
            });
        }
        
        // Close modal
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
            });
        }
        
        // Close on backdrop click
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.close();
                }
            });
        }
        
        // Reset filters
        if (this.resetBtn) {
            this.resetBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetAllFilters();
            });
        }
        
        // Apply filters
        if (this.applyBtn) {
            this.applyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.applyFilters();
            });
        }
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (this.modal && this.modal.style.display === 'flex') {
                if (e.key === 'Escape') {
                    this.close();
                }
            }
        });
    }
    
    ensureMobileCompatibility() {
        // Prevent body scroll when modal is open on mobile
        if (this.modal) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        if (this.modal.style.display === 'flex') {
                            document.body.style.overflow = 'hidden';
                            document.body.style.position = 'fixed';
                            document.body.style.width = '100%';
                            // Prevent viewport zoom on iOS
                            const viewport = document.querySelector('meta[name="viewport"]');
                            if (viewport) {
                                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
                            }
                        } else {
                            document.body.style.overflow = '';
                            document.body.style.position = '';
                            document.body.style.width = '';
                            // Restore viewport settings
                            const viewport = document.querySelector('meta[name="viewport"]');
                            if (viewport) {
                                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0');
                            }
                        }
                    }
                });
            });
            
            observer.observe(this.modal, { attributes: true });
        }
    }
    
    open() {
        if (this.modal) {
            this.modal.style.display = 'flex';
            // Focus on first input for better UX
            const firstInput = this.modal.querySelector('input, select');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }
    
    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = '';
            document.body.style.position = '';
            document.body.style.width = '';
            // Restore viewport settings
            const viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0');
            }
        }
    }
    
    resetAllFilters() {
        // Clear all filter inputs
        const inputs = this.modal.querySelectorAll('input[type="text"], input[type="email"], input[type="date"]');
        const selects = this.modal.querySelectorAll('select');
        
        inputs.forEach(input => {
            input.value = '';
            // Trigger change event for any listeners
            input.dispatchEvent(new Event('change', { bubbles: true }));
        });
        
        selects.forEach(select => {
            select.selectedIndex = 0;
            // Trigger change event for any listeners
            select.dispatchEvent(new Event('change', { bubbles: true }));
        });
        
        // Show visual feedback
        this.showResetFeedback();
    }
    
    showResetFeedback() {
        if (this.resetBtn) {
            const originalText = this.resetBtn.textContent;
            this.resetBtn.textContent = '✓ Cleared';
            this.resetBtn.style.backgroundColor = '#28a745';
            
            setTimeout(() => {
                this.resetBtn.textContent = originalText;
                this.resetBtn.style.backgroundColor = '';
            }, 1500);
        }
    }
    
    applyFilters() {
        // This method should be overridden by specific implementations
        // or called with a callback function
        console.log('Apply filters called - implement specific logic');
        this.close();
    }
    
    // Utility method to get all filter values
    getFilterValues() {
        const values = {};
        const inputs = this.modal.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            if (input.id && input.id.startsWith('filter-')) {
                const key = input.id.replace('filter-', '');
                values[key] = input.value;
            }
        });
        
        return values;
    }
    
    // Utility method to set filter values
    setFilterValues(values) {
        Object.keys(values).forEach(key => {
            const input = this.modal.querySelector(`#filter-${key}`);
            if (input) {
                input.value = values[key];
            }
        });
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter modal if it exists
    if (document.getElementById('filter-modal')) {
        window.filterModal = new FilterModal();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FilterModal;
}
