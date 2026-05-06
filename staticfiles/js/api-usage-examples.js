/**
 * Examples of how to use ShikshaWave Global APIs
 * Copy and modify these examples for your pages
 */

// Example 1: Basic usage - Load sections for a specific class
function loadSectionsExample() {
    ShikshaWaveAPI.getSections(1)
        .then(data => {
            if (data.status === 'SUCCESS') {
                console.log('Sections:', data.sections);
                // Use the data as needed
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Example 2: Populate a dropdown with sections
function populateSectionsDropdown() {
    ShikshaWaveAPI.populateSections('mySectionSelect', 1, 'Choose Section');
}

// Example 3: Setup automatic class change handler
function setupClassChangeExample() {
    // This will automatically populate sections and subjects when class changes
    ShikshaWaveAPI.setupClassChangeHandler('classSelect', 'sectionSelect', 'subjectSelect');
}

// Example 4: Load all classes and populate dropdown
function loadAllClasses() {
    ShikshaWaveAPI.getClasses()
        .then(data => {
            ShikshaWaveAPI.populateDropdown('classSelect', data, 'Select Class');
        })
        .catch(error => {
            console.error('Error loading classes:', error);
        });
}

// Example 5: Load academic years
function loadAcademicYears() {
    ShikshaWaveAPI.getAcademicYears()
        .then(data => {
            ShikshaWaveAPI.populateDropdown('academicYearSelect', data, 'Select Academic Year');
        })
        .catch(error => {
            console.error('Error loading academic years:', error);
        });
}

// Example 6: Custom dropdown population
function customDropdownExample() {
    const customData = [
        {id: 1, name: 'Option 1'},
        {id: 2, name: 'Option 2'},
        {id: 3, name: 'Option 3'}
    ];
    
    ShikshaWaveAPI.populateDropdown('customSelect', customData, 'Choose Option');
}

// Example 7: Complete page setup
function setupCompletePage() {
    document.addEventListener('DOMContentLoaded', function() {
        // Load classes
        ShikshaWaveAPI.getClasses()
            .then(data => {
                ShikshaWaveAPI.populateDropdown('classSelect', data, 'Select Class');
            });
        
        // Load academic years
        ShikshaWaveAPI.getAcademicYears()
            .then(data => {
                ShikshaWaveAPI.populateDropdown('academicYearSelect', data, 'Select Academic Year');
            });
        
        // Setup class change handler
        ShikshaWaveAPI.setupClassChangeHandler('classSelect', 'sectionSelect', 'subjectSelect');
    });
}
