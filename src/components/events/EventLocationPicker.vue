<template>
  <section class="event-location-picker">
    <div class="event-location-picker__header">
      <div class="event-location-picker__copy">
        <p class="event-location-picker__eyebrow">Location</p>
        <p class="event-location-picker__summary">
          {{ hasCoordinates ? 'Pin selected.' : 'Tap map or use current.' }}
        </p>
      </div>

      <div class="event-location-picker__actions">
        <button
          class="event-location-picker__action event-location-picker__action--primary"
          type="button"
          :disabled="disabled || locating"
          @click="handleUseCurrentLocation"
        >
          <LoaderCircle
            v-if="locating"
            :size="15"
            :stroke-width="2"
            class="event-location-picker__spinner"
          />
          <LocateFixed v-else :size="15" :stroke-width="2" />
          <span>{{ locating ? 'Locating' : 'Current' }}</span>
        </button>

        <button
          class="event-location-picker__action"
          type="button"
          :disabled="disabled || !hasCoordinates"
          @click="clearSelection"
        >
          <Trash2 :size="15" :stroke-width="2" />
          <span>Clear</span>
        </button>
      </div>
    </div>

    <div class="event-location-picker__map-shell">
      <div ref="mapEl" class="event-location-picker__map" />

      <div
        v-if="loadingMap || (!loadError && !hasCoordinates)"
        class="event-location-picker__map-overlay"
        :class="{ 'event-location-picker__map-overlay--loading': loadingMap }"
        aria-hidden="true"
      >
        <LoaderCircle
          v-if="loadingMap"
          :size="18"
          :stroke-width="2"
          class="event-location-picker__spinner"
        />
        <MapPin v-else :size="18" :stroke-width="2" />
        <span>{{ loadingMap ? 'Loading map' : 'Tap to pin' }}</span>
      </div>

      <div v-if="loadError" class="event-location-picker__map-error" role="alert">
        {{ loadError }}
      </div>
    </div>

    <div class="event-location-picker__stats">
      <article class="event-location-picker__stat">
        <span>Lat</span>
        <strong>{{ formattedLatitude }}</strong>
      </article>

      <article class="event-location-picker__stat">
        <span>Lng</span>
        <strong>{{ formattedLongitude }}</strong>
      </article>

      <article class="event-location-picker__stat">
        <span>Radius</span>
        <strong>{{ formattedRadius }}</strong>
      </article>
    </div>

    <p
      v-if="statusMessage"
      class="event-location-picker__status"
      :class="{ 'event-location-picker__status--error': statusTone === 'error' }"
      aria-live="polite"
    >
      {{ statusMessage }}
    </p>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LoaderCircle, LocateFixed, MapPin, Trash2 } from 'lucide-vue-next'
import { getCurrentPositionOrThrow } from '@/services/devicePermissions.js'

