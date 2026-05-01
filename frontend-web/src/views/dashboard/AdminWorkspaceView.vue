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

      <header class="admin-view__header">
        <div class="admin-view__header-copy">
          <p class="admin-view__eyebrow">Platform Admin</p>
          <h1>{{ sectionMeta.title }}</h1>
          <p>{{ sectionMeta.description }}</p>
        </div>

        <button
          class="admin-view__icon-button"
          type="button"
          aria-label="Refresh admin data"
          :disabled="adminState.loading"
          @click="refreshWorkspace"
        >
          <RefreshCw :size="18" :class="{ 'admin-view__spin': adminState.loading }" />
        </button>
      </header>

      <section class="admin-view__summary" aria-label="Platform summary">
        <button class="admin-view__summary-item admin-view__summary-item--primary" type="button" @click="goToSection('schools')">
          <span>Schools</span>
          <strong>{{ schools.length }}</strong>
          <small>{{ activeSchoolCount }} active</small>
        </button>
        <button class="admin-view__summary-item" type="button" @click="goToSection('accounts')">
          <span>Admins</span>
          <strong>{{ campusAccounts.length }}</strong>
          <small>{{ activeCampusAccountCount }} active</small>
        </button>
        <button class="admin-view__summary-item" type="button" @click="goToSection('oversight')">
          <span>Requests</span>
          <strong>{{ pendingRequestCount }}</strong>
          <small>pending</small>
        </button>
      </section>

      <nav class="admin-view__tabs" aria-label="Admin sections">
        <button
          v-for="item in sectionTabs"
          :key="item.key"
          class="admin-view__tab"
          :class="{ 'admin-view__tab--active': section === item.key }"
          type="button"
          :aria-current="section === item.key ? 'page' : undefined"
          @click="goToSection(item.key)"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <section class="admin-view__tools" aria-label="Filters">
        <label class="admin-view__search">
          <Search :size="17" aria-hidden="true" />
          <input
            v-model.trim="searchQuery"
            :placeholder="sectionMeta.searchPlaceholder"
            type="search"
            inputmode="search"
            autocomplete="off"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
          >
        </label>

        <label v-if="showSchoolScope" class="admin-view__scope">
          <span>Scope</span>
          <select v-model="selectedSchoolModel">
            <option value="">All schools</option>
            <option
              v-for="school in schools"
              :key="school.school_id"
              :value="String(school.school_id)"
            >
              {{ school.school_name }}
            </option>
          </select>
        </label>
      </section>

      <p
        v-if="feedback.message"
        class="admin-view__feedback"
        :class="`admin-view__feedback--${feedback.type}`"
        role="status"
      >
        {{ feedback.message }}
      </p>

      <main class="admin-view__content">
        <template v-if="section === 'overview'">
          <section class="admin-view__panel admin-view__panel--accent">
            <div class="admin-view__panel-head">
              <div>
                <p class="admin-view__mini">Actions</p>
                <h2>Today</h2>
              </div>
              <span class="admin-view__status" :class="statusClass(adminState.statuses.schools)">
                {{ statusLabel(adminState.statuses.schools) }}
              </span>
            </div>

            <div class="admin-view__action-grid">
              <button class="admin-view__action" type="button" @click="openCreateSchool">
                <Plus :size="18" />
                <span>Create school</span>
              </button>
              <button class="admin-view__action" type="button" @click="goToSection('accounts')">
                <UserCog :size="18" />
                <span>Admin accounts</span>
              </button>
              <button class="admin-view__action" type="button" @click="goToSection('oversight')">
                <BellRing :size="18" />
                <span>Notify</span>
              </button>
              <button class="admin-view__action" type="button" @click="goToSection('oversight')">
                <Database :size="18" />
                <span>Retention</span>
              </button>
            </div>
          </section>

          <div class="admin-view__mobile-breath" aria-hidden="true" />
        </template>

        <template v-else-if="section === 'schools'">
          <section class="admin-view__section">
            <button class="admin-view__primary-action" type="button" @click="showCreateForm = !showCreateForm">
              <Plus :size="18" />
              <span>{{ showCreateForm ? 'Close form' : 'Create school' }}</span>
            </button>
          </section>

          <section v-if="showCreateForm" class="admin-view__panel">
            <div class="admin-view__panel-head">
              <div>
                <p class="admin-view__mini">Create</p>
                <h2>School + Admin</h2>
              </div>
              <button class="admin-view__icon-button admin-view__icon-button--flat" type="button" aria-label="Close create form" @click="showCreateForm = false">
                <X :size="18" />
              </button>
            </div>

            <form class="admin-view__form" @submit.prevent="submitCreateSchool">
              <label class="admin-view__field">
                <span>School Name</span>
                <input v-model.trim="createForm.school_name" required type="text" autocomplete="organization">
              </label>
              <label class="admin-view__field">
                <span>School Code</span>
                <input v-model.trim="createForm.school_code" type="text" autocapitalize="characters">
              </label>

              <div class="admin-view__swatches">
                <label class="admin-view__field admin-view__field--color">
                  <span>Primary</span>
                  <input v-model="createForm.primary_color" required type="color">
                </label>
                <label class="admin-view__field admin-view__field--color">
                  <span>Secondary</span>
                  <input v-model="createForm.secondary_color" required type="color">
                </label>
              </div>

              <label class="admin-view__field">
                <span>Admin Email</span>
                <input v-model.trim="createForm.school_it_email" required type="email" autocomplete="email">
              </label>
              <label class="admin-view__field">
                <span>Temp Password</span>
                <input v-model="createForm.school_it_password" type="text" autocomplete="new-password">
              </label>
              <label class="admin-view__field">
                <span>First Name</span>
                <input v-model.trim="createForm.school_it_first_name" required type="text" autocomplete="given-name">
              </label>
              <label class="admin-view__field">
                <span>Middle Name</span>
                <input v-model.trim="createForm.school_it_middle_name" type="text" autocomplete="additional-name">
              </label>
              <label class="admin-view__field">
                <span>Last Name</span>
                <input v-model.trim="createForm.school_it_last_name" required type="text" autocomplete="family-name">
              </label>
              <label class="admin-view__field">
                <span>Logo</span>
                <input type="file" accept=".png,.jpg,.jpeg,.svg,image/png,image/jpeg,image/svg+xml" @change="handleCreateLogoChange">
              </label>

              <button class="admin-view__primary-action" type="submit" :disabled="adminState.creatingSchool">
                <LoaderCircle v-if="adminState.creatingSchool" :size="18" class="admin-view__spin" />
                <Plus v-else :size="18" />
                <span>{{ adminState.creatingSchool ? 'Creating...' : 'Create school' }}</span>
              </button>
            </form>
          </section>

          <section class="admin-view__section">
            <div class="admin-view__section-title">
              <h2>Schools</h2>
              <span>{{ filteredSchools.length }}</span>
            </div>

            <div class="admin-view__card-list">
              <article
                v-for="school in filteredSchools"
                :key="school.school_id"
                class="admin-view__card"
              >
                <div class="admin-view__card-head">
                  <div>
                    <h3>{{ school.school_name }}</h3>
                    <p>{{ school.school_code || 'No code' }}</p>
                  </div>
                  <span class="admin-view__status" :class="school.active_status ? 'admin-view__status--ready' : 'admin-view__status--blocked'">
                    {{ school.active_status ? 'Active' : 'Off' }}
                  </span>
                </div>

                <div class="admin-view__meta-grid">
                  <span>Plan <strong>{{ formatSubscriptionLabel(school.subscription_status) }}</strong></span>
                  <span>Admin <strong>{{ resolveCampusAdminEmail(school.school_id) }}</strong></span>
                </div>

                <div class="admin-view__segment-group" aria-label="Subscription status">
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

                <div class="admin-view__button-row">
                  <button class="admin-view__secondary-action" type="button" @click="toggleSchoolActive(school)">
                    <ShieldCheck :size="17" />
                    <span>{{ school.active_status ? 'Deactivate' : 'Activate' }}</span>
                  </button>
                  <button class="admin-view__secondary-action" type="button" @click="openSchoolOversight(school.school_id)">
                    <ClipboardList :size="17" />
                    <span>Audit</span>
                  </button>
                </div>
              </article>
              <p v-if="!filteredSchools.length" class="admin-view__empty">No schools found.</p>
            </div>
          </section>
        </template>

        <template v-else-if="section === 'accounts'">
          <section class="admin-view__section">
            <div class="admin-view__section-title">
              <h2>Admin Accounts</h2>
              <span>{{ filteredCampusAccounts.length }}</span>
            </div>

            <div class="admin-view__card-list">
              <article
                v-for="account in filteredCampusAccounts"
                :key="account.user_id"
                class="admin-view__card"
              >
                <div class="admin-view__card-head">
                  <div>
                    <h3>{{ formatPersonName(account.first_name, account.last_name) }}</h3>
                    <p>{{ account.email }}</p>
                  </div>
                  <span class="admin-view__avatar">{{ abbreviate(account.school_name || account.email, 2) }}</span>
                </div>

                <div class="admin-view__meta-grid">
                  <span>School <strong>{{ account.school_name || 'No scope' }}</strong></span>
                  <span>Status <strong>{{ account.is_active ? 'Active' : 'Inactive' }}</strong></span>
                </div>

                <div class="admin-view__button-row">
                  <button class="admin-view__secondary-action" type="button" @click="toggleCampusAccount(account)">
                    <UserRoundX :size="17" />
                    <span>{{ account.is_active ? 'Deactivate' : 'Activate' }}</span>
                  </button>
                  <button class="admin-view__secondary-action admin-view__secondary-action--strong" type="button" @click="resetCampusPasswordFor(account)">
                    <KeyRound :size="17" />
                    <span>Reset</span>
                  </button>
                </div>
              </article>
              <p v-if="!filteredCampusAccounts.length" class="admin-view__empty">No admin accounts found.</p>
            </div>
          </section>
        </template>

        <template v-else-if="section === 'oversight'">
          <section class="admin-view__panel">
            <div class="admin-view__panel-head">
              <div>
                <p class="admin-view__mini">Notify</p>
                <h2>Dispatch</h2>
              </div>
              <span class="admin-view__status" :class="statusClass(adminState.statuses.notifications)">
                {{ statusLabel(adminState.statuses.notifications) }}
              </span>
            </div>

            <div class="admin-view__form admin-view__form--compact">
              <label class="admin-view__field">
                <span>Threshold %</span>
                <input v-model.number="dispatchForm.threshold_percent" min="1" max="100" type="number" inputmode="numeric">
              </label>
              <label class="admin-view__field">
                <span>Min Records</span>
                <input v-model.number="dispatchForm.min_records" min="1" max="100" type="number" inputmode="numeric">
              </label>
            </div>

            <div class="admin-view__button-row">
              <button class="admin-view__secondary-action" type="button" @click="dispatchNotifications('missed_events')">
                <Send :size="17" />
                <span>Missed</span>
              </button>
              <button class="admin-view__secondary-action admin-view__secondary-action--strong" type="button" @click="dispatchNotifications('low_attendance')">
                <BellRing :size="17" />
                <span>Low attendance</span>
              </button>
            </div>

            <p v-if="lastDispatchSummary" class="admin-view__result">
              Sent {{ lastDispatchSummary.sent || 0 }} / {{ lastDispatchSummary.processed_users || 0 }}
            </p>
          </section>

          <section class="admin-view__panel">
            <div class="admin-view__panel-head">
              <div>
                <p class="admin-view__mini">Retention</p>
                <h2>Data Rules</h2>
              </div>
              <span class="admin-view__status" :class="governanceForm.auto_delete_enabled ? 'admin-view__status--warn' : 'admin-view__status--muted'">
                {{ governanceForm.auto_delete_enabled ? 'Auto' : 'Manual' }}
              </span>
            </div>

            <form class="admin-view__form" @submit.prevent="saveGovernanceSettingsForSelectedSchool">
              <label class="admin-view__field">
                <span>Attendance Days</span>
                <input v-model.number="governanceForm.attendance_retention_days" min="30" max="3650" type="number" inputmode="numeric">
              </label>
              <label class="admin-view__field">
                <span>Audit Days</span>
                <input v-model.number="governanceForm.audit_log_retention_days" min="90" max="7300" type="number" inputmode="numeric">
              </label>
              <label class="admin-view__field">
                <span>Import Days</span>
                <input v-model.number="governanceForm.import_file_retention_days" min="7" max="3650" type="number" inputmode="numeric">
              </label>

              <label class="admin-view__switch">
                <input v-model="governanceForm.auto_delete_enabled" type="checkbox">
                <span>Auto-delete</span>
              </label>

              <button class="admin-view__primary-action" type="submit">
                <Check :size="18" />
                <span>Save rules</span>
              </button>
            </form>

            <div class="admin-view__button-row">
              <button class="admin-view__secondary-action" type="button" @click="runRetention(true)">
                <History :size="17" />
                <span>Dry run</span>
              </button>
              <button class="admin-view__secondary-action admin-view__secondary-action--danger" type="button" @click="runRetention(false)">
                <Database :size="17" />
                <span>Clean</span>
              </button>
            </div>

            <p v-if="lastRetentionRun" class="admin-view__result">
              {{ lastRetentionRun.summary || 'Retention finished.' }}
            </p>
          </section>

          <section class="admin-view__section">
            <div class="admin-view__section-title">
              <h2>Requests</h2>
              <span>{{ filteredGovernanceRequests.length }}</span>
            </div>
            <div class="admin-view__card-list">
              <article
                v-for="request in filteredGovernanceRequests"
                :key="request.id"
                class="admin-view__card"
              >
                <div class="admin-view__card-head">
                  <div>
                    <h3>{{ formatRequestTitle(request) }}</h3>
                    <p>{{ resolveSchoolName(request.school_id) }} · {{ formatDateTime(request.created_at) }}</p>
                  </div>
                  <span class="admin-view__status" :class="request.status === 'pending' ? 'admin-view__status--warn' : 'admin-view__status--ready'">
                    {{ prettify(request.status) }}
                  </span>
                </div>
                <p class="admin-view__compact-text">{{ request.reason || 'No reason.' }}</p>
                <div class="admin-view__button-row">
                  <button class="admin-view__secondary-action admin-view__secondary-action--strong" type="button" @click="reviewRequest(request, 'approved')">
                    <Check :size="17" />
                    <span>Approve</span>
                  </button>
                  <button class="admin-view__secondary-action" type="button" @click="reviewRequest(request, 'rejected')">
                    <X :size="17" />
                    <span>Reject</span>
                  </button>
                </div>
              </article>
              <p v-if="!filteredGovernanceRequests.length" class="admin-view__empty">No requests.</p>
            </div>
          </section>

          <section class="admin-view__section">
            <div class="admin-view__section-title">
              <h2>Logs</h2>
              <span>{{ oversightLogFeed.length }}</span>
            </div>
            <div class="admin-view__list">
              <article
                v-for="item in oversightLogFeed"
                :key="`${item.kind}-${item.id}`"
                class="admin-view__row"
              >
                <div class="admin-view__row-main">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.meta }}</span>
                </div>
                <span class="admin-view__status admin-view__status--muted">{{ item.badge }}</span>
              </article>
              <p v-if="!oversightLogFeed.length" class="admin-view__empty">No logs.</p>
            </div>
          </section>
        </template>

        <template v-else>
          <section class="admin-view__panel">
            <div class="admin-view__panel-head">
              <div>
                <p class="admin-view__mini">Session</p>
                <h2>{{ displayName }}</h2>
              </div>
              <span class="admin-view__status admin-view__status--ready">Admin</span>
            </div>

            <div class="admin-view__meta-grid admin-view__meta-grid--profile">
              <span>Email <strong>{{ activeUser?.email || 'platform.admin@valid8.local' }}</strong></span>
              <span>Scope <strong>Platform</strong></span>
              <span>Schools <strong>{{ schools.length }}</strong></span>
              <span>Admins <strong>{{ activeCampusAccountCount }}</strong></span>
            </div>

            <button
              class="admin-view__preference"
              type="button"
              :aria-pressed="isDarkMode"
              @click="toggleDarkMode"
            >
              <span>
                <Moon :size="18" />
                Dark mode
              </span>
              <span class="admin-view__toggle" :class="{ 'admin-view__toggle--on': isDarkMode }">
                <span />
              </span>
            </button>
          </section>

          <section class="admin-view__section">
            <div class="admin-view__section-title">
              <h2>API Map</h2>
              <span>{{ adminFunctionCards.length }}</span>
            </div>
            <div class="admin-view__function-grid">
              <article
                v-for="item in adminFunctionCards"
                :key="item.key"
                class="admin-view__function"
              >
                <component :is="item.icon" :size="16" />
                <div>
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.endpoint }}</span>
                </div>
              </article>
            </div>
          </section>
        </template>
      </main>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BellRing,
  Building2,
  Check,
  ClipboardList,
  Database,
  History,
  KeyRound,
  LayoutDashboard,
  LoaderCircle,
  Moon,
  Plus,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  UserCog,
  UserRound,
  UserRoundX,
  X,
} from 'lucide-vue-next'
import SchoolItTopHeader from '@/components/dashboard/SchoolItTopHeader.vue'
import { applyTheme, isDarkMode, loadUnbrandedTheme, toggleDarkMode } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'
import { useAdminWorkspaceData } from '@/composables/useAdminWorkspaceData.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { adminDashboardPreviewData } from '@/data/adminDashboardPreview.js'

