<template>
  <section class="admin-view">
    <div class="admin-view__shell">
      <SchoolItTopHeader
        :avatar-url="avatarUrl"
        :school-name="platformLabel"
        :display-name="displayName"
        :initials="initials"
        @logout="handleLogout"
      />

      <header class="admin-view__hero">
        <div>
          <p class="admin-view__eyebrow">Platform Control</p>
          <h1 class="admin-view__title">{{ sectionMeta.title }}</h1>
          <p class="admin-view__subtitle">{{ sectionMeta.description }}</p>
        </div>

        <label v-if="schools.length" class="admin-view__scope">
          <span>School Scope</span>
          <select v-model="selectedSchoolModel" class="admin-view__select">
            <option value="">All schools</option>
            <option v-for="school in schools" :key="school.school_id" :value="String(school.school_id)">
              {{ school.school_name }}
            </option>
          </select>
        </label>
      </header>

      <section class="admin-view__toolbar">
        <label class="admin-view__search">
          <input
            v-model.trim="searchQuery"
            class="admin-view__search-input"
            :placeholder="sectionMeta.searchPlaceholder"
            type="search"
            inputmode="search"
            autocapitalize="off"
            autocorrect="off"
            autocomplete="off"
            spellcheck="false"
          >
          <Search :size="18" class="admin-view__search-icon" />
        </label>

        <button class="admin-view__pill" type="button" @click="handlePrimaryAction">
          <span class="admin-view__pill-icon">
            <component :is="sectionMeta.actionIcon" :size="16" />
          </span>
          <span>{{ sectionMeta.actionLabel }}</span>
        </button>
      </section>

      <p v-if="feedback.message" class="admin-view__feedback" :class="`admin-view__feedback--${feedback.type}`">
        {{ feedback.message }}
      </p>

      <div v-if="section === 'overview'" class="admin-view__stack">
        <section class="admin-view__metrics">
          <article class="admin-view__metric admin-view__metric--primary">
            <p>Schools</p>
            <strong>{{ schools.length }}</strong>
            <button class="admin-view__soft-button" type="button" @click="goToSection('schools')">
              <ArrowRight :size="16" />
              <span>Open Schools</span>
            </button>
          </article>
          <article class="admin-view__metric">
            <p>Active Campuses</p>
            <strong>{{ activeSchoolCount }}</strong>
            <span>{{ suspendedSchoolCount }} suspended</span>
          </article>
          <article class="admin-view__metric">
            <p>Campus Admins</p>
            <strong>{{ campusAccounts.length }}</strong>
            <span>{{ activeCampusAccountCount }} active</span>
          </article>
          <article class="admin-view__metric">
            <p>Pending Requests</p>
            <strong>{{ pendingRequestCount }}</strong>
            <span>Governance queue</span>
          </article>
        </section>

        <section class="admin-view__grid">
          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <p class="admin-view__mini">Schools List</p>
                <h2>Platform Schools</h2>
              </div>
              <button class="admin-view__ghost" type="button" @click="goToSection('schools')">Manage</button>
            </div>

            <div class="admin-view__list">
              <article v-for="school in filteredSchools.slice(0, 4)" :key="school.school_id" class="admin-view__row">
                <div>
                  <h3>{{ school.school_name }}</h3>
                  <p>{{ school.school_code || 'No code yet' }}</p>
                </div>
                <div class="admin-view__badges">
                  <span class="admin-view__badge">{{ formatSubscriptionLabel(school.subscription_status) }}</span>
                  <span class="admin-view__badge admin-view__badge--muted">{{ school.active_status ? 'Active' : 'Inactive' }}</span>
                </div>
              </article>
            </div>
          </article>

          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <p class="admin-view__mini">Oversight</p>
                <h2>Recent Activity</h2>
              </div>
              <button class="admin-view__ghost" type="button" @click="goToSection('oversight')">Open</button>
            </div>

            <div class="admin-view__list">
              <article v-for="item in filteredAuditLogs.slice(0, 5)" :key="item.id" class="admin-view__row">
                <div>
                  <h3>{{ prettify(item.action) }}</h3>
                  <p>{{ resolveSchoolName(item.school_id) }} • {{ formatDateTime(item.created_at) }}</p>
                </div>
                <span class="admin-view__badge admin-view__badge--muted">{{ prettify(item.status) }}</span>
              </article>
            </div>
          </article>
        </section>

        <section class="admin-view__grid admin-view__grid--reports">
          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <p class="admin-view__mini">Subscriptions</p>
                <h2>School Spread</h2>
              </div>
            </div>

            <div v-if="subscriptionChartData.labels.length" class="admin-view__chart">
              <ReportsBarChart :data="subscriptionChartData" :options="chartOptions.bar" />
            </div>
            <p v-else class="admin-view__muted">No school subscription data yet.</p>
          </article>

          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <p class="admin-view__mini">Operations</p>
                <h2>Audit + Notification Trend</h2>
              </div>
            </div>

            <div v-if="activityTrendChartData.labels.length" class="admin-view__chart">
              <ReportsLineChart :data="activityTrendChartData" :options="chartOptions.line" />
            </div>
            <p v-else class="admin-view__muted">Recent operational activity will appear here.</p>
          </article>

          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <p class="admin-view__mini">Governance</p>
                <h2>Queue Status</h2>
              </div>
            </div>

            <div v-if="requestStatusChartData.labels.length" class="admin-view__chart">
              <ReportsPieChart :data="requestStatusChartData" :options="chartOptions.pie" />
            </div>
            <p v-else class="admin-view__muted">No governance requests are waiting right now.</p>
          </article>
        </section>
      </div>

      <div v-else-if="section === 'schools'" class="admin-view__stack">
        <section v-if="showCreateForm" class="admin-view__card">
          <div class="admin-view__card-head">
            <div>
              <p class="admin-view__mini">Create School</p>
              <h2>New School + Campus Admin</h2>
            </div>
            <button class="admin-view__ghost" type="button" @click="showCreateForm = false">Close</button>
          </div>

          <form class="admin-view__form" @submit.prevent="submitCreateSchool">
            <div class="admin-view__form-grid">
              <label class="admin-view__field"><span>School Name</span><input v-model.trim="createForm.school_name" required type="text"></label>
              <label class="admin-view__field"><span>School Code</span><input v-model.trim="createForm.school_code" type="text"></label>
              <label class="admin-view__field"><span>Primary Color</span><input v-model="createForm.primary_color" required type="color"></label>
              <label class="admin-view__field"><span>Secondary Color</span><input v-model="createForm.secondary_color" required type="color"></label>
              <label class="admin-view__field"><span>Campus Admin Email</span><input v-model.trim="createForm.school_it_email" required type="email"></label>
              <label class="admin-view__field"><span>Temporary Password</span><input v-model="createForm.school_it_password" type="text"></label>
              <label class="admin-view__field"><span>First Name</span><input v-model.trim="createForm.school_it_first_name" required type="text"></label>
              <label class="admin-view__field"><span>Middle Name</span><input v-model.trim="createForm.school_it_middle_name" type="text"></label>
              <label class="admin-view__field"><span>Last Name</span><input v-model.trim="createForm.school_it_last_name" required type="text"></label>
              <label class="admin-view__field"><span>Logo</span><input type="file" accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml" @change="handleCreateLogoChange"></label>
            </div>

            <button class="admin-view__pill admin-view__pill--submit" type="submit" :disabled="adminState.creatingSchool">
              <span class="admin-view__pill-icon">
                <LoaderCircle v-if="adminState.creatingSchool" :size="16" class="admin-view__spinner" />
                <Plus v-else :size="16" />
              </span>
              <span>{{ adminState.creatingSchool ? 'Creating School...' : 'Create School' }}</span>
            </button>
          </form>
        </section>

        <section class="admin-view__grid">
          <article v-for="school in filteredSchools" :key="school.school_id" class="admin-view__card">
            <div class="admin-view__card-head">
              <div>
                <h2>{{ school.school_name }}</h2>
                <p class="admin-view__muted">{{ school.school_code || 'No code yet' }}</p>
              </div>
              <span class="admin-view__badge">{{ formatSubscriptionLabel(school.subscription_status) }}</span>
            </div>

            <div class="admin-view__actions">
              <button class="admin-view__ghost" type="button" @click="toggleSchoolActive(school)">
                {{ school.active_status ? 'Deactivate' : 'Activate' }}
              </button>

              <div class="admin-view__segments">
                <button
                  v-for="statusOption in subscriptionOptions"
                  :key="statusOption"
                  class="admin-view__segment"
                  :class="{ 'admin-view__segment--active': school.subscription_status === statusOption }"
                  type="button"
                  @click="setSchoolSubscription(school, statusOption)"
                >
                  {{ formatSubscriptionLabel(statusOption) }}
                </button>
              </div>
            </div>

            <div class="admin-view__footer">
              <span class="admin-view__muted">{{ resolveCampusAdminEmail(school.school_id) }}</span>
              <button class="admin-view__ghost" type="button" @click="openSchoolOversight(school.school_id)">Oversight</button>
            </div>
          </article>
        </section>
      </div>

      <div v-else-if="section === 'accounts'" class="admin-view__grid">
        <article v-for="account in filteredCampusAccounts" :key="account.user_id" class="admin-view__card">
          <div class="admin-view__card-head">
            <div>
              <h2>{{ formatPersonName(account.first_name, account.last_name) }}</h2>
              <p class="admin-view__muted">{{ account.email }}</p>
            </div>
            <span class="admin-view__badge admin-view__badge--muted">{{ abbreviate(account.school_name) }}</span>
          </div>

          <p class="admin-view__muted">{{ account.school_name || 'No school scope' }}</p>

          <div class="admin-view__actions">
            <button class="admin-view__ghost" type="button" @click="toggleCampusAccount(account)">
              <UserRoundX :size="16" />
              <span>{{ account.is_active ? 'Deactivate' : 'Activate' }}</span>
            </button>
            <button class="admin-view__ghost admin-view__ghost--primary" type="button" @click="resetCampusPasswordFor(account)">
              <KeyRound :size="16" />
              <span>Reset Password</span>
            </button>
          </div>
        </article>
      </div>

      <div v-else-if="section === 'oversight'" class="admin-view__stack">
        <section class="admin-view__grid">
          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div><p class="admin-view__mini">Notifications</p><h2>Dispatch Tools</h2></div>
            </div>
            <div class="admin-view__form-grid">
              <label class="admin-view__field"><span>Threshold %</span><input v-model.number="dispatchForm.threshold_percent" min="1" max="100" type="number"></label>
              <label class="admin-view__field"><span>Min Records</span><input v-model.number="dispatchForm.min_records" min="1" max="100" type="number"></label>
            </div>
            <div class="admin-view__actions">
              <button class="admin-view__ghost" type="button" @click="dispatchNotifications('missed_events')"><BellRing :size="16" /><span>Missed Events</span></button>
              <button class="admin-view__ghost admin-view__ghost--primary" type="button" @click="dispatchNotifications('low_attendance')"><ShieldCheck :size="16" /><span>Low Attendance</span></button>
            </div>
          </article>

          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div><p class="admin-view__mini">Governance</p><h2>Retention Rules</h2></div>
            </div>
            <form class="admin-view__form" @submit.prevent="saveGovernanceSettingsForSelectedSchool">
              <div class="admin-view__form-grid">
                <label class="admin-view__field"><span>Attendance Days</span><input v-model.number="governanceForm.attendance_retention_days" min="30" max="3650" type="number"></label>
                <label class="admin-view__field"><span>Audit Days</span><input v-model.number="governanceForm.audit_log_retention_days" min="90" max="7300" type="number"></label>
                <label class="admin-view__field"><span>Import Days</span><input v-model.number="governanceForm.import_file_retention_days" min="7" max="3650" type="number"></label>
              </div>
              <label class="admin-view__switch"><input v-model="governanceForm.auto_delete_enabled" type="checkbox"><span>Enable auto-delete</span></label>
              <div class="admin-view__actions">
                <button class="admin-view__ghost admin-view__ghost--primary" type="submit"><Check :size="16" /><span>Save</span></button>
                <button class="admin-view__ghost" type="button" @click="runRetention(true)"><History :size="16" /><span>Dry Run</span></button>
                <button class="admin-view__ghost" type="button" @click="runRetention(false)"><RefreshCw :size="16" /><span>Run Cleanup</span></button>
              </div>
            </form>
          </article>
        </section>

        <section class="admin-view__grid">
          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div><p class="admin-view__mini">Requests</p><h2>Governance Queue</h2></div>
            </div>
            <div class="admin-view__list">
              <article v-for="request in filteredGovernanceRequests" :key="request.id" class="admin-view__row admin-view__row--stack">
                <div>
                  <h3>{{ formatRequestTitle(request) }}</h3>
                  <p>{{ resolveSchoolName(request.school_id) }} • {{ formatDateTime(request.created_at) }}</p>
                  <p>{{ request.reason || 'No reason supplied.' }}</p>
                </div>
                <div class="admin-view__actions">
                  <button class="admin-view__ghost admin-view__ghost--primary" type="button" @click="reviewRequest(request, 'approved')"><Check :size="16" /></button>
                  <button class="admin-view__ghost" type="button" @click="reviewRequest(request, 'rejected')"><X :size="16" /></button>
                </div>
              </article>
            </div>
          </article>

          <article class="admin-view__card">
            <div class="admin-view__card-head">
              <div><p class="admin-view__mini">Logs</p><h2>Audit + Notifications</h2></div>
            </div>
            <div class="admin-view__list">
              <article v-for="item in oversightLogFeed" :key="`${item.kind}-${item.id}`" class="admin-view__row">
                <div>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.meta }}</p>
                </div>
                <span class="admin-view__badge admin-view__badge--muted">{{ item.badge }}</span>
              </article>
            </div>
          </article>
        </section>
      </div>

      <div v-else class="admin-view__grid">
        <article class="admin-view__card">
          <div class="admin-view__card-head">
            <div><p class="admin-view__mini">Profile</p><h2>{{ displayName }}</h2></div>
            <span class="admin-view__badge admin-view__badge--muted">Admin</span>
          </div>
          <div class="admin-view__profile">
            <div><span>Email</span><strong>{{ activeUser?.email || 'platform.admin@valid8.local' }}</strong></div>
            <div><span>Scope</span><strong>Platform-wide</strong></div>
            <div><span>Schools</span><strong>{{ schools.length }}</strong></div>
            <div><span>Campus Admins</span><strong>{{ activeCampusAccountCount }}</strong></div>
          </div>
          <button
            class="admin-view__preference"
            type="button"
            :aria-pressed="isDarkMode"
            aria-label="Toggle dark mode"
            @click="toggleDarkMode"
          >
            <span class="admin-view__preference-copy">
              <span class="admin-view__mini admin-view__mini--inline">Appearance</span>
              <strong>Dark Mode</strong>
              <small>Apply the theme across every workspace for this device.</small>
            </span>
            <span class="admin-view__settings-toggle" :class="{ 'admin-view__settings-toggle--on': isDarkMode }">
              <span class="admin-view__settings-toggle-knob" />
            </span>
          </button>
        </article>

        <article class="admin-view__card">
          <div class="admin-view__card-head">
            <div><p class="admin-view__mini">Modules</p><h2>Admin Surface</h2></div>
          </div>
          <div class="admin-view__list">
            <article class="admin-view__row"><div><h3>Schools</h3><p>Create, activate, and manage subscription states.</p></div></article>
            <article class="admin-view__row"><div><h3>Campus Admins</h3><p>Reset credentials and control platform access safely.</p></div></article>
            <article class="admin-view__row"><div><h3>Oversight</h3><p>Review audits, notifications, governance requests, and retention.</p></div></article>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, BellRing, Building2, Check, History, KeyRound, LoaderCircle, Plus, RefreshCw, Search, ShieldCheck, UserRoundX, X } from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import ReportsBarChart from '@/components/reports/ReportsBarChart.vue'
