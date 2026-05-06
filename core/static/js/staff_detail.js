/**
 * Staff Detail Page Logic
 * Handles inline editing, subject specialization, document uploads, and modals.
 */

// Global state for document preview
var documentDataStore = {};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initial salary view update
    if (typeof updateSalarySummaryView === 'function') {
        updateSalarySummaryView();
    }

    // Initial subject tags view
    if (typeof initSubjectViewTags === 'function') {
        initSubjectViewTags();
    }

    // Initialize document data store from DOM
    initDocumentStore();

    // Set up geo location listeners if contact edit is open
    setupGeoListeners();
});

function initDocumentStore() {
    document.querySelectorAll('#document-data-store .doc-data-item').forEach(item => {
        documentDataStore[item.dataset.id] = {
            data: item.dataset.content,
            fileName: item.dataset.name,
            mimeType: item.dataset.mime
        };
    });
}

function setupGeoListeners() {
    const countrySelect = document.getElementById('countrySelect');
    const stateSelect = document.getElementById('stateSelect');

    if (countrySelect) {
        countrySelect.addEventListener('change', function () {
            const districtSelect = document.getElementById('districtSelect');
            stateSelect.innerHTML = '<option value="">Select State</option>';
            districtSelect.innerHTML = '<option value="">Select District</option>';
            stateSelect.disabled = true;
            districtSelect.disabled = true;

            if (this.value) {
                loadStates(this.value);
            }
        });
    }

    if (stateSelect) {
        stateSelect.addEventListener('change', function () {
            const districtSelect = document.getElementById('districtSelect');
            districtSelect.innerHTML = '<option value="">Select District</option>';
            districtSelect.disabled = true;

            if (this.value) {
                loadDistricts(this.value);
            }
        });
    }
}

/**
 * --- COMMON UI UTILITIES ---
 */

function toggleEdit(section) {
    const container = document.getElementById(section + '-section');
    if (!container) return;

    const viewMode = container.querySelector('.view-mode');
    const editMode = container.querySelector('.edit-mode');

    if (editMode.style.display === 'none') {
        viewMode.style.display = 'none';
        editMode.style.display = 'block';

        if (section === 'contact') {
            loadCountries();
        } else if (section === 'salary') {
            calculateSalaryTotal();
            document.querySelectorAll('.salary-amount').forEach(input => {
                input.addEventListener('input', calculateSalaryTotal);
            });
        } else if (section === 'subjects') {
            loadSubjects();
        }
    } else {
        viewMode.style.display = 'block';
        editMode.style.display = 'none';
        if (section === 'salary') {
            updateSalarySummaryView();
        } else if (section === 'subjects') {
            refreshViewTags();
        }
    }
}

function updateView(section, data) {
    const container = document.getElementById(section + '-section');
    const viewMode = container.querySelector('.view-mode');

    for (const [key, value] of Object.entries(data)) {
        const cell = viewMode.querySelector(`td[data-field="${key}"]`);
        if (cell) {
            if (key === 'DateOfBirth' || key === 'DateOfJoining') {
                if (value) {
                    const date = new Date(value);
                    cell.textContent = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                }
            } else {
                cell.textContent = value || 'N/A';
            }
        }
    }
}

function showToast(message, type = 'success') {
    // Check if global showNotification exists
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) scale(0.9);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 30px 40px;
        background: var(--card-bg, #fff);
        border: 1px solid var(--border-color, #ddd);
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        z-index: 10001;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        min-width: 320px;
        max-width: 90%;
    `;

    const icon = type === 'success' ? 'check-circle' : 'exclamation-circle';
    const iconColor = type === 'success' ? '#10b981' : '#ef4444';

    toast.innerHTML = `
        <i class="fas fa-${icon}" style="font-size: 3rem; margin-bottom: 16px; color: ${iconColor};"></i>
        <span style="font-size: 1.1rem; font-weight: 500; color: var(--text-color, #333); line-height: 1.5;">${message}</span>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.visibility = 'visible';
        toast.style.transform = 'translate(-50%, -50%) scale(1)';
    }, 10);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.visibility = 'hidden';
        toast.style.transform = 'translate(-50%, -50%) scale(0.9)';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

