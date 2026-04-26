import { computed, ref, watch } from 'vue'
import {
  Bell,
  CalendarClock,
  Megaphone,
  ShieldAlert,
  TriangleAlert,
} from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import {
  BackendApiError,
  getGovernanceAccess,
  getGovernanceAnnouncementMonitor,
  getGovernanceAnnouncements,
  getMyNotificationInbox,
} from '@/services/backendApi.js'
import { getGovernanceAccessUnits } from '@/services/governanceScope.js'
import { getStoredAuthMeta } from '@/services/localAuth.js'

const READ_STATE_STORAGE_KEY = 'aura_notification_reads_v1'
const PREVIEW_READ_BUCKET_KEY = 'preview'
const MAX_INBOX_ITEMS = 60
const MAX_ANNOUNCEMENT_ITEMS = 24

const showNotifications = ref(false)
const notificationItems = ref([])
const notificationsLoading = ref(false)
const notificationsError = ref('')
const notificationsHydrated = ref(false)
const activeSessionKey = ref('')

let refreshPromise = null
let notificationBindingsReady = false

const relativeTimeFormatter = typeof Intl !== 'undefined'
  ? new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  : null

const { apiBaseUrl, token, currentUser } = useDashboardSession()

function toTimestamp(value) {
  const timestamp = new Date(value || Date.now()).getTime()
  return Number.isFinite(timestamp) ? timestamp : Date.now()
}

function sortItems(items = []) {
  return [...items].sort((left, right) => right.timestamp - left.timestamp)
}

