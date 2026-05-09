import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock('@capacitor/core', () => ({
  Capacitor: { isNativePlatform: () => false },
}))

vi.mock('@/services/devicePermissions.js', () => ({
  isNativeApp: vi.fn(() => false),
  requestCameraPermission: vi.fn(),
  requestLocationPermission: vi.fn(),
}))

import {
  isNativeApp,
  requestCameraPermission,
  requestLocationPermission,
} from '@/services/devicePermissions.js'

import { useAttendancePermissions } from '@/composables/useAttendancePermissions.js'
import AttendancePermissionGate from '@/components/attendance/AttendancePermissionGate.vue'

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockPermissionsApi(cameraState, locationState) {
  const query = vi.fn(({ name }) => {
    if (name === 'camera') return Promise.resolve({ state: cameraState })
    if (name === 'geolocation') return Promise.resolve({ state: locationState })
    return Promise.resolve({ state: 'prompt' })
  })
  Object.defineProperty(navigator, 'permissions', {
    value: { query },
    configurable: true,
    writable: true,
  })
}

function setSecureContext(secure) {
  vi.stubGlobal('isSecureContext', secure)
}

// ── Composable tests ──────────────────────────────────────────────────────────

describe('useAttendancePermissions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    isNativeApp.mockReturnValue(false)
    vi.stubGlobal('isSecureContext', true)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('starts in checking_permissions state', () => {
    const { permissionState } = useAttendancePermissions()
    expect(permissionState.value).toBe('checking_permissions')
  })

  it('transitions to permissions_granted when both are already granted', async () => {
    mockPermissionsApi('granted', 'granted')
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('permissions_granted')
  })

  it('transitions to permissions_not_requested when both are prompt', async () => {
    mockPermissionsApi('prompt', 'prompt')
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('permissions_not_requested')
  })

  it('transitions to camera_denied when only camera is denied', async () => {
    mockPermissionsApi('denied', 'granted')
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('camera_denied')
  })

  it('transitions to location_denied when only location is denied', async () => {
    mockPermissionsApi('granted', 'denied')
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('location_denied')
  })

  it('transitions to both_denied when both are denied', async () => {
    mockPermissionsApi('denied', 'denied')
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('both_denied')
  })

  it('sets insecure_context when not on HTTPS or localhost', async () => {
    vi.stubGlobal('isSecureContext', false)
    const { permissionState, checkExistingPermissions } = useAttendancePermissions()
    await checkExistingPermissions()
    expect(permissionState.value).toBe('insecure_context')
  })

  it('grants after requestPermissions when both succeed', async () => {
    mockPermissionsApi('prompt', 'prompt')
    requestCameraPermission.mockResolvedValue({ granted: true, denied: false, message: '' })
    requestLocationPermission.mockResolvedValue({ granted: true, denied: false, message: '' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('permissions_granted')
  })

  it('sets camera_denied when camera is denied on request', async () => {
    requestCameraPermission.mockResolvedValue({ granted: false, denied: true, message: 'Camera denied.' })
    requestLocationPermission.mockResolvedValue({ granted: true, denied: false, message: '' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('camera_denied')
  })

  it('sets location_denied when location is denied on request', async () => {
    requestCameraPermission.mockResolvedValue({ granted: true, denied: false, message: '' })
    requestLocationPermission.mockResolvedValue({ granted: false, denied: true, message: 'Location denied.' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('location_denied')
  })

  it('sets both_denied when both are denied on request', async () => {
    requestCameraPermission.mockResolvedValue({ granted: false, denied: true, message: 'Camera denied.' })
    requestLocationPermission.mockResolvedValue({ granted: false, denied: true, message: 'Location denied.' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('both_denied')
  })

  it('sets permission_prompt_blocked when browser silently blocks', async () => {
    requestCameraPermission.mockResolvedValue({ granted: false, denied: false, message: '' })
    requestLocationPermission.mockResolvedValue({ granted: false, denied: false, message: '' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('permission_prompt_blocked')
  })

  it('sets permission_error on unexpected throw', async () => {
    requestCameraPermission.mockRejectedValue(new Error('Unexpected'))
    requestLocationPermission.mockResolvedValue({ granted: true, denied: false, message: '' })

    const { permissionState, requestPermissions } = useAttendancePermissions()
    await requestPermissions()
    expect(permissionState.value).toBe('permission_error')
  })

  it('retryPermissions resolves to granted when permissions become granted', async () => {
    mockPermissionsApi('granted', 'granted')
    const { permissionState, retryPermissions } = useAttendancePermissions()
    await retryPermissions()
    expect(permissionState.value).toBe('permissions_granted')
  })

  it('retryPermissions sets permission_prompt_blocked when still denied', async () => {
    mockPermissionsApi('denied', 'denied')
    const { permissionState, retryPermissions } = useAttendancePermissions()
    await retryPermissions()
    expect(permissionState.value).toBe('permission_prompt_blocked')
  })
})

// ── Component tests ───────────────────────────────────────────────────────────

describe('AttendancePermissionGate', () => {
  it('renders the enable button in permissions_not_requested state', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'permissions_not_requested', errorMessage: '', isRequesting: false },
    })
    expect(wrapper.text()).toContain('Enable Camera and Location')
  })

  it('emits request when enable button is clicked', async () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'permissions_not_requested', errorMessage: '', isRequesting: false },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('request')).toBeTruthy()
  })

  it('shows retry button and denied message in both_denied state', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: {
        permissionState: 'both_denied',
        errorMessage: 'Permission denied. Camera and location access are required.',
        isRequesting: false,
      },
    })
    expect(wrapper.text()).toContain('Permission denied')
    expect(wrapper.text()).toContain('Try Again')
  })

  it('emits retry when Try Again is clicked', async () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'both_denied', errorMessage: 'Denied.', isRequesting: false },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('retry')).toBeTruthy()
  })

  it('shows retry button in camera_denied state', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'camera_denied', errorMessage: 'Camera denied.', isRequesting: false },
    })
    expect(wrapper.text()).toContain('Try Again')
  })

  it('shows retry button in location_denied state', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'location_denied', errorMessage: 'Location denied.', isRequesting: false },
    })
    expect(wrapper.text()).toContain('Try Again')
  })

  it('shows insecure context message', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: {
        permissionState: 'insecure_context',
        errorMessage: 'Camera and location permissions require HTTPS or localhost.',
        isRequesting: false,
      },
    })
    expect(wrapper.text()).toContain('HTTPS')
  })

  it('shows browser instructions in permission_prompt_blocked state', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: {
        permissionState: 'permission_prompt_blocked',
        errorMessage: 'Blocked.',
        isRequesting: false,
      },
    })
    expect(wrapper.text()).toContain('lock icon')
  })

  it('cannot be dismissed by clicking outside — no backdrop click handler', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'permissions_not_requested', errorMessage: '', isRequesting: false },
    })
    // The root element has no @click.self dismiss handler
    const root = wrapper.find('.perm-gate')
    expect(root.attributes('onclick')).toBeUndefined()
  })

  it('prevents ESC key from closing the gate', async () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'permissions_not_requested', errorMessage: '', isRequesting: false },
    })
    await wrapper.find('.perm-gate').trigger('keydown.esc')
    // No close event emitted
    expect(wrapper.emitted('close')).toBeFalsy()
  })

  it('disables button while isRequesting is true', () => {
    const wrapper = mount(AttendancePermissionGate, {
      props: { permissionState: 'permissions_not_requested', errorMessage: '', isRequesting: true },
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })
})