/**
 * --- PERSONAL INFORMATION ---
 */

async function savePersonal(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = {};

    for (const [key, value] of formData.entries()) {
        if (value && value.trim() !== '') {
            data[key] = value;
        }
    }

    try {
        const response = await fetch(window.urls.updatePersonal, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.config.csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast(result.message, 'success');
            updateView('personal', data);
            toggleEdit('personal');
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Error updating information', 'error');
    }
}

/**
 * --- CONTACT INFORMATION ---
 */

async function saveContact(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = {};

    const countrySelect = document.getElementById('countrySelect');
    const stateSelect = document.getElementById('stateSelect');
    const districtSelect = document.getElementById('districtSelect');

    for (const [key, value] of formData.entries()) {
        if (value && value.trim() !== '') {
            if (key === 'Country' && countrySelect && countrySelect.selectedIndex > 0) {
                data[key] = countrySelect.options[countrySelect.selectedIndex].text;
            } else if (key === 'State' && stateSelect && stateSelect.selectedIndex > 0) {
                data[key] = stateSelect.options[stateSelect.selectedIndex].text;
            } else if (key === 'District' && districtSelect && districtSelect.selectedIndex > 0) {
                data[key] = districtSelect.options[districtSelect.selectedIndex].text;
            } else {
                data[key] = value;
            }
        }
    }

    try {
        const response = await fetch(window.urls.updateContact, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.config.csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.status === 'success') {
            showToast(result.message, 'success');
            updateView('contact', data);
            toggleEdit('contact');
        } else {
            showToast(result.message, 'error');
        }
    } catch (error) {
        showToast('Error updating information', 'error');
    }
}

async function loadCountries() {
    try {
        const response = await fetch('/api/geo/countries/');
        const countries = await response.json();
        const countrySelect = document.getElementById('countrySelect');

        countrySelect.innerHTML = '<option value="">Select Country</option>';
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.id;
            option.textContent = country.name;
            countrySelect.appendChild(option);
        });

        const currentCountry = window.staff.Country;
        if (currentCountry) {
            const matchedOption = Array.from(countrySelect.options).find(opt => opt.textContent === currentCountry);
            if (matchedOption) {
                countrySelect.value = matchedOption.value;
                await loadStates(matchedOption.value);
            }
        }
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

async function loadStates(countryId) {
    try {
        const response = await fetch(`/api/geo/states/?country_id=${countryId}`);
        const states = await response.json();
        const stateSelect = document.getElementById('stateSelect');

        stateSelect.innerHTML = '<option value="">Select State</option>';
        stateSelect.disabled = false;

        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state.id;
            option.textContent = state.name;
            stateSelect.appendChild(option);
        });

        const currentState = window.staff.State;
        if (currentState) {
            const matchedOption = Array.from(stateSelect.options).find(opt => opt.textContent === currentState);
            if (matchedOption) {
                stateSelect.value = matchedOption.value;
                await loadDistricts(matchedOption.value);
            }
        }
    } catch (error) {
        console.error('Error loading states:', error);
    }
}

async function loadDistricts(stateId) {
    try {
        const response = await fetch(`/api/geo/districts/?state_id=${stateId}`);
        const districts = await response.json();
        const districtSelect = document.getElementById('districtSelect');

        districtSelect.innerHTML = '<option value="">Select District</option>';
        districtSelect.disabled = false;
        districts.forEach(district => {
            const option = document.createElement('option');
            option.value = district.id;
            option.textContent = district.name;
            districtSelect.appendChild(option);
        });

        const currentDistrict = window.staff.District;
        if (currentDistrict) {
            const matchedOption = Array.from(districtSelect.options).find(opt => opt.textContent === currentDistrict);
            if (matchedOption) {
                districtSelect.value = matchedOption.value;
            }
        }
    } catch (error) {
        console.error('Error loading districts:', error);
    }
}