const props = defineProps({
  preview: { type: Boolean, default: false },
  section: { type: String, default: 'overview' },
})

const router = useRouter()
const route = useRoute()
const section = computed(() => props.section)
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
  lastDispatchSummary,
  lastRetentionRun,
  initializeAdminWorkspaceData,
  refreshAdminWorkspaceData,
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

const sectionTabs = [
  { key: 'overview', label: 'Home', icon: LayoutDashboard },
  { key: 'schools', label: 'Schools', icon: Building2 },
  { key: 'accounts', label: 'Admins', icon: UserRound },
  { key: 'oversight', label: 'Audit', icon: ShieldCheck },
  { key: 'profile', label: 'Profile', icon: UserRound },
]

const sectionMetaMap = {
  overview: {
    title: 'Admin',
    description: 'Schools, accounts, audit, retention.',
    searchPlaceholder: 'Search platform',
  },
  schools: {
    title: 'Schools',
    description: 'Create and control schools.',
    searchPlaceholder: 'Search schools',
  },
  accounts: {
    title: 'Admins',
    description: 'Activate and reset school admins.',
    searchPlaceholder: 'Search admins',
  },
  oversight: {
    title: 'Audit',
    description: 'Requests, logs, notifications.',
    searchPlaceholder: 'Search audit',
  },
  profile: {
    title: 'Profile',
    description: 'Session and API map.',
    searchPlaceholder: 'Search API map',
  },
}

