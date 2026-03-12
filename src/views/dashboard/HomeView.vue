<template>
  <div class="flex flex-col gap-4 px-4 md:px-10 pb-6">
    <!-- TopBar -->
    <TopBar
      :user="currentUser"
      :unread-count="unreadAnnouncements"
      @toggle-notifications="showNotifications = !showNotifications"
    />

    <!-- Page Title -->
    <div class="mt-1 px-1 flex items-center justify-between">
      <h1 class="text-[26px] font-extrabold" style="color: var(--color-text-primary);">Home</h1>
      
      <!-- Impersonation Indicator -->
      <button 
        v-if="isImpersonating" 
        @click="stopImpersonating"
        class="flex items-center gap-3 bg-red-500 text-white px-5 py-2.5 rounded-full shadow-xl animate-pulse hover:bg-red-600 hover:scale-105 active:scale-95 transition-all outline-none border-none cursor-pointer group"
        title="Exit Inspection Mode"
      >
        <div class="flex flex-col items-start leading-none">
          <span class="text-[9px] font-black uppercase tracking-tighter opacity-70">Super Admin Mode</span>
          <span class="text-[12px] font-black uppercase tracking-widest font-black">Inspecting Campus</span>
        </div>
        <div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white/30 transition-colors">
          <X :size="18" stroke-width="3" />
        </div>
      </button>
    </div>

    <!-- Search bar + Talk to Aura AI row -->
    <div class="flex items-center gap-3">
      <!-- Search bar -->
      <div class="relative flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search..."
          class="w-full rounded-full px-5 py-3.5 text-[14px] font-medium pr-12 outline-none shadow-sm transition-all duration-150 focus:ring-2 focus:ring-black/10"
          style="background: var(--color-surface); color: var(--color-text-always-dark);"
        />
        <Search
          :size="18"
          class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none"
          style="color: var(--color-primary);"
        />
      </div>

      <!-- Talk to Aura AI (mobile only — desktop has it in the sidebar) -->
      <button
        class="md:hidden flex flex-col items-center justify-center gap-1 transition-all duration-200 hover:brightness-110 hover:scale-105 active:scale-95 flex-shrink-0"
        style="background: var(--color-primary); border-radius: 26px; width: 80px; height: 50px;"
        aria-label="Talk to Aura AI"
      >
        <div class="flex items-center gap-1.5 pt-0.5">
          <img
            :src="activeAuraLogo"
            alt="Aura"
            class="w-4 h-4 object-contain opacity-90"
          />
          <span
            class="text-[9px] font-extrabold text-left leading-[1.1] transition-colors duration-200"
            style="color: var(--color-banner-text);"
          >
            Talk to<br>Aura Ai
          </span>
        </div>
      </button>
    </div>

    <!-- Cards grid: stacked on mobile, side-by-side on desktop -->
    <div class="flex flex-col md:flex-row gap-4">
      <!-- University Banner -->
      <Transition name="card-slide" appear>
        <UniversityBanner
          class="md:flex-1"
          :school-name="schoolSettings.school_name"
          :school-logo="schoolSettings.logo_url"
          @announcement-click="handleAnnouncementClick"
        />
      </Transition>

      <!-- Latest Event card -->
      <Transition name="card-slide-delay" appear>
        <EventsCard
          class="md:flex-1"
          :events="events"
          @see-event="handleSeeEvent"
        />
      </Transition>
    </div>

    <!-- Upcoming events list (additional quick-view) -->
    <div v-if="upcomingEvents.length > 1" class="mt-2">
      <h2 class="text-[16px] font-bold mb-3 px-1" style="color: var(--color-text-primary);">Upcoming Events</h2>
      <div class="flex flex-col gap-3">
        <TransitionGroup name="list" appear>
          <div
            v-for="(event, i) in upcomingEvents.slice(1)"
            :key="event.id"
            class="rounded-2xl px-4 py-3.5 flex items-center gap-4 shadow-sm cursor-pointer transition-all duration-150 hover:shadow-md hover:scale-[1.01] active:scale-[0.99]"
            style="background: var(--color-surface);"
            @click="handleSeeEvent(event)"
          >
            <!-- Date badge -->
            <div
              class="flex flex-col items-center justify-center w-10 h-12 rounded-xl flex-shrink-0"
              style="background: var(--color-primary);"
            >
              <span class="text-[10px] font-bold" style="color: var(--color-banner-text);">
                {{ formatMonth(event.start_datetime) }}
              </span>
              <span class="text-[18px] font-extrabold leading-none" style="color: var(--color-banner-text);">
                {{ formatDay(event.start_datetime) }}
              </span>
            </div>

            <!-- Event details -->
            <div class="flex-1 min-w-0">
              <p class="text-[13px] font-bold truncate" style="color: var(--color-text-always-dark);">
                {{ event.name }}
              </p>
              <p class="text-[11px] mt-0.5 truncate" style="color: var(--color-text-muted);">
                {{ event.location }}
              </p>
            </div>

            <!-- Status badge -->
            <span
              class="text-[10px] font-semibold px-2.5 py-1 rounded-full flex-shrink-0"
              :style="statusStyle(event.status)"
            >
              {{ event.status }}
            </span>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Search, X } from 'lucide-vue-next'