/**
 * --- SUBJECT SPECIALIZATION ---
 */

let allSubjects = [];

function initSubjectViewTags() {
    const container = document.getElementById('subject-tags-view');
    if (!container) return;
    const raw = container.dataset.subjects || '';
    if (!raw.trim()) {
        container.innerHTML = '<span style="color:var(--text-muted,#888);">No subjects assigned</span>';
        return;
    }
    const subjects = raw.split(',').map(s => s.trim()).filter(Boolean);
    container.innerHTML = subjects.map(
        s => '<span class="subject-tag-view">' + s + '</span>'
    ).join('');
}

function toggleSubjectEdit() {
    var viewMode = document.getElementById('subject-view-mode');
    var editMode = document.getElementById('subject-edit-mode');
    var btn = document.getElementById('subject-edit-btn');
    if (editMode.style.display === 'none') {
        editMode.style.display = 'block';
        viewMode.style.display = 'none';
        btn.innerHTML = '<i class="fas fa-times"></i>';
        loadSubjects();
    } else {
        editMode.style.display = 'none';
        viewMode.style.display = 'block';
        btn.innerHTML = '<i class="fas fa-pencil-alt"></i>';
        refreshViewTags();
    }
}

function loadSubjects() {
    fetch(window.urls.getSubjects)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status !== 'success') { showToast('Failed to load subjects', 'error'); return; }
            allSubjects = data.subjects;
            renderEditTags();
            renderAddDropdown();
        })
        .catch(function () { showToast('Network error loading subjects', 'error'); });
}

function renderEditTags() {
    var container = document.getElementById('subject-tags-edit');
    var assigned = allSubjects.filter(function (s) { return s.assigned; });
    container.innerHTML = '';
    if (assigned.length === 0) {
        container.innerHTML = '<span style="color:var(--text-muted,#888);font-size:13px;">No subjects assigned yet</span>';
    } else {
        assigned.forEach(function (s) {
            var tag = document.createElement('span');
            tag.className = 'subject-tag-edit';
            tag.dataset.id = s.id;
            tag.innerHTML = s.name + ' <button class="remove-btn" onclick="removeSubject(' + s.id + ')" title="Remove"><i class="fas fa-times" style="font-size:8px;"></i></button>';
            container.appendChild(tag);
        });
    }
}

function renderAddDropdown() {
    var sel = document.getElementById('subject-add-select');
    var unassigned = allSubjects.filter(function (s) { return !s.assigned; });
    sel.innerHTML = '<option value="">-- Select subject to add --</option>';
    unassigned.forEach(function (s) {
        var opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.name;
        sel.appendChild(opt);
    });
}

function addSubject() {
    var sel = document.getElementById('subject-add-select');
    var subjectId = parseInt(sel.value);
    if (!subjectId) { showToast('Please select a subject', 'warning'); return; }
    subjectAction('add', subjectId);
}

function removeSubject(subjectId) {
    subjectAction('delete', subjectId);
}

function subjectAction(action, subjectId) {
    fetch(window.urls.updateSubjects, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.config.csrfToken },
        body: JSON.stringify({ action: action, subject_id: subjectId })
    })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.status === 'success') {
                var s = allSubjects.find(function (x) { return x.id === subjectId; });
                if (s) s.assigned = (action === 'add');
                renderEditTags();
                renderAddDropdown();
                refreshViewTags();
                showToast(action === 'add' ? 'Subject added' : 'Subject removed', 'success');
            } else {
                showToast(data.message || 'Error updating subjects', 'error');
            }
        })
        .catch(function () { showToast('Network error', 'error'); });
}

function refreshViewTags() {
    var container = document.getElementById('subject-tags-view');
    var assigned = allSubjects.filter(function (s) { return s.assigned; });
    if (assigned.length === 0) {
        container.innerHTML = '<span style="color:var(--text-muted,#888);">No subjects assigned</span>';
    } else {
        container.innerHTML = assigned.map(function (s) {
            return '<span class="subject-tag-view">' + s.name + '</span>';
        }).join('');
    }
}

