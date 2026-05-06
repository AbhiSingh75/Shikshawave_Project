/**
 * Global API Functions for ShikshaWave ERP
 * These functions can be used across all pages in the application
 */

// Global API Functions
window.ShikshaWaveAPI = {
    
    /**
     * Get Academic Years for the current school
     * @returns {Promise} Promise that resolves with academic years data
     */
    getAcademicYears: function() {
        return fetch('/api/academic-years/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error loading academic years:', error);
            throw error;
        });
    },

    /**
     * Get Classes for the current school
     * @returns {Promise} Promise that resolves with classes data
     */
    getClasses: function() {
        return fetch('/api/classes/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error loading classes:', error);
            throw error;
        });
    },

    /**
     * Get Sections for a specific class
     * @param {number|string} classId - The class ID
     * @returns {Promise} Promise that resolves with sections data
     */
    getSections: function(classId) {
        return fetch('/api/sections/?class_id=' + classId, {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error loading sections for class ' + classId + ':', error);
            throw error;
        });
    },

    /**
     * Get Subjects for a specific class
     * @param {number|string} classId - The class ID
     * @returns {Promise} Promise that resolves with subjects data
     */
    getSubjects: function(classId) {
        return fetch('/api/subjects-by-class/?class_id=' + classId, {
            method: 'GET',
            headers: {
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error loading subjects for class ' + classId + ':', error);
            throw error;
        });
    },

    /**
     * Get CSRF Token from the page
     * @returns {string} CSRF token
     */
    getCSRFToken: function() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    },

    /**
     * Populate a select dropdown with options
     * @param {string} selectId - The ID of the select element
     * @param {Array} data - Array of objects with id and name/text properties
     * @param {string} placeholder - Placeholder text for the first option
     * @param {string} valueField - Field name for the value (default: 'id')
     * @param {string} textField - Field name for the text (default: 'name')
     */
    populateDropdown: function(selectId, data, placeholder = 'Select Option', valueField = 'id', textField = 'name') {
        const select = document.getElementById(selectId);
        if (!select) {
            console.error('Select element with ID "' + selectId + '" not found');
            return;
        }

        // Clear existing options
        select.innerHTML = '<option value="">' + placeholder + '</option>';

        if (data && data.length > 0) {
            data.forEach(item => {
                const option = document.createElement('option');
                option.value = item[valueField];
                option.textContent = item[textField];
                select.appendChild(option);
            });
        }
    },

    /**
     * Populate sections dropdown for a specific class
     * @param {string} selectId - The ID of the sections select element
     * @param {number|string} classId - The class ID
     * @param {string} placeholder - Placeholder text
     */
    populateSections: function(selectId, classId, placeholder = 'Select Section') {
        if (!classId) {
            document.getElementById(selectId).innerHTML = '<option value="">' + placeholder + '</option>';
            return;
        }

        this.getSections(classId)
            .then(data => {
                if (data.status === 'SUCCESS' && data.sections && data.sections.length > 0) {
                    this.populateDropdown(selectId, data.sections, placeholder, 'id', 'name');
                } else {
                    document.getElementById(selectId).innerHTML = '<option value="">No sections found</option>';
                }
            })
            .catch(error => {
                document.getElementById(selectId).innerHTML = '<option value="">Error loading sections</option>';
            });
    },

    /**
     * Populate subjects dropdown for a specific class
     * @param {string} selectId - The ID of the subjects select element
     * @param {number|string} classId - The class ID
     * @param {string} placeholder - Placeholder text
     */
    populateSubjects: function(selectId, classId, placeholder = 'Select Subject') {
        if (!classId) {
            document.getElementById(selectId).innerHTML = '<option value="">' + placeholder + '</option>';
            return;
        }

        this.getSubjects(classId)
            .then(data => {
                if (data.status === 'SUCCESS' && data.subjects && data.subjects.length > 0) {
                    // Format subjects with name and code
                    const formattedSubjects = data.subjects.map(subject => ({
                        SubjectID: subject.SubjectID,
                        displayText: subject.SubjectName + ' (' + subject.SubjectCode + ')'
                    }));
                    this.populateDropdown(selectId, formattedSubjects, placeholder, 'SubjectID', 'displayText');
                } else {
                    document.getElementById(selectId).innerHTML = '<option value="">No subjects found</option>';
                }
            })
            .catch(error => {
                document.getElementById(selectId).innerHTML = '<option value="">Error loading subjects</option>';
            });
    },

    /**
     * Setup class change handler that automatically populates sections and subjects
     * @param {string} classSelectId - ID of the class select element
     * @param {string} sectionSelectId - ID of the section select element
     * @param {string} subjectSelectId - ID of the subject select element
     */
    setupClassChangeHandler: function(classSelectId, sectionSelectId, subjectSelectId) {
        const classSelect = document.getElementById(classSelectId);
        if (!classSelect) {
            console.error('Class select element with ID "' + classSelectId + '" not found');
            return;
        }

        classSelect.addEventListener('change', function() {
            const classId = this.value;
            
            // Clear sections and subjects
            if (sectionSelectId) {
                document.getElementById(sectionSelectId).innerHTML = '<option value="">Select Section</option>';
            }
            if (subjectSelectId) {
                document.getElementById(subjectSelectId).innerHTML = '<option value="">Select Subject</option>';
            }

            if (classId) {
                // Load sections and subjects
                if (sectionSelectId) {
                    ShikshaWaveAPI.populateSections(sectionSelectId, classId);
                }
                if (subjectSelectId) {
                    ShikshaWaveAPI.populateSubjects(subjectSelectId, classId);
                }
            }
        });
    }
};

// Make it available globally
window.ShikshaWaveAPI = window.ShikshaWaveAPI;
