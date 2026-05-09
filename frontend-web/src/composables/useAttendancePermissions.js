import { ref, readonly } from 'vue'
import { requestCameraPermission, requestLocationPermission, isNativeApp } from '@/services/devicePermissions.js'

/**
 * Permission gate states:
 *   checking_permissions       — initial async check in progress
 *   permissions_not_requested  — not yet asked (first visit)
 *   permissions_granted        — both camera + location granted
 *   camera_denied              — only camera denied
 *   location_denied            — only location denied
 *   both_denied                — both denied
 *   permission_prompt_blocked  — browser blocked repeated prompts
 *   permission_error           — unexpected error during request
 *   insecure_context           — not HTTPS / not localhost
 */

function isSecureContext() {
  if (typeof window === 'undefined') return true
  // Explicitly false means the browser has determined it's not secure
  if (window.isSecureContext === false) return false
  if (window.isSecureContext === true) return true
  // Fallback for browsers that don't expose isSecureContext
  const hostname = String(window.location?.hostname || '').toLowerCase().trim()
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]'
}

async function queryCameraPermissionState() {
  if (typeof navigator === 'undefined') return null
  if (typeof navigator.permissions?.query !== 'function') return null
  try {
    const status = await navigator.permissions.query({ name: 'camera' })
    return status?.state ?? null
  } catch {
    return null
  }
}

async function queryLocationPermissionState() {
  if (typeof navigator === 'undefined') return null
  if (typeof navigator.permissions?.query !== 'function') return null
  try {
    const status = await navigator.permissions.query({ name: 'geolocation' })
    return status?.state ?? null
  } catch {
    return null
  }
}

export function useAttendancePermissions({ cameraOnly = false } = {}) {
  const permissionState = ref('checking_permissions')
  const errorMessage = ref('')
  const isRequesting = ref(false)

  const insecureMessage = cameraOnly
    ? 'Camera permission requires HTTPS or localhost. Please open the app using a secure connection.'
    : 'Camera and location permissions require HTTPS or localhost. Please open the app using a secure connection.'

  function resolveState(cameraGranted, locationGranted, cameraBlocked, locationBlocked) {
    if (cameraOnly) {
      if (cameraGranted) return 'permissions_granted'
      if (cameraBlocked) return 'permission_prompt_blocked'
      return 'camera_denied'
    }
    if (cameraGranted && locationGranted) return 'permissions_granted'
    if (cameraBlocked || locationBlocked) return 'permission_prompt_blocked'
    if (!cameraGranted && !locationGranted) return 'both_denied'
    if (!cameraGranted) return 'camera_denied'
    return 'location_denied'
  }

  async function checkExistingPermissions() {
    if (!isSecureContext()) {
      permissionState.value = 'insecure_context'
      errorMessage.value = insecureMessage
      return
    }

    permissionState.value = 'checking_permissions'

    if (isNativeApp()) {
      permissionState.value = 'permissions_not_requested'
      return
    }

    const [cameraState, locationState] = await Promise.all([
      queryCameraPermissionState(),
      cameraOnly ? Promise.resolve('granted') : queryLocationPermissionState(),
    ])

    if (cameraState === null && (cameraOnly || locationState === null)) {
      permissionState.value = 'permissions_not_requested'
      return
    }

    const cameraGranted = cameraState === 'granted'
    const locationGranted = cameraOnly || locationState === 'granted'
    const cameraDenied = cameraState === 'denied'
    const locationDenied = !cameraOnly && locationState === 'denied'

    if (cameraGranted && locationGranted) {
      permissionState.value = 'permissions_granted'
      return
    }

    if (cameraDenied || locationDenied) {
      permissionState.value = resolveState(cameraGranted, locationGranted, false, false)
      errorMessage.value = buildDeniedMessage(cameraGranted, locationGranted)
      return
    }

    permissionState.value = 'permissions_not_requested'
  }

  async function requestPermissions() {
    if (!isSecureContext()) {
      permissionState.value = 'insecure_context'
      errorMessage.value = insecureMessage
      return
    }

    isRequesting.value = true
    permissionState.value = 'checking_permissions'
    errorMessage.value = ''

    try {
      const [camera, location] = await Promise.all([
        requestCameraPermission(),
        cameraOnly ? Promise.resolve({ granted: true, denied: false, message: '' }) : requestLocationPermission(),
      ])

      const cameraGranted = camera.granted
      const locationGranted = cameraOnly || location.granted

      if (cameraGranted && locationGranted) {
        permissionState.value = 'permissions_granted'
        return
      }

      const cameraBlocked = !cameraGranted && !camera.denied
      const locationBlocked = !cameraOnly && !locationGranted && !location.denied

      const nextState = resolveState(cameraGranted, locationGranted, cameraBlocked, locationBlocked)
      permissionState.value = nextState

      if (nextState === 'permission_prompt_blocked') {
        errorMessage.value = cameraOnly
          ? 'The permission prompt was blocked. Click the lock icon beside the website URL, allow Camera, then refresh the page.'
          : 'The permission prompt was blocked. Click the lock icon beside the website URL, allow Camera and Location, then refresh the page.'
        return
      }

      errorMessage.value = buildDeniedMessage(cameraGranted, locationGranted)
    } catch (err) {
      permissionState.value = 'permission_error'
      errorMessage.value = err?.message || 'An unexpected error occurred while requesting permissions.'
    } finally {
      isRequesting.value = false
    }
  }

  async function retryPermissions() {
    const [cameraState, locationState] = await Promise.all([
      queryCameraPermissionState(),
      cameraOnly ? Promise.resolve('granted') : queryLocationPermissionState(),
    ])

    const cameraGranted = cameraState === 'granted'
    const locationGranted = cameraOnly || locationState === 'granted'

    if (cameraGranted && locationGranted) {
      permissionState.value = 'permissions_granted'
      errorMessage.value = ''
      return
    }

    const cameraDenied = cameraState === 'denied'
    const locationDenied = !cameraOnly && locationState === 'denied'

    if (cameraDenied || locationDenied) {
      permissionState.value = 'permission_prompt_blocked'
      errorMessage.value = cameraOnly
        ? 'Camera access was denied. Please enable it in your browser settings, then try again. If the popup does not appear, click the lock icon beside the URL, allow Camera, then refresh the page.'
        : 'Permission denied. Camera and location access are required. Please enable them in your browser settings, then try again. If the permission popup does not appear, click the lock icon beside the website URL, allow Camera and Location, then refresh the page.'
      return
    }

    await requestPermissions()
  }

  function buildDeniedMessage(cameraGranted, locationGranted) {
    if (!cameraGranted && !locationGranted) {
      return cameraOnly
        ? 'Camera access was denied. Please enable camera access in your browser settings, then try again.'
        : 'Permission denied. Camera and location access are required. Please enable them in your browser settings, then try again.'
    }
    if (!cameraGranted) {
      return 'Camera access was denied. Please enable camera access in your browser settings, then try again.'
    }
    return 'Location access was denied. Please enable location access in your browser settings, then try again.'
  }

  return {
    permissionState: readonly(permissionState),
    errorMessage: readonly(errorMessage),
    isRequesting: readonly(isRequesting),
    checkExistingPermissions,
    requestPermissions,
    retryPermissions,
  }
}
