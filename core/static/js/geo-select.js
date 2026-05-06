class GeographySelector {
    constructor(options = {}) {
        this.defaultOptions = {
            countrySelect: '#country',
            stateSelect: '#state',
            districtSelect: '#district',
            apiBaseUrl: '/api/geo/',
            onCountryChange: null,
            onStateChange: null,
            onDistrictChange: null,
            showLoading: true,
            loadingText: 'Loading...'
        };
        
        this.options = { ...this.defaultOptions, ...options };
        this.init();
    }
    
    init() {
        this.countrySelect = document.querySelector(this.options.countrySelect);
        this.stateSelect = document.querySelector(this.options.stateSelect);
        this.districtSelect = document.querySelector(this.options.districtSelect);
        
        if (this.countrySelect) {
            this.countrySelect.addEventListener('change', () => this.fetchStates());
        }
        
        if (this.stateSelect) {
            this.stateSelect.addEventListener('change', () => this.fetchDistricts());
        }
        
        // Load countries if select exists and is empty
        if (this.countrySelect && this.countrySelect.options.length <= 1) {
            this.fetchCountries();
        }
    }
    
    // Utility to get CSRF token
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    async fetchCountries() {
        if (this.options.showLoading && this.countrySelect) {
            this.showLoading(this.countrySelect);
        }
        
        try {
            const response = await fetch(`${this.options.apiBaseUrl}countries/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            
            const countries = await response.json();
            this.populateSelect(this.countrySelect, countries);
            this.countrySelect.disabled = false;
            
            if (this.options.onCountryChange) {
                this.options.onCountryChange(countries);
            }
        } catch (error) {
            console.error('Error fetching countries:', error);
            this.showError(this.countrySelect, 'Failed to load countries');
        }
    }
    
    async fetchStates() {
        const countryId = this.countrySelect?.value;
        if (!countryId || !this.stateSelect) return;
        
        if (this.options.showLoading) {
            this.showLoading(this.stateSelect);
        }
        
        // Reset districts when country changes
        if (this.districtSelect) {
            this.resetSelect(this.districtSelect);
            this.districtSelect.disabled = true;
        }
        
        try {
            const response = await fetch(`${this.options.apiBaseUrl}states/?country_id=${countryId}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            
            const states = await response.json();
            this.populateSelect(this.stateSelect, states);
            this.stateSelect.disabled = states.length === 0;
            
            if (this.options.onStateChange) {
                this.options.onStateChange(states);
            }
        } catch (error) {
            console.error('Error fetching states:', error);
            this.showError(this.stateSelect, 'Failed to load states');
            this.stateSelect.disabled = true;
        }
    }
    
    async fetchDistricts() {
        const stateId = this.stateSelect?.value;
        if (!stateId || !this.districtSelect) return;
        
        if (this.options.showLoading) {
            this.showLoading(this.districtSelect);
        }
        
        try {
            const response = await fetch(`${this.options.apiBaseUrl}districts/?state_id=${stateId}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            
            const districts = await response.json();
            this.populateSelect(this.districtSelect, districts);
            this.districtSelect.disabled = districts.length === 0;
            
            if (this.options.onDistrictChange) {
                this.options.onDistrictChange(districts);
            }
        } catch (error) {
            console.error('Error fetching districts:', error);
            this.showError(this.districtSelect, 'Failed to load districts');
            this.districtSelect.disabled = true;
        }
    }
    
    populateSelect(selectElement, data) {
        if (!selectElement) return;
        
        // Keep the first option (Select...)
        const firstOption = selectElement.options[0];
        selectElement.innerHTML = firstOption ? firstOption.outerHTML : '<option value="">Select...</option>';
        
        if (data && data.length > 0) {
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = item.name;
                selectElement.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No options available';
            selectElement.appendChild(option);
        }
    }
    
    resetSelect(selectElement) {
        if (!selectElement) return;
        const firstOption = selectElement.options[0];
        selectElement.innerHTML = firstOption ? firstOption.outerHTML : '<option value="">Select...</option>';
        selectElement.disabled = true;
    }
    
    showLoading(selectElement) {
        if (!selectElement) return;
        
        const currentValue = selectElement.value;
        selectElement.innerHTML = `<option value="">${this.options.loadingText}</option>`;
        selectElement.disabled = true;
        
        // Restore after a short delay if the fetch fails
        setTimeout(() => {
            if (selectElement.options.length === 1 && selectElement.options[0].value === '') {
                selectElement.disabled = false;
                this.resetSelect(selectElement);
                selectElement.value = currentValue;
            }
        }, 5000);
    }
    
    showError(selectElement, message) {
        if (!selectElement) return;
        
        selectElement.innerHTML = `<option value="">${message}</option>`;
        selectElement.disabled = false;
    }
    
    // Public methods to manually trigger fetches
    loadCountries() { this.fetchCountries(); }
    loadStates() { this.fetchStates(); }
    loadDistricts() { this.fetchDistricts(); }
    
    // Method to set values programmatically
    setValues(countryId = null, stateId = null, districtId = null) {
        if (countryId && this.countrySelect) {
            this.countrySelect.value = countryId;
            this.fetchStates().then(() => {
                if (stateId && this.stateSelect) {
                    this.stateSelect.value = stateId;
                    this.fetchDistricts().then(() => {
                        if (districtId && this.districtSelect) {
                            this.districtSelect.value = districtId;
                        }
                    });
                }
            });
        }
    }
}

// Initialize automatically if data-geo-select attribute is present
document.addEventListener('DOMContentLoaded', function() {
    const geoSelectElements = document.querySelectorAll('[data-geo-select]');
    geoSelectElements.forEach(element => {
        const options = JSON.parse(element.getAttribute('data-geo-options') || '{}');
        new GeographySelector(options);
    });
});