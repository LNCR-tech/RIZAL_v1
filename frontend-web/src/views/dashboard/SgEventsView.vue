<template>
  <div class="sg-events-view">
    <section class="sg-sub-page">
    <header class="sg-sub-header dashboard-enter dashboard-enter--1">
      <div style="display: flex; align-items: center; gap: 16px;">
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
          <span class="sg-summary-val" style="color: var(--color-primary)">{{ upcomingCount }}</span>
          <span class="sg-summary-lbl">Upcoming</span>
        </div>
        <div class="sg-summary-card">
          <span class="sg-summary-val" style="color: var(--color-status-compliant)">{{ ongoingCount }}</span>
          <span class="sg-summary-lbl">Ongoing</span>
        </div>
        <div class="sg-summary-card">
          <span class="sg-summary-val" style="color: var(--color-surface-text-muted)">{{ completedCount }}</span>
          <span class="sg-summary-lbl">Completed</span>
        </div>
      </div>

      <div class="sg-sub-toolbar dashboard-enter dashboard-enter--3" :class="{'is-creating': isCreating}">
        <div class="sg-sub-search-shell" style="flex: 1;">
          <input
            v-model="searchQuery"
            type="text"
            class="sg-sub-search-input"
            placeholder="Search events"
          />
          <Search :size="18" style="color: var(--color-primary);" />
        </div>
        
        <div class="sg-create-wrapper" :class="{ 'is-expanded': isCreating }">
          <button v-if="!isCreating" class="sg-create-event-btn" type="button" @click="openCreateForm">
            <Plus :size="20" />
            <span style="margin-top: 1px;">Create<br>Event</span>
          </button>
          
          <div v-if="isCreating" class="sg-create-form">
            <header class="sg-create-form-header">
              <div>
                <p class="sg-create-eyebrow">New governance event</p>
                <h2 class="sg-create-heading">Create Event</h2>
                <p class="sg-create-copy">Set the event schedule, location, and optional attendance geofence.</p>
              </div>

              <button
                class="sg-create-close"
                type="button"
                aria-label="Close create event form"
                :disabled="isSubmitting"
                @click="closeCreateForm"
              >
                <X :size="18" />
              </button>
            </header>
            
            <form class="sg-event-fields" @submit.prevent="submitEvent">
              <div class="sg-event-fields-grid">
                <label class="sg-field-label sg-field-label--wide">
                  <span>Event Name</span>
                  <input v-model="form.name" type="text" placeholder="e.g. Campus Orientation" required />
                </label>

                <label class="sg-field-label">
                  <span>Start date & time</span>
                  <input v-model="form.start_time" type="datetime-local" required />
                </label>

                <label class="sg-field-label">
                  <span>End date & time</span>
                  <input v-model="form.end_time" type="datetime-local" required />
                </label>
              </div>
              
              <section class="sg-map-section" :class="{ 'is-required': form.require_geofence }">
                <header class="sg-map-section-header">
                  <div class="sg-map-section-title">
                    <span class="sg-map-section-icon">
                      <MapPin :size="18" />
                    </span>
                    <div>
                      <h3>Location</h3>
                      <p>{{ geofenceSummary }}</p>
                    </div>
                  </div>

                  <label class="sg-toggle-label">
                    <input v-model="form.require_geofence" type="checkbox" />
                    <span class="sg-toggle-track"></span>
                    <span>Require geofence</span>
                  </label>
                </header>

                <EventLocationPicker
                  v-model:location-label="form.location_name"
                  v-model:latitude="form.latitude"
                  v-model:longitude="form.longitude"
                  :radius-m="form.radius_meters"
                  :disabled="isSubmitting"
                />
                
                <div class="sg-coord-grid">
                  <label class="sg-field-label">
                    <span>Latitude</span>
                    <input v-model="form.latitude" type="number" step="any" placeholder="Not selected" />
                  </label>
                  <label class="sg-field-label">
                    <span>Longitude</span>
                    <input v-model="form.longitude" type="number" step="any" placeholder="Not selected" />
                  </label>
                  <label class="sg-field-label">
                    <span>Allowed Radius</span>
                    <input v-model="form.radius_meters" type="number" min="1" max="5000" step="1" placeholder="100 meters" />
                  </label>
                  <label class="sg-field-label">
                    <span>Max GPS Accuracy</span>
                    <input v-model="form.gps_accuracy" type="number" min="1" max="1000" step="1" placeholder="50 meters" />
                  </label>
                </div>

                <p class="sg-geofence-note">
                  {{ geofenceHelperText }}
                </p>
              </section>

              <p v-if="createError" class="sg-create-feedback" role="alert">
                <AlertCircle :size="16" />
                <span>{{ createError }}</span>
              </p>
              
              <div class="sg-form-actions">
                <button class="sg-cancel-event" type="button" :disabled="isSubmitting" @click="closeCreateForm">
                  Cancel
                </button>
                <button type="submit" class="sg-submit-event" :disabled="isSubmitting">
                  {{ isSubmitting ? 'Creating...' : 'Create Event' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

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
      @close="closeEventEditor"
      @save="saveEventEdits"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})
