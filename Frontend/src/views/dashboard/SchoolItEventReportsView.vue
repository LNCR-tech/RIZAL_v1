<template>
  <section class="school-it-reports">
    <div class="school-it-reports__shell">
      <SchoolItTopHeader
        class="dashboard-enter dashboard-enter--1"
        :avatar-url="avatarUrl"
        :school-name="activeSchoolSettings?.school_name || activeUser?.school_name || ''"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <div class="school-it-reports__body">
        <header class="school-it-reports__header dashboard-enter dashboard-enter--2">
          <button class="school-it-reports__back" type="button" @click="goBack" aria-label="Go Back">
            <ArrowLeft :size="20" />
          </button>
          <div class="school-it-reports__header-copy">
            <h1 class="school-it-reports__title">Reports Dashboard</h1>
            <p class="school-it-reports__subtitle">Event, student, school, and system reporting in one view.</p>
          </div>
        </header>

        <button
          class="school-it-reports__filters-toggle dashboard-enter dashboard-enter--3"
          type="button"
          :aria-expanded="String(mobileFiltersOpen)"
          @click="toggleMobileFilters"
        >
          <SlidersHorizontal :size="15" />
          <span>{{ mobileFiltersOpen ? 'Hide Filters' : 'Show Filters' }}</span>
        </button>

        <section
          v-show="!isMobileViewport || mobileFiltersOpen"
          class="school-it-reports__filters-panel dashboard-enter dashboard-enter--3"
        >
          <label class="school-it-reports__field">
            <span>Date From</span>
            <input v-model="filters.startDate" class="school-it-reports__field-input" type="date">
          </label>
          <label class="school-it-reports__field">
            <span>Date To</span>
            <input v-model="filters.endDate" class="school-it-reports__field-input" type="date">
          </label>
          <label class="school-it-reports__field">
            <span>Event</span>
            <select v-model="filters.eventId" class="school-it-reports__field-input">
              <option value="">All events</option>
              <option v-for="event in eventFilterOptions" :key="event.id" :value="String(event.id)">{{ event.name }}</option>
            </select>
          </label>
          <label class="school-it-reports__field">
            <span>Student</span>
            <select v-model="filters.studentId" class="school-it-reports__field-input">
              <option value="">All students</option>
              <option v-for="student in studentFilterOptions" :key="student.id" :value="String(student.id)">{{ student.full_name }}</option>
            </select>
          </label>
          <label class="school-it-reports__field">
            <span>Department</span>
            <select v-model="filters.departmentId" class="school-it-reports__field-input">
              <option value="">All departments</option>
              <option v-for="department in departmentFilterOptions" :key="department.id" :value="String(department.id)">{{ department.name }}</option>
            </select>
          </label>
          <button class="school-it-reports__clear-btn" type="button" @click="resetFilters">
            <X :size="14" /> Reset
          </button>
        </section>

        <nav class="school-it-reports__tabs dashboard-enter dashboard-enter--4">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="school-it-reports__tab"
            :class="{ 'school-it-reports__tab--active': activeTab === tab.id }"
            type="button"
            @click="setActiveTab(tab.id)"
          >
            <component :is="tab.icon" :size="15" />{{ tab.label }}
          </button>
        </nav>

        <section class="school-it-reports__content dashboard-enter dashboard-enter--5">
          <template v-if="activeTab === 'event'">
            <div class="school-it-reports__toolbar">
              <div class="school-it-reports__search-shell">
                <input v-model="searchQuery" class="school-it-reports__search-input" type="text" placeholder="Search events">
                <span class="school-it-reports__search-icon"><Search :size="16" /></span>
              </div>
              <button v-if="selectedEvent" class="school-it-reports__clear-btn" type="button" @click="clearSelection">
                <X :size="14" /> Clear Selection
              </button>
            </div>

            <div v-if="isLoadingEvents" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`event-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>

            <div v-else class="school-it-reports__table-wrap">
              <table class="school-it-reports__table">
                <thead>
                  <tr><th>Event</th><th>Date</th><th>Location</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  <tr
                    v-for="event in filteredEvents"
                    :key="event.id"
                    :class="{ 'school-it-reports__table-row--selected': Number(event.id) === selectedEventId }"
                    @click="viewEvent(event)"
                  >
                    <td>{{ event.name }}</td>
                    <td>{{ formatDate(event.start_datetime) }}</td>
                    <td>{{ event.location || 'N/A' }}</td>
                    <td class="school-it-reports__cell-actions">
                      <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click.stop="viewEvent(event)">View</button>
                      <button class="school-it-reports__btn school-it-reports__btn--dark" type="button" @click.stop="downloadReport(event, 'csv')">CSV</button>
                    </td>
                  </tr>
                  <tr v-if="!filteredEvents.length"><td colspan="4" class="school-it-reports__empty">No events found.</td></tr>
                </tbody>
              </table>
            </div>

            <p v-if="selectionError" class="school-it-reports__banner school-it-reports__banner--error">{{ selectionError }}</p>
            <p v-if="isLoadingSelection" class="school-it-reports__banner">Loading selected event report...</p>

            <template v-if="selectedEvent && selectedEventReport && !isLoadingSelection">
              <header class="school-it-reports__detail-header">
                <div>
                  <h2 class="school-it-reports__section-title">{{ selectedEventReport.event_name || selectedEvent.name }}</h2>
                  <p class="school-it-reports__section-subtitle">{{ formatDate(selectedEvent.start_datetime) }} | {{ selectedEvent.location || 'N/A' }}</p>
                </div>
                <div class="school-it-reports__actions">
                  <button class="school-it-reports__btn school-it-reports__btn--dark" type="button" @click="downloadReport(selectedEvent, 'csv')">
                    <Download :size="14" /> Export CSV
                  </button>
                  <button class="school-it-reports__btn school-it-reports__btn--accent" type="button" @click="downloadReport(selectedEvent, 'excel')">
                    <FileSpreadsheet :size="14" /> Export Excel
                  </button>
                </div>
              </header>

              <div class="school-it-reports__stats-grid">
                <article v-for="card in eventSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span>
                  <strong>{{ card.value }}</strong>
                  <small>{{ card.meta }}</small>
                </article>
              </div>

              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Attendance Per Event</h3>
                  <div v-if="eventBarChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsBarChart class="school-it-reports__chart-canvas" :data="eventBarChartData" :options="chartOptions.bar" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="eventPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="eventPieChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="eventLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="eventLineChartData" :options="chartOptions.line" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No trend data.</p>
                </article>
              </div>

              <div class="school-it-reports__toolbar">
                <div class="school-it-reports__search-shell">
                  <input v-model="attendeeQuery" class="school-it-reports__search-input" type="text" placeholder="Search attendees">
                  <span class="school-it-reports__search-icon"><Search :size="16" /></span>
                </div>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead>
                    <tr><th>Student ID</th><th>Name</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in filteredAttendanceRows" :key="row.key">
                      <td>{{ row.studentId }}</td>
                      <td>{{ row.studentName }}</td>
                      <td>{{ row.statusLabel }}</td>
                      <td>{{ row.timeInLabel }}</td>
                      <td>{{ row.timeOutLabel }}</td>
                      <td>{{ row.methodLabel }}</td>
                    </tr>
                    <tr v-if="!filteredAttendanceRows.length"><td colspan="6" class="school-it-reports__empty">No attendance records found.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>

          <template v-else-if="activeTab === 'student'">
            <div v-if="isLoadingOverview" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`student-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="attendanceOverviewError" class="school-it-reports__banner school-it-reports__banner--error">{{ attendanceOverviewError }}</p>
            <template v-else-if="studentReport">
              <header class="school-it-reports__detail-header">
                <div>
                  <h2 class="school-it-reports__section-title">{{ studentReport.student.student_name }}</h2>
                  <p class="school-it-reports__section-subtitle">Student ID: {{ studentReport.student.student_id || 'N/A' }}</p>
                </div>
              </header>
              <div class="school-it-reports__stats-grid">
                <article v-for="card in studentSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>
              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="studentPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="studentPieChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No chart data.</p>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="studentLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="studentLineChartData" :options="chartOptions.line" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No trend data.</p>
                </article>
              </div>

              <div class="school-it-reports__toolbar">
                <div class="school-it-reports__search-shell">
                  <input v-model="studentRecordQuery" class="school-it-reports__search-input" type="text" placeholder="Search student records">
                  <span class="school-it-reports__search-icon"><Search :size="16" /></span>
                </div>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Event</th><th>Date</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr></thead>
                  <tbody>
                    <tr v-for="record in filteredStudentRecords" :key="record.id">
                      <td>{{ record.event_name }}</td>
                      <td>{{ formatDate(record.event_date) }}</td>
                      <td>{{ formatStatusLabel(record.display_status || record.status) }}</td>
                      <td>{{ formatDateTime(record.time_in, 'N/A') }}</td>
                      <td>{{ formatDateTime(record.time_out, 'N/A') }}</td>
                      <td>{{ formatMethod(record.method) }}</td>
                    </tr>
                    <tr v-if="!filteredStudentRecords.length"><td colspan="6" class="school-it-reports__empty">No student records found.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
            <p v-else class="school-it-reports__banner">Select a student from the filter panel.</p>
          </template>

          <template v-else-if="activeTab === 'school'">
            <div v-if="isLoadingSchoolSummary" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`school-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="schoolSummaryError" class="school-it-reports__banner school-it-reports__banner--error">{{ schoolSummaryError }}</p>
            <template v-else-if="schoolSummaryPayload">
              <div class="school-it-reports__stats-grid">
                <article v-for="card in schoolSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>
              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Status Distribution</h3>
                  <div v-if="schoolPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="schoolPieChartData" :options="chartOptions.pie" />
                  </div>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Monthly Trend</h3>
                  <div v-if="schoolLineChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsLineChart class="school-it-reports__chart-canvas" :data="schoolLineChartData" :options="chartOptions.line" />
                  </div>
                </article>
                <article class="school-it-reports__panel">
                  <h3>Top Student Rates</h3>
                  <div v-if="schoolBarChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsBarChart class="school-it-reports__chart-canvas" :data="schoolBarChartData" :options="chartOptions.barPercent" />
                  </div>
                </article>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Student ID</th><th>Name</th><th>Department</th><th>Program</th><th>Total Events</th><th>Rate</th></tr></thead>
                  <tbody>
                    <tr v-for="row in topStudentsRows" :key="row.id">
                      <td>{{ row.student_id || 'N/A' }}</td>
                      <td>{{ row.full_name }}</td>
                      <td>{{ row.department_name || 'Unassigned' }}</td>
                      <td>{{ row.program_name || 'Unassigned' }}</td>
                      <td>{{ formatWhole(row.total_events) }}</td>
                      <td>{{ formatPercent(row.attendance_rate) }}%</td>
                    </tr>
                    <tr v-if="!topStudentsRows.length"><td colspan="6" class="school-it-reports__empty">No student overview rows.</td></tr>
                  </tbody>
                </table>
              </div>

              <header class="school-it-reports__detail-header">
                <div>
                  <h2 class="school-it-reports__section-title">Student Login Access Report</h2>
                  <p class="school-it-reports__section-subtitle">{{ studentLoginWindowLabel }}</p>
                </div>
              </header>

              <div class="school-it-reports__stats-grid school-it-reports__stats-grid--dense">
                <article v-for="card in studentLoginCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>

              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <h3>Login Status Distribution</h3>
                  <div v-if="studentLoginPieChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="studentLoginPieChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No login data available.</p>
                </article>
              </div>

              <div class="school-it-reports__toolbar">
                <div class="school-it-reports__search-shell">
                  <input v-model="studentLoginQuery" class="school-it-reports__search-input" type="text" placeholder="Search student login access">
                  <span class="school-it-reports__search-icon"><Search :size="16" /></span>
                </div>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Student ID</th><th>Name</th><th>Department</th><th>Program</th><th>Status</th><th>Successful Logins</th><th>Last Login</th></tr></thead>
                  <tbody>
                    <tr v-for="row in filteredStudentLoginRows" :key="row.student_profile_id || row.student_id || row.full_name">
                      <td>{{ row.student_id || 'N/A' }}</td>
                      <td>{{ row.full_name }}</td>
                      <td>{{ row.department_name || 'Unassigned' }}</td>
                      <td>{{ row.program_name || 'Unassigned' }}</td>
                      <td>
                        <span
                          class="school-it-reports__status-chip"
                          :class="row.has_logged_in ? 'school-it-reports__status-chip--success' : 'school-it-reports__status-chip--muted'"
                        >
                          {{ row.status_label }}
                        </span>
                      </td>
                      <td>{{ formatWhole(row.successful_login_count) }}</td>
                      <td>{{ formatDateTime(row.last_login_at, 'Never') }}</td>
                    </tr>
                    <tr v-if="!filteredStudentLoginRows.length"><td colspan="7" class="school-it-reports__empty">No student login rows match the current filters.</td></tr>
                  </tbody>
                </table>
              </div>
            </template>
          </template>

          <template v-else-if="activeTab === 'insights'">
            <header class="school-it-reports__detail-header">
              <div>
                <h2 class="school-it-reports__section-title">Recommended Additional Reports</h2>
                <p class="school-it-reports__section-subtitle">Derived from the current filters and aligned with the report catalog recommendations.</p>
              </div>
              <div class="school-it-reports__insight-controls">
                <label class="school-it-reports__field">
                  <span>At-Risk Threshold</span>
                  <input v-model.number="insightControls.atRiskThreshold" class="school-it-reports__field-input" type="number" min="1" max="100">
                </label>
                <label class="school-it-reports__field">
                  <span>Minimum Events</span>
                  <input v-model.number="insightControls.minimumEvents" class="school-it-reports__field-input" type="number" min="1" max="50">
                </label>
                <label class="school-it-reports__field">
                  <span>Decline Alert</span>
                  <input v-model.number="insightControls.declineThreshold" class="school-it-reports__field-input" type="number" min="1" max="100">
                </label>
              </div>
            </header>

            <p class="school-it-reports__banner">Comparison window: {{ insightComparisonSummary }}</p>
            <p v-if="insightComparisonError" class="school-it-reports__banner school-it-reports__banner--error">{{ insightComparisonError }}</p>
            <p v-else-if="isLoadingInsightComparisons" class="school-it-reports__banner">Loading comparison ranges for recovery and decline reports...</p>

            <div class="school-it-reports__stats-grid">
              <article v-for="card in insightSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
              </article>
            </div>

            <article class="school-it-reports__panel">
              <div class="school-it-reports__panel-header">
                <div>
                  <h3>School KPI Dashboard Report</h3>
                  <p class="school-it-reports__panel-subtitle">Executive snapshot of attendance quality, delay burden, incomplete flows, and participation reach.</p>
                </div>
              </div>
              <div class="school-it-reports__stats-grid school-it-reports__stats-grid--dense">
                <article v-for="card in schoolKpiCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>
            </article>

            <div class="school-it-reports__chart-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Attendance by Day of Week</h3>
                    <p class="school-it-reports__panel-subtitle">Shows which weekdays deliver the weakest attendance rates.</p>
                  </div>
                </div>
                <div v-if="attendanceByWeekdayChartData.labels.length" class="school-it-reports__chart-scroll">
                  <ReportsBarChart class="school-it-reports__chart-canvas" :data="attendanceByWeekdayChartData" :options="chartOptions.barPercent" />
                </div>
                <p v-else class="school-it-reports__panel-empty">No weekday attendance data.</p>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Attendance by Time Block</h3>
                    <p class="school-it-reports__panel-subtitle">Highlights late-frequency concentration by scheduled start time.</p>
                  </div>
                </div>
                <div v-if="attendanceByTimeBlockChartData.labels.length" class="school-it-reports__chart-scroll">
                  <ReportsBarChart class="school-it-reports__chart-canvas" :data="attendanceByTimeBlockChartData" :options="chartOptions.bar" />
                </div>
                <p v-else class="school-it-reports__panel-empty">No time block data.</p>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Year Level Attendance Distribution</h3>
                    <p class="school-it-reports__panel-subtitle">Compares cohort performance using weighted attendance rate.</p>
                  </div>
                </div>
                <div v-if="yearLevelChartData.labels.length" class="school-it-reports__chart-scroll">
                  <ReportsBarChart class="school-it-reports__chart-canvas" :data="yearLevelChartData" :options="chartOptions.barPercent" />
                </div>
                <p v-else class="school-it-reports__panel-empty">No year level data.</p>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Event Completion vs Cancellation Report</h3>
                    <p class="school-it-reports__panel-subtitle">Tracks closure quality across completed, cancelled, and still-open events.</p>
                  </div>
                </div>
                <div v-if="eventOutcomeChartData.labels.length" class="school-it-reports__chart-scroll">
                  <ReportsPieChart class="school-it-reports__chart-canvas" :data="eventOutcomeChartData" :options="chartOptions.pie" />
                </div>
                <div class="school-it-reports__metric-list">
                  <div class="school-it-reports__metric-pill">
                    <span>Completed</span>
                    <strong>{{ formatWhole(eventOutcomeSummary.completed) }}</strong>
                  </div>
                  <div class="school-it-reports__metric-pill">
                    <span>Cancelled</span>
                    <strong>{{ formatWhole(eventOutcomeSummary.cancelled) }}</strong>
                  </div>
                  <div class="school-it-reports__metric-pill">
                    <span>Completion Rate</span>
                    <strong>{{ formatPercent(eventOutcomeSummary.completionRate) }}%</strong>
                  </div>
                  <div class="school-it-reports__metric-pill">
                    <span>Cancellation Rate</span>
                    <strong>{{ formatPercent(eventOutcomeSummary.cancellationRate) }}%</strong>
                  </div>
                </div>
              </article>
            </div>

            <div class="school-it-reports__insights-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>At-Risk Attendance List</h3>
                    <p class="school-it-reports__panel-subtitle">Students below the threshold after meeting the minimum event count.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Department</th><th>Events</th><th>Absent</th><th>Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in atRiskRows" :key="`risk-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ row.department_name || row.program_name || 'Unassigned' }}</td>
                        <td>{{ formatWhole(row.total_events) }}</td>
                        <td>{{ formatWhole(row.absent_events) }}</td>
                        <td>{{ formatPercent(row.attendance_rate) }}%</td>
                      </tr>
                      <tr v-if="!atRiskRows.length"><td colspan="5" class="school-it-reports__empty">No students currently meet the at-risk threshold.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Attendance Leaderboard</h3>
                    <p class="school-it-reports__panel-subtitle">Ranks the highest performers once the minimum event requirement is met.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Program</th><th>Events</th><th>Late</th><th>Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in attendanceLeaderboardRows" :key="`leaderboard-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ row.program_name || row.department_name || 'Unassigned' }}</td>
                        <td>{{ formatWhole(row.total_events) }}</td>
                        <td>{{ formatWhole(row.late_events) }}</td>
                        <td>{{ formatPercent(row.attendance_rate) }}%</td>
                      </tr>
                      <tr v-if="!attendanceLeaderboardRows.length"><td colspan="5" class="school-it-reports__empty">No leaderboard rows yet.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <div class="school-it-reports__insights-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Top Absentees</h3>
                    <p class="school-it-reports__panel-subtitle">Prioritizes follow-up using exact absent counts from the student overview.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Department</th><th>Absent</th><th>Events</th><th>Absent Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in topAbsenteesRows" :key="`absent-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ row.department_name || row.program_name || 'Unassigned' }}</td>
                        <td>{{ formatWhole(row.absent_events) }}</td>
                        <td>{{ formatWhole(row.total_events) }}</td>
                        <td>{{ formatPercent(row.absence_rate) }}%</td>
                      </tr>
                      <tr v-if="!topAbsenteesRows.length"><td colspan="5" class="school-it-reports__empty">No absentee rows available.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Top Late Students</h3>
                    <p class="school-it-reports__panel-subtitle">Shows where punctuality interventions are most likely needed.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Program</th><th>Late</th><th>Events</th><th>Late Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in topLateRows" :key="`late-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ row.program_name || row.department_name || 'Unassigned' }}</td>
                        <td>{{ formatWhole(row.late_events) }}</td>
                        <td>{{ formatWhole(row.total_events) }}</td>
                        <td>{{ formatPercent(row.late_rate) }}%</td>
                      </tr>
                      <tr v-if="!topLateRows.length"><td colspan="5" class="school-it-reports__empty">No late rows available.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <div class="school-it-reports__insights-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Attendance Recovery Report</h3>
                    <p class="school-it-reports__panel-subtitle">Highlights the strongest positive rate changes between the current and previous comparison windows.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Previous</th><th>Current</th><th>Delta</th><th>Events</th></tr></thead>
                    <tbody>
                      <tr v-for="row in recoveryRows" :key="`recovery-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ formatPercent(row.previousRate) }}%</td>
                        <td>{{ formatPercent(row.currentRate) }}%</td>
                        <td class="school-it-reports__trend-cell school-it-reports__trend-cell--up">+{{ formatPercent(row.delta) }} pts</td>
                        <td>{{ formatWhole(Math.max(row.currentEvents, row.previousEvents)) }}</td>
                      </tr>
                      <tr v-if="!recoveryRows.length"><td colspan="5" class="school-it-reports__empty">No recovery movements for the current comparison window.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Attendance Decline Alert</h3>
                    <p class="school-it-reports__panel-subtitle">Flags students whose attendance rate dropped beyond the configured alert threshold.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Student</th><th>Previous</th><th>Current</th><th>Delta</th><th>Events</th></tr></thead>
                    <tbody>
                      <tr v-for="row in declineRows" :key="`decline-${row.id}`">
                        <td>{{ row.full_name }}</td>
                        <td>{{ formatPercent(row.previousRate) }}%</td>
                        <td>{{ formatPercent(row.currentRate) }}%</td>
                        <td class="school-it-reports__trend-cell school-it-reports__trend-cell--down">{{ formatPercent(row.delta) }} pts</td>
                        <td>{{ formatWhole(Math.max(row.currentEvents, row.previousEvents)) }}</td>
                      </tr>
                      <tr v-if="!declineRows.length"><td colspan="5" class="school-it-reports__empty">No decline alerts at the current threshold.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <div class="school-it-reports__insights-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>No-Show Event Report</h3>
                    <p class="school-it-reports__panel-subtitle">Ranks the weakest event turnouts by absent share.</p>
                  </div>
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Event</th><th>Date</th><th>Participants</th><th>Absent</th><th>No-Show Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in noShowEventRows" :key="`no-show-${row.id}`">
                        <td>{{ row.name }}</td>
                        <td>{{ formatDate(row.date) }}</td>
                        <td>{{ formatWhole(row.total) }}</td>
                        <td>{{ formatWhole(row.absent) }}</td>
                        <td>{{ formatPercent(row.noShowRate) }}%</td>
                      </tr>
                      <tr v-if="!noShowEventRows.length"><td colspan="5" class="school-it-reports__empty">No event attendance summaries available.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Repeat Participation Report</h3>
                    <p class="school-it-reports__panel-subtitle">Measures how deeply students stay engaged across multiple events.</p>
                  </div>
                </div>
                <div v-if="repeatParticipationChartData.labels.length" class="school-it-reports__chart-scroll">
                  <ReportsBarChart class="school-it-reports__chart-canvas" :data="repeatParticipationChartData" :options="chartOptions.bar" />
                </div>
                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table school-it-reports__table--compact">
                    <thead><tr><th>Bucket</th><th>Students</th><th>Total Events</th><th>Average Rate</th></tr></thead>
                    <tbody>
                      <tr v-for="row in repeatParticipationRows" :key="row.id">
                        <td>{{ row.label }}</td>
                        <td>{{ formatWhole(row.totalStudents) }}</td>
                        <td>{{ formatWhole(row.totalEvents) }}</td>
                        <td>{{ formatPercent(row.averageRate) }}%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <div class="school-it-reports__insights-grid">
              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>First-Time vs Repeat Attendee Report</h3>
                    <p class="school-it-reports__panel-subtitle">Uses the selected event together with the current student overview scope.</p>
                  </div>
                </div>
                <template v-if="selectedEvent">
                  <p class="school-it-reports__panel-note">Selected event: {{ selectedEvent.name }}</p>
                  <div v-if="firstTimeVsRepeatChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="firstTimeVsRepeatChartData" :options="chartOptions.pie" />
                  </div>
                  <div class="school-it-reports__metric-list">
                    <div class="school-it-reports__metric-pill">
                      <span>First-Time</span>
                      <strong>{{ formatWhole(firstTimeVsRepeatSummary.firstTime) }}</strong>
                    </div>
                    <div class="school-it-reports__metric-pill">
                      <span>Repeat</span>
                      <strong>{{ formatWhole(firstTimeVsRepeatSummary.repeat) }}</strong>
                    </div>
                    <div class="school-it-reports__metric-pill">
                      <span>Matched Attendees</span>
                      <strong>{{ formatWhole(firstTimeVsRepeatSummary.attendees - firstTimeVsRepeatSummary.unmatched) }}</strong>
                    </div>
                    <div class="school-it-reports__metric-pill">
                      <span>Unmatched</span>
                      <strong>{{ formatWhole(firstTimeVsRepeatSummary.unmatched) }}</strong>
                    </div>
                  </div>
                </template>
                <p v-else class="school-it-reports__panel-empty">Select an event from the filter panel or Event Reports tab to populate this report.</p>
              </article>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Event Execution Quality Report</h3>
                    <p class="school-it-reports__panel-subtitle">Focuses on late burden and incomplete sign-out patterns for the selected event.</p>
                  </div>
                </div>
                <template v-if="selectedEventReport">
                  <p class="school-it-reports__panel-note">Selected event: {{ selectedEventReport.event_name || selectedEvent?.name }}</p>
                  <div class="school-it-reports__stats-grid school-it-reports__stats-grid--dense">
                    <article v-for="card in selectedEventExecutionCards" :key="card.id" class="school-it-reports__stat-card">
                      <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                    </article>
                  </div>
                  <div class="school-it-reports__table-wrap">
                    <table class="school-it-reports__table school-it-reports__table--compact">
                      <thead><tr><th>Program</th><th>Total</th><th>Present</th><th>Late</th><th>Waiting</th><th>Absent</th></tr></thead>
                      <tbody>
                        <tr v-for="row in selectedEventReport.program_breakdown" :key="`execution-${row.program}`">
                          <td>{{ row.program }}</td>
                          <td>{{ formatWhole(row.total) }}</td>
                          <td>{{ formatWhole(row.present) }}</td>
                          <td>{{ formatWhole(row.late) }}</td>
                          <td>{{ formatWhole(row.incomplete) }}</td>
                          <td>{{ formatWhole(row.absent) }}</td>
                        </tr>
                        <tr v-if="!selectedEventReport.program_breakdown?.length"><td colspan="6" class="school-it-reports__empty">No program breakdown data for this event.</td></tr>
                      </tbody>
                    </table>
                  </div>
                </template>
                <p v-else class="school-it-reports__panel-empty">Select an event to inspect execution quality and no-show detail.</p>
              </article>
            </div>
          </template>

          <template v-else-if="activeTab === 'compliance'">
            <header class="school-it-reports__detail-header">
              <div>
                <h2 class="school-it-reports__section-title">Compliance Reports</h2>
                <p class="school-it-reports__section-subtitle">Absence-triggered sanctions, follow-up status, and export-ready event compliance summaries.</p>
              </div>
              <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="loadSanctionsSummary">Refresh</button>
            </header>

            <div v-if="isLoadingSanctionsSummary" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`compliance-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="sanctionsSummaryError" class="school-it-reports__banner school-it-reports__banner--error">{{ sanctionsSummaryError }}</p>
            <template v-else>
              <div class="school-it-reports__stats-grid">
                <article v-for="card in complianceSummaryCards" :key="card.id" class="school-it-reports__stat-card">
                  <span>{{ card.label }}</span><strong>{{ card.value }}</strong><small>{{ card.meta }}</small>
                </article>
              </div>

              <div class="school-it-reports__chart-grid">
                <article class="school-it-reports__panel">
                  <div class="school-it-reports__panel-header">
                    <div>
                      <h3>Sanction Resolution Status</h3>
                      <p class="school-it-reports__panel-subtitle">Shows how many issued sanctions still need action versus already complied items.</p>
                    </div>
                  </div>
                  <div v-if="complianceStatusChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsPieChart class="school-it-reports__chart-canvas" :data="complianceStatusChartData" :options="chartOptions.pie" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No sanctions dashboard data available.</p>
                </article>

                <article class="school-it-reports__panel">
                  <div class="school-it-reports__panel-header">
                    <div>
                      <h3>Highest Sanction Load</h3>
                      <p class="school-it-reports__panel-subtitle">Prioritizes events with the heaviest absence and pending-sanction burden.</p>
                    </div>
                  </div>
                  <div v-if="complianceLoadChartData.labels.length" class="school-it-reports__chart-scroll">
                    <ReportsBarChart class="school-it-reports__chart-canvas" :data="complianceLoadChartData" :options="chartOptions.bar" />
                  </div>
                  <p v-else class="school-it-reports__panel-empty">No sanction-heavy events to chart yet.</p>
                </article>
              </div>

              <article class="school-it-reports__panel">
                <div class="school-it-reports__panel-header">
                  <div>
                    <h3>Sanction Events Report</h3>
                    <p class="school-it-reports__panel-subtitle">Operational list of events with absences, pending items, compliance counts, and export actions.</p>
                  </div>
                </div>

                <p v-if="selectedComplianceEvent" class="school-it-reports__panel-note">
                  Selected event summary: {{ selectedComplianceEvent.event_name }} with {{ formatWhole(selectedComplianceEvent.pending_sanctions) }} pending sanctions and {{ formatPercent(selectedComplianceEvent.absence_rate_percent) }}% absence rate.
                </p>

                <div class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table">
                    <thead><tr><th>Event</th><th>Participants</th><th>Absent</th><th>Absence Rate</th><th>Pending</th><th>Complied</th><th>Export</th></tr></thead>
                    <tbody>
                      <tr v-for="row in complianceEventRows" :key="`compliance-${row.event_id}`">
                        <td>{{ row.event_name }}</td>
                        <td>{{ formatWhole(row.participant_count) }}</td>
                        <td>{{ formatWhole(row.absent_count) }}</td>
                        <td>{{ formatPercent(row.absence_rate_percent) }}%</td>
                        <td>{{ formatWhole(row.pending_sanctions) }}</td>
                        <td>{{ formatWhole(row.complied_sanctions) }}</td>
                        <td>
                          <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="downloadSanctionsExport(row)">
                            <FileSpreadsheet :size="16" />
                            <span>Export</span>
                          </button>
                        </td>
                      </tr>
                      <tr v-if="!complianceEventRows.length"><td colspan="7" class="school-it-reports__empty">No sanction-bearing events were returned by the dashboard.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </template>
          </template>

          <template v-else>
            <header class="school-it-reports__detail-header">
              <h2 class="school-it-reports__section-title">System Logs</h2>
              <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="loadSystemLogs">Refresh</button>
            </header>
            <div v-if="isLoadingSystemLogs" class="school-it-reports__skeleton-grid">
              <div v-for="index in 3" :key="`system-skeleton-${index}`" class="school-it-reports__skeleton-card" />
            </div>
            <p v-else-if="systemLogsError" class="school-it-reports__banner school-it-reports__banner--error">{{ systemLogsError }}</p>
            <template v-else>
              <div class="school-it-reports__stats-grid">
                <article class="school-it-reports__stat-card"><span>Audit Logs</span><strong>{{ formatWhole(auditLogs.total || 0) }}</strong><small>Total audit rows.</small></article>
                <article class="school-it-reports__stat-card"><span>Notification Logs</span><strong>{{ formatWhole(notificationLogs.length) }}</strong><small>Total notification rows.</small></article>
                <article class="school-it-reports__stat-card"><span>Import Job</span><strong>{{ importReport?.jobStatus?.state || 'N/A' }}</strong><small>Last import lookup state.</small></article>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Timestamp</th><th>Action</th><th>Status</th><th>Actor</th><th>Details</th></tr></thead>
                  <tbody>
                    <tr v-for="item in auditRows" :key="item.id">
                      <td>{{ formatDateTime(item.created_at, 'N/A') }}</td>
                      <td>{{ item.action }}</td>
                      <td>{{ formatStatusLabel(item.status) }}</td>
                      <td>{{ item.actor_user_id || 'N/A' }}</td>
                      <td>{{ item.details || 'No details' }}</td>
                    </tr>
                    <tr v-if="!auditRows.length"><td colspan="5" class="school-it-reports__empty">No audit logs returned.</td></tr>
                  </tbody>
                </table>
              </div>

              <div class="school-it-reports__table-wrap">
                <table class="school-it-reports__table">
                  <thead><tr><th>Timestamp</th><th>Category</th><th>Channel</th><th>Status</th><th>User</th><th>Subject</th></tr></thead>
                  <tbody>
                    <tr v-for="item in notificationRows" :key="item.id">
                      <td>{{ formatDateTime(item.created_at, 'N/A') }}</td>
                      <td>{{ item.category }}</td>
                      <td>{{ item.channel }}</td>
                      <td>{{ formatStatusLabel(item.status) }}</td>
                      <td>{{ item.user_id || 'N/A' }}</td>
                      <td>{{ item.subject || 'No subject' }}</td>
                    </tr>
                    <tr v-if="!notificationRows.length"><td colspan="6" class="school-it-reports__empty">No notification logs returned.</td></tr>
                  </tbody>
                </table>
              </div>

              <article class="school-it-reports__panel">
                <h3>Import Reports</h3>
                <div class="school-it-reports__import-tools">
                  <input v-model="importJobId" class="school-it-reports__field-input" type="text" placeholder="Import Job ID">
                  <input v-model="importPreviewToken" class="school-it-reports__field-input" type="text" placeholder="Preview Token (optional)">
                  <button class="school-it-reports__btn school-it-reports__btn--view" type="button" @click="loadImportReport">Load</button>
                </div>
                <p v-if="importError" class="school-it-reports__banner school-it-reports__banner--error">{{ importError }}</p>
                <p v-else-if="isLoadingImport" class="school-it-reports__banner">Loading import report...</p>
                <div v-else-if="importReport?.jobStatus" class="school-it-reports__table-wrap">
                  <table class="school-it-reports__table">
                    <thead><tr><th>Row</th><th>Error</th></tr></thead>
                    <tbody>
                      <tr v-for="error in importErrors" :key="`${error.row}-${error.error}`">
                        <td>{{ error.row }}</td>
                        <td>{{ error.error }}</td>
                      </tr>
                      <tr v-if="!importErrors.length"><td colspan="2" class="school-it-reports__empty">No failed rows in this import job.</td></tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </template>
          </template>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, BarChart3, Building2, Download, FileSpreadsheet, FileText, Layers3, Search, ShieldAlert, SlidersHorizontal, UserRound, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsLineChart from '@/components/reports/ReportsLineChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useStoredAuthMeta } from '@/composables/useStoredAuthMeta.js'
import { downloadEventSanctionsExport } from '@/services/backendApi.js'
import {
  getAttendanceOverview,
  getAuditLogs,
  getEventAttendanceRecords,
  getEventAttendanceReport as fetchEventReport,
  getSanctionsDashboard as fetchSanctionsDashboard,
  getImportReports,
  getNotificationLogs,
  getReportDepartments,
  getReportEvents,
  getSchoolSummary,
  getStudentReport,
  getStudentStats,
} from '@/services/reportService.js'
import { filterWorkspaceEntitiesBySchool } from '@/services/workspaceScope.js'

defineProps({ preview: { type: Boolean, default: false } })

const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const authMeta = useStoredAuthMeta()
const {
  currentUser,
  schoolSettings,
  apiBaseUrl,
  initializeDashboardSession,
  refreshSchoolSettings,
} = useDashboardSession()

const tabs = [
  { id: 'event', label: 'Event Reports', icon: BarChart3 },
  { id: 'student', label: 'Student Reports', icon: UserRound },
  { id: 'school', label: 'School Summary', icon: Building2 },
  { id: 'insights', label: 'Additional Reports', icon: Layers3 },
  { id: 'compliance', label: 'Compliance', icon: ShieldAlert },
  { id: 'system', label: 'System Logs', icon: FileText },
]
const validTabs = new Set(tabs.map((tab) => tab.id))
const activeTab = ref('event')

const filters = reactive({
  startDate: '',
  endDate: '',
  eventId: '',
  studentId: '',
  departmentId: '',
})

const searchQuery = ref('')
const attendeeQuery = ref('')
const studentRecordQuery = ref('')
const studentLoginQuery = ref('')

const events = ref([])
const departments = ref([])
const selectedEventId = ref(null)
const selectedEventReport = ref(null)
const selectedEventRecords = ref([])
const eventCache = new Map()

const isLoadingEvents = ref(true)
const isLoadingSelection = ref(false)
const isDownloading = ref('')
const selectionError = ref('')

const overviewRows = ref([])
const studentReport = ref(null)
const studentStats = ref(null)
const schoolSummary = ref(null)
const auditLogs = ref({ total: 0, items: [] })
const notificationLogs = ref([])
const importReport = ref(null)
const sanctionsSummary = ref(null)

const isLoadingOverview = ref(false)
const isLoadingSchoolSummary = ref(false)
const isLoadingSystemLogs = ref(false)
const isLoadingImport = ref(false)
const isLoadingSanctionsSummary = ref(false)

const attendanceOverviewError = ref('')
const schoolSummaryError = ref('')
const systemLogsError = ref('')
const importError = ref('')
const sanctionsSummaryError = ref('')

const importJobId = ref('')
const importPreviewToken = ref('')
const isMobileViewport = ref(false)
const mobileFiltersOpen = ref(false)
const insightControls = reactive({
  atRiskThreshold: 75,
  minimumEvents: 3,
  declineThreshold: 10,
})
const comparisonCurrentRows = ref([])
const comparisonPreviousRows = ref([])
const isLoadingInsightComparisons = ref(false)
const insightComparisonError = ref('')

let mobileMediaQuery = null

const activeUser = computed(() => currentUser.value)
const activeSchoolSettings = computed(() => schoolSettings.value)
const schoolId = computed(() => Number(activeUser.value?.school_id ?? activeSchoolSettings.value?.school_id ?? authMeta.value?.schoolId))
const displayName = computed(() => {
  const first = activeUser.value?.first_name || authMeta.value?.firstName || ''
  const middle = activeUser.value?.middle_name || ''
  const last = activeUser.value?.last_name || authMeta.value?.lastName || ''
  return [first, middle, last].filter(Boolean).join(' ') || activeUser.value?.email?.split('@')[0] || 'Campus Admin'
})
const initials = computed(() => {
  const parts = String(displayName.value || '').split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return String(displayName.value || '').slice(0, 2).toUpperCase()
})
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')

const scopedEvents = computed(() => filterWorkspaceEntitiesBySchool(events.value, schoolId.value))
const scopedDepartments = computed(() => filterWorkspaceEntitiesBySchool(departments.value, schoolId.value))

const eventFilterOptions = computed(() => [...scopedEvents.value].sort((a, b) => new Date(b.start_datetime || 0) - new Date(a.start_datetime || 0)))
const studentFilterOptions = computed(() => [...overviewRows.value].sort((a, b) => String(a.full_name || '').localeCompare(String(b.full_name || ''))))
const departmentFilterOptions = computed(() => [...scopedDepartments.value].sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''))))

const filteredEvents = computed(() => {
  const query = String(searchQuery.value || '').trim().toLowerCase()
  const start = parseDateInput(filters.startDate)
  const end = parseDateInput(filters.endDate)
  return eventFilterOptions.value
    .filter((event) => isDateInRange(event.start_datetime, start, end))
    .filter((event) => {
      if (!query) return true
      return [event.name, event.location].filter(Boolean).join(' ').toLowerCase().includes(query)
    })
})

const selectedEvent = computed(() => scopedEvents.value.find((event) => Number(event.id) === Number(selectedEventId.value)) || null)

const selectedEventAttendanceRows = computed(() => buildEventAttendanceRows(selectedEventRecords.value))

const filteredAttendanceRows = computed(() => {
  const query = String(attendeeQuery.value || '').trim().toLowerCase()
  if (!query) return selectedEventAttendanceRows.value
  return selectedEventAttendanceRows.value.filter((row) => [row.studentId, row.studentName, row.statusLabel, row.methodLabel].join(' ').toLowerCase().includes(query))
})

const filteredStudentRecords = computed(() => {
  const rows = Array.isArray(studentReport.value?.attendance_records) ? studentReport.value.attendance_records : []
  const query = String(studentRecordQuery.value || '').trim().toLowerCase()
  if (!query) return rows
  return rows.filter((record) => [record.event_name, record.status, record.display_status, record.method].filter(Boolean).join(' ').toLowerCase().includes(query))
})

const schoolSummaryPayload = computed(() => schoolSummary.value?.summary || null)
const studentLoginRows = computed(() => {
  const rows = Array.isArray(schoolSummary.value?.student_login_rows) ? schoolSummary.value.student_login_rows : []
  return rows.map((row) => buildStudentLoginRow(row))
})
const studentLoginSummary = computed(() => {
  const summary = schoolSummary.value?.student_login_summary || {}
  const totalStudents = toWholeNumber(summary.total_students ?? studentLoginRows.value.length)
  const loggedInStudents = clampWholeNumber(
    summary.logged_in_students ?? studentLoginRows.value.filter((row) => row.has_logged_in).length,
    0,
    totalStudents,
  )
  const notLoggedInStudents = clampWholeNumber(
    summary.not_logged_in_students ?? Math.max(totalStudents - loggedInStudents, 0),
    0,
    totalStudents,
  )
  const loginCoverageRate = readFiniteNumber(summary.login_coverage_rate)

  return {
    total_students: totalStudents,
    logged_in_students: loggedInStudents,
    not_logged_in_students: notLoggedInStudents,
    login_coverage_rate: loginCoverageRate != null
      ? loginCoverageRate
      : (totalStudents > 0 ? (loggedInStudents / totalStudents) * 100 : 0),
  }
})
const studentLoginWindowLabel = computed(() => {
  if (!filters.startDate && !filters.endDate) {
    return 'Successful student logins across all recorded login history in the current school scope.'
  }

  const startLabel = filters.startDate ? formatDate(filters.startDate) : 'the beginning of recorded history'
  const endLabel = filters.endDate ? formatDate(filters.endDate) : 'today'
  return `Successful student logins from ${startLabel} to ${endLabel}.`
})

const eventSummaryCards = computed(() => {
  const report = selectedEventReport.value
  if (!report) return []
  return [
    { id: 'participants', label: 'Total Participants', value: formatWhole(report.total_participants), meta: 'Students in event scope.' },
    { id: 'attendees', label: 'Attended', value: formatWhole(report.attendees), meta: 'Completed attendance rows.' },
    { id: 'late', label: 'Late', value: formatWhole(report.late_attendees), meta: 'Late attendees.' },
    { id: 'incomplete', label: 'Waiting', value: formatWhole(report.incomplete_attendees), meta: 'Waiting for sign-out.' },
    { id: 'absent', label: 'Absent', value: formatWhole(report.absentees), meta: 'Absent records.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(report.attendance_rate)}%`, meta: 'Attended vs participants.' },
  ]
})

