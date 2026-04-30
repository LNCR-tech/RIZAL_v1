<template>
  <section class="event-location-picker">
    <label class="event-location-picker__search">
      <span class="event-location-picker__search-label">Location</span>

      <div class="event-location-picker__search-shell">
        <input
          ref="searchInputEl"
          :value="locationQuery"
          class="event-location-picker__search-input"
          type="text"
          name="event_location"
          placeholder="Search nearby places"
          autocomplete="off"
          :disabled="disabled"
          @input="handleLocationInput"
          @focus="handleLocationFocus"
          @blur="handleLocationBlur"
          @keydown.down.prevent="moveSuggestionHighlight(1)"
          @keydown.up.prevent="moveSuggestionHighlight(-1)"
          @keydown.enter.prevent="confirmHighlightedSuggestion"
          @keydown.escape.prevent="dismissSuggestions"
        >

        <LoaderCircle
          v-if="searchingSuggestions"
          :size="16"
          :stroke-width="2"
          class="event-location-picker__search-spinner"
        />
      </div>

      <div
        v-if="showSuggestionPanel"
        class="event-location-picker__suggestions"
        role="listbox"
        aria-label="Suggested locations"
      >
        <button
          v-for="(suggestion, index) in locationSuggestions"
          :key="suggestion.id"
          class="event-location-picker__suggestion"
          :class="{ 'event-location-picker__suggestion--active': index === highlightedSuggestionIndex }"
          type="button"
          @mousedown.prevent="selectLocationSuggestion(suggestion)"
        >
          <strong>{{ suggestion.label }}</strong>
          <span>{{ suggestion.secondaryLabel || suggestion.displayName }}</span>
        </button>

        <p
          v-if="!locationSuggestions.length && locationSearchMessage"
          class="event-location-picker__suggestions-empty"
        >
          {{ locationSearchMessage }}
        </p>
      </div>
    </label>

    <div class="event-location-picker__header">
      <div class="event-location-picker__copy">
        <p class="event-location-picker__eyebrow">Map</p>
        <p class="event-location-picker__summary">
          {{ hasCoordinates ? 'Pin selected.' : 'Search, tap map, or use current.' }}
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
          :disabled="disabled || !hasCoordinateInput"
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
import {
  getCurrentPositionIfAvailable,
  getCurrentPositionOrThrow,
} from '@/services/devicePermissions.js'
import {
  formatCoordinateLocationLabel,
  resolveLocationLabel,
  searchLocationSuggestions,
} from '@/services/locationDisplay.js'

