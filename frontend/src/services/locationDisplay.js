const DEFAULT_REVERSE_GEOCODE_URL = 'https://nominatim.openstreetmap.org/reverse'
const DEFAULT_FORWARD_GEOCODE_URL = 'https://nominatim.openstreetmap.org/search'
const DEFAULT_LANGUAGE = 'en-PH,en'
const DEFAULT_LOCATION_SEARCH_COUNTRY_CODE = 'ph'
const locationLabelCache = new Map()

function toFiniteNumber(value) {
  const normalized = Number(value)
  return Number.isFinite(normalized) ? normalized : null
}

function toCacheKey(latitude, longitude) {
  return `${latitude.toFixed(3)}:${longitude.toFixed(3)}`
}

function pickFirstValue(values = []) {
  return values
    .map((value) => String(value || '').trim())
    .find(Boolean) || ''
}

function buildReadableAddressLabel(payload = null) {
  if (!payload || typeof payload !== 'object') return ''

  const address = payload.address && typeof payload.address === 'object'
    ? payload.address
    : {}

  const locality = pickFirstValue([
    address.city,
    address.town,
    address.municipality,
    address.village,
    address.suburb,
    address.county,
  ])
  const region = pickFirstValue([
    address.state,
    address.province,
    address.region,
  ])
  const country = pickFirstValue([address.country])

  const compactLabel = [locality, region || country]
    .filter(Boolean)
    .filter((part, index, parts) => parts.indexOf(part) === index)
    .join(', ')

  if (compactLabel) return compactLabel

  return String(payload.display_name || '')
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(', ')
}

function buildSearchBiasViewbox({ latitude, longitude, radiusMeters = null } = {}) {
  const normalizedLatitude = toFiniteNumber(latitude)
  const normalizedLongitude = toFiniteNumber(longitude)

  if (normalizedLatitude == null || normalizedLongitude == null) {
    return ''
  }

  const normalizedRadiusMeters = toFiniteNumber(radiusMeters)
  const latitudeOffset = normalizedRadiusMeters != null && normalizedRadiusMeters > 0
    ? Math.max(0.018, normalizedRadiusMeters / 111320)
    : 0.28
  const longitudeScale = Math.max(Math.cos((normalizedLatitude * Math.PI) / 180), 0.2)
  const longitudeOffset = normalizedRadiusMeters != null && normalizedRadiusMeters > 0
    ? Math.max(0.02, normalizedRadiusMeters / (111320 * longitudeScale))
    : 0.32

  const west = Math.max(-180, normalizedLongitude - longitudeOffset)
  const north = Math.min(90, normalizedLatitude + latitudeOffset)
  const east = Math.min(180, normalizedLongitude + longitudeOffset)
  const south = Math.max(-90, normalizedLatitude - latitudeOffset)
  return [west, north, east, south].join(',')
}

function buildSuggestionLabel(entry = null) {
  const payload = entry && typeof entry === 'object' ? entry : {}
  const address = payload.address && typeof payload.address === 'object'
    ? payload.address
    : {}

  const primary = pickFirstValue([
    address.amenity,
    address.building,
    address.attraction,
    address.tourism,
    address.shop,
    address.leisure,
    address.road,
    address.pedestrian,
    address.neighbourhood,
    address.suburb,
    address.village,
    address.hamlet,
    address.quarter,
    address.residential,
    address.city_district,
    address.state_district,
    payload.name,
  ])

  const fallback = buildReadableAddressLabel(payload)
  return primary || fallback || String(payload.display_name || '').trim()
}

function buildSuggestionSecondaryLabel(entry = null) {
  const payload = entry && typeof entry === 'object' ? entry : {}
  const address = payload.address && typeof payload.address === 'object'
    ? payload.address
    : {}

  const locality = pickFirstValue([
    address.neighbourhood,
    address.suburb,
    address.quarter,
    address.hamlet,
    address.village,
    address.city_district,
    address.town,
    address.city,
    address.municipality,
  ])
  const region = pickFirstValue([
    address.state,
    address.province,
    address.region,
  ])
  const country = pickFirstValue([address.country])

  const line = [locality, region || country]
    .filter(Boolean)
    .filter((part, index, parts) => parts.indexOf(part) === index)
    .join(', ')

  if (line) return line

  const parts = String(payload.display_name || '')
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)

  return parts.slice(1, 4).join(', ')
}

