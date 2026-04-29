const DEFAULT_REVERSE_GEOCODE_URL = 'https://nominatim.openstreetmap.org/reverse'
const DEFAULT_LANGUAGE = 'en-PH,en'
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