import { AlertCircle, ArrowLeft, ArrowRight, Search, Plus, Trash2, Edit2, MapPin, X } from 'lucide-vue-next'
import EventEditorSheet from '@/components/events/EventEditorSheet.vue'
import EventLocationPicker from '@/components/events/EventLocationPicker.vue'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { useSgDashboard } from '@/composables/useSgDashboard.js'
import { createIdempotencyKey } from '@/services/idempotency.js'
import {
  BackendApiError,
  createGovernanceEvent,
  deleteEvent as deleteBackendEvent,
  getEvents,
  getGovernanceAccess,
  getGovernanceUnitDetail,
  updateEvent as updateBackendEvent,
} from '@/services/backendApi.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'
import {
  getGovernanceUnitsForAction,
  normalizeGovernanceContext,
} from '@/services/governanceScope.js'
import { withPreservedGovernancePreviewQuery } from '@/services/routeWorkspace.js'

const route = useRoute()
const router = useRouter()
const { apiBaseUrl, token, dashboardState, isSchoolItSession, isAdminSession } = useDashboardSession()
const { previewBundle } = useSgPreviewBundle(() => props.preview)
const { isLoading: sgLoading } = useSgDashboard(props.preview)
const governanceUnitId = ref(null)
const governanceContext = ref('')
const governanceUnitDetailCache = new Map()

const GOVERNANCE_EVENT_UNIT_ID_STORAGE_KEY = 'aura_cached_governance_unit_id'
const GOVERNANCE_EVENT_CONTEXT_STORAGE_KEY = 'aura_cached_governance_context'
const GOVERNANCE_EVENT_USER_ID_STORAGE_KEY = 'aura_cached_governance_user_id'
const GOVERNANCE_EVENT_SESSION_ID_STORAGE_KEY = 'aura_cached_governance_session_id'
const LEGACY_SSG_UNIT_ID_STORAGE_KEY = 'aura_cached_ssg_unit_id'

const isLoading = ref(true)
const loadError = ref('')
const events = ref([])
const searchQuery = ref('')
const isMutatingEvent = ref(false)
const isEventEditorOpen = ref(false)
const editingEvent = ref(null)
const eventEditorError = ref('')

const isCreating = ref(false)
const isSubmitting = ref(false)
const createError = ref('')
const pendingCreateRequestKey = ref('')
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
const formGeofence = computed(() => getFormGeofenceValues())
const hasCompleteGeofence = computed(() => formGeofence.value.complete)
const geofenceSummary = computed(() => {
  if (form.value.require_geofence) {
    return hasCompleteGeofence.value
      ? 'Students must be inside the selected radius to sign in.'
      : 'Select a map point before saving a required geofence.'
  }

  return hasCompleteGeofence.value
    ? 'A map location will be saved, but attendance can proceed without geofence enforcement.'
    : 'Optional. Leave blank when this event does not need location-locked attendance.'
})
const geofenceHelperText = computed(() => {
  if (!hasCompleteGeofence.value) {
    return 'The app will not send radius-only data to the backend. Pick a map point to save geofence fields.'
  }

  const radius = Math.round(formGeofence.value.radius)
  const accuracy = formGeofence.value.maxAccuracy != null
    ? ` Devices must report ${Math.round(formGeofence.value.maxAccuracy)} m accuracy or better.`
    : ''

  return `Students inside ${radius} m of the marker are treated as inside the event area.${accuracy}`
})