function truncateText(value, maxLength = 160) {
  const normalized = String(value || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return 'No details available.'
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, Math.max(0, maxLength - 1)).trimEnd()}…`
}

function formatRelativeTime(value) {
  const timestamp = toTimestamp(value)
  const diffMs = timestamp - Date.now()
  const diffMinutes = Math.round(diffMs / 60000)

  if (Math.abs(diffMinutes) < 1) return 'Now'
  if (Math.abs(diffMinutes) < 60) {
    return relativeTimeFormatter
      ? relativeTimeFormatter.format(diffMinutes, 'minute')
      : `${Math.abs(diffMinutes)}m ago`
  }

  const diffHours = Math.round(diffMinutes / 60)
  if (Math.abs(diffHours) < 24) {
    return relativeTimeFormatter
      ? relativeTimeFormatter.format(diffHours, 'hour')
      : `${Math.abs(diffHours)}h ago`
  }

  const diffDays = Math.round(diffHours / 24)
  if (Math.abs(diffDays) < 7) {
    return relativeTimeFormatter
      ? relativeTimeFormatter.format(diffDays, 'day')
      : `${Math.abs(diffDays)}d ago`
  }

  return new Intl.DateTimeFormat('en-PH', {
    month: 'short',
    day: 'numeric',
  }).format(new Date(timestamp))
}

function prettifyLabel(value, fallback = 'Notification') {
  const normalized = String(value || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  if (!normalized) return fallback

  return normalized
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function normalizeRoleKey(value) {
  const normalized = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/_/g, '-')

  if (normalized === 'campus-admin') return 'school-it'
  return normalized
}

function getCurrentRoleKeys() {
  const currentRoles = Array.isArray(currentUser.value?.roles)
    ? currentUser.value.roles
    : []
  const storedRoles = Array.isArray(getStoredAuthMeta()?.roles)
    ? getStoredAuthMeta().roles
    : []

  const roles = [
    ...currentRoles.map((entry) => entry?.role?.name || entry?.name || entry),
    ...storedRoles,
  ]

  return [...new Set(
    roles
      .map((role) => normalizeRoleKey(role))
      .filter(Boolean)
  )]
}

function hasStaffAnnouncementScope() {
  const roles = getCurrentRoleKeys()
  return roles.includes('admin') || roles.includes('school-it')
}

function buildPreviewNotifications() {
  const now = Date.now()
  return sortItems([
    {
      id: 'preview:announcement:assembly',
      timestamp: now - (18 * 60 * 1000),
      title: 'Campus assembly moved to 4:00 PM',
      bodyPreview: 'The student council published a revised call time for this afternoon’s campus assembly.',
      kindLabel: 'Announcement',
      metaLabel: 'Preview',
      icon: Megaphone,
      iconBgClass: 'bg-[#FFF1E8] text-[#C2410C]',
      isUnreadCandidate: true,
    },
    {
      id: 'preview:notification:attendance',
      timestamp: now - (54 * 60 * 1000),
      title: 'Attendance recorded',
      bodyPreview: 'Your latest event attendance was synced successfully.',
      kindLabel: 'Attendance',
      metaLabel: 'Preview',
      icon: CalendarClock,
      iconBgClass: 'bg-[#EEF2FF] text-[#3730A3]',
      isUnreadCandidate: true,
    },
    {
      id: 'preview:notification:security',
      timestamp: now - (2 * 60 * 60 * 1000),
      title: 'Security notice',
      bodyPreview: 'A sign-in was detected from a new device in Manila, Philippines.',
      kindLabel: 'Security',
      metaLabel: 'Preview',
      icon: ShieldAlert,
      iconBgClass: 'bg-[#FEF2F2] text-[#B91C1C]',
      isUnreadCandidate: true,
    },
  ]).map(finalizeNotificationItem)
}

function resolveReadBucketKey() {
  const userId = Number(currentUser.value?.id ?? getStoredAuthMeta()?.userId)
  return Number.isFinite(userId) ? `user:${userId}` : PREVIEW_READ_BUCKET_KEY
}

function readStoredReadState() {
  if (typeof window === 'undefined') return {}

  try {
    const raw = localStorage.getItem(READ_STATE_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    localStorage.removeItem(READ_STATE_STORAGE_KEY)
    return {}
  }
}

function writeStoredReadState(nextValue) {
  if (typeof window === 'undefined') return
  localStorage.setItem(READ_STATE_STORAGE_KEY, JSON.stringify(nextValue))
}

function isNotificationRead(itemId) {
  const readState = readStoredReadState()
  const bucket = readState[resolveReadBucketKey()]
  return Boolean(bucket && bucket[itemId])
}

function finalizeNotificationItem(item = null) {
  if (!item || typeof item !== 'object') return null

  return {
    ...item,
    time: formatRelativeTime(item.timestamp),
    unread: Boolean(item.isUnreadCandidate) && !isNotificationRead(item.id),
  }
}

function applyReadState(items = []) {
  return sortItems(items)
    .map(finalizeNotificationItem)
    .filter(Boolean)
}

function markNotificationRead(notification) {
  const itemId = typeof notification === 'string' ? notification : notification?.id
  if (!itemId) return

  const readState = readStoredReadState()
  const bucketKey = resolveReadBucketKey()
  const bucket = {
    ...(readState[bucketKey] && typeof readState[bucketKey] === 'object' ? readState[bucketKey] : {}),
    [itemId]: Date.now(),
  }

  writeStoredReadState({
    ...readState,
    [bucketKey]: bucket,
  })

  notificationItems.value = notificationItems.value.map((item) => (
    item.id === itemId
      ? { ...item, unread: false }
      : item
  ))
}

function markAllNotificationsRead() {
  if (!notificationItems.value.length) return

  const readState = readStoredReadState()
  const bucketKey = resolveReadBucketKey()
  const bucket = {
    ...(readState[bucketKey] && typeof readState[bucketKey] === 'object' ? readState[bucketKey] : {}),
  }

  notificationItems.value.forEach((item) => {
    bucket[item.id] = Date.now()
  })

  writeStoredReadState({
    ...readState,
    [bucketKey]: bucket,
  })

  notificationItems.value = notificationItems.value.map((item) => ({
    ...item,
    unread: false,
  }))
}

function resolveNotificationVisual(category = '') {
  const normalized = String(category || '').toLowerCase()

  if (normalized.includes('security')) {
    return {
      icon: ShieldAlert,
      iconBgClass: 'bg-[#FEF2F2] text-[#B91C1C]',
      kindLabel: 'Security',
    }
  }

  if (normalized.includes('attendance')) {
    return {
      icon: TriangleAlert,
      iconBgClass: 'bg-[#FFF7ED] text-[#C2410C]',
      kindLabel: 'Attendance',
    }
  }

  if (normalized.includes('event')) {
    return {
      icon: CalendarClock,
      iconBgClass: 'bg-[#EEF2FF] text-[#3730A3]',
      kindLabel: 'Events',
    }
  }

  return {
    icon: Bell,
    iconBgClass: 'bg-[#F3F4F6] text-[#111827]',
    kindLabel: 'Notification',
  }
}

function resolveChannelLabel(value = '') {
  const normalized = String(value || '').toLowerCase()
  if (!normalized || normalized === 'none') return ''
  if (normalized === 'in_app') return 'In app'
  return prettifyLabel(normalized, 'Channel')
}

function buildNotificationSignature(item = null) {
  const createdMinute = String(item?.created_at || '').slice(0, 16)
  const metadata = item?.metadata_json && typeof item.metadata_json === 'object'
    ? JSON.stringify(item.metadata_json)
    : ''

  return [
    String(item?.category || '').toLowerCase(),
    String(item?.subject || '').trim(),
    String(item?.message || '').trim(),
    metadata,
    createdMinute,
  ].join('|')
}

function dedupeInboxItems(items = []) {
  const channelPriority = {
    in_app: 0,
    email: 1,
    sms: 2,
    none: 3,
  }
  const selected = new Map()

  ;[...items]
    .filter((item) => String(item?.status || '').toLowerCase() === 'sent')
    .sort((left, right) => toTimestamp(right?.created_at) - toTimestamp(left?.created_at))
    .forEach((item) => {
      const signature = buildNotificationSignature(item)
      const existing = selected.get(signature)

      if (!existing) {
        selected.set(signature, item)
        return
      }

      const nextPriority = channelPriority[String(item?.channel || '').toLowerCase()] ?? 99
      const currentPriority = channelPriority[String(existing?.channel || '').toLowerCase()] ?? 99
      if (nextPriority < currentPriority) {
        selected.set(signature, item)
      }
    })

  return [...selected.values()]
}

function normalizeInboxItem(item = null) {
  if (!item || typeof item !== 'object') return null

  const signature = buildNotificationSignature(item)
  const visual = resolveNotificationVisual(item.category)

  return {
    id: `notification:${signature}`,
    timestamp: toTimestamp(item.created_at),
    title: String(item.subject || '').trim() || prettifyLabel(item.category, 'Notification'),
    bodyPreview: truncateText(item.message, 170),
    kindLabel: visual.kindLabel,
    metaLabel: resolveChannelLabel(item.channel) || 'System',
    icon: visual.icon,
    iconBgClass: visual.iconBgClass,
    isUnreadCandidate: true,
  }
}

function normalizeAnnouncementItem(item = null, unit = null) {
  if (!item || typeof item !== 'object') return null
  if (String(item.status || '').toLowerCase() !== 'published') return null

  const unitLabel = String(
    unit?.unit_name
    || item?.governance_unit_name
    || item?.author_name
    || 'Governance'
  ).trim()

  return {
    id: `announcement:${item.id}`,
    timestamp: toTimestamp(item.updated_at || item.created_at),
    title: String(item.title || '').trim() || 'Announcement',
    bodyPreview: truncateText(item.body, 190),
    kindLabel: 'Announcement',
    metaLabel: unitLabel || 'Governance',
    icon: Megaphone,
    iconBgClass: 'bg-[#FFF1E8] text-[#C2410C]',
    isUnreadCandidate: true,
  }
}

function clearNotificationsForSession() {
  notificationsError.value = ''
  notificationsLoading.value = false
  notificationsHydrated.value = false

  if (String(token.value || '').trim()) {
    notificationItems.value = []
    return
  }

  notificationItems.value = buildPreviewNotifications()
}

function resolveSessionKey() {
  const authToken = String(token.value || '').trim()
  if (!authToken) return ''

  const userId = Number(currentUser.value?.id ?? getStoredAuthMeta()?.userId)
  const normalizedUserId = Number.isFinite(userId) ? userId : 'anon'
  return `${normalizedUserId}:${authToken.slice(-16)}`
}

function isIgnorableGovernanceError(error) {
  return error instanceof BackendApiError
    && [403, 404].includes(Number(error.status))
}

async function loadGovernanceAnnouncementFeed(baseUrl, authToken) {
  let access = null

  try {
    access = await getGovernanceAccess(baseUrl, authToken)
  } catch (error) {
    if (!isIgnorableGovernanceError(error)) {
      throw error
    }
  }

  const units = getGovernanceAccessUnits(access).slice(0, 6)
  const announcements = []

  if (units.length) {
    const settled = await Promise.allSettled(
      units.map((unit) => getGovernanceAnnouncements(baseUrl, authToken, unit.governance_unit_id))
    )

    settled.forEach((result, index) => {
      if (result.status !== 'fulfilled' || !Array.isArray(result.value)) return

      result.value.forEach((item) => {
        const normalized = normalizeAnnouncementItem(item, units[index])
        if (normalized) {
          announcements.push(normalized)
        }
      })
    })
  }

  if (announcements.length) {
    return sortItems(announcements).slice(0, MAX_ANNOUNCEMENT_ITEMS)
  }

  if (!hasStaffAnnouncementScope()) {
    return []
  }

  try {
    const monitoredAnnouncements = await getGovernanceAnnouncementMonitor(baseUrl, authToken, {
      status: 'published',
      limit: MAX_ANNOUNCEMENT_ITEMS,
    })

    return monitoredAnnouncements
      .map((item) => normalizeAnnouncementItem(item))
      .filter(Boolean)
      .slice(0, MAX_ANNOUNCEMENT_ITEMS)
  } catch (error) {
    if (isIgnorableGovernanceError(error)) {
      return []
    }
    throw error
  }
}

async function refreshNotifications(options = {}) {
  const {
    force = false,
    silent = false,
  } = options
  const authToken = String(token.value || '').trim()

  if (!authToken) {
    clearNotificationsForSession()
    return notificationItems.value
  }

  if (refreshPromise) {
    return refreshPromise
  }

  if (notificationsHydrated.value && !force) {
    return notificationItems.value
  }

  if (!silent) {
    notificationsLoading.value = true
  }

  refreshPromise = (async () => {
    const baseUrl = apiBaseUrl.value
    const previousItems = [...notificationItems.value]

    const [inboxResult, announcementsResult] = await Promise.allSettled([
      getMyNotificationInbox(baseUrl, authToken, { limit: MAX_INBOX_ITEMS }),
      loadGovernanceAnnouncementFeed(baseUrl, authToken),
    ])

    const mergedItems = []
    const errors = []

    if (inboxResult.status === 'fulfilled') {
      dedupeInboxItems(inboxResult.value)
        .map(normalizeInboxItem)
        .filter(Boolean)
        .forEach((item) => mergedItems.push(item))
    } else if (!isIgnorableGovernanceError(inboxResult.reason)) {
      errors.push(inboxResult.reason?.message || 'Unable to load notifications.')
    }

    if (announcementsResult.status === 'fulfilled') {
      announcementsResult.value.forEach((item) => mergedItems.push(item))
    } else if (!isIgnorableGovernanceError(announcementsResult.reason)) {
      errors.push(announcementsResult.reason?.message || 'Unable to load announcements.')
    }

    if (!mergedItems.length && errors.length) {
      notificationsError.value = errors[0]
      notificationItems.value = previousItems.length ? previousItems : []
      notificationsHydrated.value = true
      return notificationItems.value
    }

    notificationItems.value = applyReadState(mergedItems)
    notificationsError.value = ''
    notificationsHydrated.value = true
    return notificationItems.value
  })().finally(() => {
    notificationsLoading.value = false
    refreshPromise = null
  })

  return refreshPromise
}

function toggleNotifications() {
  showNotifications.value = !showNotifications.value

  if (showNotifications.value) {
    void refreshNotifications({ force: true })
  }
}

function closeNotifications() {
  showNotifications.value = false
}

const unreadNotifCount = computed(() => (
  notificationItems.value.filter((item) => item.unread).length
))

function ensureNotificationBindings() {
  if (notificationBindingsReady) return
  notificationBindingsReady = true

  watch(
    [token, currentUser],
    () => {
      const nextSessionKey = resolveSessionKey()

      if (nextSessionKey !== activeSessionKey.value) {
        activeSessionKey.value = nextSessionKey
        clearNotificationsForSession()
      } else {
        notificationItems.value = applyReadState(notificationItems.value)
      }

      if (!String(token.value || '').trim()) {
        return
      }

      void refreshNotifications({
        force: !notificationsHydrated.value,
        silent: true,
      })
    },
    { immediate: true }
  )

  if (typeof window !== 'undefined') {
    window.addEventListener('focus', () => {
      if (!String(token.value || '').trim()) return
      void refreshNotifications({ force: true, silent: true })
    }, { passive: true })
  }
}

export function useNotifications() {
  ensureNotificationBindings()

  return {
    showNotifications,
    notificationItems,
    notificationsLoading,
    notificationsError,
    unreadNotifCount,
    toggleNotifications,
    closeNotifications,
    refreshNotifications,
    markNotificationRead,
    markAllNotificationsRead,
  }
}