export function formatCoordinateLocationLabel({ latitude, longitude }) {
  const normalizedLatitude = toFiniteNumber(latitude)
  const normalizedLongitude = toFiniteNumber(longitude)

  if (normalizedLatitude == null || normalizedLongitude == null) {
    return 'Current location unavailable'
  }

  return `${normalizedLatitude.toFixed(4)}, ${normalizedLongitude.toFixed(4)}`
}

export async function resolveLocationLabel({
  latitude,
  longitude,
  preferredLabel = '',
  signal,
} = {}) {
  const normalizedLatitude = toFiniteNumber(latitude)
  const normalizedLongitude = toFiniteNumber(longitude)
  const preferred = String(preferredLabel || '').trim()

  if (preferred) return preferred
  if (normalizedLatitude == null || normalizedLongitude == null) return ''

  const cacheKey = toCacheKey(normalizedLatitude, normalizedLongitude)
  if (locationLabelCache.has(cacheKey)) {
    return locationLabelCache.get(cacheKey)
  }

  const endpoint = String(
    import.meta.env.VITE_REVERSE_GEOCODE_URL || DEFAULT_REVERSE_GEOCODE_URL
  ).trim()

  if (!endpoint) {
    return formatCoordinateLocationLabel({
      latitude: normalizedLatitude,
      longitude: normalizedLongitude,
    })
  }

  const language = String(
    import.meta.env.VITE_REVERSE_GEOCODE_LANGUAGE || DEFAULT_LANGUAGE
  ).trim()

  const url = new URL(endpoint)
  if (!url.searchParams.has('format')) url.searchParams.set('format', 'jsonv2')
  if (!url.searchParams.has('lat')) url.searchParams.set('lat', String(normalizedLatitude))
  if (!url.searchParams.has('lon')) url.searchParams.set('lon', String(normalizedLongitude))

  const response = await fetch(url.toString(), {
    method: 'GET',
    signal,
    headers: {
      Accept: 'application/json',
      'Accept-Language': language,
    },
  })

  if (!response.ok) {
    throw new Error('Unable to resolve the current location label.')
  }

  const payload = await response.json()
  const label = buildReadableAddressLabel(payload)
    || formatCoordinateLocationLabel({
      latitude: normalizedLatitude,
      longitude: normalizedLongitude,
    })

  locationLabelCache.set(cacheKey, label)
  return label
}

