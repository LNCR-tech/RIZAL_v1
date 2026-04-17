<template>
  <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <div class="sg-title-row">
        <button class="sg-sub-back" type="button" @click="goBack">
          <ArrowLeft :size="20" />
        </button>
        <h1 class="sg-sub-title">Manage Events</h1>
      </div>
    </header>

    <div v-if="isLoading" class="sg-sub-loading dashboard-enter dashboard-enter--2">
      <p>Loading events...</p>
    </div>

    <div v-else-if="loadError" class="sg-sub-error dashboard-enter dashboard-enter--2">
      <p>{{ loadError }}</p>
      <button class="sg-sub-action" type="button" @click="reload">Try Again</button>
    </div>

    <template v-else>
      <div class="sg-summary-grid dashboard-enter dashboard-enter--2">
        <div class="sg-summary-card">
          <span class="sg-summary-val">{{ events.length }}</span>
          <span class="sg-summary-lbl">Total Events</span>
        </div>
        <div class="sg-summary-card">
          <span class="sg-summary-val" style="color: #3498db">{{ upcomingCount }}</span>
          <span class="sg-summary-lbl">Upcoming</span>
        </div>
        <div class="sg-summary-card">
          <span class="sg-summary-val" style="color: #27ae60">{{ ongoingCount }}</span>
          <span class="sg-summary-lbl">Ongoing</span>
        </div>
        <div class="sg-summary-card">
          <span class="sg-summary-val" style="color: #95a5a6">{{ completedCount }}</span>
          <span class="sg-summary-lbl">Completed</span>
        </div>
      </div>

      <div class="sg-sub-toolbar dashboard-enter dashboard-enter--3" :class="{'is-creating': isCreating}">
        <div class="sg-sub-search-shell sg-sub-search-shell--grow">
          <input
            v-model="searchQuery"
            type="text"
            class="sg-sub-search-input"
            placeholder="Search events"
          />
          <Search :size="18" style="color: var(--color-primary);" />
        </div>

        <button
          v-if="canViewSanctionsDashboard"
          class="sg-sub-action sg-sub-action--sanctions"
          type="button"
          @click="openSanctionsDashboard"
        >
          Sanctions
        </button>
        
        <div v-if="!isCreating" class="sg-create-wrapper">
          <button v-show="!isCreating" class="sg-create-event-btn" type="button" @click="openCreateForm">
            <Plus :size="20" />
            <span class="sg-create-event-btn__label">Create<br>Event</span>
          </button>
        </div>
      </div>

      <section
        v-if="isCreating"
        class="sg-create-panel dashboard-enter dashboard-enter--4"
        :class="{ 'map-is-fullscreen': isMapFullscreen }"
      >
        <div class="sg-create-form">
          <header class="sg-create-form-header">
            <button class="sg-create-event-btn sg-create-event-btn--inner" type="button" @click="closeCreateForm">
              <Plus :size="20" />
              <span class="sg-create-event-btn__label">Create<br>Event</span>
            </button>
          </header>
          
          <form class="sg-event-fields" @submit.prevent="submitEvent">
            <div class="sg-event-fields-grid">
              <label class="sg-field-label sg-field-label--wide">
                Event Name
                <input v-model="form.name" type="text" placeholder="e.g. Orientation" required />
              </label>
              
              <label class="sg-field-label sg-field-label--wide">
                Location
                <input v-model="form.location_name" type="text" placeholder="e.g. University Campus" required />
              </label>
              
              <label class="sg-field-label">
                Start date & time
                <input v-model="form.start_time" type="datetime-local" required />
              </label>
              
              <label class="sg-field-label">
                End date & time
                <input v-model="form.end_time" type="datetime-local" required />
              </label>
            </div>
            
            <div class="sg-map-section">
              <p class="sg-map-section-title">Please Select Location for Attendance</p>
              
              <div class="sg-map-frame">
                <div 
                  class="sg-map-container"
                  :class="{ 'is-fullscreen': isMapFullscreen }"
                >
                  <div id="sg-leaflet-preview" class="sg-leaflet-preview" @click="toggleFullscreenMap"></div>
                  
                  <div v-if="isMapFullscreen" class="sg-map-fullscreen-overlay">
                    <button class="sg-map-confirm-btn" type="button" @click.stop="toggleFullscreenMap">
                      Confirm Location
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="sg-map-controls">
                <button class="sg-map-btn" type="button" @click="useCurrentLocation">Use Current Location</button>
                <button class="sg-map-btn sg-map-btn--clear" type="button" @click="clearLocation">
                  <Trash2 :size="14" style="color:#e74c3c" /> <span style="color:#e74c3c">Clear</span>
                </button>
              </div>
              
              <div class="sg-coord-grid">
                <label class="sg-field-label">
                  Latitude
                  <input v-model="form.latitude" type="number" step="any" placeholder="0.00000" />
                </label>
                <label class="sg-field-label">
                  Longitude
                  <input v-model="form.longitude" type="number" step="any" placeholder="0.00000" />
                </label>
                <label class="sg-field-label">
                  Allowed Radius
                  <input v-model="form.radius_meters" type="number" placeholder="100 meters" />
                </label>
                <label class="sg-field-label">
                  Max GPS Accuracy
                  <input v-model="form.gps_accuracy" type="number" placeholder="50 meters" />
                </label>
              </div>
              
              <label class="sg-checkbox-label">
                <input v-model="form.require_geofence" type="checkbox" />
                <span class="sg-checkbox-custom"></span>
                Require students to be inside this geofence when signing in.
              </label>
            </div>

            <section
              class="sg-sanctions-panel"
              :class="{ 'sg-sanctions-panel--locked': !canConfigureEventSanctions }"
            >
              <header class="sg-sanctions-panel__header">
                <p class="sg-sanctions-panel__eyebrow">Optional</p>
                <h3 class="sg-sanctions-panel__title">Sanctions Setup</h3>
              </header>

              <div
                v-if="canConfigureEventSanctions && hasSavedCreateSanctionsTemplate"
                class="sg-sanctions-recommendation"
              >
                <div class="sg-sanctions-recommendation__content">
                  <p class="sg-sanctions-recommendation__eyebrow">Recommended</p>
                  <p class="sg-sanctions-recommendation__title">Use the last saved sanctions template</p>
                  <p class="sg-sanctions-recommendation__copy">
                    {{ savedCreateSanctionsTemplateSummary }}
                  </p>
                </div>
                <button
                  class="sg-sanctions-recommendation__action"
                  type="button"
                  :disabled="isSubmitting"
                  @click="applySavedCreateSanctionsTemplate"
                >
                  Use Template
                </button>
              </div>

              <div class="sg-sanctions-toggle">
                <p class="sg-sanctions-toggle__label">Enable sanctions rules for this event</p>
                <button
                  class="sg-sanctions-toggle__button"
                  :class="{ 'sg-sanctions-toggle__button--enabled': canConfigureEventSanctions && isCreateSanctionsEnabled }"
                  type="button"
                  :disabled="isSubmitting || !canConfigureEventSanctions"
                  @click="toggleCreateSanctionsEnabled"
                >
                  {{
                    canConfigureEventSanctions
                      ? (isCreateSanctionsEnabled ? 'Disable' : 'Enable')
                      : 'No Access'
                  }}
                </button>
              </div>
              <p v-if="!canConfigureEventSanctions" class="sg-sanctions-toggle__hint">
                Requires an active <strong>SSG/SG/ORG</strong> governance role or sanctions permission.
              </p>

              <EventSanctionConfigPanel
                v-if="canConfigureEventSanctions && isCreateSanctionsEnabled"
                v-model="createSanctionsConfig"
                :disabled="isSubmitting"
                :show-enabled-toggle="false"
              />

              <EventDelegationConfigPanel
                v-if="canConfigureEventSanctions && isCreateSanctionsEnabled"
                v-model="createSanctionsDelegations"
                :governance-units="governanceUnits"
                :disabled="isSubmitting"
              />
            </section>
             
            <button type="submit" class="sg-submit-event" :disabled="isSubmitting">
              {{ isSubmitting ? 'Creating...' : 'Create Event' }}
            </button>
            <p class="sg-form-note">New governance events are created with the default upcoming status.</p>
          </form>
        </div>
      </section>

      <div class="sg-sub-card dashboard-enter dashboard-enter--4">
        <div v-if="filteredEvents.length" class="sg-events-list">
          <div
            v-for="event in filteredEvents"
            :key="event.id"
            class="sg-event-swipe-container"
            :class="{ 'sg-event-swipe-container--open': isEventSwipeOpen(event.id) }"
          >
            <div class="sg-event-actions-bg">
              <button
                class="sg-action-icon sg-action-delete"
                type="button"
                :disabled="isMutatingEvent"
                aria-label="Delete Event"
                @pointerdown.stop
                @click.stop="deleteManagedEvent(event)"
              >
                <Trash2 :size="18" />
              </button>
              <button
                class="sg-action-icon sg-action-edit"
                type="button"
                :disabled="isMutatingEvent"
                aria-label="Edit Event"
                @pointerdown.stop
                @click.stop="editManagedEvent(event)"
              >
                <Edit2 :size="18" />
              </button>
            </div>
            
            <article
              class="sg-event-row"
              :style="getEventSwipeStyle(event.id)"
              @click="handleEventRowClick(event, $event)"
              @pointerdown="onEventPointerDown(event.id, $event)"
              @pointermove="onEventPointerMove(event.id, $event)"
              @pointerup="onEventPointerEnd(event.id, $event)"
              @pointercancel="onEventPointerCancel(event.id, $event)"
              @lostpointercapture="onEventPointerCancel(event.id, $event)"
            >
              <div class="sg-event-info">
                <h3 class="sg-event-name">{{ event.title || event.name || 'Untitled' }}</h3>
                <span v-if="event.start_datetime || event.start_time" class="sg-event-date">{{ formatDate(event.start_datetime || event.start_time) }}</span>
              </div>
              
              <div class="sg-action-pill">
                <div class="sg-action-thumb">
                  <ArrowRight :size="16" />
                </div>
                <span class="sg-action-text" v-if="['upcoming', 'active', 'ongoing'].includes(String(event.status || 'upcoming').toLowerCase())">Manage</span>
                <span class="sg-action-text" v-else>View</span>
              </div>
            </article>
          </div>
        </div>
        <p v-else class="sg-sub-empty">No events found matching your search.</p>
      </div>
    </template>
  </section>

  <EventEditorSheet
    :is-open="isEventEditorOpen"
    :event="editingEvent"
    title="Edit Governance Event"
    description="Update the event details using the same backend fields the governance event API accepts."
    submit-label="Save Event"
    :saving="isMutatingEvent"
    :error-message="eventEditorError"
    :show-sanctions-panels="true"
    :can-configure-event-sanctions="canConfigureEventSanctions"
    :sanctions-config="editingSanctionsConfig"
    :sanctions-delegations="editingSanctionsDelegations"
    :governance-units="governanceUnits"
    :sanctions-loading="sanctionsPanelLoading"
    :sanctions-error-message="sanctionsPanelError"
    @close="closeEventEditor"
    @save="saveEventEdits"
  />
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})
import { ArrowLeft, ArrowRight, Search, Plus, Trash2, Edit2 } from 'lucide-vue-next'
import EventEditorSheet from '@/components/events/EventEditorSheet.vue'
import EventSanctionConfigPanel from '@/components/events/EventSanctionConfigPanel.vue'
import EventDelegationConfigPanel from '@/components/events/EventDelegationConfigPanel.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import {
  BackendApiError,
  createGovernanceEvent,
  deleteEvent as deleteBackendEvent,
  getEventSanctionConfig,
  getEventSanctionDelegation,
  getEvents,
  getGovernanceAccess,
  getGovernanceUnits,
  getGovernanceUnitDetail,
  upsertEventSanctionConfig,
  upsertEventSanctionDelegation,
  updateEvent as updateBackendEvent,
} from '@/services/backendApi.js'
import { getCurrentPositionOrThrow } from '@/services/devicePermissions.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'
import {
  getGovernanceUnitsForAction,
  normalizeGovernanceContext,
} from '@/services/governanceScope.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const route = useRoute()
const router = useRouter()
const {
  apiBaseUrl,
  token,
  dashboardState,
  isSchoolItSession,
  isAdminSession,
  sessionHasRole,
} = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { isLoading: sgLoading, permissionCodes, activeUnitId, acronym } = useSgDashboard(props.preview)
const governanceUnitId = ref(null)
const governanceContext = ref('')
const governanceUnitDetailCache = new Map()