watch(
  form,
  () => {
    if (createError.value) {
      createError.value = ''
    }
  },
  { deep: true }
)

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
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

function closeEventEditor(force = false) {
  if (!force && isMutatingEvent.value) return
  isEventEditorOpen.value = false
  editingEvent.value = null
  eventEditorError.value = ''
}

function editManagedEvent(event) {
  if (!event?.id || isMutatingEvent.value) return
  closeAllEventSwipes()
  editingEvent.value = { ...event }
  eventEditorError.value = ''
  isEventEditorOpen.value = true
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

async function saveEventEdits(payload) {
  if (!editingEvent.value?.id || isMutatingEvent.value) return

  if (props.preview) {
    replaceEventInList({
      ...editingEvent.value,
      ...payload,
    })
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
  createError.value = ''
  isCreating.value = true
}

function closeCreateForm(force = false) {
  if (isSubmitting.value && !force) return
  createError.value = ''
  pendingCreateRequestKey.value = ''
  isCreating.value = false
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
  const target = event.target
  if (target instanceof Element && target.closest('.sg-event-swipe-container')) return
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

function isValidLatitude(value) {
  return Number.isFinite(value) && value >= -90 && value <= 90
}

function isValidLongitude(value) {
  return Number.isFinite(value) && value >= -180 && value <= 180
}

function getFormGeofenceValues() {
  const latitude = toOptionalFiniteNumber(form.value.latitude)
  const longitude = toOptionalFiniteNumber(form.value.longitude)
  const radius = toOptionalFiniteNumber(form.value.radius_meters)
  const maxAccuracy = toOptionalFiniteNumber(form.value.gps_accuracy)
  const hasLatitude = latitude != null
  const hasLongitude = longitude != null
  const hasAnyCoordinate = hasLatitude || hasLongitude
  const complete = hasLatitude && hasLongitude && radius != null

  return {
    latitude,
    longitude,
    radius,
    maxAccuracy,
    hasAnyCoordinate,
    complete,
  }
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
  const geofence = getFormGeofenceValues()

  if (Number.isNaN(startTime.getTime()) || Number.isNaN(endTime.getTime())) {
    throw new Error('Please provide valid start and end dates.')
  }
  if (endTime <= startTime) {
    throw new Error('The event end time must be later than the start time.')
  }
  if (geofence.latitude != null && !isValidLatitude(geofence.latitude)) {
    throw new Error('Latitude must be between -90 and 90.')
  }
  if (geofence.longitude != null && !isValidLongitude(geofence.longitude)) {
    throw new Error('Longitude must be between -180 and 180.')
  }
  if (geofence.hasAnyCoordinate && !geofence.complete) {
    throw new Error('Latitude, longitude, and allowed radius are required together for the event geofence.')
  }
  if (geofence.complete && geofence.radius <= 0) {
    throw new Error('Allowed radius must be greater than 0 meters.')
  }
  if (geofence.complete && geofence.radius > 5000) {
    throw new Error('Allowed radius cannot be greater than 5000 meters.')
  }
  if (geofence.complete && geofence.maxAccuracy != null && geofence.maxAccuracy <= 0) {
    throw new Error('Max GPS accuracy must be greater than 0 meters.')
  }
  if (geofence.complete && geofence.maxAccuracy != null && geofence.maxAccuracy > 1000) {
    throw new Error('Max GPS accuracy cannot be greater than 1000 meters.')
  }
  if (form.value.require_geofence && !geofence.complete) {
    throw new Error('Select a map location before requiring geofence attendance.')
  }
}

function buildCreateEventPayload() {
  const geofence = getFormGeofenceValues()
  const shouldSendGeofence = geofence.complete
  const payload = {
    name: String(form.value.name || '').trim(),
    location: String(form.value.location_name || '').trim(),
    start_datetime: toBackendDateTimeValue(form.value.start_time),
    end_datetime: toBackendDateTimeValue(form.value.end_time),
    status: 'upcoming',
    geo_required: shouldSendGeofence ? Boolean(form.value.require_geofence) : false,
    geo_latitude: shouldSendGeofence ? geofence.latitude : null,
    geo_longitude: shouldSendGeofence ? geofence.longitude : null,
    geo_radius_m: shouldSendGeofence ? geofence.radius : null,
    geo_max_accuracy_m: shouldSendGeofence ? geofence.maxAccuracy : null,
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

async function createEventWithResolvedScope(url, payload, requestOptions = {}) {
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
        attempt.params,
        requestOptions
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

async function submitEvent() {
  if (isSubmitting.value) return

  isSubmitting.value = true
  createError.value = ''
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
      closeCreateForm(true)
      resetEventForm()
      return
    }

    if (!pendingCreateRequestKey.value) {
      pendingCreateRequestKey.value = createIdempotencyKey('governance-event')
    }

    await createEventWithResolvedScope(
      apiBaseUrl.value,
      buildCreateEventPayload(),
      {
        headers: {
          'X-Idempotency-Key': pendingCreateRequestKey.value,
        },
      }
    )
    closeCreateForm(true)
    resetEventForm()
    pendingCreateRequestKey.value = ''

    // Refresh events
    await loadEvents(apiBaseUrl.value)
    
  } catch (err) {
    pendingCreateRequestKey.value = ''
    createError.value = err?.message || 'Error creating event.'
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

// Safety valve: if sgLoading never resolves, force a load attempt after 7s.
onMounted(() => {
  setTimeout(() => {
    if (isLoading.value && apiBaseUrl.value) {
      loadEvents(apiBaseUrl.value)
    }
  }, 7000)
})

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
  pendingCreateRequestKey.value = ''
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
}

function resolveNextPreviewEventId() {
  return Math.max(0, ...events.value.map((event) => Number(event.id) || 0)) + 1
}
</script>

<style scoped>
@import '@/assets/css/sg-sub-views.css';

.sg-sub-header { justify-content: flex-start; }

.sg-sub-toolbar {
  display: flex;
  align-items: stretch;
  gap: 14px;
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

.sg-create-wrapper {
  position: relative;
  background: var(--color-primary);
  border-radius: 999px;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
  max-height: 52px;
  transform-origin: top right;
  flex-shrink: 0;
  width: auto;
}
.sg-create-wrapper.is-expanded {
  max-height: 1600px;
  border-radius: 28px;
  width: 100%;
}
.sg-sub-toolbar.is-creating {
  flex-direction: column;
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
.sg-create-event-btn:hover {
  filter: brightness(1.04);
}

.sg-create-form {
  padding: 24px;
  color: var(--color-primary-text);
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fade-in 0.4s ease forwards;
}
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

.sg-create-form-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}
.sg-create-eyebrow,
.sg-create-copy {
  margin: 0;
}
.sg-create-eyebrow {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.72;
}
.sg-create-heading {
  margin: 4px 0 0;
  font-size: 24px;
  line-height: 1.1;
  font-weight: 900;
  color: var(--color-primary-text);
}
.sg-create-copy {
  max-width: 620px;
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.78;
}
.sg-create-close {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-surface) 96%, transparent);
  color: var(--color-text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 160ms ease, box-shadow 160ms ease;
}
.sg-create-close:hover:not(:disabled),
.sg-create-close:focus-visible {
  background: var(--color-surface);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-surface) 24%, transparent);
  outline: none;
}

.sg-event-fields {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.sg-event-fields-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.sg-field-label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 12px;
  font-weight: 800;
  color: var(--color-primary-text);
  padding-left: 2px;
}
.sg-field-label--wide {
  grid-column: 1 / -1;
}
.sg-field-label input,
.sg-field-label select {
  background: var(--color-surface);
  border: 1px solid color-mix(in srgb, var(--color-text-primary) 8%, transparent);
  border-radius: 16px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 650;
  color: var(--color-text-primary);
  outline: none;
  width: 100%;
  box-sizing: border-box;
}
.sg-field-label input:focus {
  border-color: color-mix(in srgb, var(--color-primary-dark, #111827) 28%, white);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-surface) 28%, transparent);
}
.sg-field-label input::placeholder {
  color: var(--color-text-muted);
}

.sg-map-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border-radius: 22px;
  background: color-mix(in srgb, var(--color-surface) 94%, transparent);
  color: var(--color-text-primary);
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--color-text-primary) 8%, transparent);
}
.sg-map-section.is-required {
  box-shadow:
    inset 0 0 0 1px color-mix(in srgb, var(--color-primary-dark, #111827) 20%, transparent),
    0 18px 36px rgba(15, 23, 42, 0.1);
}
.sg-map-section .sg-field-label {
  color: var(--color-text-secondary);
}
.sg-map-section-header,
.sg-map-section-title,
.sg-toggle-label,
.sg-form-actions,
.sg-create-feedback {
  display: flex;
}
.sg-map-section-header {
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.sg-map-section-title {
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}
.sg-map-section-title h3,
.sg-map-section-title p,
.sg-geofence-note {
  margin: 0;
}
.sg-map-section-title h3 {
  font-size: 16px;
  font-weight: 900;
  color: var(--color-text-primary);
}
.sg-map-section-title p,
.sg-geofence-note {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}
.sg-map-section-icon {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, white);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sg-coord-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.sg-toggle-label {
  align-items: center;
  gap: 10px;
  font-size: 13px;
  font-weight: 800;
  color: var(--color-text-primary);
  cursor: pointer;
  white-space: nowrap;
}
.sg-toggle-label input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.sg-toggle-track {
  position: relative;
  width: 44px;
  height: 24px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.14);
  display: inline-block;
  flex-shrink: 0;
  transition: background 180ms ease;
}
.sg-toggle-track::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.18);
  transition: transform 180ms ease;
}
.sg-toggle-label input:checked + .sg-toggle-track {
  background: var(--color-primary);
}
.sg-toggle-label input:checked + .sg-toggle-track::after {
  transform: translateX(20px);
}
.sg-toggle-label input:focus-visible + .sg-toggle-track {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-primary) 18%, transparent);
}

