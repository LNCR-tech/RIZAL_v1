import { computed, ref } from 'vue'
import { Bell, CalendarDays, CircleAlert, ShieldAlert } from 'lucide-vue-next'
import { getMyNotificationInbox } from '@/services/backendApi.js'

const READ_STORAGE_PREFIX = 'aura_notification_reads:'

const showNotifications = ref(false)
const notificationLogs = ref([])
const notificationsLoading = ref(false)
const notificationsError = ref('')
const notificationContext = ref({
  baseUrl: '',
  token: '',
  sessionKey: '',
})
const readNotificationIds = ref(new Set())

let inFlightPromise = null

function getReadStorageKey(sessionKey) {
  return `${READ_STORAGE_PREFIX}${sessionKey || 'anonymous'}`
}

function loadReadNotificationIds(sessionKey) {
  if (typeof window === 'undefined') return new Set()

  try {
    const rawValue = window.localStorage.getItem(getReadStorageKey(sessionKey))
    const parsed = JSON.parse(rawValue || '[]')
    if (!Array.isArray(parsed)) return new Set()

    return new Set(
      parsed
        .map((value) => Number(value))
        .filter((value) => Number.isFinite(value) && value > 0)
    )
  } catch {
    return new Set()
  }
}

function persistReadNotificationIds() {
  if (typeof window === 'undefined') return
  if (!notificationContext.value.sessionKey) return

  window.localStorage.setItem(
    getReadStorageKey(notificationContext.value.sessionKey),
    JSON.stringify([...readNotificationIds.value])
  )
}

function markNotificationsAsRead(items = []) {
  if (!items.length) return

  let changed = false
  const nextIds = new Set(readNotificationIds.value)

  for (const item of items) {
    const notificationId = Number(item?.id)
    if (!Number.isFinite(notificationId) || notificationId <= 0 || nextIds.has(notificationId)) continue
    nextIds.add(notificationId)
    changed = true
  }

  if (!changed) return

  readNotificationIds.value = nextIds
  persistReadNotificationIds()
}