const GOVERNANCE_EVENT_UNIT_ID_STORAGE_KEY = 'aura_cached_governance_unit_id'
const GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY = 'aura_cached_governance_context'
const GOVERNANCE_EVENT_USER_ID_STORAGE_KEY = 'aura_cached_governance_user_id'
const GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY = 'aura_cached_governance_session_id'
const GOVERNANCE_EVENT_SANCTIONS_TEMPLATE_STORAGE_KEY = 'aura_cached_governance_event_sanctions_template'
const LEGACY_SSG_UNIT_ID_STORAGE_KEY = 'aura_cached_ssg_unit_id'

const isLoading = ref(true)
const loadError = ref('')
const events = ref([])
const searchQuery = ref('')
const isMutatingEvent = ref(false)
const isEventEditorOpen = ref(false)
const editingEvent = ref(null)
const eventEditorError = ref('')
const sanctionsPanelLoading = ref(false)
const sanctionsPanelError = ref('')
const governanceUnits = ref([])
const savedCreateSanctionsTemplate = ref(null)

const createSanctionsConfig = ref(createEmptySanctionsConfig())
const createSanctionsDelegations = ref([])
const editingSanctionsConfig = ref(createEmptySanctionsConfig())
const editingSanctionsDelegations = ref([])

const isCreating = ref(false)
const isSubmitting = ref(false)
const isMapFullscreen = ref(false)
const isCreateSanctionsEnabled = ref(false)
const form = ref({
  name: '',
  location_name: '',
  start_time: '',
  end_time: '',
  require_geofence: false,
  latitude: null,
  longitude: null,
  radius_meters: 100,
  gps_accuracy: 50
})

let mapInstance = null
let markerInstance = null

const eventSwipeOffsets = ref({})
const eventSwipeDragId = ref(null)
const eventSwipePointerId = ref(null)
const eventSwipeStartX = ref(0)
const eventSwipeStartY = ref(0)
const eventSwipeStartOffset = ref(0)
const eventSwipeAxisLock = ref(null)
const eventSwipeDidDrag = ref(false)

const EVENT_SWIPE_ACTION_WIDTH = 130
const EVENT_SWIPE_OPEN_THRESHOLD = 50
const EVENT_SWIPE_GESTURE_THRESHOLD = 8

const filteredEvents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return events.value
  return events.value.filter((e) =>
    [e.title, e.name, e.status].filter(Boolean).join(' ').toLowerCase().includes(q)
  )
})
const hasOpenEventSwipe = computed(() => Object.values(eventSwipeOffsets.value).some((offset) => offset > 0))