const props = defineProps({
  latitude: {
    type: [Number, String],
    default: '',
  },
  longitude: {
    type: [Number, String],
    default: '',
  },
  radiusM: {
    type: [Number, String],
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:latitude', 'update:longitude'])

const mapEl = ref(null)
const loadingMap = ref(true)
const locating = ref(false)
const loadError = ref('')
const statusMessage = ref('')
const statusTone = ref('info')

const normalizedLatitude = computed(() => toFiniteNumber(props.latitude))
const normalizedLongitude = computed(() => toFiniteNumber(props.longitude))
const normalizedRadius = computed(() => {
  const parsed = Number(props.radiusM)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
})
const hasCoordinates = computed(() => (
  normalizedLatitude.value != null
  && normalizedLongitude.value != null
))
const formattedLatitude = computed(() => formatCoordinate(normalizedLatitude.value))
const formattedLongitude = computed(() => formatCoordinate(normalizedLongitude.value))
const formattedRadius = computed(() => (
  normalizedRadius.value != null
    ? `${Math.round(normalizedRadius.value)} m`
    : 'No radius yet'
))

const defaultMapCenter = [12.8797, 121.7740]
const defaultMapZoom = 5

let leafletRef = null
let mapInstance = null
let markerInstance = null
let radiusPreview = null
let resizeObserver = null
let invalidateTimeoutId = 0
let mapInitSequence = 0
let isComponentUnmounted = false

onMounted(() => {
  isComponentUnmounted = false
  void initializeMap()
})

onBeforeUnmount(() => {
  isComponentUnmounted = true
  cleanupMap()
})

watch(
  () => [normalizedLatitude.value, normalizedLongitude.value, normalizedRadius.value],
  () => {
    syncSelectionOnMap({ focus: false })
  }
)

watch(
  () => props.disabled,
  () => {
    syncSelectionOnMap({ focus: false })
  }
)

async function initializeMap() {
  if (mapInstance || !mapEl.value) return

  const containerEl = mapEl.value
  const initSequence = ++mapInitSequence

  loadingMap.value = true
  loadError.value = ''

  try {
    await waitForStableMapContainer(containerEl)

    if (
      isComponentUnmounted
      || initSequence !== mapInitSequence
      || !isUsableMapContainer(containerEl)
      || mapEl.value !== containerEl
    ) {
      return
    }

    const [leafletModule] = await Promise.all([
      import('leaflet'),
      import('leaflet/dist/leaflet.css'),
    ])

    if (
      isComponentUnmounted
      || initSequence !== mapInitSequence
      || !containerEl?.isConnected
      || mapEl.value !== containerEl
    ) {
      return
    }

    leafletRef = leafletModule.default || leafletModule
    mapInstance = leafletRef.map(containerEl, {
      zoomControl: false,
      attributionControl: true,
      center: defaultMapCenter,
      zoom: defaultMapZoom,
    })

    leafletRef.control.zoom({ position: 'bottomright' }).addTo(mapInstance)
    leafletRef.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
      updateWhenIdle: true,
      keepBuffer: 2,
    }).addTo(mapInstance)

    mapInstance.on('click', handleMapClick)

    syncSelectionOnMap({ focus: true })
    scheduleMapInvalidate()
    observeMapResize()
  } catch (error) {
    if (!isComponentUnmounted && initSequence === mapInitSequence) {
      loadError.value = error?.message || 'Unable to load the map picker.'
    }
  } finally {
    if (initSequence === mapInitSequence) {
      loadingMap.value = false
    }
  }
}

function cleanupMap() {
  mapInitSequence += 1

  if (invalidateTimeoutId) {
    window.clearTimeout(invalidateTimeoutId)
    invalidateTimeoutId = 0
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  removeMarkerFromMap()
  removeRadiusPreview()

  if (mapInstance) {
    try {
      mapInstance.off('click', handleMapClick)
      mapInstance.remove()
    } catch {}
    mapInstance = null
  }

  leafletRef = null
}

function observeMapResize() {
  if (!mapEl.value || typeof ResizeObserver === 'undefined') return

  resizeObserver = new ResizeObserver(() => {
    if (isUsableMapContainer(mapEl.value)) {
      safeMapOperation(() => mapInstance?.invalidateSize())
    }
  })
  resizeObserver.observe(mapEl.value)
}

function scheduleMapInvalidate() {
  if (!mapInstance) return

  nextTick(() => {
    if (isUsableMapContainer(mapEl.value)) {
      safeMapOperation(() => mapInstance?.invalidateSize())
    }
    invalidateTimeoutId = window.setTimeout(() => {
      if (isUsableMapContainer(mapEl.value)) {
        safeMapOperation(() => mapInstance?.invalidateSize())
      }
      invalidateTimeoutId = 0
    }, 220)
  })
}

function handleMapClick(event) {
  if (props.disabled) return
  applyCoordinates(event.latlng.lat, event.latlng.lng, 'Pin updated.')
}

function handleMarkerDragEnd(event) {
  const latLng = event.target.getLatLng()
  applyCoordinates(latLng.lat, latLng.lng, 'Pin moved.')
}

async function handleUseCurrentLocation() {
  locating.value = true
  setStatus('', 'info')

  try {
    const position = await getCurrentPositionOrThrow({
      enableHighAccuracy: true,
      timeout: 20000,
      maximumAge: 0,
    })

    const accuracy = Number(position?.accuracy)
    const accuracyLabel = Number.isFinite(accuracy) && accuracy > 0
      ? ` (accuracy ${Math.round(accuracy)} m)`
      : ''

    applyCoordinates(
      position.latitude,
      position.longitude,
      `Current location selected${accuracyLabel}.`
    )
  } catch (error) {
    setStatus(
      error?.message || 'Unable to retrieve your current location.',
      'error'
    )
  } finally {
    locating.value = false
  }
}

function clearSelection() {
  if (props.disabled || !hasCoordinates.value) return

  emit('update:latitude', '')
  emit('update:longitude', '')
  setStatus('Pin cleared.', 'info')
  syncSelectionOnMap({ focus: true, latitude: null, longitude: null })
}

function applyCoordinates(latitude, longitude, message) {
  const roundedLatitude = Number(Number(latitude).toFixed(6))
  const roundedLongitude = Number(Number(longitude).toFixed(6))

  emit('update:latitude', roundedLatitude)
  emit('update:longitude', roundedLongitude)
  setStatus(message, 'info')

  syncSelectionOnMap({
    focus: true,
    latitude: roundedLatitude,
    longitude: roundedLongitude,
  })
}

function syncSelectionOnMap({
  focus = false,
  latitude = normalizedLatitude.value,
  longitude = normalizedLongitude.value,
} = {}) {
  if (!mapInstance || !leafletRef) return

  const hasPoint = Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude))

  if (!hasPoint) {
    removeMarkerFromMap()
    removeRadiusPreview()

    if (focus) {
      safeMapOperation(() => {
        mapInstance.setView(defaultMapCenter, defaultMapZoom, {
          animate: false,
        })
      })
    }

    return
  }

  const latLng = leafletRef.latLng(Number(latitude), Number(longitude))

  if (!markerInstance) {
    markerInstance = leafletRef.marker(latLng, {
      draggable: !props.disabled,
      autoPanOnFocus: false,
      keyboard: false,
      icon: createMarkerIcon(),
    }).addTo(mapInstance)
    markerInstance.on('dragend', handleMarkerDragEnd)
  } else {
    markerInstance.setLatLng(latLng)
    if (props.disabled) {
      markerInstance.dragging?.disable()
    } else {
      markerInstance.dragging?.enable()
    }
  }

  syncRadiusPreview(latLng)

  if (!focus) return

  if (radiusPreview) {
    safeMapOperation(() => {
      mapInstance.fitBounds(radiusPreview.getBounds().pad(0.24), {
        maxZoom: 17,
      })
    })
    return
  }

  safeMapOperation(() => {
    mapInstance.setView(latLng, Math.max(mapInstance.getZoom(), 16), {
      animate: true,
    })
  })
}

