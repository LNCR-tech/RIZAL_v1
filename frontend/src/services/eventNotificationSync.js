import { watch } from 'vue'
import { Capacitor } from '@capacitor/core'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import {
  normalizeEventStatus,
  parseEventDateTime,
  resolveEventWindowStage,
} from '@/services/attendanceFlow.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'
import { notifyEventAvailable } from '@/services/localNotifications.js'

const STORAGE_KEY = 'aura_native_event_notifications_v1'
const DEFAULT_POLL_INTERVAL_MS = 60_000
const MIN_POLL_INTERVAL_MS = 30_000
const NOTIFICATION_COOLDOWN_MS = 12 * 60 * 60 * 1000
const STATE_RETENTION_MS = 14 * 24 * 60 * 60 * 1000
const MAX_SEEN_EVENTS = 400
const MAX_NOTIFIED_EVENTS = 600
const ONGOING_WINDOW_STAGES = new Set([
  'early_check_in',
  'late_check_in',
  'absent_check_in',
  'sign_out_pending',
  'sign_out_open',
])

const eventDateFormatter = new Intl.DateTimeFormat('en-PH', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

const eventTimeFormatter = new Intl.DateTimeFormat('en-PH', {
  hour: 'numeric',
  minute: '2-digit',
})

let started = false
let stopSessionWatch = null
let pollIntervalId = null
let appStateListenerHandle = null
let processingPromise = null

function isNativePlatform() {
  try {
    return Capacitor.isNativePlatform()
  } catch {
    return false
  }
}

function resolvePollIntervalMs() {
  const configured = Number(import.meta.env.VITE_NATIVE_EVENT_NOTIFICATION_POLL_MS)
  return Number.isFinite(configured) && configured > 0
    ? Math.max(MIN_POLL_INTERVAL_MS, configured)
    : DEFAULT_POLL_INTERVAL_MS
}

function getStorage() {
  if (typeof window === 'undefined') return null
  return window.localStorage || null
}

function readNotificationState() {
  const storage = getStorage()
  if (!storage) return {}

  try {
    const raw = storage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    storage.removeItem(STORAGE_KEY)
    return {}
  }
}

function writeNotificationState(state) {
  const storage = getStorage()
  if (!storage) return

  try {
    storage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Ignore storage quota/private-mode failures. Notifications can still run in-memory.
  }
}

function normalizeBucket(bucket = null) {
  return {
    seen: bucket?.seen && typeof bucket.seen === 'object' ? bucket.seen : {},
    notified: bucket?.notified && typeof bucket.notified === 'object' ? bucket.notified : {},
  }
}

function pruneTimestampMap(map = {}, maxItems = 300, now = Date.now()) {
  return Object.entries(map)
    .filter(([, timestamp]) => {
      const normalizedTimestamp = Number(timestamp)
      return Number.isFinite(normalizedTimestamp) && (now - normalizedTimestamp) <= STATE_RETENTION_MS
    })
    .sort((left, right) => Number(right[1]) - Number(left[1]))
    .slice(0, maxItems)
    .reduce((acc, [key, timestamp]) => {
      acc[key] = timestamp
      return acc
    }, {})
}

function pruneSeenMap(map = {}, maxItems = 300) {
  return Object.entries(map)
    .slice(-maxItems)
    .reduce((acc, [key, signature]) => {
      acc[key] = signature
      return acc
    }, {})
}

function resolveUserKey(user = null, authToken = '') {
  const storedMeta = getStoredAuthMeta()
  const userId = Number(user?.id ?? storedMeta?.userId)
  if (Number.isFinite(userId)) return `user:${userId}`

  const email = String(user?.email || storedMeta?.email || '').trim().toLowerCase()
  if (email) return `email:${email}`

  const tokenSuffix = String(authToken || '').trim().slice(-24)
  return tokenSuffix ? `token:${tokenSuffix}` : 'anonymous'
}

function parseValidEventDate(value) {
  const parsed = parseEventDateTime(value)
  return Number.isFinite(parsed.getTime()) ? parsed : null
}

function toDateKey(date) {
  if (!date) return ''

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function isSameDay(left, right) {
  return Boolean(left && right && toDateKey(left) === toDateKey(right))
}

function formatEventSchedule(event = null) {
  const start = parseValidEventDate(event?.start_datetime)
  if (!start) return ''

  const end = parseValidEventDate(event?.end_datetime)
  const dateLabel = eventDateFormatter.format(start)
  const startLabel = eventTimeFormatter.format(start)

  if (!end) return `${dateLabel}, ${startLabel}`

  const endLabel = isSameDay(start, end)
    ? eventTimeFormatter.format(end)
    : `${eventDateFormatter.format(end)}, ${eventTimeFormatter.format(end)}`

  return `${dateLabel}, ${startLabel} - ${endLabel}`
}

function getEventKey(event = null) {
  const rawId = String(event?.id ?? '').trim()
  if (rawId && rawId !== '0') return `id:${rawId}`

  const fallbackKey = [
    event?.name,
    event?.start_datetime,
    event?.end_datetime,
    event?.location,
  ].map((value) => String(value || '').trim()).filter(Boolean).join('|')

  return fallbackKey ? `event:${fallbackKey}` : ''
}

function getNotificationEventId(event = null) {
  const numericId = Number(event?.id)
  return Number.isFinite(numericId) && numericId > 0
    ? numericId
    : String(event?.id || '').trim() || null
}

function buildEventSignature(event = null) {
  return [
    event?.id,
    event?.name,
    event?.status,
    event?.start_datetime,
    event?.end_datetime,
    event?.location,
    event?.scope_label,
    event?.updated_at,
    event?.created_at,
  ].map((value) => String(value || '').trim()).join('|')
}

function isEventOngoing(event = null) {
  const status = normalizeEventStatus(event?.status)
  if (status === 'ongoing') return true
  if (status === 'completed' || status === 'cancelled') return false

  const stage = resolveEventWindowStage(event, null, new Date())
  return ONGOING_WINDOW_STAGES.has(stage)
}

function isEventOpenForNewNotification(event = null) {
  const status = normalizeEventStatus(event?.status)
  if (status === 'completed' || status === 'cancelled') return false

  const end = parseValidEventDate(event?.end_datetime)
  return !end || end.getTime() >= Date.now()
}

function shouldNotify(bucket, key, now = Date.now()) {
  const previousTimestamp = Number(bucket.notified[key])
  return !Number.isFinite(previousTimestamp) || (now - previousTimestamp) > NOTIFICATION_COOLDOWN_MS
}

function markNotificationAttempt(bucket, key, now = Date.now()) {
  bucket.notified[key] = now
}

function buildNotificationPayload(event, status, dedupeKey) {
  return {
    eventId: getNotificationEventId(event),
    eventName: event?.name,
    status,
    scheduleLabel: formatEventSchedule(event),
    locationLabel: event?.location,
    dedupeKey,
  }
}

async function processNativeEventNotifications(session, reason = 'session') {
  if (!isNativePlatform()) return

  if (processingPromise) {
    return processingPromise
  }

  processingPromise = (async () => {
    const authToken = String(session.token.value || '').trim()
    const currentEvents = Array.isArray(session.events.value) ? session.events.value : []

    if (!authToken || !currentEvents.length) return

    const now = Date.now()
    const userKey = resolveUserKey(session.currentUser.value, authToken)
    const state = readNotificationState()
    const bucket = normalizeBucket(state[userKey])
    const hadSeenEvents = Object.keys(bucket.seen).length > 0
    const notificationPayloads = []

    currentEvents.forEach((event) => {
      const eventKey = getEventKey(event)
      if (!eventKey) return

      const signature = buildEventSignature(event)
      const wasSeen = Object.prototype.hasOwnProperty.call(bucket.seen, eventKey)

      if (hadSeenEvents && !wasSeen && isEventOpenForNewNotification(event)) {
        const notificationKey = `new:${eventKey}:${signature}`
        if (shouldNotify(bucket, notificationKey, now)) {
          markNotificationAttempt(bucket, notificationKey, now)
          notificationPayloads.push(buildNotificationPayload(event, 'new', `${userKey}:${notificationKey}`))
        }
      }

      if (isEventOngoing(event)) {
        const startKey = toDateKey(parseValidEventDate(event?.start_datetime)) || 'ongoing'
        const notificationKey = `ongoing:${eventKey}:${startKey}`
        if (shouldNotify(bucket, notificationKey, now)) {
          markNotificationAttempt(bucket, notificationKey, now)
          notificationPayloads.push(buildNotificationPayload(event, 'ongoing', `${userKey}:${notificationKey}`))
        }
      }

      bucket.seen[eventKey] = signature || String(now)
    })

    state[userKey] = {
      seen: pruneSeenMap(bucket.seen, MAX_SEEN_EVENTS),
      notified: pruneTimestampMap(bucket.notified, MAX_NOTIFIED_EVENTS, now),
      lastReason: reason,
      updatedAt: now,
    }
    writeNotificationState(state)

    await Promise.allSettled(
      notificationPayloads.map((payload) => notifyEventAvailable(payload))
    )
  })().finally(() => {
    processingPromise = null
  })

  return processingPromise
}

async function refreshSessionAndProcess(session, reason) {
  if (!String(session.token.value || '').trim()) return

  await session.initializeDashboardSession(true).catch(() => null)
  await processNativeEventNotifications(session, reason)
}

export function startNativeEventNotificationSync() {
  if (started || !isNativePlatform()) return
  started = true

  const session = useDashboardSession()

  stopSessionWatch = watch(
    () => [
      session.token.value,
      session.currentUser.value?.id,
      session.events.value.map((event) => buildEventSignature(event)).join('\n'),
    ],
    () => {
      void processNativeEventNotifications(session, 'session')
    },
    { immediate: true }
  )

  if (typeof window !== 'undefined') {
    window.setTimeout(() => {
      void refreshSessionAndProcess(session, 'startup')
    }, 1500)

    pollIntervalId = window.setInterval(() => {
      void refreshSessionAndProcess(session, 'poll')
    }, resolvePollIntervalMs())
  }

  import('@capacitor/app')
    .then(async ({ App }) => {
      appStateListenerHandle = await App.addListener('appStateChange', ({ isActive }) => {
        if (isActive) {
          void refreshSessionAndProcess(session, 'foreground')
        }
      })
    })
    .catch(() => null)
}

export function stopNativeEventNotificationSync() {
  stopSessionWatch?.()
  stopSessionWatch = null

  if (pollIntervalId != null && typeof window !== 'undefined') {
    window.clearInterval(pollIntervalId)
    pollIntervalId = null
  }

  appStateListenerHandle?.remove?.()
  appStateListenerHandle = null
  started = false
}