const adminFunctionCards = [
  { key: 'create-school', label: 'Create school', endpoint: 'POST /api/school/admin/create-school-it', icon: Plus },
  { key: 'list-schools', label: 'List schools', endpoint: 'GET /api/school/admin/list', icon: Building2 },
  { key: 'school-status', label: 'School status', endpoint: 'PATCH /api/school/admin/{id}/status', icon: ShieldCheck },
  { key: 'list-admins', label: 'List admins', endpoint: 'GET /api/school/admin/school-it-accounts', icon: UserCog },
  { key: 'admin-status', label: 'Admin status', endpoint: 'PATCH /api/school/admin/school-it-accounts/{id}/status', icon: UserRoundX },
  { key: 'reset-password', label: 'Reset password', endpoint: 'POST /api/school/admin/school-it-accounts/{id}/reset-password', icon: KeyRound },
  { key: 'audit-logs', label: 'Audit logs', endpoint: 'GET /api/audit-logs', icon: ClipboardList },
  { key: 'notification-logs', label: 'Notification logs', endpoint: 'GET /api/notifications/logs', icon: BellRing },
  { key: 'missed-events', label: 'Missed events', endpoint: 'POST /api/notifications/dispatch/missed-events', icon: Send },
  { key: 'low-attendance', label: 'Low attendance', endpoint: 'POST /api/notifications/dispatch/low-attendance', icon: BellRing },
  { key: 'governance-settings', label: 'Read rules', endpoint: 'GET /api/governance/settings/me', icon: Database },
  { key: 'save-governance', label: 'Save rules', endpoint: 'PUT /api/governance/settings/me', icon: Check },
  { key: 'governance-requests', label: 'Requests', endpoint: 'GET /api/governance/requests', icon: ClipboardList },
  { key: 'review-request', label: 'Review request', endpoint: 'PATCH /api/governance/requests/{id}', icon: Check },
  { key: 'run-retention', label: 'Run retention', endpoint: 'POST /api/governance/run-retention', icon: History },
]