const props = defineProps({
  locationLabel: {
    type: String,
    default: '',
  },
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

const emit = defineEmits(['update:locationLabel', 'update:latitude', 'update:longitude'])

const MIN_LATITUDE = -90
const MAX_LATITUDE = 90
const MIN_LONGITUDE = -180
const MAX_LONGITUDE = 180
const DEFAULT_MAP_CENTER = Object.freeze({
  latitude: 8.1552,
  longitude: 123.8421,
})
const DEFAULT_MAP_ZOOM = 14
const DEFAULT_MAP_MIN_ZOOM = 6
const DEFAULT_AUTO_LOCATE_ZOOM = 15
const LOCATION_SEARCH_DEBOUNCE_MS = 220
const SHORT_QUERY_SEARCH_RADIUS_M = 6000
const MEDIUM_QUERY_SEARCH_RADIUS_M = 12000
const LONG_QUERY_SEARCH_RADIUS_M = 22000

const mapEl = ref(null)
const searchInputEl = ref(null)
const loadingMap = ref(true)
const locating = ref(false)
const loadError = ref('')
const statusMessage = ref('')
const statusTone = ref('info')
const locationQuery = ref(String(props.locationLabel || ''))
const locationSuggestions = ref([])
const searchingSuggestions = ref(false)
const locationSearchError = ref('')
const highlightedSuggestionIndex = ref(-1)
const isLocationInputFocused = ref(false)

const normalizedLatitude = computed(() => toFiniteNumber(props.latitude))
const normalizedLongitude = computed(() => toFiniteNumber(props.longitude))
const normalizedRadius = computed(() => {
  const parsed = Number(props.radiusM)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
})
const hasCoordinateInput = computed(() => (
  normalizedLatitude.value != null
  || normalizedLongitude.value != null
))
const hasCoordinates = computed(() => (
  isValidLatitude(normalizedLatitude.value)
  && isValidLongitude(normalizedLongitude.value)
))
const formattedLatitude = computed(() => formatCoordinate(normalizedLatitude.value))
const formattedLongitude = computed(() => formatCoordinate(normalizedLongitude.value))
const formattedRadius = computed(() => (
  normalizedRadius.value != null
    ? `${Math.round(normalizedRadius.value)} m`
    : 'No radius yet'
))
const normalizedLocationQuery = computed(() => String(locationQuery.value || '').trim())
const locationSearchMessage = computed(() => {
  if (!normalizedLocationQuery.value) return ''
  if (searchingSuggestions.value) return 'Searching nearby locations...'
  if (locationSearchError.value) return locationSearchError.value
  if (!locationSuggestions.value.length) return 'No nearby streets, barangays, or places matched your search.'
  return ''
})
const showSuggestionPanel = computed(() => (
  !props.disabled
  && isLocationInputFocused.value
  && (
    searchingSuggestions.value
    || Boolean(locationSuggestions.value.length)
    || Boolean(locationSearchMessage.value)
  )
))

let leafletRef = null
let mapInstance = null
let markerInstance = null
let radiusPreview = null
let resizeObserver = null
let invalidateTimeoutId = 0
let mapInitSequence = 0
let isComponentUnmounted = false
let autoLocateSequence = 0
let autoLocateAttempted = false
let suggestionFetchController = null
let suggestionTimeoutId = 0
let reverseGeocodeController = null
let suppressedSearchValue = ''
let blurDismissTimeoutId = 0
let lastKnownUserCoordinates = { ...DEFAULT_MAP_CENTER }

onMounted(() => {
  isComponentUnmounted = false
  void initializeMap()
})

onBeforeUnmount(() => {
  isComponentUnmounted = true
  cleanupMap()
  clearSuggestionSearch()
  reverseGeocodeController?.abort?.()
  reverseGeocodeController = null

  if (blurDismissTimeoutId) {
    window.clearTimeout(blurDismissTimeoutId)
    blurDismissTimeoutId = 0
  }
})

watch(
  () => [normalizedLatitude.value, normalizedLongitude.value, normalizedRadius.value],
  ([latitude, longitude]) => {
    if (isValidLatitude(latitude) && isValidLongitude(longitude)) {
      lastKnownUserCoordinates = {
        latitude: Number(latitude),
        longitude: Number(longitude),
      }
    }

    syncSelectionOnMap({ focus: false })
  }
)

watch(
  () => props.disabled,
  () => {
    syncSelectionOnMap({ focus: false })
    if (props.disabled) {
      dismissSuggestions()
    }
  }
)

watch(
  () => props.locationLabel,
  (nextValue) => {
    const normalizedValue = String(nextValue || '')
    if (normalizedValue === locationQuery.value) return

    locationQuery.value = normalizedValue
    if (suppressedSearchValue && suppressedSearchValue === normalizedValue.trim()) {
      suppressedSearchValue = ''
      dismissSuggestions()
      return
    }

    scheduleSuggestionSearch()
  }
)

async function initializeMap() {
  if (mapInstance || !mapEl.value) return

  const containerEl = mapEl.value
  const initSequence = ++mapInitSequence

  loadingMap.value = true
  loadError.value = ''

  try {
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
    const worldBounds = leafletRef.latLngBounds([[-85, -180], [85, 180]])
    mapInstance = leafletRef.map(containerEl, {
      zoomControl: false,
      attributionControl: true,
      minZoom: DEFAULT_MAP_MIN_ZOOM,
      maxBounds: worldBounds,
      maxBoundsViscosity: 1,
      worldCopyJump: false,
    })

    leafletRef.control.zoom({ position: 'bottomright' }).addTo(mapInstance)
    leafletRef.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      minZoom: DEFAULT_MAP_MIN_ZOOM,
      maxZoom: 19,
      noWrap: true,
    }).addTo(mapInstance)

    mapInstance.on('click', handleMapClick)

    focusFallbackMap({ animate: false })
    syncSelectionOnMap({ focus: true })
    startAutoLocateIfIdle()
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
  autoLocateSequence += 1

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
    mapInstance?.invalidateSize()
  })
  resizeObserver.observe(mapEl.value)
}

function scheduleMapInvalidate() {
  if (!mapInstance) return

  nextTick(() => {
    mapInstance?.invalidateSize()
    invalidateTimeoutId = window.setTimeout(() => {
      mapInstance?.invalidateSize()
      invalidateTimeoutId = 0
    }, 220)
  })
}

function handleMapClick(event) {
  if (props.disabled) return
  void applyCoordinates(event.latlng.lat, event.latlng.lng, 'Pin updated.', {
    resolveLabel: true,
  })
}

