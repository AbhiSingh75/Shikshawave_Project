// Student Bulk Upload Component
// Handles 3-step flow: Upload → Preview → Commit

class StudentBulkUpload {
    constructor() {
        this.currentStep = 1;
        this.importId = null;
        this.schoolId = null;
        this.validRows = 0;
        this.invalidRows = 0;
        this.totalRows = 0;
        this.selectedFile = null;
        this.expectedColumns = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadExpectedColumns();
    }

    setupEventListeners() {
        const fileInput = document.getElementById('studentFileInput');
        const uploadArea = document.getElementById('studentUploadArea');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        }
        
        if (uploadArea) {
            uploadArea.addEventListener('click', () => fileInput?.click());
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                if (e.dataTransfer.files.length > 0) {
                    this.handleFileSelect(e.dataTransfer.files[0]);
                }
            });
        }
    }

    async loadExpectedColumns() {
        try {
            const response = await fetch('/data-import/columns/Students/');
            const data = await response.json();
            if (data.success) {
                this.expectedColumns = data.columns;
                this.displayExpectedColumns(data.columns, data.required_columns);
            }
        } catch (error) {
            console.error('Error loading columns:', error);
        }
    }

    displayExpectedColumns(columns, requiredColumns) {
        const container = document.getElementById('expectedColumnsContainer');
        if (!container) return;

        const html = `
            <div class="columns-info">
                <h4><i class="fas fa-table"></i> Expected Excel Columns (${columns.length})</h4>
                <div class="columns-grid">
                    ${columns.map(col => `
                        <span class="column-badge ${requiredColumns.includes(col) ? 'required' : ''}">
                            ${col}${requiredColumns.includes(col) ? ' *' : ''}
                        </span>
                    `).join('')}
                </div>
                <p class="columns-note"><i class="fas fa-info-circle"></i> * = Required fields</p>
            </div>
        `;
        container.innerHTML = html;
    }

    handleFileSelect(file) {
        if (!file) return;

        if (!file.name.match(/\.(xlsx|xls|csv)$/i)) {
            this.showError('Please upload Excel (.xlsx, .xls) or CSV file');
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            this.showError('File size exceeds 10MB limit');
            return;
        }

        this.selectedFile = file;
        this.displayFileInfo(file);
        document.getElementById('uploadBtn')?.removeAttribute('disabled');
    }

    displayFileInfo(file) {
        const container = document.getElementById('fileInfoContainer');
        if (!container) return;

        const html = `
            <div class="file-info-card">
                <i class="fas fa-file-excel"></i>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${(file.size / 1024).toFixed(2)} KB</div>
                </div>
                <button class="remove-file-btn" onclick="studentUpload.removeFile()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        container.innerHTML = html;
        container.style.display = 'block';
    }

    removeFile() {
        this.selectedFile = null;
        document.getElementById('studentFileInput').value = '';
        document.getElementById('fileInfoContainer').style.display = 'none';
        document.getElementById('uploadBtn')?.setAttribute('disabled', 'disabled');
    }

    async uploadAndValidate() {
        if (!this.selectedFile) {
            this.showError('Please select a file');
            return;
        }

        const schoolSelect = document.getElementById('schoolSelect');
        this.schoolId = schoolSelect ? schoolSelect.value : null;

        if (!this.schoolId) {
            this.showError('Please select a school');
            return;
        }

        this.showLoading('Uploading and validating...');

        const formData = new FormData();
        formData.append('import_file', this.selectedFile);
        formData.append('import_type', 'Students');
        formData.append('school_id', this.schoolId);

        try {
            const response = await fetch('/data-import/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.importId = data.import_id;
                this.totalRows = data.total_rows;
                this.validRows = data.valid_rows;
                this.invalidRows = data.invalid_rows;
                
                this.hideLoading();
                this.showValidationResults(data);
                this.goToStep(2);
            } else {
                this.hideLoading();
                if (data.column_validation && !data.column_validation.valid) {
                    this.showColumnMismatchError(data.column_validation);
                } else {
                    this.showError(data.error || 'Upload failed');
                }
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    showColumnMismatchError(validation) {
        const html = `
            <div class="column-mismatch-error">
                <h3><i class="fas fa-exclamation-triangle"></i> Column Mismatch Detected</h3>
                ${validation.missing.length > 0 ? `
                    <div class="missing-columns">
                        <h4>Missing Required Columns:</h4>
                        <ul>${validation.missing.map(col => `<li>${col}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                ${validation.extra.length > 0 ? `
                    <div class="extra-columns">
                        <h4>Unexpected Columns:</h4>
                        <ul>${validation.extra.map(col => `<li>${col}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                <p>Please download the template and ensure your Excel file matches the expected structure.</p>
            </div>
        `;
        
        const container = document.getElementById('validationResultsContainer');
        if (container) {
            container.innerHTML = html;
            container.style.display = 'block';
        }
    }

    showValidationResults(data) {
        const html = `
            <div class="validation-summary">
                <h3><i class="fas fa-check-circle"></i> Validation Complete</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">${data.total_rows}</div>
                        <div class="stat-label">Total Rows</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-number">${data.valid_rows}</div>
                        <div class="stat-label">Valid Rows</div>
                    </div>
                    <div class="stat-card ${data.invalid_rows > 0 ? 'danger' : ''}">
                        <div class="stat-number">${data.invalid_rows}</div>
                        <div class="stat-label">Invalid Rows</div>
                    </div>
                </div>
                ${data.invalid_rows > 0 ? `
                    <div class="validation-warning">
                        <i class="fas fa-exclamation-circle"></i>
                        ${data.invalid_rows} rows have validation errors. You can review them in the preview step.
                    </div>
                ` : ''}
            </div>
        `;
        
        const container = document.getElementById('validationResultsContainer');
        if (container) {
            container.innerHTML = html;
            container.style.display = 'block';
        }
    }

    async loadPreview() {
        if (!this.importId) return;

        this.showLoading('Loading preview...');

        try {
            const response = await fetch(`/data-import/staging/preview/${this.importId}/`);
            const data = await response.json();

            if (data.success) {
                this.hideLoading();
                this.displayPreview(data);
            } else {
                this.hideLoading();
                this.showError(data.error || 'Failed to load preview');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    displayPreview(data) {
        const validTableHtml = this.generatePreviewTable(data.valid_rows, 'Valid Records');
        const invalidTableHtml = data.invalid_rows.length > 0 
            ? this.generateErrorTable(data.invalid_rows) 
            : '';

        const html = `
            <div class="preview-container">
                <div class="preview-summary">
                    <h3><i class="fas fa-eye"></i> Data Preview</h3>
                    <p>Showing up to 100 records. Total: ${data.total_count} (${data.valid_count} valid, ${data.invalid_count} invalid)</p>
                </div>
                
                ${validTableHtml}
                
                ${invalidTableHtml}
                
                ${data.invalid_count > 0 ? `
                    <div class="error-actions">
                        <button class="btn btn-warning" onclick="studentUpload.downloadErrors()">
                            <i class="fas fa-download"></i> Download Error Report
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        const container = document.getElementById('previewContainer');
        if (container) {
            container.innerHTML = html;
        }
    }

    generatePreviewTable(rows, title) {
        if (!rows || rows.length === 0) return '';

        const columns = Object.keys(rows[0]);
        
        return `
            <div class="preview-table-section">
                <h4>${title} (${rows.length})</h4>
                <div class="table-responsive">
                    <table class="preview-table">
                        <thead>
                            <tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>
                        </thead>
                        <tbody>
                            ${rows.map(row => `
                                <tr>${columns.map(col => `<td>${row[col] || ''}</td>`).join('')}</tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    generateErrorTable(rows) {
        if (!rows || rows.length === 0) return '';

        return `
            <div class="error-table-section">
                <h4 class="error-title"><i class="fas fa-exclamation-triangle"></i> Invalid Records (${rows.length})</h4>
                <div class="table-responsive">
                    <table class="error-table">
                        <thead>
                            <tr>
                                <th>Row</th>
                                <th>Name</th>
                                <th>Gender</th>
                                <th>Mobile</th>
                                <th>Errors</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rows.map(row => `
                                <tr>
                                    <td>${row.RowNumber}</td>
                                    <td>${row.FullName || '-'}</td>
                                    <td>${row.Gender || '-'}</td>
                                    <td>${row.ParentMobile || '-'}</td>
                                    <td class="error-messages">
                                        ${Array.isArray(row.ErrorMessages) 
                                            ? row.ErrorMessages.map(err => `<div class="error-msg">${err}</div>`).join('')
                                            : row.ErrorMessages || '-'}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    async commitImport() {
        if (!this.importId) return;

        if (this.invalidRows > 0) {
            if (!confirm(`There are ${this.invalidRows} invalid rows that will be skipped. Continue with importing ${this.validRows} valid rows?`)) {
                return;
            }
        } else {
            if (!confirm(`Import ${this.validRows} student records into the database?`)) {
                return;
            }
        }

        this.showLoading('Importing records...');

        try {
            const response = await fetch(`/data-import/execute/${this.importId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (data.success) {
                this.hideLoading();
                this.showCommitResults(data);
                this.goToStep(3);
            } else {
                this.hideLoading();
                this.showError(data.error || 'Import failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showError('Network error: ' + error.message);
        }
    }

    showCommitResults(data) {
        const html = `
            <div class="commit-results">
                <div class="success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>Import Completed Successfully!</h3>
                <div class="commit-stats">
                    <div class="commit-stat success">
                        <div class="commit-number">${data.success_count}</div>
                        <div class="commit-label">Records Imported</div>
                    </div>
                    ${data.failure_count > 0 ? `
                        <div class="commit-stat danger">
                            <div class="commit-number">${data.failure_count}</div>
                            <div class="commit-label">Records Failed</div>
                        </div>
                    ` : ''}
                </div>
                <p class="commit-message">${data.message}</p>
                <div class="commit-actions">
                    <button class="btn btn-primary" onclick="location.reload()">
                        <i class="fas fa-plus"></i> Import More Students
                    </button>
                    <a href="/students/" class="btn btn-secondary">
                        <i class="fas fa-list"></i> View Students
                    </a>
                </div>
            </div>
        `;

        const container = document.getElementById('commitResultsContainer');
        if (container) {
            container.innerHTML = html;
        }
    }

    async downloadErrors() {
        if (!this.importId) return;
        window.location.href = `/data-import/errors/${this.importId}/`;
    }

    goToStep(step) {
        this.currentStep = step;
        
        // Update step indicators
        for (let i = 1; i <= 3; i++) {
            const stepEl = document.getElementById(`step${i}`);
            if (stepEl) {
                stepEl.classList.remove('active', 'completed');
                if (i < step) stepEl.classList.add('completed');
                if (i === step) stepEl.classList.add('active');
            }
        }

        // Show/hide step content
        document.querySelectorAll('.step-content').forEach(el => el.style.display = 'none');
        const currentStepEl = document.getElementById(`stepContent${step}`);
        if (currentStepEl) currentStepEl.style.display = 'block';

        // Load data for step
        if (step === 2) {
            this.loadPreview();
        }
    }

    showLoading(message) {
        const loader = document.getElementById('loadingOverlay');
        if (loader) {
            loader.querySelector('.loading-text').textContent = message;
            loader.style.display = 'flex';
        }
    }

    hideLoading() {
        const loader = document.getElementById('loadingOverlay');
        if (loader) loader.style.display = 'none';
    }

    showError(message) {
        alert(message); // Replace with better UI notification
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Initialize on page load
let studentUpload;
document.addEventListener('DOMContentLoaded', () => {
    studentUpload = new StudentBulkUpload();
});