const sectionMeta = computed(() => sectionMetaMap[props.section] || sectionMetaMap.overview)
const activeUser = computed(() => (props.preview ? adminDashboardPreviewData.user : currentUser.value))
const displayName = computed(() => {
  const user = activeUser.value
  return [user?.first_name, user?.last_name].filter(Boolean).join(' ').trim() || user?.email || 'Platform Admin'
})
const avatarUrl = computed(() => activeUser.value?.avatar_url || '')
const initials = computed(() => abbreviate(displayName.value, 2))
const platformLabel = computed(() => 'VALID8 Platform')
const showSchoolScope = computed(() => schools.value.length > 0 && section.value !== 'profile')
const activeSchoolCount = computed(() => schools.value.filter((item) => item.active_status).length)
const activeCampusAccountCount = computed(() => campusAccounts.value.filter((item) => item.is_active).length)
const pendingRequestCount = computed(() => governanceRequests.value.filter((item) => item.status === 'pending').length)
const selectedGovernanceSettings = computed(() => governanceSettingsBySchool.value?.[Number(selectedSchoolId.value)] || null)
const selectedSchoolModel = computed({
  get: () => (selectedSchoolId.value ? String(selectedSchoolId.value) : ''),
  set: (value) => selectAdminSchool(value ? Number(value) : null).catch((error) => {
    pushFeedback('error', error?.message || 'Unable to update school scope.')
  }),
})
const filteredSchools = computed(() => filterItems(schools.value, searchQuery.value, (school) => [
  school.school_name,
  school.school_code,
  school.subscription_status,
]))
const filteredCampusAccounts = computed(() => filterItems(campusAccounts.value, searchQuery.value, (item) => [
  item.email,
  item.first_name,
  item.last_name,
  item.school_name,
]))
const filteredAuditLogs = computed(() => filterItems(auditLogs.value, searchQuery.value, (item) => [
  item.action,
  item.status,
  item.details,
  resolveSchoolName(item.school_id),
]))
const filteredNotificationLogs = computed(() => filterItems(notificationLogs.value, searchQuery.value, (item) => [
  item.subject,
  item.category,
  item.status,
  resolveSchoolName(item.school_id),
]))
const filteredGovernanceRequests = computed(() => governanceRequests.value.filter((item) => {
  if (selectedSchoolId.value && Number(item?.school_id) !== Number(selectedSchoolId.value)) return false
  return matchesSearch(searchQuery.value, [
    item.request_type,
    item.status,
    item.reason,
    resolveSchoolName(item.school_id),
  ])
}))
const oversightLogFeed = computed(() => [
  ...filteredAuditLogs.value.slice(0, 8).map((item) => ({
    kind: 'audit',
    id: item.id,
    title: prettify(item.action),
    meta: `${resolveSchoolName(item.school_id)} · ${formatDateTime(item.created_at)}`,
    badge: prettify(item.status),
  })),
  ...filteredNotificationLogs.value.slice(0, 8).map((item) => ({
    kind: 'notification',
    id: item.id,
    title: item.subject || prettify(item.category),
    meta: `${resolveSchoolName(item.school_id)} · ${formatDateTime(item.created_at)}`,
    badge: prettify(item.status),
  })),
])