function handleMarkerDragEnd(event) {
  const latLng = event.target.getLatLng()
  void applyCoordinates(latLng.lat, latLng.lng, 'Pin moved.', {
    resolveLabel: true,
  })
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

    lastKnownUserCoordinates = {
      latitude: position.latitude,
      longitude: position.longitude,
    }

    await applyCoordinates(
      position.latitude,
      position.longitude,
      `Current location selected${accuracyLabel}.`,
      {
        resolveLabel: true,
      }
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

function handleLocationInput(event) {
  const nextValue = String(event?.target?.value || '')
  locationQuery.value = nextValue
  emit('update:locationLabel', nextValue)
  scheduleSuggestionSearch()
}

function handleLocationFocus() {
  if (blurDismissTimeoutId) {
    window.clearTimeout(blurDismissTimeoutId)
    blurDismissTimeoutId = 0
  }

  isLocationInputFocused.value = true
  scheduleSuggestionSearch()
}

function handleLocationBlur() {
  blurDismissTimeoutId = window.setTimeout(() => {
    isLocationInputFocused.value = false
    dismissSuggestions()
    blurDismissTimeoutId = 0
  }, 120)
}

function moveSuggestionHighlight(step = 1) {
  if (!locationSuggestions.value.length) return

  const total = locationSuggestions.value.length
  if (highlightedSuggestionIndex.value < 0) {
    highlightedSuggestionIndex.value = step > 0 ? 0 : total - 1
    return
  }

  highlightedSuggestionIndex.value = (
    highlightedSuggestionIndex.value + step + total
  ) % total
}

function confirmHighlightedSuggestion() {
  if (!locationSuggestions.value.length) return

  const targetIndex = highlightedSuggestionIndex.value >= 0
    ? highlightedSuggestionIndex.value
    : 0
  const suggestion = locationSuggestions.value[targetIndex]
  if (!suggestion) return

  void selectLocationSuggestion(suggestion)
}

function dismissSuggestions() {
  clearSuggestionSearch()
  locationSuggestions.value = []
  locationSearchError.value = ''
  highlightedSuggestionIndex.value = -1
  searchingSuggestions.value = false
}

function clearSuggestionSearch() {
  if (suggestionTimeoutId) {
    window.clearTimeout(suggestionTimeoutId)
    suggestionTimeoutId = 0
  }

  suggestionFetchController?.abort?.()
  suggestionFetchController = null
}

function scheduleSuggestionSearch() {
  clearSuggestionSearch()
  highlightedSuggestionIndex.value = -1
  locationSearchError.value = ''

  if (!isLocationInputFocused.value || props.disabled) {
    return
  }

  if (!normalizedLocationQuery.value) {
    locationSuggestions.value = []
    return
  }

  suggestionTimeoutId = window.setTimeout(() => {
    suggestionTimeoutId = 0
    void loadLocationSuggestions()
  }, LOCATION_SEARCH_DEBOUNCE_MS)
}

async function loadLocationSuggestions() {
  if (!normalizedLocationQuery.value || props.disabled) {
    locationSuggestions.value = []
    return
  }

  suggestionFetchController?.abort?.()
  suggestionFetchController = typeof AbortController !== 'undefined' ? new AbortController() : null
  searchingSuggestions.value = true
  locationSearchError.value = ''

  try {
    const nearbyAnchor = await resolveSearchBiasCoordinates()
    const suggestions = await searchLocationSuggestions({
      query: normalizedLocationQuery.value,
      near: nearbyAnchor,
      signal: suggestionFetchController?.signal,
      limit: 6,
      radiusMeters: resolveSearchRadiusMeters(normalizedLocationQuery.value),
    })

    locationSuggestions.value = suggestions
    highlightedSuggestionIndex.value = suggestions.length ? 0 : -1
  } catch (error) {
    if (error?.name === 'AbortError') return

    locationSuggestions.value = []
    locationSearchError.value = error?.message || 'Unable to search nearby locations.'
  } finally {
    searchingSuggestions.value = false
  }
}

async function resolveSearchBiasCoordinates() {
  if (isValidLatitude(normalizedLatitude.value) && isValidLongitude(normalizedLongitude.value)) {
    return {
      latitude: normalizedLatitude.value,
      longitude: normalizedLongitude.value,
    }
  }

  const resolvedUserCoordinates = await resolveNearbyUserCoordinates()
  if (resolvedUserCoordinates) {
    return resolvedUserCoordinates
  }

  if (
    Number.isFinite(Number(lastKnownUserCoordinates?.latitude))
    && Number.isFinite(Number(lastKnownUserCoordinates?.longitude))
  ) {
    return lastKnownUserCoordinates
  }

  return DEFAULT_MAP_CENTER
}

async function resolveNearbyUserCoordinates() {
  const hasResolvedNearbyCoordinates = (
    Number.isFinite(Number(lastKnownUserCoordinates?.latitude))
    && Number.isFinite(Number(lastKnownUserCoordinates?.longitude))
    && !isDefaultSearchAnchor(lastKnownUserCoordinates)
  )

  if (hasResolvedNearbyCoordinates) {
    return {
      latitude: Number(lastKnownUserCoordinates.latitude),
      longitude: Number(lastKnownUserCoordinates.longitude),
    }
  }

  const position = await getCurrentPositionIfAvailable({
    enableHighAccuracy: false,
    timeout: 1800,
    maximumAge: 180000,
  })

  if (!position) return null

  lastKnownUserCoordinates = {
    latitude: position.latitude,
    longitude: position.longitude,
  }

  return {
    latitude: position.latitude,
    longitude: position.longitude,
  }
}

function isDefaultSearchAnchor(coordinates = null) {
  const latitude = Number(coordinates?.latitude)
  const longitude = Number(coordinates?.longitude)

  return (
    Number.isFinite(latitude)
    && Number.isFinite(longitude)
    && Math.abs(latitude - DEFAULT_MAP_CENTER.latitude) < 0.000001
    && Math.abs(longitude - DEFAULT_MAP_CENTER.longitude) < 0.000001
  )
}

function resolveSearchRadiusMeters(query) {
  const normalizedLength = String(query || '').trim().length
  if (normalizedLength <= 1) return SHORT_QUERY_SEARCH_RADIUS_M
  if (normalizedLength === 2) return MEDIUM_QUERY_SEARCH_RADIUS_M
  return LONG_QUERY_SEARCH_RADIUS_M
}

async function selectLocationSuggestion(suggestion) {
  if (!suggestion) return

  const label = buildSuggestionValue(suggestion)
  setLocationLabel(label, { suppressSearch: true })
  dismissSuggestions()
  await applyCoordinates(
    suggestion.latitude,
    suggestion.longitude,
    'Location selected.',
    {
      locationLabel: label,
      focus: true,
    }
  )
}

function buildSuggestionValue(suggestion) {
  const primary = String(suggestion?.label || '').trim()
  const secondary = String(suggestion?.secondaryLabel || '').trim()
  if (!primary) return String(suggestion?.displayName || '').trim()
  if (!secondary) return primary
  if (primary.toLowerCase() === secondary.toLowerCase()) return primary
  return `${primary}, ${secondary}`
}

function clearSelection() {
  if (props.disabled || !hasCoordinateInput.value) return

  emit('update:latitude', '')
  emit('update:longitude', '')
  setStatus('Pin cleared.', 'info')
  syncSelectionOnMap({ focus: true, latitude: null, longitude: null })
}

async function applyCoordinates(latitude, longitude, message, options = {}) {
  const {
    focus = true,
    resolveLabel = false,
    locationLabel = '',
  } = options

  const roundedLatitude = Number(Number(latitude).toFixed(6))
  const roundedLongitude = Number(Number(longitude).toFixed(6))

  emit('update:latitude', roundedLatitude)
  emit('update:longitude', roundedLongitude)
  setStatus(message, 'info')

  lastKnownUserCoordinates = {
    latitude: roundedLatitude,
    longitude: roundedLongitude,
  }

  if (locationLabel) {
    setLocationLabel(locationLabel, { suppressSearch: true })
  } else if (resolveLabel) {
    await resolveAndApplyLocationLabel(roundedLatitude, roundedLongitude)
  }

  syncSelectionOnMap({
    focus,
    latitude: roundedLatitude,
    longitude: roundedLongitude,
  })
}

async function resolveAndApplyLocationLabel(latitude, longitude) {
  reverseGeocodeController?.abort?.()
  reverseGeocodeController = typeof AbortController !== 'undefined' ? new AbortController() : null

  try {
    const label = await resolveLocationLabel({
      latitude,
      longitude,
      signal: reverseGeocodeController?.signal,
    })
    if (label) {
      setLocationLabel(label, { suppressSearch: true })
      return label
    }
  } catch (error) {
    if (error?.name === 'AbortError') return ''
  }

  const fallbackLabel = formatCoordinateLocationLabel({ latitude, longitude })
  setLocationLabel(fallbackLabel, { suppressSearch: true })
  return fallbackLabel
}

function setLocationLabel(value, { suppressSearch = false } = {}) {
  const normalizedValue = String(value || '').trim()
  suppressedSearchValue = suppressSearch ? normalizedValue : ''
  locationQuery.value = normalizedValue
  emit('update:locationLabel', normalizedValue)
}

function syncSelectionOnMap({
  focus = false,
  latitude = normalizedLatitude.value,
  longitude = normalizedLongitude.value,
} = {}) {
  if (!mapInstance || !leafletRef) return

  const hasPoint = isValidLatitude(latitude) && isValidLongitude(longitude)

  if (!hasPoint) {
    removeMarkerFromMap()
    removeRadiusPreview()

    if (focus) {
      focusFallbackMap()
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
    mapInstance.fitBounds(radiusPreview.getBounds().pad(0.24), {
      maxZoom: 17,
    })
    return
  }

  mapInstance.setView(latLng, Math.max(mapInstance.getZoom(), 16), {
    animate: true,
  })
}

function focusFallbackMap({ animate = true } = {}) {
  if (!mapInstance) return

  mapInstance.setView(
    [DEFAULT_MAP_CENTER.latitude, DEFAULT_MAP_CENTER.longitude],
    DEFAULT_MAP_ZOOM,
    { animate }
  )
}

function focusNearestAvailableLocation(latitude, longitude, { animate = true } = {}) {
  if (!mapInstance || !leafletRef) return
  if (!isValidLatitude(latitude) || !isValidLongitude(longitude)) {
    focusFallbackMap({ animate })
    return
  }

  const latLng = leafletRef.latLng(Number(latitude), Number(longitude))
  mapInstance.setView(latLng, Math.max(mapInstance.getZoom(), DEFAULT_AUTO_LOCATE_ZOOM), {
    animate,
  })
}

function startAutoLocateIfIdle() {
  if (autoLocateAttempted || hasCoordinates.value || !mapInstance) return

  autoLocateAttempted = true
  const locateSequence = ++autoLocateSequence

  void (async () => {
    const position = await getCurrentPositionIfAvailable({
      enableHighAccuracy: false,
      timeout: 3500,
      maximumAge: 120000,
    })

    if (
      !position
      || isComponentUnmounted
      || locateSequence !== autoLocateSequence
      || !mapInstance
      || hasCoordinates.value
    ) {
      return
    }

    lastKnownUserCoordinates = {
      latitude: position.latitude,
      longitude: position.longitude,
    }
    focusNearestAvailableLocation(position.latitude, position.longitude)
  })()
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

function isValidLatitude(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= MIN_LATITUDE && parsed <= MAX_LATITUDE
}

function isValidLongitude(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= MIN_LONGITUDE && parsed <= MAX_LONGITUDE
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

.event-location-picker__search {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.event-location-picker__search-label {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: var(--color-text-always-dark, #111827);
}

.event-location-picker__search-shell {
  position: relative;
  display: flex;
  align-items: center;
}

.event-location-picker__search-input {
  width: 100%;
  min-height: 44px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 10px;
  background: #fff;
  color: var(--color-text-always-dark, #111827);
  padding: 0 42px 0 14px;
  font-size: 14px;
  font-weight: 600;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.event-location-picker__search-input:focus {
  outline: none;
  border-color: color-mix(in srgb, var(--color-primary, #3b82f6) 40%, white);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary, #3b82f6) 16%, transparent);
}

.event-location-picker__search-input:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.event-location-picker__search-spinner {
  position: absolute;
  right: 14px;
  color: var(--color-text-secondary, #6b7280);
  animation: event-location-picker-spin 0.9s linear infinite;
}

.event-location-picker__suggestions {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 700;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.event-location-picker__suggestion {
  width: 100%;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: inherit;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 3px;
  transition: background 140ms ease, transform 140ms ease;
}

.event-location-picker__suggestion strong {
  font-size: 13px;
  font-weight: 800;
  color: var(--color-text-always-dark, #111827);
}

.event-location-picker__suggestion span,
.event-location-picker__suggestions-empty {
  font-size: 12px;
  line-height: 1.45;
  color: var(--color-text-secondary, #6b7280);
}

.event-location-picker__suggestion:hover,
.event-location-picker__suggestion--active {
  background: color-mix(in srgb, var(--color-primary, #3b82f6) 8%, white);
  transform: translateY(-1px);
}

.event-location-picker__suggestions-empty {
  margin: 0;
  padding: 10px 12px;
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