const upcomingCount = computed(() => events.value.filter(e => String(e.status).toLowerCase() === 'upcoming').length)
const ongoingCount = computed(() => events.value.filter(e => ['ongoing', 'active'].includes(String(e.status).toLowerCase())).length)
const completedCount = computed(() => events.value.filter(e => String(e.status).toLowerCase() === 'completed').length)
const hasSanctionsRoleAccess = computed(() => (
  isSchoolItSession(dashboardState.user) || isAdminSession(dashboardState.user)
))
const normalizedPermissionCodes = computed(() => (
  (Array.isArray(permissionCodes.value) ? permissionCodes.value : [])
    .map((permissionCode) => String(permissionCode || '').trim().toLowerCase().replace(/-/g, '_'))
    .filter(Boolean)
))
const hasGovernanceSanctionsRoleAccess = computed(() => (
  Number.isFinite(Number(activeUnitId.value))
  || Boolean(normalizeGovernanceContext(acronym.value))
  || Boolean(normalizeGovernanceContext(governanceContext.value))
  || sessionHasRole('ssg', dashboardState.user)
  || sessionHasRole('sg', dashboardState.user)
  || sessionHasRole('org', dashboardState.user)
  || sessionHasRole('student_council', dashboardState.user)
  || sessionHasRole('student council', dashboardState.user)
))
const canConfigureEventSanctions = computed(() => (
  props.preview
  || hasSanctionsRoleAccess.value
  || hasGovernanceSanctionsRoleAccess.value
  || normalizedPermissionCodes.value.includes('manage_events')
  || normalizedPermissionCodes.value.includes('configure_event_sanctions')
))
const canViewSanctionsDashboard = computed(() => (
  props.preview
  || hasSanctionsRoleAccess.value
  || hasGovernanceSanctionsRoleAccess.value
  || normalizedPermissionCodes.value.includes('manage_events')
  || normalizedPermissionCodes.value.includes('configure_event_sanctions')
  || normalizedPermissionCodes.value.includes('view_sanctions_dashboard')
))
const hasSavedCreateSanctionsTemplate = computed(() => savedCreateSanctionsTemplate.value != null)
const savedCreateSanctionsTemplateSummary = computed(() => {
  const template = savedCreateSanctionsTemplate.value
  if (!template) return ''

  const items = Array.isArray(template?.sanctionConfig?.items)
    ? template.sanctionConfig.items.filter((item) => String(item?.item_name || '').trim())
    : []
  const delegations = Array.isArray(template?.sanctionsDelegations)
    ? template.sanctionsDelegations
    : []

  const summaryBits = []
  if (items.length) {
    summaryBits.push(`${items.length} sanction item${items.length === 1 ? '' : 's'}`)
  }
  if (delegations.length) {
    summaryBits.push(`${delegations.length} delegation${delegations.length === 1 ? '' : 's'}`)
  }

  const leadingNames = items
    .slice(0, 2)
    .map((item) => String(item.item_name || '').trim())
    .filter(Boolean)

  if (leadingNames.length) {
    const suffix = items.length > leadingNames.length ? ', ...' : ''
    return `${summaryBits.join(' • ') || 'Saved sanctions'}: ${leadingNames.join(', ')}${suffix}`
  }

  return summaryBits.join(' • ') || 'Saved sanctions template from your last event.'
})

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
    markerInstance = null
  }
})

function formatDate(d) {
  if (!d) return ''
  try { return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }
  catch { return d }
}

function goBack() { 
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, '/exposed/governance'))
    return
  }
  router.push('/governance') 
}

function openSanctionsDashboard() {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, '/exposed/governance/events/sanctions'))
    return
  }
  router.push('/governance/events/sanctions')
}

function goToEvent(event) {
  if (props.preview) {
    router.push(withPreservedGovernancePreviewQuery(route, { name: 'PreviewSgEventDetail', params: { id: event.id } }))
    return
  }
  router.push({ name: 'SgEventDetail', params: { id: event.id } })
}

function getEventDisplayName(event) {
  return String(event?.title || event?.name || 'this event').trim()
}

function createEmptySanctionsConfig() {
  return {
    sanctions_enabled: false,
    items: [],
  }
}

function createEmptySanctionItem() {
  return {
    item_code: '',
    item_name: '',
    item_description: '',
  }
}

function normalizeSanctionsConfigPayload(value = null) {
  const items = Array.isArray(value?.items)
    ? value.items
      .map((item) => ({
        item_code: String(item?.item_code || '').trim() || null,
        item_name: String(item?.item_name || '').trim(),
        item_description: String(item?.item_description || '').trim() || null,
      }))
      .filter((item) => item.item_name)
    : []

  return {
    sanctions_enabled: Boolean(value?.sanctions_enabled),
    items,
  }
}

function normalizeSanctionsDelegationsPayload(value = []) {
  if (!Array.isArray(value)) return []

  return value
    .map((item) => ({
      delegated_to_governance_unit_id: Number(item?.delegated_to_governance_unit_id),
      scope_type: String(item?.scope_type || 'unit').toLowerCase(),
      is_active: item?.is_active !== false,
      scope_json: item?.scope_json && typeof item.scope_json === 'object'
        ? item.scope_json
        : null,
    }))
    .filter((item) => Number.isFinite(item.delegated_to_governance_unit_id))
}

function resolveCreateSanctionsTemplateStorageKey() {
  const { userId, sessionId } = getCurrentGovernanceCacheIdentity()
  const scopeId = Number(governanceUnitId.value)
  const scopeContext = normalizeGovernanceContext(governanceContext.value)
  const keyParts = [GOVERNANCE_EVENT_SANCTIONS_TEMPLATE_STORAGE_KEY]

  if (Number.isFinite(userId)) {
    keyParts.push(`user-${userId}`)
  } else if (sessionId) {
    keyParts.push(`session-${sessionId}`)
  }

  if (Number.isFinite(scopeId)) {
    keyParts.push(`unit-${scopeId}`)
  }

  if (scopeContext) {
    keyParts.push(`context-${scopeContext.toLowerCase()}`)
  }

  return keyParts.join(':')
}

function buildCreateSanctionsTemplatePayload(sanctionsPayload = null) {
  const sanctionConfig = normalizeSanctionsConfigPayload(sanctionsPayload?.sanctionConfig)
  const sanctionsDelegations = normalizeSanctionsDelegationsPayload(sanctionsPayload?.sanctionsDelegations)

  if (!sanctionConfig.sanctions_enabled) {
    return null
  }

  return {
    sanctionConfig,
    sanctionsDelegations,
    savedAt: new Date().toISOString(),
  }
}

function hydrateCreateSanctionsTemplateFromStorage() {
  savedCreateSanctionsTemplate.value = null

  if (props.preview) return

  try {
    const rawValue = localStorage.getItem(resolveCreateSanctionsTemplateStorageKey())
    if (!rawValue) return

    const parsedValue = JSON.parse(rawValue)
    const normalizedTemplate = buildCreateSanctionsTemplatePayload(parsedValue)
    if (!normalizedTemplate) {
      return
    }

    savedCreateSanctionsTemplate.value = normalizedTemplate
  } catch {
    localStorage.removeItem(resolveCreateSanctionsTemplateStorageKey())
  }
}

function persistCreateSanctionsTemplateRecommendation(sanctionsPayload = null) {
  if (props.preview) return

  const normalizedTemplate = buildCreateSanctionsTemplatePayload(sanctionsPayload)
  if (!normalizedTemplate) return

  savedCreateSanctionsTemplate.value = normalizedTemplate
  localStorage.setItem(
    resolveCreateSanctionsTemplateStorageKey(),
    JSON.stringify(normalizedTemplate)
  )
}

function applySavedCreateSanctionsTemplate() {
  if (!canConfigureEventSanctions.value || isSubmitting.value || !savedCreateSanctionsTemplate.value) return

  createSanctionsConfig.value = normalizeSanctionsConfigPayload(savedCreateSanctionsTemplate.value.sanctionConfig)
  createSanctionsDelegations.value = normalizeSanctionsDelegationsPayload(savedCreateSanctionsTemplate.value.sanctionsDelegations)
  isCreateSanctionsEnabled.value = true
}

function enableCreateSanctionsDraft() {
  const currentConfig = normalizeSanctionsConfigPayload(createSanctionsConfig.value)
  createSanctionsConfig.value = {
    sanctions_enabled: true,
    items: currentConfig.items.length ? currentConfig.items : [createEmptySanctionItem()],
  }
}

function resetCreateSanctionsState() {
  createSanctionsConfig.value = createEmptySanctionsConfig()
  createSanctionsDelegations.value = []
}

function resetEditingSanctionsState() {
  editingSanctionsConfig.value = createEmptySanctionsConfig()
  editingSanctionsDelegations.value = []
  sanctionsPanelError.value = ''
}

async function loadGovernanceUnits(url) {
  if (props.preview || !canConfigureEventSanctions.value) {
    governanceUnits.value = []
    return
  }

  try {
    governanceUnits.value = await getGovernanceUnits(url, token.value)
  } catch {
    governanceUnits.value = []
  }
}