import ReportsLineChart from '@/components/reports/ReportsLineChart.vue'
import ReportsPieChart from '@/components/reports/ReportsPieChart.vue'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'
import { useAdminWorkspaceData } from '@/composables/useAdminWorkspaceData.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { adminDashboardPreviewData } from '@/data/adminDashboardPreview.js'
import { buildBarChartData, buildLineChartData, buildPieChartData, buildTrailingDayLabels } from '@/services/dashboardReportCharts.js'

const props = defineProps({
  preview: { type: Boolean, default: false },
  section: { type: String, default: 'overview' },
})
const section = computed(() => props.section)

const router = useRouter()
const route = useRoute()
const { logout } = useAuth()
const { currentUser, initializeDashboardSession } = useDashboardSession()
const {
  adminWorkspaceState: adminState,
  schools,
  campusAccounts,
  auditLogs,
  notificationLogs,
  governanceRequests,
  governanceSettingsBySchool,
  selectedSchoolId,
  lastPasswordReset,
  initializeAdminWorkspaceData,
  selectAdminSchool,
  createAdminSchool,
  saveAdminSchoolStatus,
  saveAdminCampusAccountStatus,
  resetAdminCampusPassword,
  dispatchAdminNotification,
  saveAdminGovernanceSettings,
  reviewAdminGovernanceRequest,
  runAdminRetentionCleanup,
} = useAdminWorkspaceData(props.preview)