watch(selectedGovernanceSettings, (value) => {
  governanceForm.attendance_retention_days = Number(value?.attendance_retention_days || 365)
  governanceForm.audit_log_retention_days = Number(value?.audit_log_retention_days || 365)
  governanceForm.import_file_retention_days = Number(value?.import_file_retention_days || 30)
  governanceForm.auto_delete_enabled = Boolean(value?.auto_delete_enabled)
}, { immediate: true })

watch(lastPasswordReset, (value) => {
  if (value?.temporary_password) {
    pushFeedback('success', `Temp password for ${value.email || 'admin'}: ${value.temporary_password}`)
  }
})

onMounted(async () => {
  applyTheme(loadUnbrandedTheme())
  if (!props.preview) await initializeDashboardSession().catch(() => null)
  await initializeAdminWorkspaceData().catch((error) => {
    pushFeedback('error', error?.message || 'Unable to load admin data.')
  })
})

onBeforeUnmount(() => {
  if (feedbackTimeoutId) window.clearTimeout(feedbackTimeoutId)
})

async function handleLogout() {
  await logout()
}

async function refreshWorkspace() {
  await refreshAdminWorkspaceData({ force: true }).catch((error) => {
    pushFeedback('error', error?.message || 'Unable to refresh admin data.')
  })
}