async function loadEventSanctionSettings(eventId) {
  if (!Number.isFinite(Number(eventId)) || !canConfigureEventSanctions.value) {
    resetEditingSanctionsState()
    return
  }

  if (props.preview) {
    resetEditingSanctionsState()
    editingSanctionsConfig.value = {
      sanctions_enabled: true,
      items: [
        { item_code: 'community_service', item_name: 'Community Service', item_description: '' },
        { item_code: 'reflection', item_name: 'Reflection Paper', item_description: '' },
      ],
    }
    return
  }

  sanctionsPanelLoading.value = true
  sanctionsPanelError.value = ''
  try {
    const [config, delegations] = await Promise.all([
      getEventSanctionConfig(apiBaseUrl.value, token.value, eventId),
      getEventSanctionDelegation(apiBaseUrl.value, token.value, eventId),
    ])
    editingSanctionsConfig.value = normalizeSanctionsConfigPayload(config)
    editingSanctionsDelegations.value = normalizeSanctionsDelegationsPayload(delegations)
  } catch (error) {
    resetEditingSanctionsState()
    sanctionsPanelError.value = error?.message || 'Unable to load sanctions settings.'
  } finally {
    sanctionsPanelLoading.value = false
  }
}

async function persistEventSanctionSettings(eventId, sanctionsPayload = null) {
  if (!canConfigureEventSanctions.value || !Number.isFinite(Number(eventId))) return
  if (!sanctionsPayload) return

  if (props.preview) return

  const normalizedConfig = normalizeSanctionsConfigPayload(sanctionsPayload?.sanctionConfig)
  const normalizedDelegations = normalizeSanctionsDelegationsPayload(sanctionsPayload?.sanctionsDelegations)

  await upsertEventSanctionConfig(apiBaseUrl.value, token.value, eventId, normalizedConfig)
  await upsertEventSanctionDelegation(apiBaseUrl.value, token.value, eventId, {
    delegations: normalizedDelegations,
  })
}

function closeEventEditor(force = false) {
  if (!force && isMutatingEvent.value) return
  isEventEditorOpen.value = false
  editingEvent.value = null
  eventEditorError.value = ''
  sanctionsPanelLoading.value = false
  resetEditingSanctionsState()
}

async function editManagedEvent(event) {
  if (!event?.id || isMutatingEvent.value) return
  closeAllEventSwipes()
  editingEvent.value = { ...event }
  eventEditorError.value = ''
  resetEditingSanctionsState()
  isEventEditorOpen.value = true
  await loadEventSanctionSettings(event.id)
}

function replaceEventInList(nextEvent) {
  const normalizedId = Number(nextEvent?.id)
  if (!Number.isFinite(normalizedId)) return
  events.value = events.value.map((entry) =>
    Number(entry?.id) === normalizedId ? { ...entry, ...nextEvent } : entry
  )
}

async function ensureGovernanceEventMutationParams(url) {
  if (buildEventQueryParams().governance_context) {
    return buildEventQueryParams()
  }

  const access = await resolveGovernanceEventAccess(url)
  const resolvedUnit = resolveGovernanceEventUnit(access)

  if (resolvedUnit) {
    syncGovernanceEventContext(resolvedUnit)
  }

  return buildEventQueryParams()
}

async function saveEventEdits(payload, sanctionsPayload = null) {
  if (!editingEvent.value?.id || isMutatingEvent.value) return

  if (props.preview) {
    replaceEventInList({
      ...editingEvent.value,
      ...payload,
    })
    if (canConfigureEventSanctions.value) {
      editingSanctionsConfig.value = normalizeSanctionsConfigPayload(sanctionsPayload?.sanctionConfig)
      editingSanctionsDelegations.value = normalizeSanctionsDelegationsPayload(sanctionsPayload?.sanctionsDelegations)
      persistCreateSanctionsTemplateRecommendation(sanctionsPayload)
    }
    closeEventEditor(true)
    return
  }

  isMutatingEvent.value = true
  eventEditorError.value = ''

  try {
    const mutationParams = await ensureGovernanceEventMutationParams(apiBaseUrl.value)
    const updatedEvent = await updateBackendEvent(
      apiBaseUrl.value,
      token.value,
      editingEvent.value.id,
      payload,
      mutationParams
    )

    try {
      await persistEventSanctionSettings(editingEvent.value.id, sanctionsPayload)
      sanctionsPanelError.value = ''
      persistCreateSanctionsTemplateRecommendation(sanctionsPayload)
    } catch (sanctionsError) {
      sanctionsPanelError.value = sanctionsError?.message || 'Unable to update sanctions settings.'
      replaceEventInList(updatedEvent)
      eventEditorError.value = 'Event details were saved, but sanctions settings failed to update.'
      return
    }

    replaceEventInList(updatedEvent)
    closeEventEditor(true)
  } catch (error) {
    eventEditorError.value = error?.message || 'Unable to save the event changes.'
  } finally {
    isMutatingEvent.value = false
  }
}

async function deleteManagedEvent(event) {
  if (!event?.id || isMutatingEvent.value) return

  const confirmed = window.confirm(`Delete ${getEventDisplayName(event)}?`)
  if (!confirmed) return

  if (props.preview) {
    closeAllEventSwipes()
    events.value = events.value.filter((entry) => Number(entry?.id) !== Number(event.id))
    if (Number(editingEvent.value?.id) === Number(event.id)) {
      closeEventEditor(true)
    }
    return
  }

  isMutatingEvent.value = true
  closeAllEventSwipes()

  try {
    const mutationParams = await ensureGovernanceEventMutationParams(apiBaseUrl.value)
    await deleteBackendEvent(
      apiBaseUrl.value,
      token.value,
      event.id,
      mutationParams
    )
    events.value = events.value.filter((entry) => Number(entry?.id) !== Number(event.id))
    if (Number(editingEvent.value?.id) === Number(event.id)) {
      closeEventEditor(true)
    }
  } catch (error) {
    alert(error?.message || 'Unable to delete the event.')
  } finally {
    isMutatingEvent.value = false
  }
}

function openCreateForm() {
  hydrateCreateSanctionsTemplateFromStorage()
  resetCreateSanctionsState()
  isCreateSanctionsEnabled.value = false
  isCreating.value = true
  initMap()
}

function closeCreateForm() {
  isCreating.value = false
  resetCreateSanctionsState()
  isCreateSanctionsEnabled.value = false
  setTimeout(() => {
    if (mapInstance) {
      mapInstance.remove()
      mapInstance = null
      markerInstance = null
    }
  }, 400) // Wait for transition
}

function initMap() {
  if (mapInstance) return
  nextTick(() => {
    setTimeout(async () => {
      const el = document.getElementById('sg-leaflet-preview')
      if (!el) return
      
      try {
        const LeafletModule = await import('leaflet')
        await import('leaflet/dist/leaflet.css')
        const L = LeafletModule.default || LeafletModule
        
        mapInstance = L.map(el).setView([14.5995, 120.9842], 13) // Default to Manila
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(mapInstance)
        
        // Define global L reference purely for the marker helper
        window._sgLeaflet = L
        
        mapInstance.on('click', (e) => {
          setMapMarker(e.latlng.lat, e.latlng.lng)
        })
        
        if (form.value.latitude && form.value.longitude) {
          setMapMarker(form.value.latitude, form.value.longitude)
        }
      } catch (err) {
        console.error('Failed to load Leaflet:', err)
      }
    }, 350) // wait for element expansion animation
  })
}

function setMapMarker(lat, lng) {
  form.value.latitude = parseFloat(lat.toFixed(6))
  form.value.longitude = parseFloat(lng.toFixed(6))
  if (markerInstance) {
    markerInstance.setLatLng([lat, lng])
  } else {
    const L = window._sgLeaflet
    if (L) markerInstance = L.marker([lat, lng]).addTo(mapInstance)
  }
  if (mapInstance) mapInstance.setView([lat, lng])
}

async function useCurrentLocation() {
  try {
    const pos = await getCurrentPositionOrThrow({
      enableHighAccuracy: true,
      timeout: 25000,
      maximumAge: 10000,
    })
    setMapMarker(pos.latitude, pos.longitude)
  } catch (error) {
    alert(error?.message || 'Unable to retrieve your location. Make sure GPS or device location services are turned on, then try again.')
  }
}