export async function searchLocationSuggestions({
  query = '',
  near = null,
  signal,
  limit = 6,
  radiusMeters = null,
} = {}) {
  const normalizedQuery = String(query || '').trim()
  if (!normalizedQuery) return []

  const endpoint = String(
    import.meta.env.VITE_FORWARD_GEOCODE_URL || DEFAULT_FORWARD_GEOCODE_URL
  ).trim()

  if (!endpoint) return []

  const language = String(
    import.meta.env.VITE_REVERSE_GEOCODE_LANGUAGE || DEFAULT_LANGUAGE
  ).trim()
  const preferredCountryCode = String(
    import.meta.env.VITE_LOCATION_SEARCH_COUNTRY_CODE || DEFAULT_LOCATION_SEARCH_COUNTRY_CODE
  ).trim().toLowerCase()
  const normalizedRadiusMeters = toFiniteNumber(radiusMeters)
  const nearCoordinates = {
    latitude: toFiniteNumber(near?.latitude),
    longitude: toFiniteNumber(near?.longitude),
  }

  const url = new URL(endpoint)
  if (!url.searchParams.has('format')) url.searchParams.set('format', 'jsonv2')
  if (!url.searchParams.has('q')) url.searchParams.set('q', normalizedQuery)
  if (!url.searchParams.has('addressdetails')) url.searchParams.set('addressdetails', '1')
  if (!url.searchParams.has('namedetails')) url.searchParams.set('namedetails', '1')
  if (!url.searchParams.has('extratags')) url.searchParams.set('extratags', '1')
  if (!url.searchParams.has('limit')) url.searchParams.set('limit', String(Math.max(1, Math.min(8, Number(limit) || 6))))
  if (!url.searchParams.has('dedupe')) url.searchParams.set('dedupe', '1')
  if (preferredCountryCode && !url.searchParams.has('countrycodes')) {
    url.searchParams.set('countrycodes', preferredCountryCode)
  }

  const viewbox = buildSearchBiasViewbox({
    ...nearCoordinates,
    radiusMeters: normalizedRadiusMeters,
  })
  if (viewbox && !url.searchParams.has('viewbox')) {
    url.searchParams.set('viewbox', viewbox)
  }
  if (viewbox && !url.searchParams.has('bounded')) {
    url.searchParams.set('bounded', '1')
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    signal,
    headers: {
      Accept: 'application/json',
      'Accept-Language': language,
    },
  })

  if (!response.ok) {
    throw new Error('Unable to search nearby locations.')
  }

  const payload = await response.json()
  if (!Array.isArray(payload)) return []

  const suggestions = payload
    .map((entry, index) => {
      const latitude = toFiniteNumber(entry?.lat)
      const longitude = toFiniteNumber(entry?.lon)
      if (latitude == null || longitude == null) return null

      const label = buildSuggestionLabel(entry)
      if (!label) return null

      return {
        id: String(entry?.place_id || `${latitude}:${longitude}:${index}`),
        label,
        secondaryLabel: buildSuggestionSecondaryLabel(entry),
        latitude,
        longitude,
        displayName: String(entry?.display_name || '').trim(),
        distanceMeters: measureDistanceMeters(nearCoordinates, { latitude, longitude }),
      }
    })
    .filter(Boolean)

  if (nearCoordinates.latitude == null || nearCoordinates.longitude == null) {
    return suggestions
  }

  const searchRadius = normalizedRadiusMeters != null && normalizedRadiusMeters > 0
    ? normalizedRadiusMeters
    : null
  const filteredSuggestions = searchRadius == null
    ? suggestions
    : suggestions.filter((entry) => (
      entry.distanceMeters == null || entry.distanceMeters <= searchRadius * 1.5
    ))

  return filteredSuggestions.sort((left, right) => {
    const leftDistance = toFiniteNumber(left?.distanceMeters)
    const rightDistance = toFiniteNumber(right?.distanceMeters)

    if (leftDistance == null && rightDistance == null) {
      return String(left?.label || '').localeCompare(String(right?.label || ''))
    }
    if (leftDistance == null) return 1
    if (rightDistance == null) return -1
    if (leftDistance !== rightDistance) return leftDistance - rightDistance
    return String(left?.label || '').localeCompare(String(right?.label || ''))
  })
}

export function measureDistanceMeters(origin = null, destination = null) {
  const originLatitude = toFiniteNumber(origin?.latitude)
  const originLongitude = toFiniteNumber(origin?.longitude)
  const destinationLatitude = toFiniteNumber(destination?.latitude)
  const destinationLongitude = toFiniteNumber(destination?.longitude)

  if (
    originLatitude == null
    || originLongitude == null
    || destinationLatitude == null
    || destinationLongitude == null
  ) {
    return null
  }

  const earthRadiusM = 6371000
  const latitudeDelta = ((destinationLatitude - originLatitude) * Math.PI) / 180
  const longitudeDelta = ((destinationLongitude - originLongitude) * Math.PI) / 180
  const startLatitude = (originLatitude * Math.PI) / 180
  const endLatitude = (destinationLatitude * Math.PI) / 180
  const a =
    (Math.sin(latitudeDelta / 2) ** 2)
    + (Math.cos(startLatitude) * Math.cos(endLatitude) * (Math.sin(longitudeDelta / 2) ** 2))

  return 2 * earthRadiusM * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function formatVenueDistance(distanceMeters) {
  const normalizedDistance = toFiniteNumber(distanceMeters)
  if (normalizedDistance == null || normalizedDistance < 0) return ''

  if (normalizedDistance >= 1000) {
    const kilometers = normalizedDistance / 1000
    const rounded = kilometers >= 10 ? Math.round(kilometers) : Math.round(kilometers * 10) / 10
    return `${rounded} km to venue`
  }

  return `${Math.round(normalizedDistance)} m to venue`
}
