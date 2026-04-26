import { Capacitor } from '@capacitor/core'

const isNative = Capacitor.isNativePlatform()
const ATTENDANCE_CHANNEL_ID = 'attendance-updates'
const EVENT_CHANNEL_ID = 'event-updates'
const DEDUPE_WINDOW_MS = 15_000
const CHANNELS = {
  [ATTENDANCE_CHANNEL_ID]: {
    id: ATTENDANCE_CHANNEL_ID,
    name: 'Attendance Updates',
    description: 'Attendance confirmations from Aura.',
    lightColor: '#0A84FF',
  },
  [EVENT_CHANNEL_ID]: {
    id: EVENT_CHANNEL_ID,
    name: 'Event Updates',
    description: 'New and ongoing event alerts from Aura.',
    lightColor: '#76FF03',
  },
}

let LocalNotificationsPlugin = null
const notificationChannelsReady = new Set()
let nextNotificationId = Math.floor(Date.now() % 2_000_000_000)

const deliveredNotificationKeys = new Map()

function wrapPlugin(plugin, methodNames = []) {
  if (!plugin) return null

  return methodNames.reduce((wrapped, methodName) => {
    if (typeof plugin?.[methodName] !== 'function') return wrapped

    wrapped[methodName] = (...args) => plugin[methodName](...args)
    return wrapped
  }, {})
}

function normalizeAction(action) {
  return String(action || '').trim().toLowerCase().replace(/[\s-]+/g, '_')
}

function isCheckInAction(action) {
  return ['sign_in', 'time_in'].includes(normalizeAction(action))
}

function isCheckOutAction(action) {
  return ['sign_out', 'time_out', 'timeout'].includes(normalizeAction(action))
}

function normalizeText(value, fallback) {
  const normalized = String(value || '').trim()
  return normalized || fallback
}

function getNextNotificationId() {
  nextNotificationId += 1

  if (nextNotificationId >= 2_147_483_000) {
    nextNotificationId = 1
  }

  return nextNotificationId
}

function shouldDeliverNotification(dedupeKey = '') {
  const now = Date.now()

  for (const [key, timestamp] of deliveredNotificationKeys.entries()) {
    if ((now - timestamp) > DEDUPE_WINDOW_MS) {
      deliveredNotificationKeys.delete(key)
    }
  }

  if (!dedupeKey) return true

  const previousTimestamp = deliveredNotificationKeys.get(dedupeKey)
  if (Number.isFinite(previousTimestamp) && (now - previousTimestamp) < DEDUPE_WINDOW_MS) {
    return false
  }

  deliveredNotificationKeys.set(dedupeKey, now)
  return true
}

async function loadLocalNotifications() {
  if (LocalNotificationsPlugin) return LocalNotificationsPlugin

  try {
    const mod = await import('@capacitor/local-notifications')
    LocalNotificationsPlugin = wrapPlugin(mod.LocalNotifications, [
      'checkPermissions',
      'requestPermissions',
      'createChannel',
      'schedule',
    ])
    return LocalNotificationsPlugin
  } catch {
    return null
  }
}

async function ensureNotificationPermission(LocalNotifications) {
  try {
    const currentPermissions = await LocalNotifications.checkPermissions()
    let permissionState = currentPermissions?.display || 'prompt'

    if (permissionState === 'prompt' || permissionState === 'prompt-with-rationale') {
      const requestedPermissions = await LocalNotifications.requestPermissions()
      permissionState = requestedPermissions?.display || permissionState
    }

    return permissionState === 'granted'
  } catch {
    return false
  }
}

async function ensureNotificationChannel(LocalNotifications, channelId = ATTENDANCE_CHANNEL_ID) {
  if (notificationChannelsReady.has(channelId)) return

  try {
    const channel = CHANNELS[channelId] || CHANNELS[ATTENDANCE_CHANNEL_ID]
    await LocalNotifications.createChannel({
      ...channel,
      importance: 5,
      visibility: 1,
      vibration: true,
      lights: true,
    })
  } catch {
    // Ignore channel creation failures and continue with the default behavior.
  } finally {
    notificationChannelsReady.add(channelId)
  }
}

async function scheduleNativeNotification({
  title,
  body,
  dedupeKey = '',
  extra = null,
  channelId = ATTENDANCE_CHANNEL_ID,
}) {
  if (!isNative) return false
  if (!shouldDeliverNotification(dedupeKey)) return false

  const LocalNotifications = await loadLocalNotifications()
  if (!LocalNotifications) return false

  const hasPermission = await ensureNotificationPermission(LocalNotifications)
  if (!hasPermission) return false

  await ensureNotificationChannel(LocalNotifications, channelId)

  try {
    await LocalNotifications.schedule({
      notifications: [
        {
          id: getNextNotificationId(),
          title,
          body,
          largeBody: body,
          channelId,
          autoCancel: true,
          extra,
        },
      ],
    })

    return true
  } catch {
    return false
  }
}

export async function notifyAttendanceMarked({
  audience = 'self',
  action,
  eventName,
  studentName,
} = {}) {
  const normalizedAction = normalizeAction(action)
  const checkedIn = isCheckInAction(normalizedAction)
  const checkedOut = isCheckOutAction(normalizedAction)

  if (!checkedIn && !checkedOut) {
    return false
  }

  const safeEventName = normalizeText(eventName, 'this event')
  const safeStudentName = normalizeText(studentName, 'A student')

  if (String(audience || '').trim().toLowerCase() === 'kiosk') {
    return scheduleNativeNotification({
      title: checkedOut ? `${safeStudentName} checked out` : `${safeStudentName} checked in`,
      body: checkedOut
        ? `${safeStudentName} checked out of ${safeEventName}.`
        : `${safeStudentName} checked in to ${safeEventName}.`,
      dedupeKey: `kiosk:${safeStudentName}:${safeEventName}:${normalizedAction}`,
      extra: {
        audience: 'kiosk',
        action: normalizedAction,
        eventName: safeEventName,
        studentName: safeStudentName,
      },
    })
  }

  return scheduleNativeNotification({
    title: checkedOut ? 'Checked out' : 'Checked in',
    body: checkedOut
      ? `You checked out of ${safeEventName}.`
      : `You checked in to ${safeEventName}.`,
    dedupeKey: `self:${safeEventName}:${normalizedAction}`,
    extra: {
      audience: 'self',
      action: normalizedAction,
      eventName: safeEventName,
    },
  })
}

export async function notifyEventAvailable({
  eventId = null,
  eventName,
  status = 'ongoing',
  scheduleLabel = '',
  locationLabel = '',
  dedupeKey = '',
} = {}) {
  const normalizedStatus = String(status || '').trim().toLowerCase()
  const safeEventName = normalizeText(eventName, 'Event')
  const details = [
    normalizeText(scheduleLabel, ''),
    normalizeText(locationLabel, ''),
  ].filter(Boolean).join(' - ')

  return scheduleNativeNotification({
    title: normalizedStatus === 'new' ? 'New event posted' : 'Event is ongoing',
    body: details ? `${safeEventName} - ${details}` : safeEventName,
    dedupeKey: dedupeKey || `event:${normalizedStatus}:${eventId || safeEventName}:${details}`,
    channelId: EVENT_CHANNEL_ID,
    extra: {
      audience: 'student',
      type: 'event',
      status: normalizedStatus,
      eventId,
      eventName: safeEventName,
    },
  })
}