function openCreateSchool() {
  showCreateForm.value = true
  goToSection('schools')
}

function goToSection(nextSection) {
  const base = props.preview ? '/exposed/admin' : '/admin'
  const nextPath = nextSection === 'overview' ? base : `${base}/${nextSection}`
  if (route.path !== nextPath) router.push(nextPath)
}

async function submitCreateSchool() {
  try {
    const created = await createAdminSchool({
      ...createForm,
      school_code: createForm.school_code || undefined,
      school_it_middle_name: createForm.school_it_middle_name || undefined,
      school_it_password: createForm.school_it_password || undefined,
    })
    pushFeedback('success', `Created ${created?.school?.school_name || createForm.school_name}.`)
    Object.assign(createForm, createDefaultSchoolForm())
    showCreateForm.value = false
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to create school.')
  }
}

function handleCreateLogoChange(event) {
  createForm.logo = event?.target?.files?.[0] || null
}

async function toggleSchoolActive(school) {
  try {
    await saveAdminSchoolStatus(school.school_id, { active_status: !school.active_status })
    pushFeedback('success', `${school.school_name} updated.`)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to update school.')
  }
}

async function setSchoolSubscription(school, value) {
  if (school.subscription_status === value) return
  try {
    await saveAdminSchoolStatus(school.school_id, { subscription_status: value })
    pushFeedback('success', `${school.school_name}: ${formatSubscriptionLabel(value)}.`)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to update subscription.')
  }
}

async function toggleCampusAccount(account) {
  try {
    await saveAdminCampusAccountStatus(account.user_id, !account.is_active)
    pushFeedback('success', `${formatPersonName(account.first_name, account.last_name)} updated.`)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to update account.')
  }
}

async function resetCampusPasswordFor(account) {
  try {
    await resetAdminCampusPassword(account.user_id)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to reset password.')
  }
}

async function dispatchNotifications(kind) {
  try {
    const params = kind === 'low_attendance'
      ? {
          school_id: selectedSchoolId.value,
          threshold_percent: dispatchForm.threshold_percent,
          min_records: dispatchForm.min_records,
        }
      : { school_id: selectedSchoolId.value }
    const result = await dispatchAdminNotification(kind, params)
    pushFeedback('success', `${prettify(result?.category || kind)} sent: ${result?.sent || 0}.`)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to dispatch notifications.')
  }
}

