// Student Grid Entry - Excel-like interface for bulk data entry
class StudentGridEntry {
    constructor() {
        this.rows = [];
        this.columns = [
            {field: 'FullName', header: 'Full Name*', width: 150, required: true},
            {field: 'Gender', header: 'Gender*', width: 100, required: true, type: 'select', options: ['Male', 'Female', 'Other']},
            {field: 'DateOfBirth', header: 'DOB*', width: 120, required: true, type: 'date'},
            {field: 'Age', header: 'Age', width: 60},
            {field: 'BloodGroup', header: 'Blood', width: 90, type: 'select', options: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']},
            {field: 'Category', header: 'Category', width: 100, type: 'select', options: ['General', 'SC', 'ST', 'OBC', 'EWS']},
            {field: 'Religion', header: 'Religion', width: 110, type: 'select', options: ['Hinduism', 'Islam', 'Christianity', 'Sikhism', 'Jainism', 'Buddhism', 'Others']},
            {field: 'Nationality', header: 'Nationality', width: 110, type: 'select', options: ['Indian', 'Nepali', 'Bhutani']},
            {field: 'StudentAadhaar', header: 'Aadhaar', width: 120},
            {field: 'MotherTongue', header: 'Mother Tongue', width: 100},
            {field: 'PresentAddress', header: 'Present Address', width: 200},
            {field: 'PermanentAddress', header: 'Permanent Address', width: 200},
            {field: 'Country', header: 'Country', width: 120},
            {field: 'State', header: 'State', width: 120},
            {field: 'District', header: 'District', width: 120},
            {field: 'ParentMobile', header: 'Parent Mobile*', width: 120, required: true},
            {field: 'AlternateNumber', header: 'Alt Mobile', width: 120},
            {field: 'Email', header: 'Email', width: 150},
            {field: 'FatherName', header: 'Father Name*', width: 150, required: true},
            {field: 'FatherOccupation', header: 'Father Occupation', width: 130},
            {field: 'FatherQualification', header: 'Father Qualification', width: 150},
            {field: 'FatherAadhaar', header: 'Father Aadhaar', width: 120},
            {field: 'FatherMobile', header: 'Father Mobile', width: 120},
            {field: 'MotherName', header: 'Mother Name', width: 150},
            {field: 'MotherOccupation', header: 'Mother Occupation', width: 130},
            {field: 'MotherQualification', header: 'Mother Qualification', width: 150},
            {field: 'MotherAadhaar', header: 'Mother Aadhaar', width: 120},
            {field: 'MotherMobile', header: 'Mother Mobile', width: 120},
            {field: 'GuardianName', header: 'Guardian Name', width: 150},
            {field: 'GuardianRelation', header: 'Guardian Relation', width: 120},
            {field: 'GuardianMobile', header: 'Guardian Mobile', width: 120},
            {field: 'LastSchool', header: 'Last School', width: 180},
            {field: 'LastClass', header: 'Last Class', width: 100},
            {field: 'TCNumber', header: 'TC Number', width: 120},
            {field: 'MediumOfInstruction', header: 'Medium', width: 100},
            {field: 'AdmissionClass', header: 'Class*', width: 80, required: true},
            {field: 'Section', header: 'Section*', width: 80, required: true},
            {field: 'Stream', header: 'Stream', width: 100},
            {field: 'ModeOfAdmission', header: 'Mode', width: 100},
            {field: 'AdmissionDate', header: 'Adm Date*', width: 120, required: true, type: 'date'}
        ];
        this.gridContainer = null;
        this.schoolId = null;
    }

    init(containerId, schoolId) {
        this.gridContainer = document.getElementById(containerId);
        this.schoolId = schoolId;
        this.addRows(10); // Start with 10 empty rows
        this.render();
    }

    addRows(count) {
        for (let i = 0; i < count; i++) {
            const row = {};
            this.columns.forEach(col => row[col.field] = '');
            this.rows.push(row);
        }
        this.render();
    }

    addSingleRow() {
        const row = {};
        this.columns.forEach(col => row[col.field] = '');
        this.rows.push(row);
        this.render();
    }

    deleteRow(idx) {
        if (this.rows.length <= 1) {
            alert('Cannot delete the last row');
            return;
        }
        if (confirm(`Delete row ${idx + 1}?`)) {
            this.rows.splice(idx, 1);
            this.render();
        }
    }

    render() {
        const html = `
            <div class="grid-toolbar">
                <button class="btn btn-sm btn-success" onclick="studentGrid.addSingleRow()">
                    <i class="fas fa-plus"></i> Add Row
                </button>
                <button class="btn btn-sm btn-secondary" onclick="studentGrid.addRows(5)">
                    <i class="fas fa-plus-circle"></i> Add 5 Rows
                </button>
                <button class="btn btn-sm btn-primary" onclick="studentGrid.validateAndSave()">
                    <i class="fas fa-check"></i> Validate & Save
                </button>
                <button class="btn btn-sm btn-danger" onclick="studentGrid.clearAll()">
                    <i class="fas fa-trash-alt"></i> Clear All
                </button>
                <span class="grid-info">Total Rows: ${this.rows.length}</span>
            </div>
            <div class="grid-wrapper">
                <table class="data-grid" id="studentDataGrid">
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            ${this.columns.map(col => `<th style="width: ${col.width}px;">${col.header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${this.rows.map((row, idx) => this.renderRow(row, idx)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        this.gridContainer.innerHTML = html;
        this.attachEvents();
    }

    renderRow(row, idx) {
        return `
            <tr data-row="${idx}">
                <td class="row-number">
                    ${idx + 1}
                    <button class="delete-row-btn" onclick="studentGrid.deleteRow(${idx})" title="Delete Row">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
                ${this.columns.map(col => this.renderCell(row, col, idx)).join('')}
            </tr>
        `;
    }

    renderCell(row, col, rowIdx) {
        const value = row[col.field] || '';
        const cellId = `cell_${rowIdx}_${col.field}`;
        
        if (col.type === 'select') {
            return `
                <td>
                    <select id="${cellId}" class="grid-input" data-row="${rowIdx}" data-field="${col.field}">
                        <option value="">-</option>
                        ${col.options.map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                    </select>
                </td>
            `;
        } else if (col.type === 'date') {
            return `<td><input type="date" id="${cellId}" class="grid-input" value="${value}" data-row="${rowIdx}" data-field="${col.field}"></td>`;
        } else {
            return `<td><input type="text" id="${cellId}" class="grid-input" value="${value}" data-row="${rowIdx}" data-field="${col.field}"></td>`;
        }
    }

    attachEvents() {
        document.querySelectorAll('.grid-input').forEach(input => {
            const field = input.dataset.field;
            
            // Format Aadhaar and Mobile on input
            if (['StudentAadhaar', 'FatherAadhaar', 'MotherAadhaar'].includes(field)) {
                input.addEventListener('input', (e) => {
                    let val = e.target.value.replace(/\D/g, '').slice(0, 12);
                    e.target.value = val;
                });
            } else if (['ParentMobile', 'AlternateNumber', 'FatherMobile', 'MotherMobile', 'GuardianMobile'].includes(field)) {
                input.addEventListener('input', (e) => {
                    let val = e.target.value.replace(/\D/g, '').slice(0, 10);
                    e.target.value = val;
                });
            }
            
            input.addEventListener('change', (e) => {
                const row = parseInt(e.target.dataset.row);
                const field = e.target.dataset.field;
                this.rows[row][field] = e.target.value;
            });
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.moveToNextCell(e.target);
                }
            });
        });
    }

    moveToNextCell(currentInput) {
        const allInputs = Array.from(document.querySelectorAll('.grid-input'));
        const currentIndex = allInputs.indexOf(currentInput);
        if (currentIndex < allInputs.length - 1) {
            allInputs[currentIndex + 1].focus();
        }
    }

    clearAll() {
        if (confirm('Clear all entered data?')) {
            this.rows = [];
            this.addRows(10);
            this.render();
        }
    }

    async validateAndSave() {
        const filledRows = this.rows.filter(row => 
            Object.values(row).some(val => val && val.trim() !== '')
        );

        if (filledRows.length === 0) {
            alert('Please enter at least one student record');
            return;
        }

        // Validate required fields and formats
        const errors = [];
        const emailRegex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/i;
        
        filledRows.forEach((row, idx) => {
            const rowNum = idx + 1;
            
            // Required fields
            this.columns.filter(col => col.required).forEach(col => {
                if (!row[col.field] || row[col.field].trim() === '') {
                    errors.push(`Row ${rowNum}: ${col.header} is required`);
                }
            });
            
            // Aadhaar validation (12 digits)
            ['StudentAadhaar', 'FatherAadhaar', 'MotherAadhaar'].forEach(field => {
                if (row[field] && row[field].replace(/\D/g, '').length !== 12) {
                    errors.push(`Row ${rowNum}: ${field} must be 12 digits`);
                }
            });
            
            // Mobile validation (10 digits)
            ['ParentMobile', 'AlternateNumber', 'FatherMobile', 'MotherMobile', 'GuardianMobile'].forEach(field => {
                if (row[field] && row[field].replace(/\D/g, '').length !== 10) {
                    errors.push(`Row ${rowNum}: ${field} must be 10 digits`);
                }
            });
            
            // Email validation
            if (row['Email'] && !emailRegex.test(row['Email'])) {
                errors.push(`Row ${rowNum}: Invalid email format`);
            }
        });

        if (errors.length > 0) {
            alert('Validation Errors:\n' + errors.slice(0, 10).join('\n') + (errors.length > 10 ? '\n...and more' : ''));
            return;
        }

        // Show loading
        this.showLoading('Saving student records...');

        try {
            const response = await fetch('/data-import/grid/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    school_id: this.schoolId,
                    students: filledRows
                })
            });

            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                alert(`Success! ${data.success_count} students saved.\n${data.failure_count > 0 ? data.failure_count + ' failed.' : ''}`);
                if (data.failure_count === 0) {
                    this.clearAll();
                }
            } else {
                alert('Error: ' + data.error);
            }
        } catch (error) {
            this.hideLoading();
            alert('Network error: ' + error.message);
        }
    }

    showLoading(message) {
        const overlay = document.createElement('div');
        overlay.id = 'gridLoadingOverlay';
        overlay.innerHTML = `
            <div class="loading-overlay" style="display: flex;">
                <div class="spinner"></div>
                <div class="loading-text">${message}</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    hideLoading() {
        const overlay = document.getElementById('gridLoadingOverlay');
        if (overlay) overlay.remove();
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!token) {
            const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
            return cookieValue || '';
        }
        return token;
    }
}

let studentGrid;