function clearLocation() {
  form.value.latitude = null
  form.value.longitude = null
  if (markerInstance) {
    markerInstance.remove()
    markerInstance = null
  }
}

function toggleFullscreenMap() {
  isMapFullscreen.value = !isMapFullscreen.value
  setTimeout(() => {
    if (mapInstance) mapInstance.invalidateSize()
  }, 400)
}

function getEventSwipeOffset(eventId) {
  return Number(eventSwipeOffsets.value[eventId] || 0)
}

function isEventSwipeOpen(eventId) {
  return getEventSwipeOffset(eventId) > 0
}

function getEventSwipeStyle(eventId) {
  return { '--sg-event-swipe-offset': `-${getEventSwipeOffset(eventId)}px` }
}

function setEventSwipeOffset(eventId, offset) {
  const normalizedOffset = Math.max(0, Math.min(EVENT_SWIPE_ACTION_WIDTH, Number(offset) || 0))
  if (normalizedOffset === 0) {
    if (!Object.keys(eventSwipeOffsets.value).length) return
    eventSwipeOffsets.value = {}
    return
  }
  eventSwipeOffsets.value = { [eventId]: normalizedOffset }
}

function closeAllEventSwipes() {
  if (!hasOpenEventSwipe.value) return
  eventSwipeOffsets.value = {}
}

function handleDocumentPointerDown(event) {
  if (!hasOpenEventSwipe.value) return
  if (event.target.closest('.sg-event-swipe-container')) return
  closeAllEventSwipes()
}

function handleEventRowClick(eventRecord, event) {
  const eventId = Number(eventRecord?.id)
  if (eventSwipeDidDrag.value) {
    event.stopPropagation()
    eventSwipeDidDrag.value = false
    return
  }
  if (isEventSwipeOpen(eventId)) {
    event.stopPropagation()
    setEventSwipeOffset(eventId, 0)
    return
  }
  goToEvent(eventRecord)
}

function onEventPointerDown(eventId, event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  event.currentTarget.setPointerCapture(event.pointerId)
  eventSwipeDragId.value = eventId
  eventSwipePointerId.value = event.pointerId
  eventSwipeStartX.value = event.clientX
  eventSwipeStartY.value = event.clientY
  eventSwipeStartOffset.value = getEventSwipeOffset(eventId)
  eventSwipeAxisLock.value = null
  eventSwipeDidDrag.value = false
}

function onEventPointerMove(eventId, event) {
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  const deltaX = event.clientX - eventSwipeStartX.value
  const deltaY = event.clientY - eventSwipeStartY.value
  if (!eventSwipeAxisLock.value) {
    if (Math.abs(deltaX) > EVENT_SWIPE_GESTURE_THRESHOLD || Math.abs(deltaY) > EVENT_SWIPE_GESTURE_THRESHOLD) {
      eventSwipeAxisLock.value = Math.abs(deltaX) > Math.abs(deltaY) ? 'horizontal' : 'vertical'
    }
  }
  if (eventSwipeAxisLock.value === 'horizontal') {
    eventSwipeDidDrag.value = true
    setEventSwipeOffset(eventId, eventSwipeStartOffset.value - deltaX)
  }
}

function onEventPointerEnd(eventId, event) {
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  eventSwipeDragId.value = null
  eventSwipePointerId.value = null
  if (eventSwipeAxisLock.value === 'horizontal' && eventSwipeDidDrag.value) {
    const currentOffset = getEventSwipeOffset(eventId)
    const isOpening = currentOffset > eventSwipeStartOffset.value
    if (isOpening && currentOffset > EVENT_SWIPE_OPEN_THRESHOLD) {
      setEventSwipeOffset(eventId, EVENT_SWIPE_ACTION_WIDTH)
    } else if (!isOpening && currentOffset < EVENT_SWIPE_ACTION_WIDTH - EVENT_SWIPE_OPEN_THRESHOLD) {
      setEventSwipeOffset(eventId, 0)
    } else {
      setEventSwipeOffset(eventId, isOpening ? EVENT_SWIPE_ACTION_WIDTH : 0)
    }
  }
  eventSwipeAxisLock.value = null
}

function onEventPointerCancel(eventId, event) {
  if (eventSwipeDragId.value !== eventId || eventSwipePointerId.value !== event.pointerId) return
  eventSwipeDragId.value = null
  eventSwipePointerId.value = null
  if (eventSwipeStartOffset.value > 0) {
    setEventSwipeOffset(eventId, EVENT_SWIPE_ACTION_WIDTH)
  } else {
    setEventSwipeOffset(eventId, 0)
  }
  eventSwipeAxisLock.value = null
}

function resolveGovernanceEventUnit(access = null) {
  return getGovernanceEventCandidateUnits(access)[0] || null
}

function getCurrentGovernanceCacheIdentity() {
  const authMeta = getStoredAuthMeta()
  return {
    userId: Number(authMeta?.userId),
    sessionId: String(authMeta?.sessionId || '').trim(),
  }
}

function clearGovernanceEventContextStorage() {
  localStorage.removeItem(GOVERNANCE_EVENT_UNIT_ID_STORAGE_KEY)
  localStorage.removeItem(GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY)
  localStorage.removeItem(GOVERNANCE_EVENT_USER_ID_STORAGE_KEY)
  localStorage.removeItem(GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY)
  localStorage.removeItem(LEGACY_SSG_UNIT_ID_STORAGE_KEY)
}

function getGovernanceEventCandidateUnits(access = null) {
  const preferredOptions = {
    requiredPermissionCode: 'manage_events',
    preferredUnitId: governanceUnitId.value,
    preferredContext: governanceContext.value,
  }

  const permittedUnits = getGovernanceUnitsForAction(access, preferredOptions)
  if (permittedUnits.length > 0) {
    return permittedUnits
  }

  return getGovernanceUnitsForAction(access, {
    preferredUnitId: governanceUnitId.value,
    preferredContext: governanceContext.value,
  })
}

function syncGovernanceEventContext(unit = null, explicitContext = '') {
  const nextUnitId = Number(unit?.governance_unit_id)
  const nextContext = normalizeGovernanceContext(explicitContext || unit?.unit_type)

  governanceUnitId.value = Number.isFinite(nextUnitId) ? nextUnitId : null
  governanceContext.value = nextContext

  if (governanceUnitId.value != null) {
    const cacheIdentity = getCurrentGovernanceCacheIdentity()
    localStorage.setItem(GOVERNANCE_EVENT_UNIT_ID_STORAGE_KEY, String(governanceUnitId.value))
    if (Number.isFinite(cacheIdentity.userId)) {
      localStorage.setItem(GOVERNANCE_EVENT_USER_ID_STORAGE_KEY, String(cacheIdentity.userId))
    } else {
      localStorage.removeItem(GOVERNANCE_EVENT_USER_ID_STORAGE_KEY)
    }
    if (cacheIdentity.sessionId) {
      localStorage.setItem(GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY, cacheIdentity.sessionId)
    } else {
      localStorage.removeItem(GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY)
    }
    localStorage.setItem(LEGACY_SSG_UNIT_ID_STORAGE_KEY, String(governanceUnitId.value))
  } else {
    clearGovernanceEventContextStorage()
  }

  if (governanceContext.value) {
    localStorage.setItem(GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY, governanceContext.value)
  } else {
    localStorage.removeItem(GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY)
  }
}

