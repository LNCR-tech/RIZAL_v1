<template>
  <main class="event-detail">
    <header class="detail-header dashboard-enter dashboard-enter--1">
      <button class="icon-btn icon-btn--ghost icon-btn--back" type="button" aria-label="Back" @click="goBack">
        <ArrowLeft :size="18" />
      </button>

      <div class="header-spacer"></div>

      <button class="icon-btn icon-btn--ghost icon-btn--bell" type="button" aria-label="Notifications">
        <Bell :size="18" />
      </button>
    </header>

    <section v-if="event" class="detail-body" aria-labelledby="event-detail-title">
      <section class="event-summary dashboard-enter dashboard-enter--2">
        <div class="event-summary__top">
          <span :class="['status-pill', statusPillClass]">
            <span class="status-dot" :class="statusDotClass" aria-hidden="true"></span>
            <span>{{ statusLabel }}</span>
          </span>
        </div>
        <h1 id="event-detail-title" class="event-title">{{ eventName }}</h1>
        <div class="summary-list" aria-label="Event overview">
          <div class="summary-item">
            <CalendarClock :size="17" aria-hidden="true" />
            <span>{{ dateRange }}</span>
          </div>
          <div class="summary-item">
            <MapPin :size="17" aria-hidden="true" />
            <span>{{ locationText }}</span>
          </div>
        </div>
      </section>

      <section class="detail-grid dashboard-enter dashboard-enter--3" aria-label="Event details">
        <article class="detail-panel">
          <header class="panel-header">
            <CalendarClock :size="17" aria-hidden="true" />
            <h2>Schedule</h2>
          </header>
          <div class="time-grid">
            <div>
              <span>Starts</span>
              <strong>{{ startDateText }}</strong>
              <small>{{ startTimeText }}</small>
            </div>
            <div>
              <span>Ends</span>
              <strong>{{ endDateText }}</strong>
              <small>{{ endTimeText }}</small>
            </div>
          </div>
        </article>

        <article class="detail-panel">
          <header class="panel-header">
            <MapPin :size="17" aria-hidden="true" />
            <h2>Location</h2>
          </header>
          <p class="venue-name">{{ locationText }}</p>
          <p class="venue-coordinates">{{ coordinateSummary }}</p>
          <button
            class="detail-action"
            type="button"
            :disabled="!mapDestination"
            @click="openInMaps"
          >
            <Navigation :size="16" aria-hidden="true" />
            Open in Maps
          </button>
        </article>
      </section>

      <section class="map-panel dashboard-enter dashboard-enter--4">
        <header class="section-header">
          <div>
            <p class="eyebrow">Location Preview</p>
            <h2>Map</h2>
          </div>
          <span :class="['geo-state', { 'geo-state--muted': !hasGeo }]">{{ mapStateLabel }}</span>
        </header>
        <div class="map-shell">
          <iframe
            v-if="mapUrl"
            class="map-frame"
            :src="mapUrl"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
            aria-label="Event location map"
          />
          <div v-else class="map-fallback" aria-label="Map not available">
            <MapPin :size="20" aria-hidden="true" />
            <span>Coordinates unavailable</span>
          </div>
        </div>
      </section>

      <section class="geo-panel dashboard-enter dashboard-enter--5" aria-label="Attendance geofence">
        <header class="section-header">
          <div>
            <p class="eyebrow">Attendance</p>
            <h2>Geofence</h2>
          </div>
          <span class="geo-state">{{ geofenceRequiredLabel }}</span>
        </header>
        <div class="geo-list">
          <article>
            <Crosshair :size="16" aria-hidden="true" />
            <span>Latitude</span>
            <strong>{{ latitudeText }}</strong>
          </article>
          <article>
            <Crosshair :size="16" aria-hidden="true" />
            <span>Longitude</span>
            <strong>{{ longitudeText }}</strong>
          </article>
          <article>
            <Ruler :size="16" aria-hidden="true" />
            <span>Radius</span>
            <strong>{{ radiusText }}</strong>
          </article>
          <article>
            <LocateFixed :size="16" aria-hidden="true" />
            <span>Max Accuracy</span>
            <strong>{{ accuracyText }}</strong>
          </article>
        </div>
      </section>
    </section>

    <section v-else class="empty-state">
      <p>Event not found.</p>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  Bell,
  CalendarClock,
  Crosshair,
  LocateFixed,
  MapPin,
  Navigation,
  Ruler,
} from 'lucide-vue-next'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { useSgPreviewBundle } from '@/composables/useSgPreviewBundle.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'
import { hasNavigableHistory, isGovernancePreviewPath, resolveBackFallbackLocation } from '@/services/routeWorkspace.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const route = useRoute()
const router = useRouter()
const { ensureDashboardEvent, getDashboardEventById } = useDashboardSession()
const isCouncilPreviewRoute = computed(() => props.preview && isGovernancePreviewPath(route))
const isSchoolItPreviewRoute = computed(() => props.preview && route.path.startsWith('/exposed/workspace'))
const { previewBundle } = useSgPreviewBundle(isCouncilPreviewRoute)