function prettifyNotificationValue(value) {
  return String(value || '')
    .replace(/[_-]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function compactNotificationText(value, maxLength = 96) {
  const normalized = String(value || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return ''
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, Math.max(0, maxLength - 1)).trimEnd()}...`
}

function formatNotificationTime(isoValue) {
  const timestamp = new Date(isoValue).getTime()
  if (!Number.isFinite(timestamp)) return 'Just now'

  const diffMs = Date.now() - timestamp
  const minuteMs = 60 * 1000
  const hourMs = 60 * minuteMs
  const dayMs = 24 * hourMs

  if (diffMs < minuteMs) return 'Just now'
  if (diffMs < hourMs) return `${Math.max(1, Math.round(diffMs / minuteMs))}m ago`
  if (diffMs < dayMs) return `${Math.max(1, Math.round(diffMs / hourMs))}h ago`
  if (diffMs < dayMs * 7) return `${Math.max(1, Math.round(diffMs / dayMs))}d ago`

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(timestamp))
}

function resolveNotificationVisual(item = null) {
  const category = String(item?.category || '').trim().toLowerCase()
  const status = String(item?.status || '').trim().toLowerCase()

  if (category === 'account_security') {
    return {
      icon: ShieldAlert,
      iconBgClass: 'bg-[#FFF1F2] text-[#D92D20]',
    }
  }

  if (category === 'event_reminder') {
    return {
      icon: CalendarDays,
      iconBgClass: 'bg-[#EFF6FF] text-[#2563EB]',
    }
  }

  if (category === 'missed_events' || category === 'low_attendance' || status === 'failed') {
    return {
      icon: CircleAlert,
      iconBgClass: status === 'failed'
        ? 'bg-[#FEF2F2] text-[#DC2626]'
        : 'bg-[#FFF7ED] text-[#EA580C]',
    }
  }

  return {
    icon: Bell,
    iconBgClass: 'bg-[#F4F4F4] text-[#111]',
  }
}

function buildNotificationDescription(item = null) {
  const lines = String(item?.message || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  const preferredLine = lines.find((line) => !/^hi\b/i.test(line))
    || lines[0]
    || item?.subject
    || 'System notification'

  return compactNotificationText(preferredLine, 104)
}

function buildNotificationDetails(item = null) {
  const detailParts = [
    prettifyNotificationValue(item?.channel || 'in_app'),
    prettifyNotificationValue(item?.status || 'unknown'),
  ]

  if (item?.error_message) {
    detailParts.push(compactNotificationText(item.error_message, 70))
  }

  return detailParts.filter(Boolean).join(' • ')
}

function mapNotificationItem(item = null) {
  if (!item || typeof item !== 'object') return null

  const notificationId = Number(item.id)
  const { icon, iconBgClass } = resolveNotificationVisual(item)

  return {
    id: notificationId,
    icon,
    iconBgClass,
    title: compactNotificationText(item.subject || prettifyNotificationValue(item.category || 'notification'), 58),
    time: formatNotificationTime(item.created_at),
    description: buildNotificationDescription(item),
    details: buildNotificationDetails(item),
    unread: !readNotificationIds.value.has(notificationId),
  }
}

export async function refreshNotifications(options = {}) {
  const { force = false, limit = 50 } = options
  const { baseUrl, token } = notificationContext.value

  if (!baseUrl || !token) {
    notificationLogs.value = []
    notificationsError.value = ''
    return []
  }

  if (notificationsLoading.value && !force && inFlightPromise) {
    return inFlightPromise
  }

  notificationsLoading.value = true
  notificationsError.value = ''

  inFlightPromise = getMyNotificationInbox(baseUrl, token, { limit })
    .then((items) => {
      notificationLogs.value = Array.isArray(items) ? items : []
      if (showNotifications.value) {
        markNotificationsAsRead(notificationLogs.value)
      }
      return notificationLogs.value
    })
    .catch((error) => {
      notificationsError.value = error?.message || 'Unable to load notifications right now.'
      return notificationLogs.value
    })
    .finally(() => {
      notificationsLoading.value = false
      inFlightPromise = null
    })

  return inFlightPromise
}

export async function syncNotificationSession({ baseUrl = '', token = '', sessionKey = '' } = {}) {
  const normalizedContext = {
    baseUrl: String(baseUrl || '').trim(),
    token: String(token || '').trim(),
    sessionKey: String(sessionKey || '').trim(),
  }

  const didSessionChange = normalizedContext.sessionKey !== notificationContext.value.sessionKey
    || normalizedContext.baseUrl !== notificationContext.value.baseUrl
    || normalizedContext.token !== notificationContext.value.token

  notificationContext.value = normalizedContext

  if (!normalizedContext.baseUrl || !normalizedContext.token || !normalizedContext.sessionKey) {
    notificationLogs.value = []
    notificationsError.value = ''
    readNotificationIds.value = new Set()
    return []
  }

  if (didSessionChange) {
    readNotificationIds.value = loadReadNotificationIds(normalizedContext.sessionKey)
  }

  if (!didSessionChange && notificationLogs.value.length) {
    return notificationLogs.value
  }

  return refreshNotifications({ force: true })
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value

  if (!showNotifications.value) return

  markNotificationsAsRead(notificationLogs.value)
  void refreshNotifications({ force: true }).then((items) => {
    markNotificationsAsRead(items)
  })
}

const notifications = computed(() => (
  notificationLogs.value
    .map(mapNotificationItem)
    .filter(Boolean)
))

const unreadNotifCount = computed(() => notifications.value.filter((item) => item.unread).length)

export function useNotifications() {
  return {
    showNotifications,
    notifications,
    notificationsLoading,
    notificationsError,
    unreadNotifCount,
    refreshNotifications,
    syncNotificationSession,
    toggleNotifications,
  }
}