function hydrateGovernanceEventContextFromStorage() {
  const { userId: currentUserId, sessionId: currentSessionId } = getCurrentGovernanceCacheIdentity()
  const cachedUserId = Number(localStorage.getItem(GOVERNANCE_EVENT_USER_ID_STORAGE_KEY))
  const cachedSessionId = String(localStorage.getItem(GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY) || '').trim()
  const hasCachedIdentity = Number.isFinite(cachedUserId) || Boolean(cachedSessionId)

  if (
    hasCachedIdentity &&
    (
      (Number.isFinite(cachedUserId) && (!Number.isFinite(currentUserId) || cachedUserId !== currentUserId)) ||
      (cachedSessionId && cachedSessionId !== currentSessionId)
    )
  ) {
    clearGovernanceEventContextStorage()
    governanceUnitId.value = null
    governanceContext.value = ''
    return
  }

  const cachedUnitId = Number(
    localStorage.getItem(GOVERNANCE_EVENT_UNIT_ID_STORAGE_KEY)
    || localStorage.getItem(LEGACY_SSG_UNIT_ID_STORAGE_KEY)
  )
  const cachedContext = normalizeGovernanceContext(localStorage.getItem(GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY))

  governanceUnitId.value = Number.isFinite(cachedUnitId) ? cachedUnitId : null
  governanceContext.value = cachedContext
}