const eventId = computed(() => Number(route.params.id))
const previewEvent = computed(() => {
  if (isCouncilPreviewRoute.value) {
    return previewBundle.value?.events?.find((entry) => Number(entry?.id) === eventId.value) ?? null
  }

  const byStudent = studentDashboardPreviewData.events.find((entry) => Number(entry?.id) === eventId.value)
  if (byStudent) return byStudent
  // Add fallback for School IT preview events if viewed from Reports table
  const byAdmin = schoolItPreviewData?.events?.find((entry) => Number(entry?.id) === eventId.value)
  return byAdmin ?? null
})
const event = computed(() => props.preview ? previewEvent.value : getDashboardEventById(eventId.value))

const eventName = computed(() => {
  const name = event.value?.title || event.value?.name || event.value?.event_name
  return String(name || 'Untitled event').trim()
})

const previewSchoolSettings = computed(() => {
  if (isCouncilPreviewRoute.value) return previewBundle.value?.schoolSettings || null
  if (isSchoolItPreviewRoute.value) return schoolItPreviewData.schoolSettings
  return studentDashboardPreviewData.schoolSettings
})

usePreviewTheme(() => props.preview, previewSchoolSettings)

onMounted(() => {
  if (props.preview) return
  ensureDashboardEvent(eventId.value).catch(() => null)
})

function goBack() {
  if (hasNavigableHistory(route)) {
    router.back()
    return
  }

  router.push(resolveBackFallbackLocation(route, { eventId: eventId.value }))
}

const statusConfig = {
  upcoming: { label: 'Upcoming', dot: 'dot--yellow' },
  ongoing: { label: 'Ongoing', dot: 'dot--red' },
  completed: { label: 'Completed', dot: 'dot--green' },
  cancelled: { label: 'Cancelled', dot: 'dot--gray' },
}

const statusKey = computed(() => {
  const key = String(event.value?.status || 'upcoming').toLowerCase()
  return statusConfig[key] ? key : 'upcoming'
})

const statusLabel = computed(() => statusConfig[statusKey.value].label)
const statusDotClass = computed(() => statusConfig[statusKey.value].dot)
const statusPillClass = computed(() => `status-pill--${statusKey.value}`)

function toValidDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const startDate = computed(() =>
  toValidDate(event.value?.start_datetime || event.value?.start_time || event.value?.starts_at)
)
const endDate = computed(() =>
  toValidDate(event.value?.end_datetime || event.value?.end_time || event.value?.ends_at)
)