function syncRadiusPreview(latLng) {
  if (!mapInstance || !leafletRef) return

  const radius = normalizedRadius.value
  if (!radius) {
    removeRadiusPreview()
    return
  }

  const accentColor = resolveAccentColor()

  if (!radiusPreview) {
    radiusPreview = leafletRef.circle(latLng, {
      radius,
      color: accentColor,
      weight: 2,
      opacity: 0.9,
      fillColor: accentColor,
      fillOpacity: 0.12,
    }).addTo(mapInstance)
    return
  }

  radiusPreview.setLatLng(latLng)
  radiusPreview.setRadius(radius)
  radiusPreview.setStyle({
    color: accentColor,
    fillColor: accentColor,
  })
}

function createMarkerIcon() {
  return leafletRef.divIcon({
    className: 'event-location-picker__pin-wrapper',
    html: '<span class="event-location-picker__pin-core"></span>',
    iconSize: [22, 22],
    iconAnchor: [11, 11],
  })
}

function removeMarkerFromMap() {
  if (!markerInstance) return

  try {
    markerInstance.off('dragend', handleMarkerDragEnd)
    markerInstance.dragging?.disable?.()
  } catch {}

  try {
    if (mapInstance?.hasLayer?.(markerInstance)) {
      mapInstance.removeLayer(markerInstance)
    } else {
      markerInstance.remove?.()
    }
  } catch {}

  markerInstance = null
}

function removeRadiusPreview() {
  if (!radiusPreview) return

  try {
    if (mapInstance?.hasLayer?.(radiusPreview)) {
      mapInstance.removeLayer(radiusPreview)
    } else {
      radiusPreview.remove?.()
    }
  } catch {}

  radiusPreview = null
}

function resolveAccentColor() {
  if (typeof window === 'undefined') return '#3b82f6'

  const color = window.getComputedStyle(document.documentElement)
    .getPropertyValue('--color-primary')
    .trim()

  return color || '#3b82f6'
}

function setStatus(message, tone = 'info') {
  statusMessage.value = String(message || '').trim()
  statusTone.value = tone
}