import TopBar from '@/components/dashboard/TopBar.vue'
import UniversityBanner from '@/components/dashboard/UniversityBanner.vue'
import EventsCard from '@/components/dashboard/EventsCard.vue'

import { mockCurrentUser, mockEvents, mockSchoolSettings, mockAnnouncements } from '@/data/mockData.js'
import { loadTheme, applyTheme, activeAuraLogo } from '@/config/theme.js'
import { userService } from '@/services/userService.js'
import { eventService } from '@/services/eventService.js'

// --- State ---
const searchQuery = ref('')
const showNotifications = ref(false)
const isLoading = ref(true)

// --- Data ---
const currentUser = ref(mockCurrentUser)
const events = ref(mockEvents)
const announcements = ref(mockAnnouncements)
const schoolSettings = ref({
  ...mockSchoolSettings,
  school_name: localStorage.getItem('aura_impersonate_school_name') || mockSchoolSettings.school_name,
  logo_url: localStorage.getItem('aura_impersonate_school_logo') || mockSchoolSettings.logo_url
})

// --- Fetch Data ---
onMounted(async () => {
  // Apply theme (handles both normal and impersonated school themes)
  applyTheme(loadTheme())

  try {
    isLoading.value = true
    
    // Fetch user profile
    const user = await userService.getMe()
    if (user) currentUser.value = user
    
    // Update theme if school settings are available in user profile
    // (This depends on the API shape, adjusting to user.school_id logic if needed)
    
    // Fetch events
    const realEvents = await eventService.getEvents({ limit: 10 })
    if (realEvents && realEvents.length > 0) {
      events.value = realEvents
    }
  } catch (error) {
    console.error('Error fetching home data:', error)
  } finally {
    isLoading.value = false
  }
})

// --- Computed ---
const isImpersonating = computed(() => !!localStorage.getItem('aura_impersonate_school_id'))

const upcomingEvents = computed(() =>
  events.value.filter((e) => e.status === 'upcoming' || e.status === 'ongoing')
)

const unreadAnnouncements = computed(() =>
  announcements.value.filter((a) => !a.is_read).length
)

// --- Formatters ---
function formatMonth(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('en', { month: 'short' }).toUpperCase()
}

function formatDay(dt) {
  if (!dt) return ''
  return new Date(dt).getDate()
}

function statusStyle(status) {
  const map = {
    upcoming: { background: 'rgba(170,255,0,0.2)', color: '#3a5c00' },
    ongoing: { background: 'rgba(0,200,100,0.15)', color: '#006633' },
    completed: { background: 'rgba(0,0,0,0.08)', color: '#555' },
    cancelled: { background: 'rgba(255,80,80,0.12)', color: '#cc0000' },
  }
  return map[status] ?? map.upcoming
}

// --- Handlers ---
function handleAnnouncementClick() {
  // TODO: navigate to announcements page or open modal
  console.log('Announcement clicked')
}

function handleSeeEvent(event) {
  // TODO: navigate to event detail page
  console.log('See event:', event)
}

function stopImpersonating() {
  localStorage.removeItem('aura_impersonate_school_id')
  localStorage.removeItem('aura_impersonate_school_name')
  localStorage.removeItem('aura_impersonate_school_logo')
  window.location.href = '/super-admin/campuses'
}
</script>

<style scoped>
/* Card entrance animations */
.card-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.card-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.card-slide-delay-enter-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.08s;
}
.card-slide-delay-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

/* List item entrance */
.list-enter-active {
  transition: all 0.3s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}
.list-move {
  transition: transform 0.3s ease;
}
</style>
