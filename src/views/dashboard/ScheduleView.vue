<template>
  <div class="events-page">
    
    <!-- ── Header ─────────────────────────────────────────────────────── -->
    <TopBar
      class="dashboard-enter dashboard-enter--1"
      :user="activeUser"
      :unread-count="activeUnreadAnnouncements"
      @toggle-notifications="showNotifications = !showNotifications"
    />

    <!-- ── Title & Filters ────────────────────────────────────────────── -->
    <div class="events-content dashboard-enter dashboard-enter--2">
      <h1 class="page-title">Events</h1>
      
      <div class="filters-scroll">
        <div class="filters-track">
          <button 
            v-for="filter in filters" 
            :key="filter.id"
            class="filter-pill"
            :class="[
              { 'filter-pill--active': activeFilter === filter.id },
              filter.variant === 'outline' ? 'filter-pill--outline' : ''
            ]"
            @click="activeFilter = filter.id"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>

      <!-- ── Events List ──────────────────────────────────────────────── -->
      <div v-if="filteredEvents.length > 0" class="events-grid dashboard-enter dashboard-enter--3">
        <EventCard 
          v-for="event in filteredEvents" 
          :key="event.id" 
          :event="event"
          :is-attended="isEventAttended(event)"
          :attendance-record="getAttendanceRecord(event)"
          @click="handleEventClick"
          @open-detail="handleOpenDetail"
        />
      </div>
      
      <div v-else class="empty-state dashboard-enter dashboard-enter--3">
        <p>No events found for this category.</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import EventCard from '@/components/dashboard/EventCard.vue'
import TopBar from '@/components/dashboard/TopBar.vue'

import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { usePreviewTheme } from '@/composables/usePreviewTheme.js'
import { studentDashboardPreviewData } from '@/data/studentDashboardPreview.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  currentUser,
  events,
  getLatestAttendanceForEvent,
  hasAttendanceForEvent,
  unreadAnnouncements,
} = useDashboardSession()
const showNotifications = ref(false)

const router = useRouter()
const activeUser = computed(() => props.preview ? studentDashboardPreviewData.user : currentUser.value)
const activeEvents = computed(() => props.preview ? studentDashboardPreviewData.events : events.value)
const activeAttendanceRecords = computed(() => props.preview ? studentDashboardPreviewData.attendanceRecords : [])
const activeUnreadAnnouncements = computed(() => props.preview ? 0 : unreadAnnouncements.value)
const activeSchoolSettings = computed(() => props.preview ? studentDashboardPreviewData.schoolSettings : null)

usePreviewTheme(() => props.preview, activeSchoolSettings)

// ── Filters & Events Logic ────────────────────────────────────────────
const schoolEvents = computed(() => {
  const schoolId = Number(activeUser.value?.school_id)
  return activeEvents.value.filter((event) => !Number.isFinite(schoolId) || Number(event?.school_id) === schoolId)
})
const filters = [
  { id: 'all', label: 'All' },
  { id: 'ongoing', label: 'On Going' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'completed', label: 'Done' },
  { id: 'maps', label: 'Calendar & Maps', variant: 'outline' }, // Placeholder for future feature
]

const activeFilter = ref('all')

const statusRank = {
  ongoing: 0,
  upcoming: 1,
  completed: 2,
  cancelled: 3,
}

function normalizeStatus(status) {
  return status === 'done' ? 'completed' : status
}

const filteredEvents = computed(() => {
  let items = schoolEvents.value
  if (activeFilter.value !== 'all' && activeFilter.value !== 'maps') {
    items = items.filter(e => normalizeStatus(e.status) === activeFilter.value)
  }
  if (activeFilter.value === 'maps') return []
  return [...items].sort((a, b) => {
    const aRank = statusRank[normalizeStatus(a.status)] ?? 99
    const bRank = statusRank[normalizeStatus(b.status)] ?? 99
    if (aRank !== bRank) return aRank - bRank
    return new Date(a.start_datetime) - new Date(b.start_datetime)
  })
})

function handleEventClick(event) {
  if (!event?.id) return
  if (!props.preview && event.status === 'ongoing' && !isEventAttended(event)) {
    router.push(`/dashboard/schedule/${event.id}/attendance`)
    return
  }
  router.push(props.preview ? `/exposed/dashboard/schedule/${event.id}` : `/dashboard/schedule/${event.id}`)
}

function handleOpenDetail(event) {
  if (!event?.id) return
  router.push(props.preview ? `/exposed/dashboard/schedule/${event.id}` : `/dashboard/schedule/${event.id}`)
}

function isEventAttended(event) {
  if (props.preview) {
    return activeAttendanceRecords.value.some((attendance) => {
      const status = String(attendance?.status ?? '').toLowerCase()
      const hasTimeIn = Boolean(attendance?.time_in)
      return Number(attendance?.event_id) === Number(event?.id) && (
        status === 'present' ||
        status === 'late' ||
        hasTimeIn
      )
    })
  }
  return hasAttendanceForEvent(event?.id)
}

function getAttendanceRecord(event) {
  if (props.preview) {
    return activeAttendanceRecords.value
      .filter((attendance) => Number(attendance?.event_id) === Number(event?.id))
      .sort((left, right) => {
        const leftTime = new Date(left?.time_in || left?.created_at || 0).getTime()
        const rightTime = new Date(right?.time_in || right?.created_at || 0).getTime()
        return rightTime - leftTime
      })[0] ?? null
  }
  return getLatestAttendanceForEvent(event?.id)
}
</script>

<style scoped>
/* ── Page Base ───────────────────────────────────────────────────── */
.events-page {
  min-height: 100vh;
  padding: 28px 22px 100px; /* Bottom padding for mobile nav */
  background: var(--color-bg);
}

/* ── Page Title & Content ────────────────────────────────────────── */
.events-content {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.page-title {
  font-size: 24px;
  font-weight: 800;
  color: var(--color-text-always-dark);
  margin-bottom: 22px;
  letter-spacing: -0.5px;
}

/* ── Filters Scroll Track ────────────────────────────────────────── */
.filters-scroll {
  /* Hide scrollbar but allow horizontal scroll */
  overflow-x: auto;
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
  margin: 0 -22px 28px; /* Pull margins out to bleed edge */
  padding: 0 22px; /* Push content back in */
}

.filters-scroll::-webkit-scrollbar {
  display: none;
}

.filters-track {
  display: flex;
  gap: 10px;
  width: max-content;
}

.filter-pill {
  padding: 10px 22px;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  font-size: 14px;
  font-weight: 500;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-pill--active {
  background: var(--color-pill-row-active-bg);
  border-color: var(--color-pill-row-active-bg);
  color: var(--color-pill-row-active-text);
  font-weight: 600;
}

.filter-pill--outline {
  border-color: var(--color-pill-row-outline);
}

.filter-pill:active {
  transform: scale(0.96);
}

/* ── Events Grid ─────────────────────────────────────────────────── */
.events-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: rgba(0,0,0,0.4);
  font-weight: 500;
}

/* ── Desktop adjustments (md+) ───────────────────────────────────── */
@media (min-width: 768px) {
  .events-page {
    padding: 36px 36px 40px;
  }

  .filters-scroll {
    margin: 0 0 32px 0;
    padding: 0;
  }
  
  .events-content {
    max-width: 960px;
  }
}

@media (min-width: 900px) {
  /* Two-column layout like the reference */
  .events-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 28px;
  }
}
</style>