function toOptionalFiniteNumber(value) {
  if (value == null || value === '') return null
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function toBackendDateTimeValue(value) {
  return String(value || '').trim()
}

function hasExplicitGovernanceEventPreference() {
  return governanceUnitId.value != null || Boolean(governanceContext.value)
}

function sessionAllowsDefaultGovernanceEventScope() {
  return isSchoolItSession(dashboardState.user) || isAdminSession(dashboardState.user)
}

function shouldKeepDefaultGovernanceEventScope() {
  return sessionAllowsDefaultGovernanceEventScope() && !hasExplicitGovernanceEventPreference()
}

function normalizeScopeIdList(values = []) {
  return [...new Set(
    (Array.isArray(values) ? values : [values])
      .map((value) => Number(value))
      .filter(Number.isFinite)
  )]
}

function buildScopedEventPayload(payload, unitDetail = null) {
  return {
    ...payload,
    department_ids: normalizeScopeIdList([unitDetail?.department_id]),
    program_ids: normalizeScopeIdList([unitDetail?.program_id]),
  }
}

function getGovernanceEventScopeDepth(unitDetail = null) {
  const hasDepartmentScope = Number.isFinite(Number(unitDetail?.department_id))
  const hasProgramScope = Number.isFinite(Number(unitDetail?.program_id))

  if (!hasDepartmentScope && !hasProgramScope) return 0
  if (hasProgramScope) return 2
  return 1
}

function orderGovernanceEventCandidates(candidates = []) {
  if (!sessionAllowsDefaultGovernanceEventScope() || candidates.length <= 1) {
    return candidates
  }

  const preferredCandidates = hasExplicitGovernanceEventPreference()
    ? candidates.slice(0, 1)
    : []
  const remainingCandidates = preferredCandidates.length
    ? candidates.slice(1)
    : [...candidates]

  remainingCandidates.sort((left, right) =>
    getGovernanceEventScopeDepth(left?.detail) - getGovernanceEventScopeDepth(right?.detail)
  )

  return [...preferredCandidates, ...remainingCandidates]
}

async function getGovernanceEventUnitDetail(url, unit = null) {
  const normalizedUnitId = Number(unit?.governance_unit_id ?? unit?.id)
  if (!Number.isFinite(normalizedUnitId)) return null

  if (governanceUnitDetailCache.has(normalizedUnitId)) {
    return governanceUnitDetailCache.get(normalizedUnitId)
  }

  const detail = await getGovernanceUnitDetail(url, token.value, normalizedUnitId)
  governanceUnitDetailCache.set(normalizedUnitId, detail)
  return detail
}

function buildEventQueryParams() {
  const params = {}

  if (governanceContext.value) {
    params.governance_context = governanceContext.value
  }

  return params
}

function validateEventForm() {
  const startTime = new Date(form.value.start_time)
  const endTime = new Date(form.value.end_time)

  if (Number.isNaN(startTime.getTime()) || Number.isNaN(endTime.getTime())) {
    throw new Error('Please provide valid start and end dates.')
  }
  if (endTime <= startTime) {
    throw new Error('The event end time must be later than the start time.')
  }
  if (form.value.require_geofence && (form.value.latitude == null || form.value.longitude == null)) {
    throw new Error('Select a map location before requiring geofence attendance.')
  }
}

function buildCreateEventPayload() {
  const payload = {
    name: String(form.value.name || '').trim(),
    location: String(form.value.location_name || '').trim(),
    start_datetime: toBackendDateTimeValue(form.value.start_time),
    end_datetime: toBackendDateTimeValue(form.value.end_time),
    status: 'upcoming',
    geo_required: Boolean(form.value.require_geofence),
    geo_latitude: toOptionalFiniteNumber(form.value.latitude),
    geo_longitude: toOptionalFiniteNumber(form.value.longitude),
    geo_radius_m: toOptionalFiniteNumber(form.value.radius_meters),
    geo_max_accuracy_m: toOptionalFiniteNumber(form.value.gps_accuracy),
    department_ids: [],
    program_ids: [],
  }

  if (!payload.name) {
    throw new Error('Event name is required.')
  }
  if (!payload.location) {
    throw new Error('Event location is required.')
  }

  return payload
}

async function resolveGovernanceEventAccess(url) {
  try {
    return await getGovernanceAccess(url, token.value)
  } catch (error) {
    if (
      error instanceof BackendApiError &&
      [403, 404].includes(Number(error.status))
    ) {
      return null
    }

    throw error
  }
}

async function buildCreateEventAttempts(url, access = null, payload) {
  const attempts = []
  const seenKeys = new Set()
  const candidateUnits = getGovernanceEventCandidateUnits(access)

  const candidateEntries = orderGovernanceEventCandidates(
    await Promise.all(
      candidateUnits.map(async (unit) => {
        try {
          const detail = await getGovernanceEventUnitDetail(url, unit)
          return { unit, detail }
        } catch {
          return { unit, detail: null }
        }
      })
    )
  )

  const pushAttempt = ({ context = '', unit = null, nextPayload = payload } = {}) => {
    const normalizedContext = normalizeGovernanceContext(context || unit?.unit_type)
    const scopedPayload = {
      ...payload,
      ...nextPayload,
      department_ids: normalizeScopeIdList(nextPayload?.department_ids),
      program_ids: normalizeScopeIdList(nextPayload?.program_ids),
    }
    const cacheKey = JSON.stringify({
      context: normalizedContext || '',
      department_ids: scopedPayload.department_ids,
      program_ids: scopedPayload.program_ids,
    })
    if (seenKeys.has(cacheKey)) return

    seenKeys.add(cacheKey)
    attempts.push({
      context: normalizedContext,
      unit,
      payload: scopedPayload,
      params: normalizedContext ? { governance_context: normalizedContext } : {},
    })
  }

  if (governanceContext.value) {
    const preferredEntry = candidateEntries.find(({ unit }) =>
      governanceUnitId.value != null && Number(unit?.governance_unit_id) === Number(governanceUnitId.value)
    ) || candidateEntries.find(({ detail, unit }) =>
      normalizeGovernanceContext(detail?.unit_type || unit?.unit_type) === governanceContext.value
    )

    if (preferredEntry) {
      pushAttempt({
        context: governanceContext.value,
        unit: preferredEntry.unit,
        nextPayload: buildScopedEventPayload(payload, preferredEntry.detail || null),
      })
    }
  }

  candidateEntries.forEach(({ unit, detail }) => {
    pushAttempt({
      context: detail?.unit_type || unit?.unit_type,
      unit,
      nextPayload: buildScopedEventPayload(payload, detail),
    })
  })

  if (sessionAllowsDefaultGovernanceEventScope() || !access || candidateUnits.length === 0) {
    pushAttempt({
      context: '',
      unit: null,
      nextPayload: buildScopedEventPayload(payload, null),
    })
  }

  return attempts
}

function canRetryCreateEvent(error) {
  return (
    error instanceof BackendApiError &&
    [400, 403, 404, 409, 422, 500].includes(Number(error.status))
  )
}

async function createEventWithResolvedScope(url, payload) {
  const access = await resolveGovernanceEventAccess(url)
  const attempts = await buildCreateEventAttempts(url, access, payload)

  let lastError = null

  for (let index = 0; index < attempts.length; index += 1) {
    const attempt = attempts[index]

    try {
      const createdEvent = await createGovernanceEvent(
        url,
        token.value,
        attempt.payload,
        attempt.params
      )

      if (attempt.context) {
        syncGovernanceEventContext(attempt.unit, attempt.context)
      } else {
        syncGovernanceEventContext(null)
      }

      return createdEvent
    } catch (error) {
      lastError = error
      const isLastAttempt = index === attempts.length - 1
      if (isLastAttempt || !canRetryCreateEvent(error)) {
        throw error
      }
    }
  }

  throw lastError || new Error('Unable to create the event.')
}

function toggleCreateSanctionsEnabled() {
  if (isSubmitting.value || !canConfigureEventSanctions.value) return
  isCreateSanctionsEnabled.value = !isCreateSanctionsEnabled.value
  if (!isCreateSanctionsEnabled.value) {
    resetCreateSanctionsState()
    return
  }

  enableCreateSanctionsDraft()
}

async function submitEvent() {
  isSubmitting.value = true
  try {
    validateEventForm()

    if (props.preview) {
      const payload = buildCreateEventPayload()
      events.value = [
        {
          ...payload,
          id: resolveNextPreviewEventId(),
          title: payload.name,
        },
        ...events.value,
      ]
      closeCreateForm()
      resetEventForm()
      return
    }

    const createdEvent = await createEventWithResolvedScope(apiBaseUrl.value, buildCreateEventPayload())
    try {
      if (isCreateSanctionsEnabled.value) {
        enableCreateSanctionsDraft()
        const sanctionsPayload = {
          sanctionConfig: createSanctionsConfig.value,
          sanctionsDelegations: createSanctionsDelegations.value,
        }
        await persistEventSanctionSettings(createdEvent?.id, sanctionsPayload)
        persistCreateSanctionsTemplateRecommendation(sanctionsPayload)
      }
    } catch (sanctionsError) {
      alert(sanctionsError?.message || 'Event was created but sanctions settings could not be saved.')
    }
    closeCreateForm()
    resetEventForm()

    // Refresh events
    await loadEvents(apiBaseUrl.value)
    
  } catch (err) {
    alert(err?.message || 'Error creating event.')
  } finally {
    isSubmitting.value = false
  }
}

watch(
  [apiBaseUrl, () => sgLoading.value, () => route.query?.variant],
  async ([url]) => {
    if (!url || sgLoading.value) return
    await loadEvents(url)
  },
  { immediate: true }
)

watch(
  [governanceUnitId, governanceContext],
  () => {
    hydrateCreateSanctionsTemplateFromStorage()
  },
  { immediate: true }
)

async function loadEvents(url) {
  if (props.preview) {
    events.value = Array.isArray(previewBundle.value?.events)
      ? previewBundle.value.events.map((event) => ({ ...event, title: event.title || event.name }))
      : []
    isLoading.value = false
    return
  }

  isLoading.value = true
  loadError.value = ''
  try {
    // 1. Use the cached governance scope first so the list can render immediately.
    hydrateGovernanceEventContextFromStorage()
    const keepDefaultScope = shouldKeepDefaultGovernanceEventScope()

    // 2. Fetch events immediately using the cached governance scope when available.
    try {
      events.value = await getEvents(url, token.value, keepDefaultScope ? {} : buildEventQueryParams())
    } catch (error) {
      if (keepDefaultScope || !hasExplicitGovernanceEventPreference()) {
        throw error
      }

      const access = await resolveGovernanceEventAccess(url)
      const resolvedUnit = resolveGovernanceEventUnit(access)

      if (!resolvedUnit) {
        throw error
      }

      syncGovernanceEventContext(resolvedUnit)
      events.value = await getEvents(url, token.value, buildEventQueryParams())
    }

    await loadGovernanceUnits(url)

    if (keepDefaultScope) {
      return
    }

    // 3. Refresh governance access in the background so SSG, SG, and ORG users stay in the right scope.
    getGovernanceAccess(url, token.value).then((access) => {
      const previousUnitId = governanceUnitId.value
      const previousContext = governanceContext.value
      syncGovernanceEventContext(resolveGovernanceEventUnit(access))

      if (
        governanceUnitId.value !== previousUnitId
        || governanceContext.value !== previousContext
      ) {
        getEvents(url, token.value, buildEventQueryParams())
          .then((res) => { events.value = res })
      }
    }).catch(() => {})

  } catch (e) {
    loadError.value = e?.message || 'Unable to load events.'
  } finally { 
    isLoading.value = false 
  }
}

async function reload() { if (apiBaseUrl.value) await loadEvents(apiBaseUrl.value) }

function resetEventForm() {
  form.value = {
    name: '',
    location_name: '',
    start_time: '',
    end_time: '',
    require_geofence: false,
    latitude: null,
    longitude: null,
    radius_meters: 100,
    gps_accuracy: 50,
  }
  resetCreateSanctionsState()
}

function resolveNextPreviewEventId() {
  return Math.max(0, ...events.value.map((event) => Number(event.id) || 0)) + 1
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-sub-header { justify-content: flex-start; }

.sg-title-row {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.sg-sub-toolbar {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  flex-wrap: wrap;
}
.sg-sub-search-shell--grow {
  flex: 1 1 280px;
  min-width: 0;
}
.sg-sub-action--sanctions {
  align-self: stretch;
  border-radius: 999px;
  min-height: 52px;
  padding: 0 18px;
  font-weight: 700;
  flex: 0 0 auto;
}
.sg-sub-search-shell {
  background: var(--color-surface);
  border-radius: 999px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}
.sg-sub-search-input {
  flex: 1;
  background: transparent;
  border: none;
  height: 52px;
  font-size: 15px;
  color: var(--color-text-primary);
  outline: none;
}
.sg-sub-search-input::placeholder {
  color: var(--color-text-muted);
}

/* Expanding Form Wrapper Styling */
.sg-create-wrapper {
  position: relative;
  background: var(--color-primary); /* Lime Green form base */
  border-radius: 999px;
  overflow: hidden;
  flex: 0 0 auto;
  width: auto;
  max-width: 100%;
}
.sg-create-panel {
  position: relative;
  background: var(--color-primary);
  border-radius: 32px;
  overflow: visible;
  z-index: 2;
}
.sg-create-panel.map-is-fullscreen {
  overflow: visible !important;
  z-index: 99999;
}

.sg-create-event-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--color-primary-text);
  border: none;
  padding: 0 24px;
  min-height: 52px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 13px;
  line-height: 1.1;
  text-align: left;
  cursor: pointer;
  transition: filter 0.15s ease;
  white-space: nowrap;
}
.sg-create-event-btn__label {
  display: inline-block;
  margin-top: 1px;
}
.sg-create-event-btn:hover {
  filter: brightness(1.04);
}
.sg-create-event-btn--inner {
  padding: 0;
  min-height: auto;
}

.sg-create-form {
  padding: 0 clamp(16px, 4vw, 24px) clamp(24px, 4vw, 32px);
  color: var(--color-primary-text);
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fade-in 0.4s ease forwards;
  min-width: 0;
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sg-create-form-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: 52px; /* matches the original button height exactly */
}

.sg-event-fields {
  display: grid;
  gap: 16px;
  min-width: 0;
}
.sg-event-fields-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.sg-field-label--wide {
  grid-column: 1 / -1;
}
.sg-field-label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary-text);
  padding-left: 2px;
  min-width: 0;
}
.sg-field-label input {
  background: var(--color-surface);
  border: none;
  border-radius: 999px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  outline: none;
  width: 100%;
  box-sizing: border-box;
}
.sg-field-label input::placeholder {
  color: var(--color-text-muted);
}