const searchQuery = ref('')
const showCreateForm = ref(false)
const feedback = reactive({ type: 'success', message: '' })
const createForm = reactive(createDefaultSchoolForm())
const governanceForm = reactive({
  attendance_retention_days: 365,
  audit_log_retention_days: 365,
  import_file_retention_days: 30,
  auto_delete_enabled: false,
})
const dispatchForm = reactive({
  threshold_percent: 75,
  min_records: 3,
})
let feedbackTimeoutId = null

const sectionMetaMap = {
  overview: { title: 'Admin Dashboard', description: 'Track schools, campus-admin operations, and platform oversight from one command surface.', searchPlaceholder: 'Search schools, logs, or requests', actionLabel: 'Open Schools', actionIcon: Building2 },
  schools: { title: 'Schools', description: 'Provision campuses, create school accounts, and control activation and subscription states.', searchPlaceholder: 'Search schools', actionLabel: 'Create School', actionIcon: Plus },
  accounts: { title: 'Campus Admin Accounts', description: 'Manage school-scoped admin accounts and rotate credentials cleanly.', searchPlaceholder: 'Search campus-admin accounts', actionLabel: 'Oversight', actionIcon: ShieldCheck },
  oversight: { title: 'Oversight', description: 'Review audit activity, dispatch notifications, and manage governance retention.', searchPlaceholder: 'Search logs and requests', actionLabel: 'Refresh', actionIcon: RefreshCw },
  profile: { title: 'Admin Profile', description: 'Review the current platform-admin session and module coverage.', searchPlaceholder: 'Search summary', actionLabel: 'Schools', actionIcon: Building2 },
}