function toFiniteNumber(value) {
  if (value == null || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function isUsableMapContainer(element) {
  if (!element?.isConnected) return false

  const rect = element.getBoundingClientRect()
  return rect.width > 0 && rect.height > 0
}

async function waitForStableMapContainer(element) {
  if (typeof window === 'undefined') return

  for (let attempt = 0; attempt < 12; attempt += 1) {
    if (isComponentUnmounted || element !== mapEl.value) return
    if (isUsableMapContainer(element)) return

    await new Promise((resolve) => window.requestAnimationFrame(resolve))
  }
}

function safeMapOperation(operation) {
  try {
    operation()
  } catch (error) {
    const message = String(error?.message || '')
    if (message.toLowerCase().includes('infinite number of tiles')) {
      loadError.value = 'The map is still sizing. Reopen this panel or use current location if it does not appear.'
      return
    }

    throw error
  }
}

function formatCoordinate(value) {
  return Number.isFinite(Number(value))
    ? Number(value).toFixed(6)
    : 'Not selected'
}
</script>

<style scoped>
.event-location-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-location-picker__header,
.event-location-picker__actions {
  display: flex;
}

.event-location-picker__header {
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.event-location-picker__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-location-picker__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary, #6b7280);
}

.event-location-picker__summary,
.event-location-picker__status,
.event-location-picker__map-error {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.event-location-picker__summary {
  color: var(--color-text-secondary, #6b7280);
}

.event-location-picker__actions {
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.event-location-picker__action {
  min-height: 40px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 8px;
  background: #fff;
  color: var(--color-text-always-dark, #111827);
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
}

.event-location-picker__action:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary, #3b82f6) 28%, white);
  box-shadow: 0 12px 24px rgba(17, 24, 39, 0.08);
}

.event-location-picker__action--primary {
  background: color-mix(in srgb, var(--color-primary, #3b82f6) 10%, white);
}

.event-location-picker__action:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.event-location-picker__map-shell {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: #f8fafc;
}

.event-location-picker__map {
  min-height: 220px;
}

.event-location-picker__map-overlay,
.event-location-picker__map-error {
  position: absolute;
  left: 16px;
  right: 16px;
  top: 16px;
  z-index: 500;
  padding: 10px 12px;
  border-radius: 8px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.event-location-picker__map-overlay {
  pointer-events: none;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  max-width: calc(100% - 32px);
  background: rgba(255, 255, 255, 0.88);
  color: var(--color-text-always-dark, #111827);
  font-size: 13px;
  font-weight: 700;
}

.event-location-picker__map-overlay--loading {
  background: rgba(15, 23, 42, 0.84);
  color: #f8fafc;
}

.event-location-picker__map-error {
  background: rgba(254, 242, 242, 0.92);
  color: #b91c1c;
  font-weight: 700;
}

.event-location-picker__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.event-location-picker__stat {
  min-width: 0;
  padding: 10px 11px;
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(17, 24, 39, 0.08);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-location-picker__stat span {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-secondary, #6b7280);
}

.event-location-picker__stat strong {
  font-size: 12px;
  font-weight: 800;
  color: var(--color-text-always-dark, #111827);
  overflow-wrap: anywhere;
}

.event-location-picker__status {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  font-weight: 700;
}

.event-location-picker__status--error {
  background: rgba(220, 38, 38, 0.08);
  color: #b91c1c;
}

.event-location-picker__spinner {
  animation: event-location-picker-spin 0.9s linear infinite;
}

.event-location-picker__map :deep(.leaflet-container) {
  width: 100%;
  height: 100%;
  min-height: 220px;
  font: inherit;
}

.event-location-picker__map :deep(.leaflet-control-attribution) {
  border-radius: 10px 0 0 0;
  font-size: 10px;
}

.event-location-picker__map :deep(.leaflet-control-zoom a) {
  width: 34px;
  height: 34px;
  line-height: 34px;
  color: var(--color-text-always-dark, #111827);
}

.event-location-picker__map :deep(.event-location-picker__pin-wrapper) {
  background: transparent;
  border: none;
}

.event-location-picker__map :deep(.event-location-picker__pin-core) {
  display: block;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: var(--color-primary, #3b82f6);
  border: 4px solid #fff;
  box-shadow:
    0 10px 20px rgba(15, 23, 42, 0.18),
    0 0 0 6px color-mix(in srgb, var(--color-primary, #3b82f6) 18%, transparent);
}

@keyframes event-location-picker-spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 760px) {
  .event-location-picker__header {
    align-items: stretch;
    flex-direction: column;
  }

  .event-location-picker__actions {
    width: 100%;
    justify-content: stretch;
  }

  .event-location-picker__action {
    flex: 1 1 0;
  }

  .event-location-picker__map,
  .event-location-picker__map :deep(.leaflet-container) {
    min-height: 200px;
  }
}

@media (max-width: 520px) {
  .event-location-picker__stats {
    grid-template-columns: 1fr;
  }
}
</style>