const studentSummaryCards = computed(() => {
  const summary = studentReport.value?.student
  if (!summary) return []
  return [
    { id: 'total', label: 'Total Events', value: formatWhole(summary.total_events), meta: 'Events in selected range.' },
    { id: 'attended', label: 'Attended', value: formatWhole(summary.attended_events), meta: 'Present + late.' },
    { id: 'late', label: 'Late', value: formatWhole(summary.late_events), meta: 'Late records.' },
    { id: 'absent', label: 'Absent', value: formatWhole(summary.absent_events), meta: 'Absent records.' },
    { id: 'excused', label: 'Excused', value: formatWhole(summary.excused_events), meta: 'Excused records.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(summary.attendance_rate)}%`, meta: 'Attended vs total.' },
  ]
})

const schoolSummaryCards = computed(() => {
  const summary = schoolSummaryPayload.value
  if (!summary) return []
  return [
    { id: 'total', label: 'Total Records', value: formatWhole(summary.total_attendance_records), meta: 'Attendance rows.' },
    { id: 'attended', label: 'Attended', value: formatWhole(summary.attended_count), meta: 'Present + late rows.' },
    { id: 'rate', label: 'Attendance Rate', value: `${formatPercent(summary.attendance_rate)}%`, meta: 'Attended vs total.' },
    { id: 'students', label: 'Unique Students', value: formatWhole(summary.unique_students), meta: 'Distinct students.' },
    { id: 'events', label: 'Unique Events', value: formatWhole(summary.unique_events), meta: 'Distinct events.' },
    { id: 'excused', label: 'Excused', value: formatWhole(summary.excused_count), meta: 'Excused rows.' },
  ]
})
const studentLoginCards = computed(() => {
  const summary = studentLoginSummary.value
  return [
    { id: 'scope', label: 'Students In Scope', value: formatWhole(summary.total_students), meta: 'Student accounts covered by the current report filters.' },
    { id: 'logged-in', label: 'Logged In', value: formatWhole(summary.logged_in_students), meta: 'Students with at least one successful login in this report window.' },
    { id: 'not-logged-in', label: 'No Login Yet', value: formatWhole(summary.not_logged_in_students), meta: 'Students without a successful login in this report window.' },
    { id: 'coverage', label: 'Login Coverage', value: `${formatPercent(summary.login_coverage_rate)}%`, meta: 'Successful-login coverage across the scoped student roster.' },
  ]
})

const overviewAnalyticsRows = computed(() => (Array.isArray(overviewRows.value) ? overviewRows.value : []).map((row) => buildOverviewAnalyticsRow(row)))
const comparisonCurrentAnalyticsRows = computed(() => (Array.isArray(comparisonCurrentRows.value) ? comparisonCurrentRows.value : []).map((row) => buildOverviewAnalyticsRow(row)))
const comparisonPreviousAnalyticsRows = computed(() => (Array.isArray(comparisonPreviousRows.value) ? comparisonPreviousRows.value : []).map((row) => buildOverviewAnalyticsRow(row)))
const insightComparisonWindow = computed(() => buildComparisonWindow(filters.startDate, filters.endDate))
const insightComparisonSummary = computed(() => {
  const window = insightComparisonWindow.value
  return `${formatDate(window.current.start)} to ${formatDate(window.current.end)} compared with ${formatDate(window.previous.start)} to ${formatDate(window.previous.end)}`
})
const overviewLookup = computed(() => {
  const lookup = new Map()
  for (const row of overviewAnalyticsRows.value) {
    if (row.id) lookup.set(`profile:${row.id}`, row)
    if (row.student_id) lookup.set(`student:${normalizeLookupKey(row.student_id)}`, row)
    if (row.full_name) lookup.set(`name:${normalizeLookupKey(row.full_name)}`, row)
  }
  return lookup
})
const overviewTotals = computed(() => overviewAnalyticsRows.value.reduce((accumulator, row) => {
  accumulator.totalEvents += row.total_events
  accumulator.attended += row.attended_events
  accumulator.late += row.late_events
  accumulator.absent += row.absent_events
  accumulator.incomplete += row.incomplete_events
  accumulator.excused += row.excused_events
  return accumulator
}, {
  totalEvents: 0,
  attended: 0,
  late: 0,
  absent: 0,
  incomplete: 0,
  excused: 0,
}))
const schoolKpiCards = computed(() => {
  const totals = overviewTotals.value
  const denominator = totals.totalEvents || 0
  const uniqueStudents = Number(schoolSummaryPayload.value?.unique_students ?? overviewAnalyticsRows.value.length)
  const uniqueEvents = Number(schoolSummaryPayload.value?.unique_events ?? 0)
  return [
    { id: 'attendance-rate', label: 'Attendance Rate', value: `${formatPercent(denominator > 0 ? (totals.attended / denominator) * 100 : 0)}%`, meta: 'Valid attended events across the filtered student scope.' },
    { id: 'late-rate', label: 'Late Rate', value: `${formatPercent(denominator > 0 ? (totals.late / denominator) * 100 : 0)}%`, meta: 'Late events as a share of tracked events.' },
    { id: 'absent-rate', label: 'Absent Rate', value: `${formatPercent(denominator > 0 ? (totals.absent / denominator) * 100 : 0)}%`, meta: 'Absent events inside the selected report scope.' },
    { id: 'incomplete-rate', label: 'Incomplete Rate', value: `${formatPercent(denominator > 0 ? (totals.incomplete / denominator) * 100 : 0)}%`, meta: 'Open or unfinished attendance records.' },
    { id: 'reach', label: 'Participation Reach', value: formatWhole(uniqueStudents), meta: 'Students covered by the current report filters.' },
    { id: 'events', label: 'Event Coverage', value: formatWhole(uniqueEvents), meta: 'Distinct events contributing to these KPIs.' },
  ]
})
const atRiskRows = computed(() => {
  const threshold = Number(insightControls.atRiskThreshold || 0)
  const minimumEvents = Number(insightControls.minimumEvents || 0)
  return overviewAnalyticsRows.value
    .filter((row) => row.total_events >= minimumEvents && row.attendance_rate < threshold)
    .sort((a, b) => {
      if (a.attendance_rate !== b.attendance_rate) return a.attendance_rate - b.attendance_rate
      if (a.absent_events !== b.absent_events) return b.absent_events - a.absent_events
      return String(a.full_name || '').localeCompare(String(b.full_name || ''))
    })
    .slice(0, 12)
})
const topAbsenteesRows = computed(() => overviewAnalyticsRows.value
  .filter((row) => row.total_events > 0)
  .sort((a, b) => {
    if (a.absent_events !== b.absent_events) return b.absent_events - a.absent_events
    if (a.absence_rate !== b.absence_rate) return b.absence_rate - a.absence_rate
    return a.attendance_rate - b.attendance_rate
  })
  .slice(0, 10))
const topLateRows = computed(() => overviewAnalyticsRows.value
  .filter((row) => row.total_events > 0)
  .sort((a, b) => {
    if (a.late_events !== b.late_events) return b.late_events - a.late_events
    if (a.late_rate !== b.late_rate) return b.late_rate - a.late_rate
    return a.attendance_rate - b.attendance_rate
  })
  .slice(0, 10))
const attendanceLeaderboardRows = computed(() => overviewAnalyticsRows.value
  .filter((row) => row.total_events >= Number(insightControls.minimumEvents || 0))
  .sort((a, b) => {
    if (a.attendance_rate !== b.attendance_rate) return b.attendance_rate - a.attendance_rate
    if (a.total_events !== b.total_events) return b.total_events - a.total_events
    return a.late_events - b.late_events
  })
  .slice(0, 10))
const yearLevelRows = computed(() => {
  const buckets = new Map()
  for (const row of overviewAnalyticsRows.value) {
    const key = row.year_level == null ? 'Unspecified' : `Year ${row.year_level}`
    if (!buckets.has(key)) {
      buckets.set(key, {
        label: key,
        studentCount: 0,
        totalEvents: 0,
        attended: 0,
        late: 0,
        absent: 0,
        incomplete: 0,
        excused: 0,
        sortOrder: row.year_level == null ? Number.POSITIVE_INFINITY : Number(row.year_level),
      })
    }
    const bucket = buckets.get(key)
    bucket.studentCount += 1
    bucket.totalEvents += row.total_events
    bucket.attended += row.attended_events
    bucket.late += row.late_events
    bucket.absent += row.absent_events
    bucket.incomplete += row.incomplete_events
    bucket.excused += row.excused_events
  }

  return Array.from(buckets.values())
    .map((bucket) => ({
      ...bucket,
      attendanceRate: bucket.totalEvents > 0 ? (bucket.attended / bucket.totalEvents) * 100 : 0,
    }))
    .sort((a, b) => a.sortOrder - b.sortOrder)
})
const yearLevelChartData = computed(() => ({
  labels: yearLevelRows.value.map((row) => row.label),
  datasets: [{ label: 'Attendance Rate (%)', data: yearLevelRows.value.map((row) => roundPercent(row.attendanceRate)), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))
const repeatParticipationRows = computed(() => {
  const ranges = [
    { id: 'once', label: '1 event', min: 1, max: 1 },
    { id: 'few', label: '2-3 events', min: 2, max: 3 },
    { id: 'steady', label: '4-6 events', min: 4, max: 6 },
    { id: 'engaged', label: '7+ events', min: 7, max: Number.POSITIVE_INFINITY },
  ]

  return ranges.map((range) => {
    const matchedRows = overviewAnalyticsRows.value.filter((row) => row.total_events >= range.min && row.total_events <= range.max)
    const totalStudents = matchedRows.length
    const totalEvents = matchedRows.reduce((sum, row) => sum + row.total_events, 0)
    return {
      ...range,
      totalStudents,
      totalEvents,
      averageRate: totalStudents > 0 ? matchedRows.reduce((sum, row) => sum + row.attendance_rate, 0) / totalStudents : 0,
    }
  })
})
const repeatParticipationChartData = computed(() => ({
  labels: repeatParticipationRows.value.map((row) => row.label),
  datasets: [{ label: 'Students', data: repeatParticipationRows.value.map((row) => row.totalStudents), backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(16,185,129,0.88)', 'rgba(15,23,42,0.88)'], borderRadius: 10 }],
}))
const comparisonDeltaRows = computed(() => {
  const currentRows = new Map(comparisonCurrentAnalyticsRows.value.map((row) => [String(row.id), row]))
  const previousRows = new Map(comparisonPreviousAnalyticsRows.value.map((row) => [String(row.id), row]))
  const keys = new Set([...currentRows.keys(), ...previousRows.keys()])
  const minimumEvents = Number(insightControls.minimumEvents || 0)
  const rows = []

  for (const key of keys) {
    const current = currentRows.get(key) || null
    const previous = previousRows.get(key) || null
    const totalEvents = Math.max(Number(current?.total_events || 0), Number(previous?.total_events || 0))
    if (totalEvents < minimumEvents) continue

    const currentRate = Number(current?.attendance_rate || 0)
    const previousRate = Number(previous?.attendance_rate || 0)
    rows.push({
      id: Number(current?.id ?? previous?.id ?? 0),
      student_id: current?.student_id || previous?.student_id || null,
      full_name: current?.full_name || previous?.full_name || 'Unknown Student',
      department_name: current?.department_name || previous?.department_name || null,
      program_name: current?.program_name || previous?.program_name || null,
      currentRate,
      previousRate,
      currentEvents: Number(current?.total_events || 0),
      previousEvents: Number(previous?.total_events || 0),
      delta: roundToTwo(currentRate - previousRate),
    })
  }

  return rows.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
})
const recoveryRows = computed(() => comparisonDeltaRows.value.filter((row) => row.delta > 0).sort((a, b) => b.delta - a.delta).slice(0, 10))
const declineRows = computed(() => comparisonDeltaRows.value.filter((row) => row.delta <= -Number(insightControls.declineThreshold || 0)).sort((a, b) => a.delta - b.delta).slice(0, 10))
const eventInsightRows = computed(() => filteredEvents.value.map((event) => {
  const cachedReport = eventCache.get(Number(event.id))?.report || null
  const liveReport = Number(event.id) === Number(selectedEventId.value) ? selectedEventReport.value : null
  const report = liveReport || cachedReport
  const summary = event?.attendance_summary && typeof event.attendance_summary === 'object' ? event.attendance_summary : {}
  const total = toWholeNumber(report?.total_participants ?? summary.total_attendance_records ?? 0)
  const late = toWholeNumber(report?.late_attendees ?? summary.late_count ?? 0)
  const absent = toWholeNumber(report?.absentees ?? summary.absent_count ?? 0)
  const excused = toWholeNumber(report?.excused_attendees ?? summary.excused_count ?? 0)
  const attended = toWholeNumber(report?.attendees ?? summary.attended_count ?? (toWholeNumber(summary.present_count ?? 0) + late))
  const incomplete = toWholeNumber(report?.incomplete_attendees ?? 0)
  return {
    id: Number(event.id || 0),
    name: event.name,
    date: event.start_datetime,
    status: String(event.status || 'upcoming').toLowerCase(),
    total,
    attended,
    late,
    absent,
    excused,
    incomplete,
    attendanceRate: total > 0 ? (attended / total) * 100 : 0,
    noShowRate: total > 0 ? (absent / total) * 100 : 0,
    lateRate: total > 0 ? (late / total) * 100 : 0,
    incompleteRate: total > 0 ? (incomplete / total) * 100 : 0,
    weekday: getWeekdayLabel(event.start_datetime),
    timeBlock: getTimeBlockLabel(event.start_datetime),
  }
}))
const noShowEventRows = computed(() => eventInsightRows.value
  .filter((row) => row.total > 0)
  .sort((a, b) => {
    if (a.noShowRate !== b.noShowRate) return b.noShowRate - a.noShowRate
    return b.absent - a.absent
  })
  .slice(0, 10))
const attendanceByWeekdayRows = computed(() => {
  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  const buckets = new Map(weekdays.map((label) => [label, { label, total: 0, attended: 0, late: 0, absent: 0 }]))
  for (const row of eventInsightRows.value) {
    const bucket = buckets.get(row.weekday)
    if (!bucket) continue
    bucket.total += row.total
    bucket.attended += row.attended
    bucket.late += row.late
    bucket.absent += row.absent
  }
  return weekdays.map((label) => {
    const bucket = buckets.get(label)
    return {
      ...bucket,
      attendanceRate: bucket.total > 0 ? (bucket.attended / bucket.total) * 100 : 0,
    }
  })
})
const attendanceByWeekdayChartData = computed(() => ({
  labels: attendanceByWeekdayRows.value.map((row) => row.label),
  datasets: [{ label: 'Attendance Rate (%)', data: attendanceByWeekdayRows.value.map((row) => roundPercent(row.attendanceRate)), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))
const attendanceByTimeBlockRows = computed(() => {
  const blocks = ['Before 8 AM', '8 AM - 12 PM', '12 PM - 4 PM', '4 PM and later']
  const buckets = new Map(blocks.map((label) => [label, { label, late: 0, total: 0, attended: 0 }]))
  for (const row of eventInsightRows.value) {
    const bucket = buckets.get(row.timeBlock)
    if (!bucket) continue
    bucket.late += row.late
    bucket.total += row.total
    bucket.attended += row.attended
  }
  return blocks.map((label) => {
    const bucket = buckets.get(label)
    return {
      ...bucket,
      lateRate: bucket.total > 0 ? (bucket.late / bucket.total) * 100 : 0,
    }
  })
})
const attendanceByTimeBlockChartData = computed(() => ({
  labels: attendanceByTimeBlockRows.value.map((row) => row.label),
  datasets: [{ label: 'Late Count', data: attendanceByTimeBlockRows.value.map((row) => row.late), backgroundColor: 'rgba(245,158,11,0.88)', borderRadius: 10 }],
}))
const eventOutcomeSummary = computed(() => {
  const counts = { completed: 0, cancelled: 0, ongoing: 0, upcoming: 0 }
  for (const event of filteredEvents.value) {
    const status = String(event?.status || '').toLowerCase()
    if (Object.hasOwn(counts, status)) counts[status] += 1
  }
  const trackedClosed = counts.completed + counts.cancelled
  return {
    ...counts,
    completionRate: trackedClosed > 0 ? (counts.completed / trackedClosed) * 100 : 0,
    cancellationRate: trackedClosed > 0 ? (counts.cancelled / trackedClosed) * 100 : 0,
  }
})
const eventOutcomeChartData = computed(() => ({
  labels: ['Completed', 'Cancelled', 'Open / Upcoming'],
  datasets: [{ data: [eventOutcomeSummary.value.completed, eventOutcomeSummary.value.cancelled, eventOutcomeSummary.value.ongoing + eventOutcomeSummary.value.upcoming], backgroundColor: ['rgba(16,185,129,0.88)', 'rgba(239,68,68,0.88)', 'rgba(0,87,184,0.88)'], borderWidth: 0 }],
}))
const firstTimeVsRepeatSummary = computed(() => {
  const summary = { firstTime: 0, repeat: 0, unmatched: 0, attendees: 0 }
  for (const row of selectedEventAttendanceRows.value) {
    if (row.status === 'absent') continue
    summary.attendees += 1
    const matchedOverview = overviewLookup.value.get(`student:${normalizeLookupKey(row.studentId)}`) || overviewLookup.value.get(`name:${normalizeLookupKey(row.studentName)}`) || null
    if (!matchedOverview) {
      summary.unmatched += 1
      continue
    }
    if (matchedOverview.total_events <= 1) summary.firstTime += 1
    else summary.repeat += 1
  }
  return {
    ...summary,
    firstTimeRate: summary.attendees > 0 ? (summary.firstTime / summary.attendees) * 100 : 0,
    repeatRate: summary.attendees > 0 ? (summary.repeat / summary.attendees) * 100 : 0,
  }
})
const firstTimeVsRepeatChartData = computed(() => ({
  labels: ['First-Time', 'Repeat'],
  datasets: [{ data: [firstTimeVsRepeatSummary.value.firstTime, firstTimeVsRepeatSummary.value.repeat], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)'], borderWidth: 0 }],
}))
const selectedEventExecutionCards = computed(() => {
  const report = selectedEventReport.value
  if (!report) return []
  const total = Number(report.total_participants || 0)
  return [
    { id: 'selected-no-show', label: 'No-Show Rate', value: `${formatPercent(total > 0 ? (Number(report.absentees || 0) / total) * 100 : 0)}%`, meta: 'Absences for the selected event.' },
    { id: 'selected-late', label: 'Late Burden', value: `${formatPercent(total > 0 ? (Number(report.late_attendees || 0) / total) * 100 : 0)}%`, meta: 'Late attendees as a share of participants.' },
    { id: 'selected-waiting', label: 'Incomplete Rate', value: `${formatPercent(total > 0 ? (Number(report.incomplete_attendees || 0) / total) * 100 : 0)}%`, meta: 'Students still waiting for sign-out.' },
    { id: 'selected-attendance', label: 'Attendance Rate', value: `${formatPercent(report.attendance_rate || 0)}%`, meta: 'Completed attended rows vs participants.' },
  ]
})
const insightSummaryCards = computed(() => {
  const totals = overviewTotals.value
  const denominator = totals.totalEvents || 0
  const atRiskCount = atRiskRows.value.length
  const declineCount = declineRows.value.length
  const flaggedNoShowEvents = noShowEventRows.value.filter((row) => row.noShowRate >= 25).length
  const repeatEngagement = repeatParticipationRows.value.find((row) => row.id === 'engaged')?.totalStudents || 0
  return [
    { id: 'risk-count', label: 'At-Risk Students', value: formatWhole(atRiskCount), meta: `Below ${formatWhole(insightControls.atRiskThreshold)}% with ${formatWhole(insightControls.minimumEvents)}+ events.` },
    { id: 'decline-count', label: 'Decline Alerts', value: formatWhole(declineCount), meta: `Drop of ${formatWhole(insightControls.declineThreshold)} points or more.` },
    { id: 'avg-rate', label: 'Average Attendance', value: `${formatPercent(denominator > 0 ? (totals.attended / denominator) * 100 : 0)}%`, meta: 'Current filtered overview performance.' },
    { id: 'late-cases', label: 'Late Cases', value: formatWhole(totals.late), meta: 'Late events across students in scope.' },
    { id: 'no-show-events', label: 'No-Show Events', value: formatWhole(flaggedNoShowEvents), meta: 'Events with at least 25% no-show rate.' },
    { id: 'repeat-engagement', label: 'Deep Engagement', value: formatWhole(repeatEngagement), meta: 'Students with seven or more tracked events.' },
  ]
})
const topStudentsRows = computed(() => [...overviewAnalyticsRows.value].sort((a, b) => Number(b.attendance_rate || 0) - Number(a.attendance_rate || 0)).slice(0, 20))
const filteredStudentLoginRows = computed(() => {
  const query = String(studentLoginQuery.value || '').trim().toLowerCase()
  const rows = [...studentLoginRows.value].sort((a, b) => {
    if (a.has_logged_in !== b.has_logged_in) return Number(a.has_logged_in) - Number(b.has_logged_in)
    const loginDelta = new Date(b.last_login_at || 0).getTime() - new Date(a.last_login_at || 0).getTime()
    if (Number.isFinite(loginDelta) && loginDelta !== 0) return loginDelta
    return String(a.full_name || '').localeCompare(String(b.full_name || ''))
  })
  if (!query) return rows
  return rows.filter((row) => [
    row.student_id,
    row.full_name,
    row.department_name,
    row.program_name,
    row.status_label,
  ].filter(Boolean).join(' ').toLowerCase().includes(query))
})
const auditRows = computed(() => Array.isArray(auditLogs.value?.items) ? auditLogs.value.items : [])
const notificationRows = computed(() => Array.isArray(notificationLogs.value) ? notificationLogs.value : [])
const importErrors = computed(() => Array.isArray(importReport.value?.jobStatus?.errors) ? importReport.value.jobStatus.errors : [])
const complianceEventRows = computed(() => {
  const rows = Array.isArray(sanctionsSummary.value?.events) ? sanctionsSummary.value.events : []
  return [...rows].sort((a, b) => {
    if (Number(a.pending_sanctions || 0) !== Number(b.pending_sanctions || 0)) return Number(b.pending_sanctions || 0) - Number(a.pending_sanctions || 0)
    if (Number(a.absent_count || 0) !== Number(b.absent_count || 0)) return Number(b.absent_count || 0) - Number(a.absent_count || 0)
    return Number(b.absence_rate_percent || 0) - Number(a.absence_rate_percent || 0)
  })
})
const selectedComplianceEvent = computed(() => {
  const selectedId = Number(selectedEventId.value)
  if (!Number.isFinite(selectedId)) return complianceEventRows.value[0] || null
  return complianceEventRows.value.find((row) => Number(row.event_id) === selectedId) || complianceEventRows.value[0] || null
})
const complianceSummaryCards = computed(() => {
  const summary = sanctionsSummary.value || {}
  const totalEvents = Number(summary.total_events || complianceEventRows.value.length || 0)
  const totalParticipants = Number(summary.total_participants || 0)
  const totalAbsent = Number(summary.total_absent || 0)
  const pending = Number(summary.total_pending_sanctions || 0)
  const complied = Number(summary.total_complied_sanctions || 0)
  const absenceRate = Number(summary.overall_absence_rate_percent || 0)
  return [
    { id: 'compliance-events', label: 'Sanctioned Events', value: formatWhole(totalEvents), meta: 'Events that currently contribute to sanctions reporting.' },
    { id: 'compliance-participants', label: 'Tracked Participants', value: formatWhole(totalParticipants), meta: 'Participants covered by the sanctions dashboard.' },
    { id: 'compliance-absent', label: 'Absent Students', value: formatWhole(totalAbsent), meta: 'Absences that can trigger sanction workflows.' },
    { id: 'compliance-pending', label: 'Pending Sanctions', value: formatWhole(pending), meta: 'Issued sanctions still waiting for compliance.' },
    { id: 'compliance-complied', label: 'Complied Sanctions', value: formatWhole(complied), meta: 'Resolved sanction records across the current school scope.' },
    { id: 'compliance-rate', label: 'Overall Absence Rate', value: `${formatPercent(absenceRate)}%`, meta: 'School-wide absence share across sanction-reporting events.' },
  ]
})
const complianceStatusChartData = computed(() => {
  const summary = sanctionsSummary.value || {}
  const pending = Number(summary.total_pending_sanctions || 0)
  const complied = Number(summary.total_complied_sanctions || 0)
  if (pending <= 0 && complied <= 0) return { labels: [], datasets: [] }
  return {
    labels: ['Pending', 'Complied'],
    datasets: [{ data: [pending, complied], backgroundColor: ['rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})
const complianceLoadChartData = computed(() => {
  const rows = complianceEventRows.value.slice(0, 8)
  if (!rows.length) return { labels: [], datasets: [] }
  return {
    labels: rows.map((row) => row.event_name),
    datasets: [{ label: 'Pending Sanctions', data: rows.map((row) => Number(row.pending_sanctions || 0)), backgroundColor: 'rgba(239,68,68,0.88)', borderRadius: 10 }],
  }
})

const eventChartRows = computed(() => filteredEvents.value.slice(0, 10).map((event) => {
  const report = eventCache.get(Number(event.id))?.report
  const summary = event.attendance_summary || {}
  return {
    name: event.name,
    date: event.start_datetime,
    total: Number(report?.total_participants ?? summary.total_attendance_records ?? 0),
    attended: Number(report?.attendees ?? summary.attended_count ?? summary.present_count ?? 0),
    late: Number(report?.late_attendees ?? summary.late_count ?? 0),
    absent: Number(report?.absentees ?? summary.absent_count ?? 0),
    excused: Number(summary.excused_count ?? 0),
  }
}))

const eventBarChartData = computed(() => ({
  labels: eventChartRows.value.map((row) => row.name),
  datasets: [{ label: 'Attended', data: eventChartRows.value.map((row) => row.attended), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))

const eventPieChartData = computed(() => {
  const report = selectedEventReport.value
  if (!report) return { labels: [], datasets: [] }
  const late = Number(report.late_attendees || 0)
  const absent = Number(report.absentees || 0)
  const present = Math.max(Number(report.attendees || 0) - late, 0)
  const excused = Number(report.excused_attendees || 0)
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [present, late, absent, excused], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})

const eventLineChartData = computed(() => buildMonthlyLineData(eventChartRows.value))
const schoolLineChartData = computed(() => buildMonthlyLineData(eventChartRows.value))

const studentPieChartData = computed(() => {
  const summary = studentReport.value?.student
  if (!summary) return { labels: [], datasets: [] }
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [Number(summary.attended_events || 0) - Number(summary.late_events || 0), Number(summary.late_events || 0), Number(summary.absent_events || 0), Number(summary.excused_events || 0)], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})

const studentLineChartData = computed(() => buildStudentTrendLineData(studentStats.value?.trend_data))

const schoolPieChartData = computed(() => {
  const summary = schoolSummaryPayload.value
  if (!summary) return { labels: [], datasets: [] }
  return {
    labels: ['Present', 'Late', 'Absent', 'Excused'],
    datasets: [{ data: [Number(summary.present_count || 0), Number(summary.late_count || 0), Number(summary.absent_count || 0), Number(summary.excused_count || 0)], backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(245,158,11,0.88)', 'rgba(239,68,68,0.88)', 'rgba(16,185,129,0.88)'], borderWidth: 0 }],
  }
})
const studentLoginPieChartData = computed(() => {
  const summary = studentLoginSummary.value
  if (summary.total_students <= 0) return { labels: [], datasets: [] }
  return {
    labels: ['Logged In', 'No Login Recorded'],
    datasets: [{
      data: [summary.logged_in_students, summary.not_logged_in_students],
      backgroundColor: ['rgba(0,87,184,0.88)', 'rgba(148,163,184,0.88)'],
      borderWidth: 0,
    }],
  }
})

const schoolBarChartData = computed(() => ({
  labels: topStudentsRows.value.slice(0, 8).map((row) => row.full_name),
  datasets: [{ label: 'Attendance Rate (%)', data: topStudentsRows.value.slice(0, 8).map((row) => roundPercent(row.attendance_rate)), backgroundColor: 'rgba(0,87,184,0.88)', borderRadius: 10 }],
}))

const chartOptions = {
  pie: { plugins: { legend: { position: 'bottom' } } },
  line: { scales: { y: { beginAtZero: true } } },
  bar: { scales: { y: { beginAtZero: true } } },
  barPercent: { scales: { y: { beginAtZero: true, max: 100 } } },
}

let selectionRequestId = 0
let overviewRequestId = 0
let studentRequestId = 0
let summaryRequestId = 0
let logsRequestId = 0
let insightComparisonRequestId = 0

onMounted(async () => {
  initializeMobileLayout()
  await initializeDashboardSession().catch(() => null)
  if (!schoolSettings.value) await refreshSchoolSettings().catch(() => null)
  applyTabFromRoute()
  await Promise.all([loadEvents(), loadDepartments(), loadAttendanceOverview(), loadSchoolSummary(), loadSystemLogs(), loadInsightComparisons(), loadSanctionsSummary()])
  await syncEventFromRoute()
})

onBeforeUnmount(() => {
  teardownMobileLayout()
})

watch(() => route.query.section, () => applyTabFromRoute(), { immediate: true })
watch([() => route.query.eventId, scopedEvents, isLoadingEvents], () => { syncEventFromRoute().catch(() => null) }, { immediate: true })
watch(() => filters.eventId, () => { handleEventFilterChange().catch(() => null) })
watch(() => filters.studentId, () => { loadStudentReport().catch(() => null) })
watch(() => [filters.startDate, filters.endDate, filters.departmentId], () => {
  loadAttendanceOverview().catch(() => null)
  loadSchoolSummary().catch(() => null)
  loadInsightComparisons().catch(() => null)
})
watch(filteredEvents, () => { prefetchEventReports().catch(() => null) })

function resolveApiContext() {
  return {
    token: localStorage.getItem('aura_token') || '',
    baseUrl: apiBaseUrl.value || '',
  }
}

function applyMobileViewport(matches) {
  const wasMobile = isMobileViewport.value
  isMobileViewport.value = Boolean(matches)

  if (isMobileViewport.value && !wasMobile) {
    mobileFiltersOpen.value = false
  }

  if (!isMobileViewport.value) {
    mobileFiltersOpen.value = true
  }
}

function initializeMobileLayout() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
  mobileMediaQuery = window.matchMedia('(max-width: 720px)')
  applyMobileViewport(mobileMediaQuery.matches)

  if (typeof mobileMediaQuery.addEventListener === 'function') {
    mobileMediaQuery.addEventListener('change', handleMobileViewportChange)
    return
  }

  if (typeof mobileMediaQuery.addListener === 'function') {
    mobileMediaQuery.addListener(handleMobileViewportChange)
  }
}

function teardownMobileLayout() {
  if (!mobileMediaQuery) return

  if (typeof mobileMediaQuery.removeEventListener === 'function') {
    mobileMediaQuery.removeEventListener('change', handleMobileViewportChange)
    mobileMediaQuery = null
    return
  }

  if (typeof mobileMediaQuery.removeListener === 'function') {
    mobileMediaQuery.removeListener(handleMobileViewportChange)
  }
  mobileMediaQuery = null
}

function handleMobileViewportChange(event) {
  applyMobileViewport(event?.matches)
}

function toggleMobileFilters() {
  if (!isMobileViewport.value) return
  mobileFiltersOpen.value = !mobileFiltersOpen.value
}

function applyTabFromRoute() {
  const section = String(route.query.section || '').trim().toLowerCase()
  activeTab.value = validTabs.has(section) ? section : 'event'
}

function setActiveTab(tabId) {
  if (!validTabs.has(tabId)) return
  activeTab.value = tabId
  if (String(route.query.section || '').toLowerCase() === tabId) return
  router.replace({ query: { ...route.query, section: tabId } }).catch(() => null)
}

async function loadEvents() {
  isLoadingEvents.value = true

  try {
    events.value = await getReportEvents(resolveApiContext())
  } catch (error) {
    selectionError.value = error?.message || 'Unable to load events.'
  } finally {
    isLoadingEvents.value = false
  }
}

async function prefetchEventReports() {
  const candidates = filteredEvents.value.slice(0, 8)
  if (!candidates.length) return
  await Promise.all(candidates.map(async (event) => {
    try {
      await getEventBundle(event)
    } catch {
      return null
    }
    return null
  }))
}

async function loadDepartments() {
  try {
    departments.value = await getReportDepartments(resolveApiContext())
  } catch {
    departments.value = []
  }
}

async function loadAttendanceOverview() {
  const requestId = ++overviewRequestId
  isLoadingOverview.value = true
  attendanceOverviewError.value = ''

  try {
    const rows = await getAttendanceOverview({
      ...resolveApiContext(),
      params: {
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined,
        department_id: toPositiveInt(filters.departmentId),
        limit: 250,
      },
    })

    if (requestId !== overviewRequestId) return
    overviewRows.value = Array.isArray(rows) ? rows : []

    if (filters.studentId && !overviewRows.value.some((row) => Number(row.id) === Number(filters.studentId))) {
      filters.studentId = ''
    }
    if (!filters.studentId && overviewRows.value.length) {
      filters.studentId = String(overviewRows.value[0].id)
    }
  } catch (error) {
    if (requestId !== overviewRequestId) return
    attendanceOverviewError.value = error?.message || 'Unable to load student overview.'
    overviewRows.value = []
  } finally {
    if (requestId === overviewRequestId) isLoadingOverview.value = false
  }
}

async function loadStudentReport() {
  const studentId = toPositiveInt(filters.studentId)
  if (!studentId) {
    studentReport.value = null
    studentStats.value = null
    return
  }

  const requestId = ++studentRequestId
  try {
    const payload = await Promise.all([
      getStudentReport(studentId, {
        ...resolveApiContext(),
        params: {
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
        },
      }),
      getStudentStats(studentId, {
        ...resolveApiContext(),
        params: {
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
          group_by: 'month',
        },
      }),
    ])

    if (requestId !== studentRequestId) return
    studentReport.value = payload[0]
    studentStats.value = payload[1]
  } catch {
    if (requestId !== studentRequestId) return
    studentReport.value = null
    studentStats.value = null
  }
}

async function loadSchoolSummary() {
  const requestId = ++summaryRequestId
  isLoadingSchoolSummary.value = true
  schoolSummaryError.value = ''

  try {
    const payload = await getSchoolSummary({
      ...resolveApiContext(),
      params: {
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined,
        department_id: toPositiveInt(filters.departmentId),
      },
    })

    if (requestId !== summaryRequestId) return
    schoolSummary.value = payload
  } catch (error) {
    if (requestId !== summaryRequestId) return
    schoolSummaryError.value = error?.message || 'Unable to load school summary.'
    schoolSummary.value = null
  } finally {
    if (requestId === summaryRequestId) isLoadingSchoolSummary.value = false
  }
}

async function loadInsightComparisons() {
  const requestId = ++insightComparisonRequestId
  const window = insightComparisonWindow.value
  isLoadingInsightComparisons.value = true
  insightComparisonError.value = ''

  try {
    const [currentRows, previousRows] = await Promise.all([
      getAttendanceOverview({
        ...resolveApiContext(),
        params: {
          start_date: window.current.start,
          end_date: window.current.end,
          department_id: toPositiveInt(filters.departmentId),
          limit: 250,
        },
      }),
      getAttendanceOverview({
        ...resolveApiContext(),
        params: {
          start_date: window.previous.start,
          end_date: window.previous.end,
          department_id: toPositiveInt(filters.departmentId),
          limit: 250,
        },
      }),
    ])

    if (requestId !== insightComparisonRequestId) return
    comparisonCurrentRows.value = Array.isArray(currentRows) ? currentRows : []
    comparisonPreviousRows.value = Array.isArray(previousRows) ? previousRows : []
  } catch (error) {
    if (requestId !== insightComparisonRequestId) return
    insightComparisonError.value = error?.message || 'Unable to load comparison ranges for additional reports.'
    comparisonCurrentRows.value = []
    comparisonPreviousRows.value = []
  } finally {
    if (requestId === insightComparisonRequestId) isLoadingInsightComparisons.value = false
  }
}

async function loadSystemLogs() {
  const requestId = ++logsRequestId
  isLoadingSystemLogs.value = true
  systemLogsError.value = ''

  try {
    const [auditPayload, notificationPayload] = await Promise.all([
      getAuditLogs({
        ...resolveApiContext(),
        params: {
          limit: 100,
          offset: 0,
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
        },
      }),
      getNotificationLogs({ ...resolveApiContext(), params: { limit: 150 } }),
    ])

    if (requestId !== logsRequestId) return
    auditLogs.value = auditPayload || { total: 0, items: [] }
    notificationLogs.value = Array.isArray(notificationPayload) ? notificationPayload : []
  } catch (error) {
    if (requestId !== logsRequestId) return
    systemLogsError.value = error?.message || 'Unable to load system logs.'
    auditLogs.value = { total: 0, items: [] }
    notificationLogs.value = []
  } finally {
    if (requestId === logsRequestId) isLoadingSystemLogs.value = false
  }
}

async function loadImportReport() {
  const jobId = String(importJobId.value || '').trim()
  const previewToken = String(importPreviewToken.value || '').trim()
  importError.value = ''

  if (!jobId && !previewToken) {
    importError.value = 'Enter an import job ID or preview token.'
    return
  }

  isLoadingImport.value = true
  try {
    importReport.value = await getImportReports({
      ...resolveApiContext(),
      jobId: jobId || undefined,
      previewToken: previewToken || undefined,
    })
  } catch (error) {
    importError.value = error?.message || 'Unable to load import report.'
    importReport.value = null
  } finally {
    isLoadingImport.value = false
  }
}

async function loadSanctionsSummary() {
  isLoadingSanctionsSummary.value = true
  sanctionsSummaryError.value = ''

  try {
    sanctionsSummary.value = await fetchSanctionsDashboard(resolveApiContext())
  } catch (error) {
    sanctionsSummaryError.value = error?.message || 'Unable to load sanctions dashboard.'
    sanctionsSummary.value = null
  } finally {
    isLoadingSanctionsSummary.value = false
  }
}

async function downloadSanctionsExport(row) {
  const eventId = Number(row?.event_id)
  if (!Number.isFinite(eventId)) return

  const key = `sanctions:${eventId}`
  if (isDownloading.value === key) return
  isDownloading.value = key

  try {
    const blob = await downloadEventSanctionsExport(resolveApiContext().baseUrl, resolveApiContext().token, eventId)
    triggerDownload(blob, `${sanitize(row?.event_name || `event_${eventId}_sanctions`)}.xlsx`)
  } finally {
    isDownloading.value = ''
  }
}

async function syncEventFromRoute() {
  const routeEventId = normalizeId(route.query.eventId)
  if (!routeEventId) {
    if (selectedEventId.value != null) clearSelection({ updateRoute: false })
    return
  }
  if (routeEventId === Number(selectedEventId.value) && selectedEventReport.value) return

  const event = scopedEvents.value.find((item) => Number(item.id) === routeEventId)
  if (!event) return
  filters.eventId = String(routeEventId)
  await viewEvent(event, { updateRoute: false })
}

async function handleEventFilterChange() {
  const eventId = normalizeId(filters.eventId)
  if (!eventId) {
    if (selectedEventId.value != null) clearSelection()
    return
  }
  if (eventId === Number(selectedEventId.value)) return

  const event = scopedEvents.value.find((item) => Number(item.id) === eventId)
  if (!event) return
  await viewEvent(event)
}

async function viewEvent(event, { updateRoute = true } = {}) {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) return null

  selectedEventId.value = eventId
  filters.eventId = String(eventId)
  selectionError.value = ''
  isLoadingSelection.value = true
  const requestId = ++selectionRequestId

  if (updateRoute && normalizeId(route.query.eventId) !== eventId) {
    router.replace({ query: { ...route.query, eventId: String(eventId) } }).catch(() => null)
  }

  try {
    const bundle = await getEventBundle(event)
    if (requestId !== selectionRequestId) return null
    selectedEventReport.value = bundle.report
    selectedEventRecords.value = bundle.records
    return bundle
  } catch (error) {
    if (requestId !== selectionRequestId) return null
    selectionError.value = error?.message || 'Unable to load selected event report.'
    selectedEventReport.value = null
    selectedEventRecords.value = []
    return null
  } finally {
    if (requestId === selectionRequestId) isLoadingSelection.value = false
  }
}

async function getEventBundle(event) {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) throw new Error('Invalid event')
  if (eventCache.has(eventId)) return eventCache.get(eventId)

  const bundle = await loadLiveEventBundle(eventId)

  eventCache.set(eventId, bundle)
  return bundle
}

async function loadLiveEventBundle(eventId) {
  const ctx = resolveApiContext()
  const [report, records] = await Promise.all([
    fetchEventReport(eventId, ctx),
    getEventAttendanceRecords(eventId, {
      ...ctx,
      params: {
        active_only: false,
      },
    }),
  ])
  return { report, records: Array.isArray(records) ? records : [] }
}

function clearSelection({ updateRoute = true } = {}) {
  selectedEventId.value = null
  selectedEventReport.value = null
  selectedEventRecords.value = []
  filters.eventId = ''
  attendeeQuery.value = ''

  if (updateRoute) {
    const nextQuery = { ...route.query }
    delete nextQuery.eventId
    router.replace({ query: nextQuery }).catch(() => null)
  }
}

function resetFilters() {
  filters.startDate = ''
  filters.endDate = ''
  filters.departmentId = ''
  if (selectedEventId.value != null) clearSelection()
}

async function downloadReport(event, format = 'csv') {
  const eventId = Number(event?.id)
  if (!Number.isFinite(eventId)) return

  const key = `${eventId}:${format}`
  if (isDownloading.value === key) return
  isDownloading.value = key

  try {
    const bundle = await viewEvent(event) || await getEventBundle(event)
    const rows = filteredAttendanceRows.value
    if (format === 'excel') downloadExcel(bundle.report, rows)
    else downloadCsv(bundle.report, rows)
  } finally {
    isDownloading.value = ''
  }
}

function downloadCsv(report, rows) {
  const lines = [
    ['Event', report?.event_name || 'Event'],
    ['Date', report?.event_date || 'N/A'],
    ['Location', report?.event_location || 'N/A'],
    [],
    ['Summary'],
    ['Total Participants', formatWhole(report?.total_participants || 0)],
    ['Completed Attendance', formatWhole(report?.attendees || 0)],
    ['Late Attendees', formatWhole(report?.late_attendees || 0)],
    ['Waiting for Sign Out', formatWhole(report?.incomplete_attendees || 0)],
    ['Absent', formatWhole(report?.absentees || 0)],
    ['Attendance Rate', `${formatPercent(report?.attendance_rate || 0)}%`],
    [],
    ['Student ID', 'Student Name', 'Status', 'Sign In', 'Sign Out', 'Method'],
    ...rows.map((row) => [row.studentId, row.studentName, row.statusLabel, row.timeInLabel, row.timeOutLabel, row.methodLabel]),
  ]
  const content = `\uFEFF${lines.map((line) => line.map(csvField).join(',')).join('\r\n')}`
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  triggerDownload(blob, `${sanitize(report?.event_name || 'event_report')}.csv`)
}

function downloadExcel(report, rows) {
  const html = `
    <html><head><meta charset="utf-8"></head><body>
    <h1>${escapeHtml(report?.event_name || 'Event Report')}</h1>
    <p>${escapeHtml(report?.event_date || 'N/A')} | ${escapeHtml(report?.event_location || 'N/A')}</p>
    <table border="1" cellspacing="0" cellpadding="6">
      <tr><th>Student ID</th><th>Student Name</th><th>Status</th><th>Sign In</th><th>Sign Out</th><th>Method</th></tr>
      ${rows.map((row) => `<tr><td>${escapeHtml(row.studentId)}</td><td>${escapeHtml(row.studentName)}</td><td>${escapeHtml(row.statusLabel)}</td><td>${escapeHtml(row.timeInLabel)}</td><td>${escapeHtml(row.timeOutLabel)}</td><td>${escapeHtml(row.methodLabel)}</td></tr>`).join('')}
    </table></body></html>`
  const blob = new Blob([`\uFEFF${html}`], { type: 'application/vnd.ms-excel;charset=utf-8;' })
  triggerDownload(blob, `${sanitize(report?.event_name || 'event_report')}.xls`)
}

function buildEventAttendanceRows(records) {
  const latestByStudent = new Map()

  for (const record of Array.isArray(records) ? records : []) {
    const key = String(record?.student_id || record?.student_name || record?.attendance?.student_id || '')
    const existing = latestByStudent.get(key)
    const timestamp = new Date(record?.attendance?.time_out || record?.attendance?.time_in || 0).getTime()
    const existingTimestamp = new Date(existing?.attendance?.time_out || existing?.attendance?.time_in || 0).getTime()
    if (!existing || timestamp > existingTimestamp) latestByStudent.set(key, record)
  }

  return Array.from(latestByStudent.values()).map((record) => {
    const attendance = record?.attendance || {}
    const status = resolveAttendanceStatus(attendance)
    return {
      key: `${record?.student_id || record?.student_name || 'student'}:${attendance.id || attendance.time_in || 'row'}`,
      studentId: String(record?.student_id || 'N/A'),
      studentName: String(record?.student_name || 'Unknown Student'),
      status,
      statusLabel: formatStatusLabel(status),
      timeInLabel: formatDateTime(attendance.time_in, 'N/A'),
      timeOutLabel: formatDateTime(attendance.time_out, status === 'waiting' ? 'Waiting' : 'N/A'),
      methodLabel: formatMethod(attendance.method),
    }
  })
}

function buildOverviewAnalyticsRow(row = {}) {
  const totalEvents = toWholeNumber(row?.total_events)
  const explicitAttendanceRate = readFiniteNumber(row?.attendance_rate)
  const explicitAttended = readFiniteNumber(row?.attended_events)
  const attendedEvents = clampWholeNumber(
    explicitAttended != null
      ? explicitAttended
      : ((explicitAttendanceRate || 0) / 100) * totalEvents,
    0,
    totalEvents,
  )
  const lateEvents = clampWholeNumber(row?.late_events, 0, attendedEvents)
  const incompleteEvents = clampWholeNumber(row?.incomplete_events, 0, totalEvents)
  const excusedEvents = clampWholeNumber(row?.excused_events, 0, totalEvents)
  const explicitAbsent = readFiniteNumber(row?.absent_events)
  const absentEvents = clampWholeNumber(
    explicitAbsent != null
      ? explicitAbsent
      : Math.max(totalEvents - attendedEvents - incompleteEvents - excusedEvents, 0),
    0,
    totalEvents,
  )
  const attendanceRate = explicitAttendanceRate != null
    ? explicitAttendanceRate
    : (totalEvents > 0 ? (attendedEvents / totalEvents) * 100 : 0)

  return {
    ...row,
    total_events: totalEvents,
    attended_events: attendedEvents,
    late_events: lateEvents,
    incomplete_events: incompleteEvents,
    absent_events: absentEvents,
    excused_events: excusedEvents,
    attendance_rate: attendanceRate,
    present_events: Math.max(attendedEvents - lateEvents, 0),
    late_rate: totalEvents > 0 ? (lateEvents / totalEvents) * 100 : 0,
    absence_rate: totalEvents > 0 ? (absentEvents / totalEvents) * 100 : 0,
  }
}

function buildStudentLoginRow(row = {}) {
  const successfulLoginCount = toWholeNumber(row?.successful_login_count)
  const lastLoginAt = typeof row?.last_login_at === 'string' && row.last_login_at.trim()
    ? row.last_login_at
    : null
  const hasLoggedIn = row?.has_logged_in === true || successfulLoginCount > 0 || Boolean(lastLoginAt)

  return {
    ...row,
    student_profile_id: toWholeNumber(row?.student_profile_id),
    student_id: String(row?.student_id || '').trim() || null,
    full_name: String(row?.full_name || 'Unknown Student').trim() || 'Unknown Student',
    department_name: String(row?.department_name || '').trim() || null,
    program_name: String(row?.program_name || '').trim() || null,
    successful_login_count: successfulLoginCount,
    last_login_at: lastLoginAt,
    has_logged_in: hasLoggedIn,
    status_label: hasLoggedIn ? 'Logged In' : 'No Login Recorded',
  }
}

function buildComparisonWindow(startValue, endValue) {
  let currentStart = parseDateInput(startValue)
  let currentEnd = parseDateInput(endValue)

  if (currentStart && !currentEnd) currentEnd = shiftDate(currentStart, 29)
  if (!currentStart && currentEnd) currentStart = shiftDate(currentEnd, -29)

  if (!currentStart && !currentEnd) {
    currentEnd = new Date()
    currentEnd.setHours(0, 0, 0, 0)
    currentStart = shiftDate(currentEnd, -29)
  }

  if (currentEnd < currentStart) {
    const swap = currentStart
    currentStart = currentEnd
    currentEnd = swap
  }

  const dayCount = Math.max(1, differenceInDaysInclusive(currentStart, currentEnd))
  const previousEnd = shiftDate(currentStart, -1)
  const previousStart = shiftDate(previousEnd, -(dayCount - 1))

  return {
    current: {
      start: toIsoDate(currentStart),
      end: toIsoDate(currentEnd),
      days: dayCount,
    },
    previous: {
      start: toIsoDate(previousStart),
      end: toIsoDate(previousEnd),
      days: dayCount,
    },
  }
}

function buildMonthlyLineData(rows) {
  const byMonth = new Map()
  for (const row of Array.isArray(rows) ? rows : []) {
    const date = new Date(row.date || '')
    if (Number.isNaN(date.getTime())) continue
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!byMonth.has(key)) byMonth.set(key, { attended: 0, total: 0 })
    const bucket = byMonth.get(key)
    bucket.attended += Number(row.attended || 0)
    bucket.total += Number(row.total || 0)
  }
  const labels = Array.from(byMonth.keys()).sort((a, b) => a.localeCompare(b))
  return {
    labels,
    datasets: [{
      label: 'Attendance Rate (%)',
      data: labels.map((label) => {
        const bucket = byMonth.get(label)
        return bucket.total > 0 ? roundPercent((bucket.attended / bucket.total) * 100) : 0
      }),
      borderColor: 'rgba(0,87,184,0.88)',
      backgroundColor: 'rgba(0,87,184,0.88)',
      tension: 0.25,
    }],
  }
}

function buildStudentTrendLineData(rows) {
  const trendRows = Array.isArray(rows) ? rows : []
  if (!trendRows.length) return { labels: [], datasets: [] }

  const grouped = new Map()
  for (const row of trendRows) {
    const period = String(row?.period || '').trim()
    if (!period) continue
    if (!grouped.has(period)) grouped.set(period, { present: 0, late: 0, absent: 0, excused: 0 })
    const bucket = grouped.get(period)
    const status = normalizeStatus(row?.status)
    if (Object.hasOwn(bucket, status)) bucket[status] += Number(row?.count || 0)
  }

  const labels = Array.from(grouped.keys()).sort((a, b) => a.localeCompare(b))
  return {
    labels,
    datasets: [
      { label: 'Present', data: labels.map((label) => grouped.get(label).present), borderColor: 'rgba(0,87,184,0.88)', backgroundColor: 'rgba(0,87,184,0.88)', tension: 0.25 },
      { label: 'Late', data: labels.map((label) => grouped.get(label).late), borderColor: 'rgba(245,158,11,0.88)', backgroundColor: 'rgba(245,158,11,0.88)', tension: 0.25 },
      { label: 'Absent', data: labels.map((label) => grouped.get(label).absent), borderColor: 'rgba(239,68,68,0.88)', backgroundColor: 'rgba(239,68,68,0.88)', tension: 0.25 },
      { label: 'Excused', data: labels.map((label) => grouped.get(label).excused), borderColor: 'rgba(16,185,129,0.88)', backgroundColor: 'rgba(16,185,129,0.88)', tension: 0.25 },
    ],
  }
}

function parseDateInput(value) {
  if (!value) return null
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return null
  return date
}

function isDateInRange(value, start, end) {
  const date = new Date(value || 0)
  if (Number.isNaN(date.getTime())) return true
  if (start && date < start) return false
  if (end) {
    const endBoundary = new Date(end)
    endBoundary.setHours(23, 59, 59, 999)
    if (date > endBoundary) return false
  }
  return true
}

function resolveAttendanceStatus(attendance = {}) {
  const completion = String(attendance.completion_state || '').toLowerCase()
  const status = String(attendance.display_status || attendance.status || '').toLowerCase()
  if (completion !== 'completed') return 'waiting'
  if (status === 'late') return 'late'
  if (status === 'absent') return 'absent'
  if (status === 'excused') return 'excused'
  return 'present'
}

function normalizeStatus(status) {
  const value = String(status || '').toLowerCase()
  if (['present', 'late', 'absent', 'excused'].includes(value)) return value
  return 'waiting'
}

function formatStatusLabel(status) {
  const value = normalizeStatus(status)
  if (value === 'waiting') return 'Waiting'
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function formatMethod(method) {
  const value = String(method || '').trim().toLowerCase()
  if (value === 'face_scan') return 'Face Scan'
  if (value === 'manual') return 'Manual'
  return value || 'Unknown'
}

function normalizeId(value) {
  const raw = Array.isArray(value) ? value[0] : value
  const normalized = Number(raw)
  return Number.isFinite(normalized) ? normalized : null
}

function toPositiveInt(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized) || normalized <= 0) return undefined
  return Math.round(normalized)
}

function formatDate(value) {
  if (!value) return 'Unspecified Date'
  const normalized = String(value)
  const date = /^\d{4}-\d{2}-\d{2}$/.test(normalized) ? new Date(`${normalized}T00:00:00`) : new Date(normalized)
  if (Number.isNaN(date.getTime())) return normalized
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function formatDateTime(value, fallback = 'N/A') {
  if (!value) return fallback
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

function roundPercent(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.max(0, Math.min(100, Math.round(normalized)))
}

function formatPercent(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized.toFixed(2).replace(/\.00$/, '') : '0'
}

function formatWhole(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return '0'
  return Math.round(normalized).toLocaleString('en-US')
}

function readFiniteNumber(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function toWholeNumber(value) {
  const normalized = readFiniteNumber(value)
  if (normalized == null) return 0
  return Math.max(0, Math.round(normalized))
}

function clampWholeNumber(value, min = 0, max = Number.POSITIVE_INFINITY) {
  return Math.max(min, Math.min(max, toWholeNumber(value)))
}

function roundToTwo(value) {
  const normalized = Number(value)
  if (!Number.isFinite(normalized)) return 0
  return Math.round(normalized * 100) / 100
}

function normalizeLookupKey(value) {
  return String(value || '').trim().toLowerCase()
}

function getWeekdayLabel(value) {
  const date = new Date(value || 0)
  if (Number.isNaN(date.getTime())) return 'Unscheduled'
  return new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(date)
}

function getTimeBlockLabel(value) {
  const date = new Date(value || 0)
  if (Number.isNaN(date.getTime())) return 'Unscheduled'
  const hour = date.getHours()
  if (hour < 8) return 'Before 8 AM'
  if (hour < 12) return '8 AM - 12 PM'
  if (hour < 16) return '12 PM - 4 PM'
  return '4 PM and later'
}

function shiftDate(value, days) {
  const date = new Date(value)
  date.setDate(date.getDate() + Number(days || 0))
  return date
}

function differenceInDaysInclusive(start, end) {
  const milliseconds = new Date(end).getTime() - new Date(start).getTime()
  return Math.floor(milliseconds / 86400000) + 1
}

function toIsoDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function sanitize(value) {
  return String(value || 'event_report').trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'event_report'
}

function csvField(value) {
  const text = String(value ?? '')
  const safe = /^[=+\-@]/.test(text) ? `'${text}` : text
  return `"${safe.replace(/"/g, '""')}"`
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function goBack() {
  router.push({ name: 'SchoolItSchedule' })
}

async function handleLogout() {
  await logout()
}
</script>

<style scoped>
.school-it-reports {
  min-height: 100vh;
  padding: 30px 28px 120px;
  font-family: 'Manrope', sans-serif;
  background: var(--color-bg, #f3f4f6);
}

.school-it-reports__shell {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
}

.school-it-reports__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 32px;
}

.school-it-reports__header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.school-it-reports__back {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.school-it-reports__header-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.school-it-reports__title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: var(--color-text-always-dark, #111827);
}

.school-it-reports__subtitle {
  margin: 0;
  font-size: 15px;
  color: var(--color-text-secondary, #6b7280);
}

.school-it-reports__filters-panel {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  padding: 16px;
  border-radius: 24px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 16px 34px rgba(15, 23, 42, 0.06);
}

.school-it-reports__filters-toggle {
  display: none;
  min-height: 42px;
  border: none;
  border-radius: 999px;
  padding: 0 14px;
  background: #ffffff;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
  color: #111827;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
}

.school-it-reports__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.school-it-reports__field-input {
  min-height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  padding: 0 10px;
  font: inherit;
  font-size: 14px;
  text-transform: none;
  letter-spacing: 0;
  color: #111827;
  background: #fff;
}

.school-it-reports__clear-btn {
  min-height: 40px;
  border: none;
  border-radius: 999px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
}

.school-it-reports__tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.school-it-reports__tab {
  border: none;
  border-radius: 999px;
  min-height: 38px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #334155;
  white-space: nowrap;
}

.school-it-reports__tab--active {
  background: var(--color-primary, #0057B8);
  color: #fff;
}

.school-it-reports__content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 22px;
  border-radius: 28px;
  background: #fff;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.08);
}

.school-it-reports__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.school-it-reports__search-shell {
  width: min(100%, 360px);
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  display: flex;
  align-items: center;
  padding: 0 10px 0 16px;
}

.school-it-reports__search-input {
  flex: 1;
  border: none;
  outline: none;
  font: inherit;
  font-size: 14px;
  color: #111827;
  background: transparent;
}

.school-it-reports__search-icon {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.school-it-reports__table-wrap {
  overflow-x: auto;
  width: 100%;
}

.school-it-reports__table {
  width: 100%;
  min-width: 760px;
  border-collapse: separate;
  border-spacing: 0;
}

.school-it-reports__table th {
  text-align: left;
  padding: 12px 14px;
  border-bottom: 2px solid #f1f5f9;
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.school-it-reports__table td {
  padding: 14px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.school-it-reports__table-row--selected {
  background: color-mix(in srgb, var(--color-primary, #0057B8) 10%, white);
}

.school-it-reports__cell-actions {
  display: inline-flex;
  gap: 8px;
}

.school-it-reports__empty {
  text-align: center !important;
  color: #64748b;
  padding: 28px !important;
}

.school-it-reports__btn {
  border: none;
  border-radius: 999px;
  min-height: 34px;
  padding: 0 14px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.school-it-reports__btn--view {
  background: var(--color-primary, #0057B8);
  color: #fff;
}

.school-it-reports__btn--dark {
  background: #111827;
  color: #fff;
}

.school-it-reports__btn--accent {
  background: var(--color-secondary, #FFD400);
  color: #111827;
}

.school-it-reports__banner {
  border-radius: 16px;
  padding: 12px 14px;
  background: color-mix(in srgb, var(--color-primary, #0057B8) 8%, white);
  color: #0f172a;
}

.school-it-reports__banner--error {
  background: color-mix(in srgb, #ef4444 12%, white);
  color: #991b1b;
}

.school-it-reports__detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}

.school-it-reports__section-title {
  margin: 0;
  font-size: 21px;
  font-weight: 800;
  color: #111827;
}

.school-it-reports__section-subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.school-it-reports__actions {
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.school-it-reports__insight-controls {
  display: grid;
  grid-template-columns: repeat(3, minmax(140px, 1fr));
  gap: 10px;
  width: min(100%, 520px);
}

.school-it-reports__stats-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.school-it-reports__stats-grid--dense {
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
}

.school-it-reports__stat-card {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #fff;
}

.school-it-reports__stat-card span {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 800;
}

.school-it-reports__stat-card strong {
  font-size: 24px;
  line-height: 1.1;
  color: var(--color-primary, #0057B8);
}

.school-it-reports__stat-card small {
  font-size: 12px;
  color: #64748b;
  line-height: 1.4;
}

.school-it-reports__chart-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.school-it-reports__chart-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.school-it-reports__chart-canvas {
  min-width: 0;
}

.school-it-reports__panel {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
  background: #fff;
}

.school-it-reports__panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.school-it-reports__panel h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #111827;
}

.school-it-reports__panel-subtitle,
.school-it-reports__panel-note {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.5;
}

.school-it-reports__panel-empty {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.school-it-reports__insights-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.school-it-reports__metric-list {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  margin-top: 12px;
}

.school-it-reports__metric-pill {
  padding: 12px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.16);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.school-it-reports__metric-pill span {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: #64748b;
}

.school-it-reports__metric-pill strong {
  font-size: 18px;
  color: #111827;
}

.school-it-reports__status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.school-it-reports__status-chip--success {
  background: rgba(5, 150, 105, 0.12);
  color: #047857;
}

.school-it-reports__status-chip--muted {
  background: rgba(148, 163, 184, 0.16);
  color: #475569;
}

.school-it-reports__table--compact {
  min-width: 0;
}

.school-it-reports__table--compact th,
.school-it-reports__table--compact td {
  padding: 12px;
}

.school-it-reports__trend-cell {
  font-weight: 800;
}

.school-it-reports__trend-cell--up {
  color: #047857;
}

.school-it-reports__trend-cell--down {
  color: #b91c1c;
}

.school-it-reports__import-tools {
  display: grid;
  gap: 8px;
  grid-template-columns: 1fr 1fr auto;
  margin-bottom: 10px;
}

.school-it-reports__skeleton-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.school-it-reports__skeleton-card {
  min-height: 140px;
  border-radius: 16px;
  background: linear-gradient(90deg, rgba(226, 232, 240, 0.8) 25%, rgba(241, 245, 249, 0.95) 50%, rgba(226, 232, 240, 0.8) 75%);
  background-size: 220% 100%;
  animation: reports-skeleton 1.2s ease-in-out infinite;
}

@keyframes reports-skeleton {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (max-width: 1160px) {
  .school-it-reports__filters-panel {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .school-it-reports {
    padding: 20px 12px 80px;
  }

  .school-it-reports__header {
    align-items: center;
  }

  .school-it-reports__title {
    font-size: 22px;
  }

  .school-it-reports__filters-toggle {
    display: inline-flex;
    width: 100%;
  }

  .school-it-reports__content {
    padding: 16px;
  }

  .school-it-reports__filters-panel {
    grid-template-columns: 1fr;
    padding: 12px;
    border-radius: 16px;
  }

  .school-it-reports__stats-grid,
  .school-it-reports__chart-grid,
  .school-it-reports__insights-grid {
    grid-template-columns: 1fr;
  }

  .school-it-reports__actions {
    width: 100%;
  }

  .school-it-reports__actions .school-it-reports__btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .school-it-reports__cell-actions {
    display: flex;
    flex-direction: column;
  }

  .school-it-reports__table {
    min-width: 640px;
  }

  .school-it-reports__chart-canvas {
    min-width: 420px;
  }

  .school-it-reports__search-shell {
    width: 100%;
  }

  .school-it-reports__import-tools {
    grid-template-columns: 1fr;
  }

  .school-it-reports__insight-controls {
    width: 100%;
    grid-template-columns: 1fr;
  }
}
</style>