async function saveGovernanceSettingsForSelectedSchool() {
  try {
    await saveAdminGovernanceSettings({
      attendance_retention_days: governanceForm.attendance_retention_days,
      audit_log_retention_days: governanceForm.audit_log_retention_days,
      import_file_retention_days: governanceForm.import_file_retention_days,
      auto_delete_enabled: governanceForm.auto_delete_enabled,
    }, { schoolId: selectedSchoolId.value })
    pushFeedback('success', 'Rules saved.')
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to save rules.')
  }
}

async function reviewRequest(item, status) {
  try {
    await reviewAdminGovernanceRequest(item.id, { status })
    pushFeedback('success', `${formatRequestTitle(item)} ${prettify(status)}.`)
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to update request.')
  }
}

async function runRetention(dryRun) {
  try {
    const result = await runAdminRetentionCleanup({ dry_run: dryRun }, { schoolId: selectedSchoolId.value })
    pushFeedback('success', result?.summary || 'Retention finished.')
  } catch (error) {
    pushFeedback('error', error?.message || 'Unable to run retention.')
  }
}

function openSchoolOversight(schoolId) {
  selectedSchoolModel.value = String(schoolId)
  goToSection('oversight')
}

function resolveSchoolName(schoolId) {
  return schools.value.find((item) => Number(item?.school_id) === Number(schoolId))?.school_name || `School #${schoolId}`
}

function resolveCampusAdminEmail(schoolId) {
  return campusAccounts.value.find((item) => Number(item?.school_id) === Number(schoolId))?.email || 'No admin'
}

function formatPersonName(firstName, lastName) {
  return [firstName, lastName].filter(Boolean).join(' ').trim() || 'School Admin'
}

function formatSubscriptionLabel(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized === 'trial') return 'Trial'
  if (normalized === 'suspended') return 'Suspended'
  return 'Active'
}

function formatRequestTitle(item) {
  return `${prettify(item.request_type)} request`
}

function formatDateTime(value) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(value))
  } catch {
    return String(value || '')
  }
}

