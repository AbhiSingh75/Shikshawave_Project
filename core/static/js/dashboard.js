/**
 * Dashboard Specific Logic for ShikshaWave
 * Handles Modals, Filters, Stats, and Charts
 */

(function (window) {
    const Dashboard = {
        charts: {},

        init() {
            this.loadInitialStats();
            this.bindEvents();
        },

        bindEvents() {
            // Global click handler to close modals if clicking outside
            window.onclick = (event) => {
                const modals = document.querySelectorAll('.stats-modal');
                modals.forEach(modal => {
                    if (event.target === modal) {
                        modal.classList.remove('show');
                        document.body.style.overflow = '';
                    }
                });
            };
        },

        async loadInitialStats() {
            this.loadTodayAttendance();
            this.loadRevenueStats();
            this.loadStaffAttendanceStats();
            this.loadExpenseStats();
            this.loadInitialTicketPulse();
            this.loadSubscriptionStats();
        },

        // API Helpers
        async fetch(url) {
            try {
                const res = await fetch(url);
                return await res.json();
            } catch (err) {
                console.error(`Dashboard API Error (${url}):`, err);
                return { success: false };
            }
        },

        // Modals Management
        openModal(id, initFn) {
            const modal = document.getElementById(id);
            if (!modal) return;
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            if (typeof initFn === 'function') initFn.call(this);
        },

        closeModal(id) {
            const modal = document.getElementById(id);
            if (modal) modal.classList.remove('show');
            document.body.style.overflow = '';
        },

        // --- Pulse (Dashboard Home) ---
        async loadTodayAttendance() {
            const data = await this.fetch('/api/dashboard/attendance/');
            if (data.success && data.stats) {
                const s = data.stats;
                const today = document.getElementById('todayAttendance');
                if (today) today.textContent = `${s.attendance_percentage}%`;
                
                const absent = document.getElementById('todayAbsent');
                if (absent) absent.textContent = `Absent: ${s.absent_percentage}% | Late: ${s.late_percentage}%`;
                

            }
        },

        async loadRevenueStats() {
            const today = new Date().toISOString().split('T')[0];
            const data = await this.fetch(`/api/dashboard/revenue/?from_date=${today}&to_date=${today}`);
            if (data.success && data.stats) {
                const s = data.stats;

                const total = document.getElementById('totalRevenue');
                if (total) total.textContent = `₹${s.total_revenue.toLocaleString('en-IN')}`;
                const pending = document.getElementById('pendingAmount');
                if (pending) pending.textContent = `Pending: ₹${s.total_pending.toLocaleString('en-IN')}`;
            }
        },

        async loadStaffAttendanceStats() {
            const data = await this.fetch('/api/dashboard/staff-attendance/');
            if (data.success && data.stats) {
                const s = data.stats;
                const el = document.getElementById('staffAttendancePercent');
                if (el) el.textContent = `${s.present_percentage}%`;
                const sub = document.getElementById('staffAttendanceLabel');
                if (sub) sub.textContent = `Absent: ${s.absent_percentage}% | Late: ${s.late_percentage}%`;
            }
        },

        async loadExpenseStats() {
            const today = new Date().toISOString().split('T')[0];
            const data = await this.fetch(`/api/dashboard/expense/?from_date=${today}&to_date=${today}`);
            if (data.success && data.stats) {
                const s = data.stats;
                const total = document.getElementById('totalExpense');
                if (total) total.textContent = `₹${s.total_expense.toLocaleString('en-IN')}`;
                const pending = document.getElementById('expensePending');
                if (pending) pending.textContent = `Pending: ₹${s.total_pending.toLocaleString('en-IN')}`;
            }
        },

        // --- Student Section ---
        async loadStudentFilters() {
            // 1. Set Default Dates (Local Timezone - avoid UTC shift)
            const d = new Date();
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            const lastDayDate = new Date(d.getFullYear(), d.getMonth() + 1, 0);
            const lastDay = `${lastDayDate.getFullYear()}-${String(lastDayDate.getMonth() + 1).padStart(2, '0')}-${String(lastDayDate.getDate()).padStart(2, '0')}`;
            
            const fromEl = document.getElementById('modalFromDate');
            const toEl = document.getElementById('modalToDate');
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = lastDay;

            // 2. Load Classes
            const data = await this.fetch('/api/classes/');
            const select = document.getElementById('modalClass');
            if (select && data.classes) {
                select.innerHTML = '<option value="">All Classes</option>';
                data.classes.forEach(c => select.add(new Option(c.ClassName, c.ClassID)));
                
                // Add listener for sections
                select.onchange = () => this.loadSections(select.value);
            }
            
            this.applyStudentFilters();
        },

        async loadSections(classId) {
            const select = document.getElementById('modalSection');
            if (!select) return;
            
            if (!classId) {
                select.innerHTML = '<option value="">All Sections</option>';
                return;
            }

            const data = await this.fetch(`/api/sections/?class_id=${classId}`);
            if (data.status === 'SUCCESS' && data.sections) {
                select.innerHTML = '<option value="">All Sections</option>';
                data.sections.forEach(s => select.add(new Option(s.SectionName, s.SectionID)));
            }
        },

        async applyStudentFilters() {
            const params = new URLSearchParams({ show_active_only: '1' });
            
            // Explicit Mapping for backend keys (matching Proc_DashboardStudentStats_Get)
            const mapping = {
                'modalFromDate': 'from_date',
                'modalToDate': 'to_date',
                'modalClass': 'class_id',
                'modalSection': 'section_id',
                'modalGender': 'gender',
                'modalCategory': 'category'
            };

            Object.entries(mapping).forEach(([fieldId, apiKey]) => {
                const el = document.getElementById(fieldId);
                if (el && el.value) params.append(apiKey, el.value);
            });

            const data = await this.fetch(`/api/dashboard/students/?${params.toString()}`);
            if (data.success) {
                this.updateStudentStats(data.stats, data.admission_trend, data.class_breakdown);
            }
        },

        updateStudentStats(stats, trend, breakdown) {
            // 1. Overall Stats (PascalCase)
            const mappings = {
                'modalTotal': stats.TotalStudents,
                'modalMale': stats.MaleStudents,
                'modalFemale': stats.FemaleStudents,
                'modalGeneral': stats.GeneralCategory,
                'modalOBC': stats.OBCCategory,
                'modalSC': stats.SCCategory,
                'modalST': stats.STCategory,
                'modalInactive': stats.InactiveStudents
            };

            Object.entries(mappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val !== undefined ? val : 0;
            });

            // --- India Standard: Student Pulse Logic ---
            if (stats) {
                const total = stats.TotalStudents || 0;
                const active = stats.ActiveStudents || 0;
                const female = stats.FemaleStudents || 0;
                const male = stats.MaleStudents || 0;
                
                const activeStrength = total > 0 ? Math.round((active / total) * 100) : 100;
                const pulseActive = document.getElementById('pulseActiveStrength');
                if (pulseActive) pulseActive.textContent = `${activeStrength}%`;
                
                const pulseGender = document.getElementById('pulseGenderRatio');
                if (pulseGender) {
                    const ratio = male > 0 ? (female / male).toFixed(2) : (female > 0 ? '1.0' : '0.0');
                    pulseGender.textContent = `1:${ratio}`;
                }

                const pulseAdmissions = document.getElementById('pulseAdmissionMomentum');
                if (pulseAdmissions && trend && trend.length > 0) {
                    const latest = trend[trend.length - 1]?.NewAdmissions || 0;
                    const prev = trend.length > 1 ? trend[trend.length - 2]?.NewAdmissions : 0;
                    const growthS = prev > 0 ? Math.round(((latest - prev) / prev) * 100) : (latest > 0 ? 100 : 0);
                    pulseAdmissions.textContent = `${growthS >= 0 ? '+' : ''}${growthS}%`;
                }
            }

            // 2. Class-Wise Distribution Tiles (PascalCase)
            const grid = document.getElementById('classDistributionGrid');
            if (grid && breakdown) {
                grid.innerHTML = breakdown.map(cls => `
                    <div class="sw-class-tile">
                        <h4>Class ${cls.ClassName}</h4>
                        <span class="tile-value">${cls.StudentCount}</span>
                        <span class="tile-subvalue">Students</span>
                    </div>
                `).join('');
            }

            // 3. Admission Trend Chart
            const isDark = document.body.classList.contains('dark-mode');
            const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#004aad';

            if (trend && trend.length > 0) {
                this.renderChart('admissionTrendChart', 'line', {
                    labels: trend.map(t => t.MonthYear),
                    datasets: [{
                        label: 'New Admissions',
                        data: trend.map(t => t.NewAdmissions),
                        borderColor: isDark ? '#60a5fa' : primaryColor,
                        backgroundColor: isDark ? 'rgba(96, 165, 250, 0.15)' : 'rgba(0, 74, 173, 0.08)',
                        borderWidth: 4,
                        pointBackgroundColor: isDark ? '#60a5fa' : primaryColor,
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.45,
                        fill: true
                    }]
                });
            }

            // 4. Admission Revenue Bar Chart (Aesthetic Improvements)
            if (breakdown && breakdown.length > 0) {
                this.renderChart('classRevenueChart', 'bar', {
                    labels: breakdown.map(cls => cls.ClassName),
                    datasets: [{
                        label: 'Admission Revenue (₹)',
                        data: breakdown.map(cls => cls.AdmissionRevenue),
                        backgroundColor: isDark ? 'rgba(52, 211, 153, 0.7)' : 'rgba(16, 185, 129, 0.8)',
                        borderColor: isDark ? '#34d399' : '#10b981',
                        borderWidth: 2,
                        borderRadius: 8,
                        barThickness: 35,
                        maxBarThickness: 50
                    }]
                });
            }
        },


        // --- Teacher Section ---
        async loadTeacherData() {
            // 1. Set Default Dates (Current Month)
            const d = new Date();
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            const lastDayDate = new Date(d.getFullYear(), d.getMonth() + 1, 0);
            const lastDay = `${lastDayDate.getFullYear()}-${String(lastDayDate.getMonth() + 1).padStart(2, '0')}-${String(lastDayDate.getDate()).padStart(2, '0')}`;
            
            const fromEl = document.getElementById('teacherFromDate');
            const toEl = document.getElementById('teacherToDate');
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = lastDay;

            // 2. Populate profile types dropdown
            const select = document.getElementById('teacherDepartment');
            if (select && select.options.length <= 1) {
                const profiles = await this.fetch('/api/staff-profiles/');
                if (profiles && profiles.length > 0) {
                    profiles.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p.ProfileName;
                        opt.textContent = p.ProfileName;
                        select.appendChild(opt);
                    });
                }
            }
            this.applyTeacherFilters();
        },

        async applyTeacherFilters() {
            const params = new URLSearchParams({ show_active_only: '1' });
            
            // Explicit Mapping for teacher modal (matching Proc_DashboardEmployeeStats_Get)
            const mapping = {
                'teacherFromDate': 'from_date',
                'teacherToDate': 'to_date',
                'teacherDepartment': 'department',
                'teacherGender': 'gender',
                'teacherType': 'employment_type'
            };

            Object.entries(mapping).forEach(([fieldId, apiKey]) => {
                const el = document.getElementById(fieldId);
                if (el && el.value) params.append(apiKey, el.value);
            });

            const data = await this.fetch(`/api/dashboard/employees/?${params.toString()}`);
            if (data.success) {
                this.updateTeacherStats(data.stats, data.profile_breakdown, data.hiring_trend);
            }
        },

        updateTeacherStats(stats, breakdown, trend) {
            // 1. Overall Stats (PascalCase)
            const mappings = {
                'teacherTotal': stats.TotalEmployees,
                'teacherMale': stats.MaleEmployees,
                'teacherFemale': stats.FemaleEmployees,
                'teacherPermanent': stats.PermanentEmployees,
                'teacherContract': stats.ContractEmployees,
                'teacherGuest': stats.GuestEmployees
            };

            Object.entries(mappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val !== undefined ? val : 0;
            });

            // --- India Standard: Teacher Pulse Logic ---
            const totalE = stats.TotalEmployees || 0;
            const permE = stats.PermanentEmployees || 0;
            const femaleE = stats.FemaleEmployees || 0;
            const maleE = stats.MaleEmployees || 0;

            const stability = totalE > 0 ? Math.round((permE / totalE) * 100) : 0;
            const pulseStability = document.getElementById('pulseTeacherStability');
            if (pulseStability) pulseStability.textContent = `${stability}%`;

            const pulseGenderT = document.getElementById('pulseTeacherGender');
            if (pulseGenderT) {
                const ratioT = maleE > 0 ? (femaleE / maleE).toFixed(2) : (femaleE > 0 ? '1.0' : '0.0');
                pulseGenderT.textContent = `1:${ratioT}`;
            }

            const pulseHiring = document.getElementById('pulseTeacherHiring');
            if (pulseHiring) pulseHiring.textContent = stats.TotalEmployees || 0;

            // 2. Profile Distribution Tiles (PascalCase)
            const grid = document.getElementById('profileDistributionGrid');
            if (grid && breakdown) {
                grid.innerHTML = breakdown.map(prof => `
                    <div class="sw-class-tile">
                        <h4>${prof.EmployeeType}</h4>
                        <span class="tile-value">${prof.EmployeeCount}</span>
                        <span class="tile-subvalue">Total Staff</span>
                    </div>
                `).join('');
            }

            // 3. Hiring Trend Chart
            const isDark = document.body.classList.contains('dark-mode');
            const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim() || '#004aad';

            if (trend && trend.length > 0) {
                this.renderChart('staffHiringChart', 'line', {
                    labels: trend.map(t => t.MonthYear),
                    datasets: [{
                        label: 'New Hirings',
                        data: trend.map(t => t.NewHires),
                        borderColor: isDark ? '#10b981' : '#059669',
                        backgroundColor: isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(5, 150, 105, 0.08)',
                        borderWidth: 4,
                        pointBackgroundColor: isDark ? '#10b981' : '#059669',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        tension: 0.45,
                        fill: true
                    }]
                });
            }
        },

        // --- Attendance Section ---
        async loadAttendanceData() {
            // 1. Set Default Dates (Current Month)
            const d = new Date();
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            const lastDayDate = new Date(d.getFullYear(), d.getMonth() + 1, 0);
            const lastDay = `${lastDayDate.getFullYear()}-${String(lastDayDate.getMonth() + 1).padStart(2, '0')}-${String(lastDayDate.getDate()).padStart(2, '0')}`;
            
            const fromEl = document.getElementById('attendanceFromDate');
            const toEl = document.getElementById('attendanceToDate');
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = lastDay;

            // 2. Load Classes
            const data = await this.fetch('/api/classes/');
            const select = document.getElementById('attendanceClass');
            if (select && data.classes) {
                select.innerHTML = '<option value="">All Classes</option>';
                data.classes.forEach(c => select.add(new Option(c.ClassName, c.ClassID)));
                select.onchange = () => this.loadAttendanceSections(select.value);
            }
            this.applyAttendanceFilters();
        },

        async loadAttendanceSections(classId) {
            const select = document.getElementById('attendanceSection');
            if (!select) return;
            if (!classId) {
                select.innerHTML = '<option value="">All Sections</option>';
                return;
            }
            const data = await this.fetch(`/api/sections/?class_id=${classId}`);
            if (data.status === 'SUCCESS' && data.sections) {
                select.innerHTML = '<option value="">All Sections</option>';
                data.sections.forEach(s => select.add(new Option(s.SectionName, s.SectionID)));
            }
        },

        async applyAttendanceFilters() {
            const params = new URLSearchParams();
            const mapping = {
                'attendanceFromDate': 'from_date',
                'attendanceToDate': 'to_date',
                'attendanceClass': 'class_id',
                'attendanceSection': 'section_id'
            };

            Object.entries(mapping).forEach(([fieldId, apiKey]) => {
                const el = document.getElementById(fieldId);
                if (el && el.value) params.append(apiKey, el.value);
            });

            // Fetch Stats and Trend in parallel
            const [statsData, trendData] = await Promise.all([
                this.fetch(`/api/dashboard/attendance/?${params.toString()}`),
                this.fetch(`/api/dashboard/attendance/trend/?${params.toString()}`)
            ]);

            if (statsData.success) {
                this.updateAttendanceStats(statsData.stats, trendData.trend);
            }
        },

        updateAttendanceStats(stats, trend) {
            if (stats) {
                // Main Stats Grid
                const avgEl = document.getElementById('attendanceAvg');
                if (avgEl) avgEl.textContent = `${stats.attendance_percentage || 0}%`;

                const presEl = document.getElementById('attendancePresent');
                if (presEl) presEl.textContent = stats.present_count || 0;

                const absEl = document.getElementById('attendanceAbsent');
                if (absEl) absEl.textContent = stats.absent_count || 0;

                // Pulse Metrics (Actionable Insights)
                const complianceEl = document.getElementById('pulseAttendanceCompliance');
                if (complianceEl) {
                    const pct = stats.attendance_percentage || 0;
                    complianceEl.textContent = `${pct}%`;
                    complianceEl.parentElement.classList.toggle('pulse-risk-alert', pct < 75);
                }

                const stabilityEl = document.getElementById('pulseAttendanceStability');
                if (stabilityEl) stabilityEl.textContent = `${stats.attendance_percentage || 0}%`;

                const riskEl = document.getElementById('pulseAttendanceRisk');
                if (riskEl) riskEl.textContent = stats.absent_count || 0;
            }

            if (trend && trend.length > 0) {
                this.renderChart('attendanceTrendChart', 'line', {
                    labels: trend.map(t => t.MonthYear),
                    datasets: [{
                        label: 'Attendance Rate (%)',
                        data: trend.map(t => t.PresentPercentage),
                        borderColor: '#004aad',
                        backgroundColor: 'rgba(0, 74, 173, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                });
            }
        },

        // --- Revenue Section ---
        async loadRevenueData() {
            const d = new Date();
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            const lastDayDate = new Date(d.getFullYear(), d.getMonth() + 1, 0);
            const lastDay = `${lastDayDate.getFullYear()}-${String(lastDayDate.getMonth() + 1).padStart(2, '0')}-${String(lastDayDate.getDate()).padStart(2, '0')}`;
            
            const fromEl = document.getElementById('revenueFromDate');
            const toEl = document.getElementById('revenueToDate');
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = lastDay;

            const data = await this.fetch('/api/classes/');
            const select = document.getElementById('revenueClass');
            if (select && data.classes) {
                select.innerHTML = '<option value="">All Classes</option>';
                data.classes.forEach(c => select.add(new Option(c.ClassName, c.ClassID)));
            }
            this.applyRevenueFilters();
        },

        async applyRevenueFilters() {
            const params = new URLSearchParams();
            const mapping = {
                'revenueFromDate': 'from_date',
                'revenueToDate': 'to_date',
                'revenueClass': 'class_id',
                'revenuePaymentMode': 'payment_mode',
                'revenuePaymentFor': 'payment_for'
            };

            Object.entries(mapping).forEach(([fieldId, apiKey]) => {
                const el = document.getElementById(fieldId);
                if (el && el.value) params.append(apiKey, el.value);
            });

            const data = await this.fetch(`/api/dashboard/revenue/?${params.toString()}`);
            if (data.success) {
                this.updateRevenueStats(data.stats, data.monthly_trend);
            }
        },

        updateRevenueStats(stats, trend) {
            const mappings = {
                'revenueTotalRevenue': `₹${stats.total_revenue.toLocaleString('en-IN')}`,
                'revenueAdmission': `₹${stats.admission_revenue.toLocaleString('en-IN')}`,
                'revenueFee': `₹${stats.fee_revenue.toLocaleString('en-IN')}`,
                'revenueTotalDiscount': `₹${stats.total_discount.toLocaleString('en-IN')}`,
                'revenueTotalPending': `₹${stats.total_pending.toLocaleString('en-IN')}`,
                'revenueTotalTransactions': stats.total_transactions
            };

            Object.entries(mappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });

            // --- India Standard: Revenue Pulse Logic ---
            const collected = stats.total_revenue || 0;
            const pendingR = stats.total_pending || 0;
            const efficiency = (collected + pendingR) > 0 ? Math.round((collected / (collected + pendingR)) * 100) : 0;
            
            const effEl = document.getElementById('pulseCollectionEfficiency');
            if (effEl) effEl.textContent = `${efficiency}%`;

            const revStuEl = document.getElementById('pulseRevenuePerStudent');
            if (revStuEl) {
                // Approximate ARPU using transactions if specific student count not in stats
                const divisor = stats.total_transactions || 1;
                const perStu = Math.round(collected / divisor);
                revStuEl.textContent = `₹${perStu.toLocaleString('en-IN')}`;
            }

            const duesElR = document.getElementById('pulseOutstandingDues');
            if (duesElR) duesElR.textContent = `₹${pendingR.toLocaleString('en-IN')}`;

            if (trend && trend.length > 0) {
                this.renderChart('revenueTrendChart', 'bar', {
                    labels: trend.map(t => t.month_year),
                    datasets: [{
                        label: 'Monthly Revenue (₹)',
                        data: trend.map(t => t.revenue),
                        backgroundColor: 'rgba(52, 211, 153, 0.7)',
                        borderRadius: 8
                    }]
                });
            }
        },

        // --- Expense Section ---
        async loadExpenseData() {
            const d = new Date();
            const currentMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            
            const fromEl = document.getElementById('expenseFromDate');
            const toEl = document.getElementById('expenseToDate');
            if (fromEl) fromEl.value = currentMonth;
            if (toEl) toEl.value = currentMonth;

            this.applyExpenseFilters();
        },

        async applyExpenseFilters() {
            const fromMonth = document.getElementById('expenseFromDate')?.value;
            const toMonth = document.getElementById('expenseToDate')?.value;
            const empType = document.getElementById('expenseEmploymentType')?.value;

            const params = new URLSearchParams();
            if (fromMonth) params.append('from_date', `${fromMonth}-01`);
            if (toMonth) params.append('to_date', `${toMonth}-01`); // Backend treats month input as starting day
            if (empType) params.append('employment_type', empType);

            const data = await this.fetch(`/api/dashboard/expense/?${params.toString()}`);
            if (data.success) {
                this.updateExpenseStats(data.stats, data.trend);
            }
        },

        updateExpenseStats(stats, trend) {
            const mappings = {
                'expenseTotalExpense': `₹${stats.total_expense.toLocaleString('en-IN')}`,
                'expenseTotalPaid': `₹${stats.total_paid.toLocaleString('en-IN')}`,
                'expenseTotalPending': `₹${stats.total_pending.toLocaleString('en-IN')}`,
                'expensePermanent': `₹${stats.permanent_expense.toLocaleString('en-IN')}`,
                'expenseContract': `₹${stats.contract_expense.toLocaleString('en-IN')}`,
                'expenseGuest': `₹${stats.guest_expense.toLocaleString('en-IN')}`,
                'expensePaidEmployees': stats.paid_employees,
                'expenseUnpaidEmployees': stats.unpaid_employees
            };

            Object.entries(mappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });

            // --- India Standard: Expense Pulse Logic ---
            const totalExp = stats.total_expense || 0;
            const paidExp = stats.total_paid || 0;
            const efficiencyExp = totalExp > 0 ? Math.round((paidExp / totalExp) * 100) : 0;

            const complianceExpEl = document.getElementById('pulseExpenseCompliance');
            if (complianceExpEl) complianceExpEl.textContent = `${efficiencyExp}%`;

            const costEl = document.getElementById('pulseOperationalCost');
            if (costEl) {
                const avg = stats.paid_employees > 0 ? Math.round(totalExp / stats.paid_employees) : 0;
                costEl.textContent = `₹${avg.toLocaleString('en-IN')}`;
            }

            const liabilityEl = document.getElementById('pulseFinancialLiability');
            if (liabilityEl) liabilityEl.textContent = `₹${stats.total_pending.toLocaleString('en-IN')}`;

            if (trend && trend.length > 0) {
                this.renderChart('expenseTrendChart', 'bar', {
                    labels: trend.map(t => t.month_year),
                    datasets: [{
                        label: 'Monthly Expense (₹)',
                        data: trend.map(t => t.total_expense),
                        backgroundColor: 'rgba(239, 68, 68, 0.7)',
                        borderRadius: 8
                    }]
                });
            }
        },

        // --- Staff Attendance Section ---
        async loadStaffAttendanceData() {
            const d = new Date();
            const today = d.toISOString().split('T')[0];
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            
            const dateEl = document.getElementById('staffAttendanceDate');
            const fromEl = document.getElementById('staffAttendanceFromDate');
            const toEl = document.getElementById('staffAttendanceToDate');
            
            if (dateEl) dateEl.value = today;
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = today;

            this.applyStaffAttendanceFilters();
        },

        async applyStaffAttendanceFilters() {
            const params = new URLSearchParams();
            const mapping = {
                'staffAttendanceFromDate': 'from_date',
                'staffAttendanceToDate': 'to_date',
                'staffAttendanceType': 'employment_type'
            };

            Object.entries(mapping).forEach(([fieldId, apiKey]) => {
                const el = document.getElementById(fieldId);
                if (el && el.value) params.append(apiKey, el.value);
            });

            const data = await this.fetch(`/api/dashboard/staff-attendance/?${params.toString()}`);
            if (data.success) {
                this.updateStaffAttendanceStats(data.stats);
            }
        },

        updateStaffAttendanceStats(stats) {
            const mappings = {
                'staffAttendanceTotal': stats.total_marked,
                'staffAttendancePresent': stats.present_count,
                'staffAttendanceAbsent': stats.absent_count,
                'staffAttendanceLeave': stats.leave_count,
                'staffAttendanceLate': stats.late_count,
                'staffAttendanceHoliday': 0 // Not implemented in current procedue
            };

            Object.entries(mappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });

            // --- India Standard: Staff Attendance Pulse Row Logic ---
            const totalS = stats.total_marked || 0;
            const presentS = stats.present_count || 0;
            const pctS = totalS > 0 ? Math.round((presentS / totalS) * 100) : 0;

            const pulsePres = document.getElementById('pulseStaffPresenteeism');
            if (pulsePres) pulsePres.textContent = `${pctS}%`;

            const pulseLate = document.getElementById('pulseStaffLateness');
            if (pulseLate) {
                const latePct = totalS > 0 ? ((stats.late_count / totalS) * 100).toFixed(1) : '0.0';
                pulseLate.textContent = `${latePct}%`;
            }

            const pulseLeaveS = document.getElementById('pulseStaffOnLeave');
            if (pulseLeaveS) pulseLeaveS.textContent = stats.leave_count || 0;
        },

        // --- Chart Helper ---
        renderChart(id, type, data, options = {}) {
            const ctx = document.getElementById(id)?.getContext('2d');
            if (!ctx) return;

            if (this.charts[id]) this.charts[id].destroy();

            const isDark = document.body.classList.contains('dark-mode');
            const themeColor = isDark ? '#818cf8' : '#6366f1';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
            const textColor = isDark ? '#94a3b8' : '#64748b';

            // Check if chart type is linear (requires scales)
            const isLinear = ['line', 'bar', 'radar', 'scatter'].includes(type);

            this.charts[id] = new Chart(ctx, {
                type: type,
                data: data,
                options: Object.assign({
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 1000, easing: 'easeOutQuart' },
                    plugins: { 
                        legend: { 
                            display: true, 
                            position: 'top',
                            labels: { 
                                color: textColor, 
                                font: { size: 11, weight: '700' },
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: isDark ? '#1e293b' : '#fff',
                            titleColor: isDark ? '#f1f5f9' : '#1e293b',
                            bodyColor: isDark ? '#94a3b8' : '#64748b',
                            borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            usePointStyle: true,
                            cornerRadius: 10
                        }
                    },
                    scales: isLinear ? {
                        y: {
                            beginAtZero: true,
                            grid: { color: gridColor, drawBorder: false },
                            ticks: { 
                                color: textColor, 
                                font: { size: 10, weight: '600' },
                                padding: 8
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { 
                                color: textColor, 
                                font: { size: 10, weight: '600' },
                                padding: 8
                            }
                        }
                    } : {} // No scales for pie/doughnut/polar
                }, options)
            });
        },

        async loadSubscriptionStats() {
            const el = document.getElementById('subscriptionRevenue');
            if (!el) return; // Exit if element not present (non-admin)

            const data = await this.fetch('/api/dashboard/subscription-revenue/');
            if (data.success && data.stats) {
                const s = data.stats;
                el.textContent = `₹${s.total_paid.toLocaleString('en-IN')}`;
                const sub = document.getElementById('subscriptionStatus');
                if (sub) sub.textContent = `Paid: ₹${s.total_paid.toLocaleString('en-IN')} | Unpaid: ₹${s.pending_amount.toLocaleString('en-IN')}`;
            }
        },

        // --- Ticket Section ---
        async loadInitialTicketPulse() {
            const data = await this.fetch('/api/dashboard/ticket-stats/');
            if (data.success && data.stats) {
                const s = data.stats;
                const el = document.getElementById('ticketSlaValue');
                if (el) el.textContent = `${s.ResolutionRate}%`;
                const sub = document.getElementById('ticketStatsSub');
                if (sub) sub.textContent = `Avg Time: ${s.AvgResolutionTimeHours}h | Critical: ${s.CriticalVolume}`;
            }
        },

        async loadTicketModalData() {
            const d = new Date();
            const firstDay = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
            const lastDay = d.toISOString().split('T')[0];
            
            const fromEl = document.getElementById('ticketModalFromDate');
            const toEl = document.getElementById('ticketModalToDate');
            if (fromEl) fromEl.value = firstDay;
            if (toEl) toEl.value = lastDay;

            // Populate school list for Super Admins
            await this.loadTicketSchools();

            this.applyTicketFilters();
        },

        async loadTicketSchools() {
            const select = document.getElementById('ticketModalSchool');
            if (!select) return;

            const data = await this.fetch('/api/school-dropdown/');
            if (data.status === 'SUCCESS' && data.data) {
                const currentVal = select.value;
                select.innerHTML = '<option value="">All Schools</option>';
                data.data.forEach(s => {
                    const option = new Option(s.name, s.id);
                    select.add(option);
                });
                if (currentVal) select.value = currentVal;
            }
        },

        async applyTicketFilters() {
            const params = new URLSearchParams();
            const fromDate = document.getElementById('ticketModalFromDate')?.value;
            const toDate = document.getElementById('ticketModalToDate')?.value;
            const schoolId = document.getElementById('ticketModalSchool')?.value;

            if (fromDate) params.append('from_date', fromDate);
            if (toDate) params.append('to_date', toDate);
            if (schoolId) params.append('school_id', schoolId);

            const data = await this.fetch(`/api/dashboard/ticket-stats/?${params.toString()}`);
            if (data.success) {
                this.updateTicketStats(data.stats, data.trend, data.distribution, data.leaderboard);
            }
        },

        resetTicketFilters() {
            this.loadTicketModalData();
        },

        updateTicketStats(stats, trend, distribution, leaderboard) {
            // 1. Grid Mappings (Flagship 8-Tile Design)
            const gridMappings = {
                'modalTicketTotal': stats.TotalInPeriod || 0,
                'modalTicketOpen': stats.OpenCount || 0,
                'modalTicketProgress': stats.InProgressCount || 0,
                'modalTicketResolved': stats.ResolvedCount || 0,
                'modalTicketCritical': (distribution.Priorities?.find(p => p.PriorityName === 'Critical') || {count: 0}).count,
                'modalTicketHigh': (distribution.Priorities?.find(p => p.PriorityName === 'High') || {count: 0}).count,
                'modalTicketMedium': (distribution.Priorities?.find(p => p.PriorityName === 'Medium') || {count: 0}).count,
                'modalTicketLow': (distribution.Priorities?.find(p => p.PriorityName === 'Low') || {count: 0}).count
            };
            Object.entries(gridMappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });

            // Pulse row fallbacks
            const pulseMappings = {
                'pulseTicketSLA': `${stats.ResolutionRate || 0}%`,
                'pulseTicketSpeed': `${stats.AvgResolutionTimeHours || 0}h`,
                'pulseTicketCritical': stats.CriticalVolume || 0
            };
            Object.entries(pulseMappings).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });

            // 2. Trend Chart (Enhanced Aesthetic)
            if (trend && trend.length > 0) {
                this.renderChart('ticketTrendChart', 'line', {
                    labels: trend.map(t => t.Date),
                    datasets: [
                        {
                            label: 'Total Volume',
                            data: trend.map(t => t.Volume),
                            borderColor: '#6366f1',
                            backgroundColor: 'rgba(99, 102, 241, 0.08)',
                            fill: true,
                            tension: 0.45,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        },
                        {
                            label: 'Resolved',
                            data: trend.map(t => t.Resolved),
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.08)',
                            fill: true,
                            tension: 0.45,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }
                    ]
                });
            }

            // 3. Priority Distribution (Specialized Doughnut with Total)
            if (distribution && distribution.Priorities) {
                const totalPrio = distribution.Priorities.reduce((acc, p) => acc + p.count, 0);
                const countEl = document.getElementById('prioTotalCount');
                if (countEl) countEl.textContent = totalPrio;

                this.renderChart('ticketPriorityChart', 'doughnut', {
                    labels: distribution.Priorities.map(p => p.PriorityName),
                    datasets: [{
                        data: distribution.Priorities.map(p => p.count),
                        backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'].slice(0, distribution.Priorities.length),
                        borderWidth: 0,
                        hoverOffset: 12
                    }]
                }, {
                    cutout: '75%',
                    plugins: { 
                        legend: { 
                            position: 'bottom', 
                            labels: { 
                                usePointStyle: true, 
                                padding: 15,
                                font: { size: 10, weight: '700' }
                            } 
                        } 
                    }
                });
            }

            // 4. Categories List (Visual Progress Bars)
            const catList = document.getElementById('ticketCategoryList');
            if (catList && distribution.Categories) {
                const maxCount = Math.max(...distribution.Categories.map(c => c.count)) || 1;
                
                catList.innerHTML = distribution.Categories.map(c => {
                    const pct = Math.round((c.count / maxCount) * 100);
                    return `
                        <div class="sw-category-metric">
                            <div class="metric-header">
                                <span class="category-name">${c.CategoryName}</span>
                                <span class="category-count">${c.count}</span>
                            </div>
                            <div class="sw-elite-progress-mini">
                                <div class="progress-bar" style="width: ${pct}%"></div>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            // 5. Leaderboard
            const table = document.getElementById('ticketLeaderboardTable');
            if (table && leaderboard) {
                if (leaderboard.length === 0) {
                    table.innerHTML = '<tr><td colspan="5" class="text-center opacity-50">No data available for the selected period</td></tr>';
                } else {
                    table.innerHTML = leaderboard.map(l => {
                        const efficiency = l.assigned > 0 ? Math.round((l.resolved / l.assigned) * 100) : 0;
                        return `
                            <tr>
                                <td class="font-bold">${l.UserName}</td>
                                <td class="text-center">${l.assigned}</td>
                                <td class="text-center">${l.resolved}</td>
                                <td class="text-center">${l.avg_speed}h</td>
                                <td>
                                    <div class="sw-elite-progress-mini">
                                        <div class="progress-bar" style="width: ${efficiency}%"></div>
                                        <span class="progress-text">${efficiency}%</span>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }).join('');
                }
            }
        }
    };

    // Public API
    window.Dashboard = Dashboard;

    // Legacy mapping (to avoid changing template onclicks for now)
    window.openStudentModal = () => Dashboard.openModal('studentModal', Dashboard.loadStudentFilters);
    window.closeStudentModal = () => Dashboard.closeModal('studentModal');
    window.applyModalFilters = () => Dashboard.applyStudentFilters();

    window.openTeacherModal = () => Dashboard.openModal('teacherModal', Dashboard.loadTeacherData);
    window.closeTeacherModal = () => Dashboard.closeModal('teacherModal');
    window.applyTeacherFilters = () => Dashboard.applyTeacherFilters();
    window.resetTeacherFilters = () => Dashboard.loadTeacherData();

    window.openAttendanceModal = () => Dashboard.openModal('attendanceModal', Dashboard.loadAttendanceData);
    window.closeAttendanceModal = () => Dashboard.closeModal('attendanceModal');
    window.applyAttendanceFilters = () => Dashboard.applyAttendanceFilters();
    window.resetAttendanceFilters = () => Dashboard.loadAttendanceData();

    window.openRevenueModal = () => Dashboard.openModal('revenueModal', Dashboard.loadRevenueData);
    window.closeRevenueModal = () => Dashboard.closeModal('revenueModal');
    window.applyRevenueFilters = () => Dashboard.applyRevenueFilters();
    window.resetRevenueFilters = () => Dashboard.loadRevenueData();

    window.openStaffAttendanceModal = () => Dashboard.openModal('staffAttendanceModal', Dashboard.loadStaffAttendanceData);
    window.closeStaffAttendanceModal = () => Dashboard.closeModal('staffAttendanceModal');
    window.applyStaffAttendanceFilters = () => Dashboard.applyStaffAttendanceFilters();
    window.resetStaffAttendanceFilters = () => Dashboard.loadStaffAttendanceData();

    window.openExpenseModal = () => Dashboard.openModal('expenseModal', Dashboard.loadExpenseData);
    window.closeExpenseModal = () => Dashboard.closeModal('expenseModal');
    window.applyExpenseFilters = () => Dashboard.applyExpenseFilters();
    window.resetExpenseFilters = () => Dashboard.loadExpenseData();

    window.openTicketInsightsModal = () => Dashboard.openModal('ticketModal', Dashboard.loadTicketModalData);

    window.addEventListener('DOMContentLoaded', () => {
        Dashboard.init();
        

    });

})(window);