/**
 * --- SALARY MANAGEMENT ---
 */

function calculateSalaryTotal() {
    let totalEarnings = 0;
    let totalDeductions = 0;

    document.querySelectorAll('.edit-mode .sw-salary-item').forEach(item => {
        const input = item.querySelector('.salary-amount');
        if (!input) return;
        const amount = parseFloat(input.value) || 0;

        if (item.classList.contains('deduction')) {
            totalDeductions += amount;
        } else {
            totalEarnings += amount;
        }
    });

    const netSalary = totalEarnings - totalDeductions;

    const earningsElem = document.getElementById('totalEarningsEdit');
    const deductionsElem = document.getElementById('totalDeductionsEdit');
    const netElem = document.getElementById('netSalaryEdit');

    if (earningsElem) earningsElem.textContent = `₹${totalEarnings.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (deductionsElem) deductionsElem.textContent = `₹${totalDeductions.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (netElem) netElem.textContent = `₹${netSalary.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

function updateSalarySummaryView() {
    let totalEarnings = 0;
    let totalDeductions = 0;

    document.querySelectorAll('.view-mode .sw-info-item').forEach(item => {
        const display = item.querySelector('.value.currency');
        if (!display) return;
        const amountText = display.textContent.replace('₹', '').replace(/,/g, '');
        const amount = parseFloat(amountText) || 0;

        if (item.classList.contains('deduction')) {
            totalDeductions += amount;
        } else {
            totalEarnings += amount;
        }
    });

    const netSalary = totalEarnings - totalDeductions;

    const tE = document.getElementById('totalEarningsView');
    const tD = document.getElementById('totalDeductionsView');
    const nS = document.getElementById('netSalaryView');

    if (tE) tE.textContent = `₹${totalEarnings.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (tD) tD.textContent = `₹${totalDeductions.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (nS) nS.textContent = `₹${netSalary.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
}

async function saveSalary(event) {
    event.preventDefault();
    const form = event.target;
    const salary_breakup = [];

    form.querySelectorAll('.sw-salary-item[data-component-id]').forEach(row => {
        const componentId = row.getAttribute('data-component-id');
        const amountInput = row.querySelector('input[name="amount_' + componentId + '"]');
        if (amountInput) {
            const amount = parseFloat(amountInput.value) || 0;
            salary_breakup.push({
                ComponentID: parseInt(componentId),
                Amount: amount
            });
        }
    });

    if (salary_breakup.length === 0) {
        showToast('No salary components found to update', 'warning');
        return;
    }

    try {
        const response = await fetch(window.urls.updateSalary, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.config.csrfToken
            },
            body: JSON.stringify({ salary_breakup })
        });

        const result = await response.json();
        if (result.status === 'success') {
            showToast(result.message, 'success');

            // Update the view mode amounts
            salary_breakup.forEach(item => {
                const viewItem = document.querySelector('.view-mode .sw-info-item[data-component-id="' + item.ComponentID + '"]');
                if (viewItem) {
                    const display = viewItem.querySelector('.value.currency');
                    if (display) {
                        display.textContent = '₹' + item.Amount.toLocaleString('en-IN', { minimumFractionDigits: 2 });
                    }
                }
            });

            updateSalarySummaryView();
            toggleEdit('salary');
        } else {
            showToast(result.message || 'Error updating salary', 'error');
        }
    } catch (error) {
        console.error('Salary upate error:', error);
        showToast('Error updating salary', 'error');
    }
}

/**
 * --- SALARY HISTORY MODAL ---
 */

function openSalaryModal(employeeCode) {
    const currentYear = new Date().getFullYear();
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    fetchSalaryData(currentYear);
    populateYearFilter(currentYear);
}

function populateYearFilter(currentYear) {
    const select = document.getElementById('salaryYearFilter');
    if (!select) return;
    let options = '';
    for (let i = 0; i < 10; i++) {
        const year = currentYear - i;
        options += `<option value="${year}">${year}</option>`;
    }
    options += '<option value="custom">Other Year...</option>';
    select.innerHTML = options;
}

function filterSalaryByYear() {
    const select = document.getElementById('salaryYearFilter');
    const input = document.getElementById('customYearInput');
    const value = select.value;

    if (value === 'custom') {
        select.style.display = 'none';
        input.style.display = 'block';
        input.focus();
        input.onchange = function () {
            const yearNum = parseInt(this.value);
            if (yearNum >= 2000 && yearNum <= 2100) {
                const exists = Array.from(select.options).find(opt => opt.value == yearNum);
                if (!exists) {
                    const newOption = document.createElement('option');
                    newOption.value = yearNum;
                    newOption.textContent = yearNum;
                    select.insertBefore(newOption, select.lastChild);
                }
                select.value = yearNum;
                select.style.display = 'block';
                input.style.display = 'none';
                fetchSalaryData(yearNum);
            } else {
                showToast('Year must be between 2000 and 2100', 'error');
                this.value = '';
            }
        };
        input.onblur = function () {
            if (!this.value) {
                select.style.display = 'block';
                input.style.display = 'none';
                select.value = new Date().getFullYear();
            }
        };
    } else {
        fetchSalaryData(value);
    }
}

function fetchSalaryData(year) {
    const employeeCode = window.staff.EmployeeCode;
    const schoolId = window.staff.SchoolID;

    fetch(`/salary/list/?employee_code=${employeeCode}&year=${year}&school_id=${schoolId}`)
        .then(r => r.json())
        .then(data => {
            if (data.status === 'SUCCESS') {
                displaySalaryData(data.salaries);
            } else {
                showToast('Error loading salary data: ' + (data.message || 'Unknown error'), 'error');
            }
        })
        .catch(err => {
            console.error('Fetch error:', err);
            showToast('Error loading salary data', 'error');
        });
}

function displaySalaryData(salaries) {
    const tbody = document.getElementById('salaryTableBody');
    if (!tbody) return;

    if (!salaries || salaries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 40px;">No salary records found</td></tr>';
        return;
    }

    tbody.innerHTML = salaries.map((sal, idx) => `
        <tr>
            <td>${idx + 1}</td>
            <td style="text-align: center;">
                ${sal.payment_status === 'Paid' ? `
                    <div style="display: flex; justify-content: center; gap: 8px;">
                        <button class="action-btn download-btn" 
                            onclick="downloadSalarySlip('${sal.encrypted_payment_id}', '${sal.salary_reference_id}')"
                            title="View/Download Slip">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn resend-btn" onclick="resendSalarySlip('${sal.encrypted_payment_id}')" title="Send Email">
                            <i class="fas fa-envelope"></i>
                        </button>
                    </div>
                ` : '-'}
            </td>
            <td style="text-align: center;">${sal.salary_month}</td>
            <td><strong class="salary-ref-id">${sal.salary_reference_id || '-'}</strong></td>
            <td style="text-align: right;">₹${parseFloat(sal.gross_salary || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td style="text-align: right;">₹${parseFloat(sal.deductions || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td style="text-align: right;"><strong>₹${parseFloat(sal.net_salary || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong></td>
            <td style="text-align: center;"><span style="color: ${sal.payment_status === 'Paid' ? 'var(--success-color, #10b981)' : 'var(--warning-color, #f59e0b)'}; font-weight: 600;">${sal.payment_status}</span></td>
            <td>${sal.payment_date || '-'}</td>
            <td style="text-align: center;">${sal.payment_mode || '-'}</td>
        </tr>
    `).join('');
}

async function resendSalarySlip(encryptedPaymentId) {
    if (!confirm('Are you sure you want to resend this salary slip via email?')) {
        return;
    }

    try {
        const response = await fetch(`/salary/slip/${encryptedPaymentId}/resend/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.config.csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        const result = await response.json();
        if (result.status === 'SUCCESS' || result.status === 'success') {
            showToast(result.message, 'success');
        } else {
            showToast(result.message || 'Error resending salary slip', 'error');
        }
    } catch (error) {
        console.error('Resend salary slip error:', error);
        showToast('Error resending salary slip', 'error');
    }
}

function closeSalaryModal() {
    const modal = document.getElementById('salaryModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

/**
 * --- DOCUMENT MANAGEMENT ---
 */

function viewDocument(docId) {
    const docInfo = documentDataStore[docId];
    if (!docInfo) {
        alert('Document data not found');
        return;
    }

    const modal = document.getElementById('documentModal');
    const content = document.getElementById('docContent');
    const title = document.getElementById('docTitle');

    title.innerHTML = '<i class="fas fa-file"></i> ' + docInfo.fileName;

    if (docInfo.mimeType.includes('image') || docInfo.fileName.match(/\.(jpg|jpeg|png|gif)$/i)) {
        content.innerHTML = '<img src="data:image/jpeg;base64,' + docInfo.data + '" alt="' + docInfo.fileName + '" />';
    } else if (docInfo.mimeType.includes('pdf') || docInfo.fileName.endsWith('.pdf')) {
        content.innerHTML = '<embed src="data:application/pdf;base64,' + docInfo.data + '" type="application/pdf" />';
    } else {
        content.innerHTML = `<div style="text-align: center; padding: 40px;">
            <i class="fas fa-file-download" style="font-size: 48px; color: var(--primary-color); margin-bottom: 20px;"></i>
            <p style="color: var(--text-light); margin-bottom: 20px;">Cannot preview this file type.</p>
            <a href="data:${docInfo.mimeType};base64,${docInfo.data}" download="${docInfo.fileName}" class="btn btn-primary">
                <i class="fas fa-download"></i> Download File
            </a>
        </div>`;
    }

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeDocumentModal() {
    const modal = document.getElementById('documentModal');
    const content = document.getElementById('docContent');
    if (modal) modal.classList.remove('show');
    if (content) content.innerHTML = '';
    document.body.style.overflow = '';
}

// Helper to close any open modal
function closeAllModals() {
    closeSalaryModal();
    closeDocumentModal();
    closeTimetableModal();
}

function handleDocumentUpload(input, docType) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('documentType', docType);
    formData.append('documentFile', file);
    formData.append('csrfmiddlewaretoken', window.config.csrfToken);

    fetch(window.urls.updateDocument, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.config.csrfToken
        }
    })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                showToast(result.message, 'success');
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast(result.message, 'error');
                input.value = '';
            }
        })
        .catch(error => {
            console.error('Document upload error:', error);
            showToast('Error uploading document', 'error');
            input.value = '';
        });
}

let docRowCount = 0;
function addDocumentRow() {
    docRowCount++;
    const container = document.querySelector('.sw-documents-grid');
    if (!container) return;

    const card = document.createElement('div');
    card.className = 'sw-document-modern-card';
    card.innerHTML = `
        <div class="doc-icon-wrapper">
            <i class="fas fa-file-upload"></i>
        </div>
        <div class="doc-info">
            <select class="form-control" id="docType${docRowCount}" onchange="enableUpload(${docRowCount})" style="margin-bottom: 5px; font-size: 0.85rem; padding: 4px 8px;">
                <option value="">Select Document Type</option>
                <option value="PAN Card">PAN Card</option>
                <option value="Aadhaar Card">Aadhaar Card</option>
                <option value="Passport">Passport</option>
                <option value="Driving License">Driving License</option>
                <option value="Voter ID">Voter ID</option>
                <option value="Bank Passbook">Bank Passbook</option>
                <option value="Salary Slip">Salary Slip</option>
                <option value="Experience Certificate">Experience Certificate</option>
                <option value="Education Certificate">Education Certificate</option>
                <option value="Other">Other</option>
            </select>
            <div class="doc-filename" id="docName${docRowCount}">No file selected</div>
        </div>
        <div class="doc-actions">
            <input type="file" id="docFile${docRowCount}" accept=".pdf,.jpg,.jpeg,.png" style="display: none;" disabled>
            <button type="button" class="action-btn upload" id="btnUpload${docRowCount}" onclick="triggerUpload(${docRowCount})" style="opacity: 0.5; pointer-events: none;" title="Upload">
                <i class="fas fa-plus"></i>
            </button>
            <button type="button" class="action-btn replace" onclick="this.closest('.sw-document-modern-card').remove()" title="Remove">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(card);
}

function enableUpload(id) {
    const select = document.getElementById('docType' + id);
    const input = document.getElementById('docFile' + id);
    const btn = document.getElementById('btnUpload' + id);

    if (select.value) {
        input.disabled = false;
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
        input.onchange = function () {
            const fileName = this.files[0] ? this.files[0].name : 'No file selected';
            document.getElementById('docName' + id).textContent = fileName;
            handleDocumentUpload(this, select.value);
        };
    }
}

function triggerUpload(id) {
    const input = document.getElementById('docFile' + id);
    input.click();
}

/**
 * --- TIMETABLE MODAL ---
 */

function openTimetableModal(employeeCode, employeeName) {
    const modal = document.getElementById('timetableModal');
    if (!modal) return;

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    document.getElementById('timetableTeacherName').textContent = employeeName;
    document.getElementById('timetableLoading').style.display = 'block';
    document.getElementById('timetableContent').style.display = 'none';
    document.getElementById('timetableError').style.display = 'none';

    const url = window.urls.getTimetable + `?employee_code=${employeeCode}&teacher_name=${encodeURIComponent(employeeName)}`;

    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            document.getElementById('timetableLoading').style.display = 'none';
            if (data.success) {
                displayTimetableData(data.data);
                document.getElementById('timetableContent').style.display = 'block';
            } else {
                document.getElementById('timetableError').textContent = data.message || 'Error loading timetable data';
                document.getElementById('timetableError').style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            document.getElementById('timetableLoading').style.display = 'none';
            document.getElementById('timetableError').textContent = 'Network error: ' + error.message;
            document.getElementById('timetableError').style.display = 'block';
        });
}

function closeTimetableModal() {
    const modal = document.getElementById('timetableModal');
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function displayTimetableData(data) {
    const container = document.getElementById('timetableContent');
    if (!container) return;

    if (!data || data.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: var(--text-light);">
                <i class="fas fa-calendar-times" style="font-size: 4rem; color: var(--border-color, #ddd); margin-bottom: 20px;"></i>
                <h3>No Timetables Found</h3>
                <p>This teacher is not assigned to any timetable.</p>
            </div>
        `;
        return;
    }

    const timetableMap = {};
    data.forEach(row => {
        const timetableId = row.TimetableID || 'default';
        if (!timetableMap[timetableId]) {
            timetableMap[timetableId] = {
                TimetableID: row.TimetableID,
                ClassName: row.ClassName,
                SectionName: row.SectionName,
                AcademicYear: row.AcademicYear,
                EffectiveFrom: row.EffectiveFrom,
                periods: {},
                slots: []
            };
        }

        if (row.PeriodID && !timetableMap[timetableId].periods[row.PeriodID]) {
            timetableMap[timetableId].periods[row.PeriodID] = {
                PeriodID: row.PeriodID,
                PeriodName: row.PeriodName,
                PeriodType: row.PeriodType,
                StartTime: row.StartTime,
                EndTime: row.EndTime,
                DisplayOrder: row.DisplayOrder || 0
            };
        }

        if (row.SlotID) {
            timetableMap[timetableId].slots.push({
                SlotID: row.SlotID,
                DayOfWeek: row.DayOfWeek,
                PeriodID: row.PeriodID,
                SubjectName: row.SubjectName,
                TeacherName: row.TeacherName,
                ClassName: row.ClassName,
                SectionName: row.SectionName
            });
        }
    });

    const timetables = Object.values(timetableMap);
    if (timetables.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: var(--text-light);">
                <i class="fas fa-calendar-times" style="font-size: 4rem; color: var(--border-color, #ddd); margin-bottom: 20px;"></i>
                <h3>No Valid Timetables Found</h3>
                <p>Unable to process timetable data for this teacher.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = timetables.map(t => renderTimetableCard(t)).join('');
}

function renderTimetableCard(timetableData) {
    const periods = Object.values(timetableData.periods).sort((a, b) => (a.DisplayOrder || 0) - (b.DisplayOrder || 0));
    const slots = timetableData.slots;
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const isDark = document.body.classList.contains('dark-mode');
    const bgColor = isDark ? 'var(--secondary-color, #1a1f2e)' : 'white';
    const altBg = isDark ? 'var(--light-gray, #2a2f3e)' : '#f9fafb';
    const classSection = timetableData.SectionName ?
        `${timetableData.ClassName || 'Unknown Class'} - ${timetableData.SectionName}` :
        (timetableData.ClassName || 'Unknown Class');

    if (periods.length === 0) {
        return `
            <div style="background: ${bgColor}; padding: 20px; border-radius: 12px; box-shadow: var(--card-shadow); margin-bottom: 20px; border-left: 4px solid var(--primary-color);">
                <div style="text-align: center; padding: 40px; color: var(--text-light);">
                    <h3 style="color: var(--primary-color); margin: 0 0 10px 0;">${classSection}</h3>
                    <p>No periods defined for this timetable.</p>
                </div>
            </div>
        `;
    }

    let html = `
        <div style="background: ${bgColor}; padding: 20px; border-radius: 12px; box-shadow: var(--card-shadow); margin-bottom: 20px; border-left: 4px solid var(--primary-color);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                <div>
                    <h3 style="color: var(--primary-color); margin: 0; font-size: 1.3rem;">${classSection}</h3>
                    <p style="color: var(--text-light, #888); margin: 5px 0 0 0; font-size: 0.85rem;">
                        ${timetableData.AcademicYear || 'N/A'} | 
                        ${timetableData.EffectiveFrom ? new Date(timetableData.EffectiveFrom).toLocaleDateString('en-GB') : 'N/A'}
                    </p>
                </div>
            </div>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                    <thead>
                        <tr style="background: var(--primary-color, #004aad); color: white;">
                            <th style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); text-align: left; min-width: 90px;">Day</th>
                            ${periods.map(p => `
                                <th style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); text-align: center; min-width: 110px;">
                                    <div>${p.PeriodName || 'Period'}</div>
                                    <div style="font-size: 0.75rem; opacity: 0.9; font-weight: 400;">
                                        ${p.StartTime ? p.StartTime.substring(0, 5) : ''}-${p.EndTime ? p.EndTime.substring(0, 5) : ''}
                                    </div>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>`;

    days.forEach((day, dayIndex) => {
        html += `<tr style="background: ${dayIndex % 2 === 0 ? altBg : bgColor};">
            <td style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); font-weight: 600; color: var(--text-color, #333);">${day}</td>`;

        periods.forEach(period => {
            const slot = slots.find(s => s.DayOfWeek === dayIndex + 1 && s.PeriodID === period.PeriodID);

            if (period.PeriodType === 'Break') {
                html += `<td style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); text-align: center; background: #fef3c7; color: #92400e; font-weight: 500;">Break</td>`;
            } else if (slot) {
                const classInfo = slot.SectionName ? `${slot.ClassName} - ${slot.SectionName}` : (slot.ClassName || '');
                html += `
                    <td style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); text-align: center;">
                        <div style="font-weight: 600; color: var(--text-color, #333);">${slot.SubjectName || '-'}</div>
                        ${classInfo ? `<div style="font-size: 0.7rem; color: var(--primary-color, #004aad); margin-top: 2px; font-weight: 600;">${classInfo}</div>` : ''}
                    </td>
                `;
            } else {
                html += `<td style="padding: 10px 8px; border: 1px solid var(--border-color, #ddd); text-align: center; color: var(--text-light, #888);">-</td>`;
            }
        });
        html += `</tr>`;
    });

    html += `</tbody></table></div></div>`;
    return html;
}

// Global escape key listener
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeAllModals();
    }
});