function formatDateOnly(date) {
  if (!date) return 'Not set'
  return new Intl.DateTimeFormat('en-PH', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}

function formatTimeOnly(date) {
  if (!date) return 'Not set'
  return new Intl.DateTimeFormat('en-PH', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

const startDateText = computed(() => formatDateOnly(startDate.value))
const startTimeText = computed(() => formatTimeOnly(startDate.value))
const endDateText = computed(() => formatDateOnly(endDate.value))
const endTimeText = computed(() => formatTimeOnly(endDate.value))

const locationText = computed(() => {
  const location = event.value?.location || event.value?.venue || event.value?.address
  return String(location || 'Location not set').trim()
})

const dateRange = computed(() => {
  const start = startDate.value
  const end = endDate.value
  if (!start || !end) return 'Schedule not set'
  const datePart = start.toLocaleDateString('en-PH', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
  const timePart = `${start.toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })} - ${end.toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })}`
  return `${datePart} at ${timePart}`
})

const geoLatitude = computed(() => Number(event.value?.geo_latitude))
const geoLongitude = computed(() => Number(event.value?.geo_longitude))
function isValidLatitude(value) {
  return Number.isFinite(value) && value >= -90 && value <= 90
}

function isValidLongitude(value) {
  return Number.isFinite(value) && value >= -180 && value <= 180
}

const hasGeo = computed(() =>
  isValidLatitude(geoLatitude.value) && isValidLongitude(geoLongitude.value)
)

const latitudeText = computed(() => {
  if (!hasGeo.value) return '--'
  return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 6 }).format(geoLatitude.value)
})

const longitudeText = computed(() => {
  if (!hasGeo.value) return '--'
  return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 6 }).format(geoLongitude.value)
})

const coordinateSummary = computed(() => {
  if (!hasGeo.value) return 'Coordinates not configured'
  return `${latitudeText.value}, ${longitudeText.value}`
})

const radiusText = computed(() => {
  const radius = Number(event.value?.geo_radius_m ?? event.value?.geo_radius_meters)
  return Number.isFinite(radius) && radius > 0 ? `${Math.round(radius)} m` : 'Not set'
})

const accuracyText = computed(() => {
  const maxAccuracy = Number(event.value?.geo_max_accuracy_m ?? event.value?.geo_max_accuracy_meters)
  return Number.isFinite(maxAccuracy) && maxAccuracy > 0 ? `${Math.round(maxAccuracy)} m` : 'Not set'
})

const mapStateLabel = computed(() => (hasGeo.value ? 'Pinned' : 'No coordinates'))

function isEnabledFlag(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value === 1
  if (typeof value === 'string') return ['1', 'true', 'yes'].includes(value.trim().toLowerCase())
  return false
}

const geofenceRequiredLabel = computed(() => isEnabledFlag(event.value?.geo_required) ? 'Required' : 'Optional')

const mapUrl = computed(() => {
  if (!hasGeo.value) return null
  const lat = geoLatitude.value
  const lon = geoLongitude.value
  const configuredRadius = Number(event.value?.geo_radius_m ?? event.value?.geo_radius_meters)
  const radius = Number.isFinite(configuredRadius) && configuredRadius > 0 ? configuredRadius : 350

  const latDelta = radius / 111320
  const longitudeMeters = 111320 * Math.cos((lat * Math.PI) / 180)
  const lonDelta = radius / (Math.abs(longitudeMeters) > 1 ? longitudeMeters : 1)
  const bbox = [
    (lon - lonDelta).toFixed(6),
    (lat - latDelta).toFixed(6),
    (lon + lonDelta).toFixed(6),
    (lat + latDelta).toFixed(6),
  ].join(',')

  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lon}`
})

const mapDestination = computed(() => {
  if (hasGeo.value) {
    return `${geoLatitude.value},${geoLongitude.value}`
  }
  const fallback = locationText.value.trim()
  return fallback || ''
})

function openInMaps() {
  if (!mapDestination.value) return
  const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(mapDestination.value)}`
  window.open(url, '_blank', 'noopener')
}
</script>

<style scoped>
.event-detail {
  min-height: 100vh;
  padding: 20px 16px 118px;
  background: var(--color-bg);
  color: var(--color-text-always-dark);
}

.detail-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  width: min(100%, 720px);
  margin: 0 auto 14px;
  padding: 4px 0 8px;
  background: var(--color-bg);
}