const sectionMeta = computed(() => sectionMetaMap[props.section] || sectionMetaMap.overview)
const activeUser = computed(() => (props.preview ? adminDashboardPreviewData.user : currentUser.value))
const displayName = computed(() => {
  const user = activeUser.value
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim() || user?.email || 'Platform Admin'
})
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const initials = computed(() => abbreviate(displayName.value, 2))
const platformLabel = computed(() => 'VALID8 Platform')
const activeSchoolCount = computed(() => schools.value.filter((item) => item.active_status).length)
const suspendedSchoolCount = computed(() => schools.value.filter((item) => item.subscription_status === 'suspended').length)
const activeCampusAccountCount = computed(() => campusAccounts.value.filter((item) => item.is_active).length)
const pendingRequestCount = computed(() => governanceRequests.value.filter((item) => item.status === 'pending').length)
const selectedGovernanceSettings = computed(() => governanceSettingsBySchool.value?.[Number(selectedSchoolId.value)] || null)
const selectedSchoolModel = computed({
  get: () => (selectedSchoolId.value ? String(selectedSchoolId.value) : ''),
  set: (value) => selectAdminSchool(value ? Number(value) : null).catch((error) => pushFeedback('error', error?.message || 'Unable to update school scope.')),
})
const filteredSchools = computed(() => filterItems(schools.value, searchQuery.value, (school) => [school.school_name, school.school_code, school.subscription_status]))
const filteredCampusAccounts = computed(() => filterItems(campusAccounts.value, searchQuery.value, (item) => [item.email, item.first_name, item.last_name, item.school_name]))
const filteredAuditLogs = computed(() => filterItems(auditLogs.value, searchQuery.value, (item) => [item.action, item.status, item.details, resolveSchoolName(item.school_id)]))
const filteredNotificationLogs = computed(() => filterItems(notificationLogs.value, searchQuery.value, (item) => [item.subject, item.category, item.status, resolveSchoolName(item.school_id)]))
const filteredGovernanceRequests = computed(() => governanceRequests.value.filter((item) => {
  if (selectedSchoolId.value && Number(item?.school_id) !== Number(selectedSchoolId.value)) return false
  return matchesSearch(searchQuery.value, [item.request_type, item.status, item.reason, resolveSchoolName(item.school_id)])
}))
const oversightLogFeed = computed(() => [
  ...filteredAuditLogs.value.slice(0, 4).map((item) => ({ kind: 'audit', id: item.id, title: prettify(item.action), meta: `${resolveSchoolName(item.school_id)} • ${formatDateTime(item.created_at)}`, badge: prettify(item.status) })),
  ...filteredNotificationLogs.value.slice(0, 4).map((item) => ({ kind: 'notification', id: item.id, title: item.subject, meta: `${resolveSchoolName(item.school_id)} • ${formatDateTime(item.created_at)}`, badge: prettify(item.status) })),
])