.sg-create-feedback {
  align-items: flex-start;
  gap: 10px;
  margin: 0;
  padding: 12px 14px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-status-non-compliant) 12%, transparent);
  color: var(--color-status-non-compliant);
  font-size: 13px;
  font-weight: 800;
  line-height: 1.5;
}
.sg-form-actions {
  justify-content: flex-end;
  gap: 12px;
}
.sg-submit-event,
.sg-cancel-event {
  border: none;
  border-radius: 999px;
  padding: 15px 22px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: filter 160ms ease, box-shadow 160ms ease;
}
.sg-submit-event {
  background: var(--color-surface);
  color: var(--color-text-primary);
}
.sg-cancel-event {
  background: color-mix(in srgb, var(--color-surface) 28%, transparent);
  color: var(--color-primary-text);
}
.sg-submit-event:hover:not(:disabled),
.sg-cancel-event:hover:not(:disabled),
.sg-submit-event:focus-visible,
.sg-cancel-event:focus-visible {
  filter: brightness(1.03);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-surface) 24%, transparent);
  outline: none;
}
.sg-submit-event:disabled,
.sg-cancel-event:disabled,
.sg-create-close:disabled {
  opacity: 0.62;
  cursor: not-allowed;
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
  .sg-create-form {
    padding: 18px;
  }
  .sg-create-form-header,
  .sg-map-section-header {
    flex-direction: column;
  }
  .sg-create-form-header {
    padding-right: 52px;
  }
  .sg-create-close {
    position: absolute;
    top: 16px;
    right: 16px;
  }
  .sg-event-fields-grid,
  .sg-coord-grid {
    grid-template-columns: 1fr;
  }
  .sg-toggle-label,
  .sg-form-actions {
    width: 100%;
  }
  .sg-form-actions {
    flex-direction: column-reverse;
  }
  .sg-submit-event,
  .sg-cancel-event {
    width: 100%;
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
.sg-action-delete { color: var(--color-status-non-compliant); }
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
  font-size: 18px;
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
  letter-spacing: 0;
}
</style>