/* Map specific styling */
.sg-map-section {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 24px;
  background: color-mix(in srgb, var(--color-surface) 18%, transparent);
}
.sg-map-section-title {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  color: var(--color-primary-text);
  letter-spacing: 0.02em;
}
.sg-map-frame {
  position: relative;
  width: 100%;
  min-height: 220px;
  height: clamp(220px, 34vw, 280px);
}
.sg-map-container {
  position: absolute; /* positioned inside the protective 200px height wrapper */
  top: 0; left: 0; right: 0; bottom: 0;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
  z-index: 10;
}
@keyframes map-pop-in {
  from { opacity: 0; transform: scale(0.98) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.sg-map-container.is-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  border-radius: 0;
  z-index: 999999;
  box-shadow: 0 0 100vw rgba(0,0,0,0.8);
  animation: map-pop-in 0.25s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}
.sg-leaflet-preview {
  width: 100%;
  height: 100%;
  background: #e2e8f0;
}
.sg-map-fullscreen-overlay {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000; /* above leaflet ui */
}
.sg-map-confirm-btn {
  background: var(--color-primary);
  color: #000;
  font-weight: 800;
  padding: 12px 24px;
  border-radius: 999px;
  border: none;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  cursor: pointer;
}

.sg-map-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.sg-map-btn {
  flex: 1 1 180px;
  background: var(--color-surface);
  border: none;
  border-radius: 999px;
  padding: 14px;
  font-weight: 700;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--color-text-primary);
}

.sg-coord-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.sg-checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--color-primary-text);
  cursor: pointer;
  margin: 0;
}
.sg-checkbox-label input {
  display: none;
}
.sg-checkbox-custom {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-surface);
  display: inline-block;
  flex-shrink: 0;
  position: relative;
}
.sg-checkbox-label input:checked + .sg-checkbox-custom::after {
  content: '';
  position: absolute;
  top: 6px; left: 6px; right: 6px; bottom: 6px;
  background: var(--color-primary-dark);
  border-radius: 50%;
}

.sg-submit-event {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: none;
  border-radius: 999px;
  padding: 18px;
  font-size: 15px;
  font-weight: 800;
  cursor: pointer;
  width: 100%;
  min-height: 54px;
}
.sg-form-note {
  font-size: 11px;
  text-align: center;
  color: color-mix(in srgb, var(--color-primary-text) 70%, transparent);
  margin: 0;
}
.sg-sanctions-panel {
  display: grid;
  gap: 12px;
  margin: 8px 0 4px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--color-primary-text) 18%, transparent);
  background: color-mix(in srgb, var(--color-surface) 90%, transparent);
}
.sg-sanctions-panel--locked {
  border-color: color-mix(in srgb, #f59e0b 32%, transparent);
}
.sg-sanctions-recommendation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-primary) 14%, white);
  border: 1px solid color-mix(in srgb, var(--color-primary) 22%, transparent);
}
.sg-sanctions-recommendation__content {
  display: grid;
  gap: 4px;
  min-width: 0;
}
.sg-sanctions-recommendation__eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--color-text-secondary) 80%, transparent);
}
.sg-sanctions-recommendation__title {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: var(--color-text-primary);
}
.sg-sanctions-recommendation__copy {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: color-mix(in srgb, var(--color-text-secondary) 86%, transparent);
}
.sg-sanctions-recommendation__action {
  border: none;
  border-radius: 999px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 12px;
  font-weight: 800;
  min-height: 36px;
  padding: 0 16px;
  cursor: pointer;
  flex: 0 0 auto;
}
.sg-sanctions-recommendation__action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.sg-sanctions-panel__header {
  display: grid;
  gap: 2px;
}
.sg-sanctions-panel__eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--color-text-secondary) 80%, transparent);
}
.sg-sanctions-panel__title {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: var(--color-text-primary);
}
.sg-sanctions-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.sg-sanctions-toggle__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.sg-sanctions-toggle__hint {
  margin: -2px 0 2px;
  font-size: 11px;
  font-weight: 700;
  color: color-mix(in srgb, #b45309 80%, transparent);
}
.sg-sanctions-toggle__button {
  border: 1px solid color-mix(in srgb, var(--color-text-primary) 20%, transparent);
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-primary);
  font-weight: 700;
  font-size: 12px;
  min-height: 32px;
  padding: 0 12px;
  cursor: pointer;
}
.sg-sanctions-toggle__button--enabled {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border-color: transparent;
}
.sg-sanctions-toggle__button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

@media (max-width: 760px) {
  .sg-sub-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .sg-sub-search-shell--grow,
  .sg-sub-action--sanctions,
  .sg-create-wrapper {
    width: 100%;
  }

  .sg-sub-action--sanctions,
  .sg-create-event-btn {
    width: 100%;
    justify-content: center;
  }

  .sg-create-form-header {
    justify-content: flex-start;
  }

  .sg-event-fields-grid,
  .sg-coord-grid {
    grid-template-columns: 1fr;
  }

  .sg-field-label--wide {
    grid-column: auto;
  }

  .sg-map-section {
    padding: 14px;
    border-radius: 20px;
  }

  .sg-map-frame {
    min-height: 200px;
    height: 220px;
  }

  .sg-map-controls,
  .sg-sanctions-toggle,
  .sg-sanctions-recommendation {
    flex-direction: column;
    align-items: stretch;
  }

  .sg-map-btn,
  .sg-sanctions-toggle__button,
  .sg-sanctions-recommendation__action {
    width: 100%;
  }

  .sg-map-fullscreen-overlay {
    left: 16px;
    right: 16px;
    transform: none;
    bottom: 24px;
  }

  .sg-map-confirm-btn {
    width: 100%;
  }
}

.sg-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}
.sg-summary-card {
  background: var(--color-surface);
  border-radius: 20px;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0,0,0,0.03);
}
.sg-summary-val {
  font-size: 26px;
  font-weight: 900;
  line-height: 1;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}
.sg-summary-lbl {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

@media (max-width: 600px) {
  .sg-summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.sg-sub-card {
  background: transparent;
  box-shadow: none;
  padding: 0;
}

.sg-events-list { 
  display: flex; 
  flex-direction: column; 
  gap: 16px; 
}

/* Swipe Structural Container */
.sg-event-swipe-container {
  position: relative;
  width: 100%;
  border-radius: 999px; /* highly rounded */
  overflow: hidden;
}

/* Behind the scenes action buttons */
.sg-event-actions-bg {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  padding: 0 24px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 60%, transparent);
  z-index: 1;
}

.sg-action-icon {
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}
.sg-action-icon:hover { transform: scale(1.1); }
.sg-action-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
.sg-action-delete { color: #e74c3c; }
.sg-action-edit { color: var(--color-text-primary); border-color: color-mix(in srgb, var(--color-text-primary) 30%, transparent); }

/* Foreground Pill (The Main Row) */
.sg-event-row { 
  position: relative;
  z-index: 2;
  display: flex; 
  align-items: center; 
  justify-content: space-between; 
  gap: 16px; 
  padding: 12px 12px 12px 28px; 
  border-radius: 999px; 
  background: var(--color-surface); /* Pure white or surface */
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
  cursor: pointer; 
  touch-action: pan-y;
  transition: transform 0.2s cubic-bezier(0.2, 0.8, 0.2, 1); 
  transform: translateX(var(--sg-event-swipe-offset, 0px));
}

@media (hover: hover) {
  .sg-event-swipe-container:not(.sg-event-swipe-container--open) .sg-event-row:hover {
    transform: translateX(calc(var(--sg-event-swipe-offset, 0px) - 4px));
  }
}

.sg-event-info { 
  flex: 1; 
  min-width: 0; 
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.sg-event-name { 
  font-size: clamp(16px, 4vw, 19px); 
  font-weight: 800; 
  color: var(--color-primary); /* The lime green from the request */
  margin: 0 0 2px 0; 
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sg-event-date { 
  font-size: 13px; 
  font-weight: 600;
  color: color-mix(in srgb, var(--color-text-secondary) 80%, transparent); 
}

/* Bright Inner Action Pill */
.sg-action-pill {
  display: flex;
  align-items: center;
  background: var(--color-primary);
  border-radius: 999px;
  padding: 6px 20px 6px 6px;
  gap: 12px;
  transition: filter 0.2s ease;
  flex-shrink: 0;
}
.sg-event-row:hover .sg-action-pill {
  filter: brightness(1.04);
}
.sg-action-thumb {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-nav, #0c0c0c); /* Black circle */
  color: var(--color-nav-text, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sg-action-text {
  font-size: 13px;
  font-weight: 800;
  color: var(--color-nav, #000); /* Black text */
  letter-spacing: -0.02em;
}
</style>