const scopedAuditLogs = computed(() => selectedSchoolId.value
  ? auditLogs.value.filter((item) => Number(item?.school_id) === Number(selectedSchoolId.value))
  : auditLogs.value
)
const scopedNotificationLogs = computed(() => selectedSchoolId.value
  ? notificationLogs.value.filter((item) => Number(item?.school_id) === Number(selectedSchoolId.value))
  : notificationLogs.value
)
const scopedGovernanceRequests = computed(() => selectedSchoolId.value
  ? governanceRequests.value.filter((item) => Number(item?.school_id) === Number(selectedSchoolId.value))
  : governanceRequests.value
)

const subscriptionChartData = computed(() => {
  const counts = {
    active: 0,
    trial: 0,
    suspended: 0,
  }

  for (const school of schools.value) {
    const key = String(school?.subscription_status || 'trial').toLowerCase()
    if (Object.hasOwn(counts, key)) counts[key] += 1
  }

  return buildBarChartData([
    { label: 'Active', value: counts.active },
    { label: 'Trial', value: counts.trial },
    { label: 'Suspended', value: counts.suspended },
  ], {
    label: 'Schools',
    backgroundColor: 'rgba(0,87,184,0.82)',
  })
})

const activityTrendChartData = computed(() => {
  const labels = buildTrailingDayLabels(7)
  const buckets = new Map(labels.map((item) => [item.key, { audits: 0, notifications: 0 }]))

  for (const item of scopedAuditLogs.value) {
    const key = String(item?.created_at || '').slice(0, 10)
    if (buckets.has(key)) buckets.get(key).audits += 1
  }

  for (const item of scopedNotificationLogs.value) {
    const key = String(item?.created_at || '').slice(0, 10)
    if (buckets.has(key)) buckets.get(key).notifications += 1
  }

  return buildLineChartData(
    labels.map((item) => item.label),
    [
      { label: 'Audit Logs', data: labels.map((item) => buckets.get(item.key).audits), borderColor: 'rgba(0,87,184,0.88)' },
      { label: 'Notifications', data: labels.map((item) => buckets.get(item.key).notifications), borderColor: 'rgba(16,185,129,0.88)' },
    ]
  )
})

const requestStatusChartData = computed(() => {
  const grouped = new Map()
  for (const item of scopedGovernanceRequests.value) {
    const status = prettify(item?.status || 'pending')
    grouped.set(status, (grouped.get(status) || 0) + 1)
  }

  return buildPieChartData(Array.from(grouped.entries()).map(([label, value]) => ({ label, value })))
})

const chartOptions = {
  bar: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  },
  line: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  },
  pie: {
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  },
}

usePreviewTheme(() => props.preview, computed(() => ({
  school_name: 'VALID8 Platform',
  primary_color: schools.value[0]?.primary_color || '#AAFF00',
  secondary_color: schools.value[0]?.secondary_color || '#64748B',
  logo_url: schools.value[0]?.logo_url || null,
})))