.header-spacer {
  flex: 1;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  border: none;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.icon-btn:active {
  transform: scale(0.95);
}

.icon-btn--ghost {
  background: #ffffff;
  border: 1px solid rgba(17, 24, 39, 0.08);
  box-shadow: 0 8px 20px rgba(17, 24, 39, 0.08);
}

.detail-body {
  display: grid;
  gap: 14px;
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
}

.event-summary,
.detail-panel,
.map-panel,
.geo-panel {
  background: var(--color-surface);
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 8px;
  box-shadow: 0 14px 34px rgba(17, 24, 39, 0.07);
}

.event-summary {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.event-summary__top {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.event-title {
  font-size: 24px;
  line-height: 1.16;
  font-weight: 800;
  color: var(--color-text-always-dark);
  margin: 0;
  overflow-wrap: anywhere;
}

.summary-list {
  display: grid;
  gap: 10px;
}

.summary-item {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  align-items: start;
  gap: 10px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
}

.summary-item svg {
  color: var(--color-primary);
  margin-top: 1px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.detail-panel,
.map-panel,
.geo-panel {
  padding: 16px;
}

.panel-header,
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.section-header {
  justify-content: space-between;
  align-items: flex-start;
}

.panel-header h2,
.section-header h2 {
  margin: 0;
  font-size: 15px;
  line-height: 1.2;
  color: var(--color-text-always-dark);
}

.panel-header svg {
  color: var(--color-primary);
}

.eyebrow {
  margin: 0 0 3px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}

.time-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.time-grid div {
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 8px;
  background: rgba(17, 24, 39, 0.025);
}

.time-grid span,
.geo-list span {
  display: block;
  margin-bottom: 5px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
}

.time-grid strong,
.time-grid small {
  display: block;
  color: var(--color-text-always-dark);
}

.time-grid strong {
  font-size: 13px;
  line-height: 1.25;
}

.time-grid small {
  margin-top: 2px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.venue-name {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.25;
  color: var(--color-text-always-dark);
  overflow-wrap: anywhere;
}

.venue-coordinates {
  margin: 6px 0 14px;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-muted);
  overflow-wrap: anywhere;
}

.detail-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  width: 100%;
  padding: 0 14px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.detail-action:active {
  transform: scale(0.98);
}

.detail-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.map-shell {
  position: relative;
  width: 100%;
  min-height: 188px;
  aspect-ratio: 16 / 10;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f7f8;
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.map-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.map-fallback {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  overflow: hidden;
  background-image:
    linear-gradient(to right, rgba(17, 24, 39, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(17, 24, 39, 0.05) 1px, transparent 1px);
  background-size: 24px 24px;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 800;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 30px;
  background: rgba(17, 24, 39, 0.06);
  border-radius: 999px;
  padding: 0 12px;
  font-size: 11px;
  font-weight: 800;
  color: var(--color-text-always-dark);
  border: 1px solid rgba(17, 24, 39, 0.08);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot--red { background: #ef4444; }
.dot--yellow { background: #f59e0b; }
.dot--green { background: #22c55e; }
.dot--gray { background: #cfcfcf; }

.status-pill--upcoming { background: rgba(245, 158, 11, 0.12); }
.status-pill--ongoing { background: rgba(239, 68, 68, 0.12); }
.status-pill--completed { background: rgba(34, 197, 94, 0.12); }
.status-pill--cancelled { background: rgba(107, 114, 128, 0.12); }

.geo-state {
  display: flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(17, 24, 39, 0.06);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 800;
}

.geo-state--muted {
  color: var(--color-text-muted);
}

.geo-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.geo-list article {
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 8px;
  background: rgba(17, 24, 39, 0.025);
}

.geo-list svg {
  color: var(--color-primary);
  margin-bottom: 8px;
}

.geo-list strong {
  display: block;
  min-height: 18px;
  color: var(--color-text-always-dark);
  font-size: 13px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-muted);
  font-weight: 600;
}

@media (min-width: 768px) {
  .event-detail {
    padding: 28px 24px 44px;
  }

  .detail-header {
    margin-bottom: 18px;
  }

  .event-title {
    font-size: 30px;
  }

  .detail-grid {
    grid-template-columns: 1fr 1fr;
  }

  .map-shell {
    min-height: 260px;
  }

  .geo-list {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