function prettify(value) {
  return String(value || '').replace(/_/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

function abbreviate(value, maxLetters = 4) {
  const words = String(value || '').trim().match(/[A-Za-z0-9]+/g) || []
  return words.slice(0, maxLetters).map((word) => word[0]?.toUpperCase() || '').join('') || 'AD'
}

function matchesSearch(query, values) {
  const needle = String(query || '').trim().toLowerCase()
  return !needle || values.some((value) => String(value || '').toLowerCase().includes(needle))
}

function filterItems(items, query, mapper) {
  return items.filter((item) => matchesSearch(query, mapper(item)))
}

function statusLabel(value) {
  const normalized = String(value || 'idle')
  if (normalized === 'ready') return 'Ready'
  if (normalized === 'loading') return 'Loading'
  if (normalized === 'blocked') return 'Blocked'
  if (normalized === 'absent') return 'None'
  if (normalized === 'error') return 'Error'
  return 'Idle'
}

function statusClass(value) {
  const normalized = String(value || 'idle')
  if (normalized === 'ready') return 'admin-view__status--ready'
  if (normalized === 'loading') return 'admin-view__status--warn'
  if (normalized === 'blocked' || normalized === 'error') return 'admin-view__status--blocked'
  return 'admin-view__status--muted'
}

function pushFeedback(type, message) {
  if (feedbackTimeoutId) window.clearTimeout(feedbackTimeoutId)
  feedback.type = type
  feedback.message = message
  feedbackTimeoutId = window.setTimeout(() => {
    feedback.type = 'success'
    feedback.message = ''
  }, 4200)
}

function createDefaultSchoolForm() {
  return {
    school_name: '',
    school_code: '',
    primary_color: '#0891B2',
    secondary_color: '#22C55E',
    school_it_email: '',
    school_it_first_name: '',
    school_it_middle_name: '',
    school_it_last_name: '',
    school_it_password: '',
    logo: null,
  }
}

const subscriptionOptions = ['active', 'trial', 'suspended']
</script>

<style scoped>
.admin-view {
  min-height: 100vh;
  padding: calc(env(safe-area-inset-top, 0px) + 18px) 14px calc(env(safe-area-inset-bottom, 0px) + 108px);
  background: var(--color-bg);
  color: var(--color-text-primary);
  font-family: Manrope, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.admin-view__shell {
  width: 100%;
  max-width: 1040px;
  margin: 0 auto;
}

.admin-view__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
}

.admin-view__header-copy {
  min-width: 0;
}

.admin-view__eyebrow,
.admin-view__mini,
.admin-view__field span,
.admin-view__scope span {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.admin-view__header h1 {
  margin: 4px 0 0;
  color: var(--color-text-primary);
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
}

.admin-view__header p:not(.admin-view__eyebrow) {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 0.92rem;
  line-height: 1.45;
}

.admin-view__icon-button,
.admin-view__section-title button {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(10px);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.admin-view__icon-button:hover:not(:disabled) {
  background: #ffffff;
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-1px);
}

.admin-view__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.admin-view__summary-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  min-height: 100px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
  transition: all 0.24s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.admin-view__summary-item:hover {
  background: #ffffff;
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.admin-view__summary-item--primary {
  background: color-mix(in srgb, var(--color-primary) 8%, rgba(255, 255, 255, 0.9));
  border-color: color-mix(in srgb, var(--color-primary) 30%, transparent);
}

.admin-view__summary-item--primary strong {
  color: var(--color-primary);
}

.admin-view__summary-item strong {
  margin-top: auto;
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
}

.admin-view__tabs {
  position: sticky;
  top: 12px;
  z-index: 8;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 4px;
  margin-top: 16px;
  padding: 4px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.admin-view__tab {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 58px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.admin-view__tab:hover:not(.admin-view__tab--active) {
  color: var(--color-text-primary);
  background: rgba(0, 0, 0, 0.03);
}

.admin-view__tab--active {
  background: var(--color-primary);
  color: #ffffff;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary) 25%, transparent);
}

.admin-view__tools {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.admin-view__search,
.admin-view__scope {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding: 0 16px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--color-text-primary);
  transition: all 0.2s ease;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}

.admin-view__search:focus-within,
.admin-view__scope:focus-within {
  border-color: var(--color-primary);
  background: #ffffff;
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 8%, transparent);
}

.admin-view__search input,
.admin-view__scope select {
  color: var(--color-text-primary);
  font-size: 0.92rem;
}

.admin-view__panel,
.admin-view__section,
.admin-view__card {
  padding: 24px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
}

.admin-view__panel--accent {
  background: linear-gradient(135deg, color-mix(in srgb, var(--color-primary) 5%, rgba(255, 255, 255, 0.9)) 0%, rgba(255, 255, 255, 0.9) 100%);
  border-color: color-mix(in srgb, var(--color-primary) 15%, transparent);
}

.admin-view__panel-head h2,
.admin-view__section-title h2,
.admin-view__card h3 {
  color: var(--color-text-primary);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.admin-view__action,
.admin-view__primary-action,
.admin-view__secondary-action {
  min-height: 48px;
  border-radius: 12px;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.admin-view__primary-action {
  background: var(--color-primary);
  color: #ffffff;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.admin-view__secondary-action {
  background: rgba(0, 0, 0, 0.03);
  color: var(--color-text-primary);
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
}

.admin-view__secondary-action:hover {
  background: rgba(0, 0, 0, 0.05);
  border-color: color-mix(in srgb, var(--color-border) 60%, transparent);
}

.admin-view__field input {
  min-height: 50px;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 12px;
  padding: 0 16px;
  color: var(--color-text-primary);
}

.admin-view__list,
.admin-view__card-list,
.admin-view__form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-view__function {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.admin-view__function svg {
  margin-top: 2px;
  color: var(--color-primary);
}

.admin-view__function strong,
.admin-view__row-main strong {
  display: block;
  overflow-wrap: anywhere;
  color: var(--color-text-primary);
  font-size: 0.86rem;
  line-height: 1.25;
}

.admin-view__function span,
.admin-view__row-main span,
.admin-view__card p,
.admin-view__compact-text,
.admin-view__result,
.admin-view__empty {
  margin: 3px 0 0;
  overflow-wrap: anywhere;
  color: var(--color-text-secondary);
  font-size: 0.78rem;
  line-height: 1.4;
}

.admin-view__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--color-border) 40%, transparent);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.admin-view__row-main {
  min-width: 0;
}

.admin-view__status {
  border-radius: 999px;
  font-weight: 700;
  padding: 4px 12px;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.admin-view__status--ready {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent);
}

.admin-view__status--warn {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.admin-view__status--blocked {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.admin-view__meta-grid span {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid color-mix(in srgb, var(--color-border) 30%, transparent);
  color: var(--color-text-muted);
}

.admin-view__meta-grid strong {
  color: var(--color-text-primary);
}

.admin-view__segment-group {
  background: rgba(0, 0, 0, 0.03);
  padding: 4px;
  border-radius: 12px;
}

.admin-view__segment--active {
  background: var(--color-primary);
  color: #ffffff;
}

@media (min-width: 720px) {
  .admin-view { padding: 0 32px; }
  .admin-view__header h1 { font-size: 2.8rem; }
  .admin-view__content { gap: 24px; }
}
</style>