watch(selectedGovernanceSettings, (value) => {
  governanceForm.attendance_retention_days = Number(value?.attendance_retention_days || 365)
  governanceForm.audit_log_retention_days = Number(value?.audit_log_retention_days || 365)
  governanceForm.import_file_retention_days = Number(value?.import_file_retention_days || 30)
  governanceForm.auto_delete_enabled = Boolean(value?.auto_delete_enabled)
}, { immediate: true })

watch(lastPasswordReset, (value) => {
  if (value?.temporary_password) {
    pushFeedback('success', `Temporary password for ${value.email || 'campus admin'}: ${value.temporary_password}`)
  }
})

onMounted(async () => {
  if (!props.preview) await initializeDashboardSession().catch(() => null)
  await initializeAdminWorkspaceData().catch((error) => pushFeedback('error', error?.message || 'Unable to load the admin workspace.'))
})

async function handleLogout() { await logout() }
function handlePrimaryAction() { if (props.section === 'schools') { showCreateForm.value = !showCreateForm.value; return }; if (props.section === 'accounts') { goToSection('oversight'); return }; if (props.section === 'oversight') { initializeAdminWorkspaceData({ force: true }).catch(() => null); return }; goToSection('schools') }
function goToSection(section) { const base = props.preview ? '/exposed/admin' : '/admin'; const next = section === 'overview' ? base : `${base}/${section}`; if (route.path !== next) router.push(next) }
async function submitCreateSchool() { try { const created = await createAdminSchool({ ...createForm, school_code: createForm.school_code || undefined, school_it_middle_name: createForm.school_it_middle_name || undefined, school_it_password: createForm.school_it_password || undefined }); pushFeedback('success', `Created ${created?.school?.school_name || createForm.school_name}.`); Object.assign(createForm, createDefaultSchoolForm()); showCreateForm.value = false } catch (error) { pushFeedback('error', error?.message || 'Unable to create the school.') } }
function handleCreateLogoChange(event) { createForm.logo = event?.target?.files?.[0] || null }
async function toggleSchoolActive(school) { try { await saveAdminSchoolStatus(school.school_id, { active_status: !school.active_status }); pushFeedback('success', `${school.school_name} updated.`) } catch (error) { pushFeedback('error', error?.message || 'Unable to update school status.') } }
async function setSchoolSubscription(school, value) { if (school.subscription_status === value) return; try { await saveAdminSchoolStatus(school.school_id, { subscription_status: value }); pushFeedback('success', `${school.school_name} moved to ${formatSubscriptionLabel(value)}.`) } catch (error) { pushFeedback('error', error?.message || 'Unable to update subscription.') } }
async function toggleCampusAccount(account) { try { await saveAdminCampusAccountStatus(account.user_id, !account.is_active); pushFeedback('success', `${formatPersonName(account.first_name, account.last_name)} updated.`) } catch (error) { pushFeedback('error', error?.message || 'Unable to update account status.') } }
async function resetCampusPasswordFor(account) { try { await resetAdminCampusPassword(account.user_id) } catch (error) { pushFeedback('error', error?.message || 'Unable to reset password.') } }
async function dispatchNotifications(kind) { try { const params = kind === 'low_attendance' ? { school_id: selectedSchoolId.value, threshold_percent: dispatchForm.threshold_percent, min_records: dispatchForm.min_records } : { school_id: selectedSchoolId.value }; const result = await dispatchAdminNotification(kind, params); pushFeedback('success', `${prettify(result?.category || kind)} sent to ${result?.sent || 0} users.`) } catch (error) { pushFeedback('error', error?.message || 'Unable to dispatch notifications.') } }
async function saveGovernanceSettingsForSelectedSchool() { try { await saveAdminGovernanceSettings({ attendance_retention_days: governanceForm.attendance_retention_days, audit_log_retention_days: governanceForm.audit_log_retention_days, import_file_retention_days: governanceForm.import_file_retention_days, auto_delete_enabled: governanceForm.auto_delete_enabled }, { schoolId: selectedSchoolId.value }); pushFeedback('success', 'Governance settings updated.') } catch (error) { pushFeedback('error', error?.message || 'Unable to save governance settings.') } }
async function reviewRequest(item, status) { try { await reviewAdminGovernanceRequest(item.id, { status }); pushFeedback('success', `${formatRequestTitle(item)} marked ${prettify(status)}.`) } catch (error) { pushFeedback('error', error?.message || 'Unable to update governance request.') } }
async function runRetention(dryRun) { try { const result = await runAdminRetentionCleanup({ dry_run: dryRun }, { schoolId: selectedSchoolId.value }); pushFeedback('success', result?.summary || 'Retention cleanup finished.') } catch (error) { pushFeedback('error', error?.message || 'Unable to run retention cleanup.') } }
function openSchoolOversight(schoolId) { selectedSchoolModel.value = String(schoolId); goToSection('oversight') }
function resolveSchoolName(schoolId) { return schools.value.find((item) => Number(item?.school_id) === Number(schoolId))?.school_name || `School #${schoolId}` }
function resolveCampusAdminEmail(schoolId) { return campusAccounts.value.find((item) => Number(item?.school_id) === Number(schoolId))?.email || 'No campus admin yet' }
function formatPersonName(firstName, lastName) { return [firstName, lastName].filter(Boolean).join(' ').trim() || 'Campus Admin' }
function formatSubscriptionLabel(value) { const normalized = String(value || '').toLowerCase(); return normalized === 'trial' ? 'Trial' : normalized === 'suspended' ? 'Suspended' : 'Active' }
function formatRequestTitle(item) { return `${prettify(item.request_type)} request` }
function formatDateTime(value) { try { return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) } catch { return String(value || '') } }
function prettify(value) { return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function abbreviate(value, maxLetters = 4) { const words = String(value || '').trim().match(/[A-Za-z0-9]+/g) || []; return words.slice(0, maxLetters).map((word) => word[0]?.toUpperCase() || '').join('.') || 'AD' }
function matchesSearch(query, values) { const needle = String(query || '').trim().toLowerCase(); return !needle || values.some((value) => String(value || '').toLowerCase().includes(needle)) }
function filterItems(items, query, mapper) { return items.filter((item) => matchesSearch(query, mapper(item))) }
function pushFeedback(type, message) { if (feedbackTimeoutId) window.clearTimeout(feedbackTimeoutId); feedback.type = type; feedback.message = message; feedbackTimeoutId = window.setTimeout(() => { feedback.type = 'success'; feedback.message = '' }, 4000) }
function createDefaultSchoolForm() { return { school_name: '', school_code: '', primary_color: '#AAFF00', secondary_color: '#64748B', school_it_email: '', school_it_first_name: '', school_it_middle_name: '', school_it_last_name: '', school_it_password: '', logo: null } }

const subscriptionOptions = ['active', 'trial', 'suspended']
</script>

<style scoped>
.admin-view{min-height:100vh;padding:30px 28px 120px;font-family:'Manrope',sans-serif}
.admin-view__shell{width:100%;max-width:1180px;margin:0 auto}
.admin-view__hero,.admin-view__toolbar,.admin-view__card-head,.admin-view__actions,.admin-view__footer,.admin-view__row,.admin-view__scope{display:flex;align-items:center;justify-content:space-between;gap:14px}
.admin-view__hero{margin-top:24px;align-items:flex-end}
.admin-view__eyebrow,.admin-view__mini,.admin-view__field span,.admin-view__profile span,.admin-view__scope span{margin:0 0 6px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--color-text-muted)}
.admin-view__title{margin:0;font-size:clamp(34px,4vw,52px);line-height:.96;letter-spacing:-.06em;color:var(--color-text-primary)}
.admin-view__subtitle{margin:10px 0 0;max-width:620px;font-size:15px;line-height:1.6;color:var(--color-text-secondary)}
.admin-view__scope{flex-direction:column;align-items:flex-start}
.admin-view__select,.admin-view__search-input,.admin-view__field input{width:100%;border:none;outline:none;background:var(--color-field-surface);color:var(--color-text-primary);font:inherit}
.admin-view__select{min-width:220px;height:52px;padding:0 18px;border-radius:999px}
.admin-view__toolbar{margin-top:18px;display:grid;grid-template-columns:minmax(0,1fr) auto}
.admin-view__search{display:flex;align-items:center;gap:12px;min-height:62px;padding:0 18px;border-radius:999px;background:var(--color-surface);box-shadow:0 16px 36px rgba(15,23,42,.04)}
.admin-view__search-input{background:transparent;font-size:15px}
.admin-view__search-icon{color:var(--color-primary);flex-shrink:0}
.admin-view__pill,.admin-view__ghost,.admin-view__segment,.admin-view__soft-button{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:none;border-radius:999px;font-weight:700}
.admin-view__pill{min-height:62px;padding:0 18px;background:var(--color-secondary);color:var(--color-secondary-text)}
.admin-view__pill-icon{width:36px;height:36px;border-radius:999px;display:grid;place-items:center;background:#0A0A0A;color:#fff}
.admin-view__pill--submit{align-self:flex-start}
.admin-view__ghost,.admin-view__soft-button{min-height:42px;padding:0 16px;background:var(--color-field-surface);color:var(--color-text-primary)}
.admin-view__ghost--primary{background:var(--color-secondary);color:var(--color-secondary-text)}
.admin-view__feedback{margin:16px 0 0;padding:14px 18px;border-radius:22px;background:rgba(255,255,255,.8);font-size:14px;font-weight:600}
.admin-view__feedback--success{color:#166534}.admin-view__feedback--error{color:#B42318}
.admin-view__stack,.admin-view__list{display:flex;flex-direction:column;gap:18px}
.admin-view__metrics,.admin-view__grid,.admin-view__form-grid,.admin-view__profile{display:grid;gap:16px}
.admin-view__metrics{grid-template-columns:repeat(4,minmax(0,1fr));margin-top:18px}
.admin-view__grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.admin-view__metric,.admin-view__card{background:var(--color-surface);border-radius:32px;box-shadow:0 18px 40px rgba(15,23,42,.04)}
.admin-view__metric{padding:22px;display:flex;flex-direction:column;gap:10px;min-height:170px}
.admin-view__metric--primary{background:var(--color-primary);color:var(--color-primary-text)}
.admin-view__metric p,.admin-view__metric span{margin:0;font-size:13px;color:inherit;opacity:.78}
.admin-view__metric strong{font-size:56px;line-height:.9;letter-spacing:-.06em}
.admin-view__soft-button{margin-top:auto;align-self:flex-start;padding-left:8px;background:#0A0A0A;color:#fff}
.admin-view__card{padding:22px}
.admin-view__grid--reports{grid-template-columns:repeat(3,minmax(0,1fr))}
.admin-view__chart{min-height:260px}
.admin-view__card h2,.admin-view__row h3{margin:0;color:var(--color-text-primary);line-height:1.05;letter-spacing:-.04em}
.admin-view__card h2{font-size:28px}
.admin-view__muted,.admin-view__row p{margin:6px 0 0;font-size:14px;line-height:1.5;color:var(--color-text-secondary)}
.admin-view__badges,.admin-view__segments{display:flex;gap:10px;flex-wrap:wrap}
.admin-view__badge{display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:0 14px;border-radius:999px;background:var(--color-secondary);color:var(--color-secondary-text);font-size:12px;font-weight:700}
.admin-view__badge--muted{background:var(--color-field-surface);color:var(--color-text-primary)}
.admin-view__row{padding:16px 18px;border-radius:24px;background:var(--color-field-surface)}
.admin-view__row--stack{align-items:flex-start}
.admin-view__segments{padding:4px;background:var(--color-field-surface);border-radius:999px}
.admin-view__segment{min-height:34px;padding:0 14px;background:transparent;color:var(--color-text-secondary)}
.admin-view__segment--active{background:#0A0A0A;color:#fff}
.admin-view__form{display:flex;flex-direction:column;gap:16px}
.admin-view__form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.admin-view__field{display:flex;flex-direction:column;gap:8px}
.admin-view__field input{min-height:50px;padding:0 16px;border-radius:18px}
.admin-view__field input[type="file"],.admin-view__field input[type="color"]{padding:10px 16px}
.admin-view__switch{display:flex;align-items:center;gap:10px;padding:14px 16px;border-radius:20px;background:var(--color-field-surface);font-size:14px;font-weight:600;color:var(--color-text-primary)}
.admin-view__switch input{accent-color:var(--color-secondary)}
.admin-view__profile{grid-template-columns:repeat(2,minmax(0,1fr))}
.admin-view__profile div{display:flex;flex-direction:column;gap:6px;padding:16px 18px;border-radius:22px;background:var(--color-field-surface)}
.admin-view__profile strong{font-size:15px;color:var(--color-text-primary)}
.admin-view__preference{width:100%;margin-top:16px;padding:16px 18px;border:none;border-radius:24px;background:var(--color-field-surface);display:flex;align-items:center;justify-content:space-between;gap:16px;text-align:left;color:var(--color-text-primary);font:inherit;cursor:pointer}
.admin-view__preference-copy{display:flex;flex-direction:column;gap:4px}
.admin-view__preference-copy strong{font-size:15px;line-height:1.1;color:var(--color-text-primary)}
.admin-view__preference-copy small{font-size:13px;line-height:1.45;color:var(--color-text-secondary)}
.admin-view__mini--inline{margin:0}
.admin-view__settings-toggle{position:relative;flex-shrink:0;width:44px;height:26px;border-radius:999px;background:color-mix(in srgb,var(--color-text-primary) 12%, transparent);transition:background-color .22s ease}
.admin-view__settings-toggle--on{background:var(--color-primary)}
.admin-view__settings-toggle-knob{position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:999px;background:var(--color-surface);transition:transform .25s cubic-bezier(.34,1.56,.64,1)}
.admin-view__settings-toggle--on .admin-view__settings-toggle-knob{transform:translateX(18px)}
.admin-view__spinner{animation:admin-view-spin .9s linear infinite}
@keyframes admin-view-spin{to{transform:rotate(360deg)}}
@media (max-width:1100px){.admin-view__metrics,.admin-view__grid--reports{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:767px){.admin-view{padding:26px 18px 118px}.admin-view__hero,.admin-view__toolbar,.admin-view__row,.admin-view__card-head,.admin-view__actions,.admin-view__footer{flex-direction:column;align-items:stretch}.admin-view__toolbar{grid-template-columns:1fr}.admin-view__pill,.admin-view__soft-button{width:100%}.admin-view__metrics,.admin-view__grid,.admin-view__form-grid,.admin-view__profile{grid-template-columns:1fr}}
@media (max-width:420px){.admin-view__metric,.admin-view__card{border-radius:28px}.admin-view__card h2{font-size:24px}}
</style>
