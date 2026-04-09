<template>
  <header class="flex items-center justify-between px-0 pt-5 pb-2 md:px-0 md:pt-6">
    <!-- Profile Card (Expands on Hover or Tap) -->
    <button 
      @click="isProfileExpanded = !isProfileExpanded"
      class="profile-pill flex items-center rounded-full pl-3 pr-4 py-2 transition-all duration-300 cursor-pointer"
      :class="{ 'is-expanded': isProfileExpanded }"
      style="background: var(--color-profile-bg);"
    >
      <div class="flex items-center gap-3">
        <!-- Avatar -->
        <div class="relative flex-shrink-0">
          <img
            v-if="avatarUrl"
            :src="avatarUrl"
            :alt="displayName"
            class="w-10 h-10 rounded-full object-cover"
          />
          <div
            v-else
            class="avatar-fallback w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-colors duration-300"
            style="background: var(--color-nav); color: var(--color-nav-text);"
          >
            {{ initials }}
          </div>
          <!-- Online dot -->
          <span
            class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 transition-colors duration-300"
            style="background: var(--color-primary); border-color: var(--color-profile-bg);"
          />
        </div>

        <!-- Name & greeting -->
        <div class="leading-none text-left">
          <p class="text-[10px] font-medium transition-colors duration-300" style="color: var(--color-surface-text-muted);">Welcome Back</p>
          <p class="text-[13px] font-bold transition-colors duration-300" style="color: var(--color-profile-text);">{{ displayName }}</p>
        </div>
      </div>
      
      <!-- Hidden Sign Out section (Reveals on Hover or active state) -->
      <div 
        @click.stop="handleLogout"
        class="signout-pill flex items-center overflow-hidden max-w-0 opacity-0 transition-all duration-300 ease-in-out whitespace-nowrap hover:opacity-75 cursor-pointer"
      >
          <LogOut :size="18" color="#D92D20" :stroke-width="2.5" class="mr-2" />
        <span class="text-[14px] font-medium" style="color: #D92D20; letter-spacing: -0.02em;">Sign Out</span>
      </div>
    </button>

    <!-- Right side actions -->
    <div class="flex items-center gap-2">
      <!-- Notifications & Theme Toggle Pill -->
      <div 
        class="flex items-center gap-1 transition-colors duration-300 relative"
        style="border-radius: 28px; padding: 6px 10px; background: var(--color-nav-pill-bg);"
      >
        <!-- Bell notification -->
        <button
          @click="toggleNotifications"
          class="relative flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 active:scale-95"
          style="color: var(--color-nav-pill-text);"
          aria-label="Notifications"
          :aria-expanded="showNotifications ? 'true' : 'false'"
        >
          <Bell :size="18" color="var(--color-nav-pill-text)" :stroke-width="2" />
          <!-- unread badge -->
          <span
            v-if="unreadCount > 0"
            class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
            style="background: var(--color-primary);"
          />
        </button>

        <!-- Notifications Dropdown -->
        <Transition name="notif-dropdown">
          <div
            v-if="showNotifications"
            class="notifications-dropdown"
          >
            <div class="notif-header">
              <span class="notif-title">Notifications</span>
              <button 
                v-if="notifications.length" 
                class="notif-mark-read"
                @click="markAllRead"
              >
                Mark all read
              </button>
            </div>
            <div class="notif-list">
              <div
                v-for="notif in notifications"
                :key="notif.id"
                class="notif-item"
                :class="{ 'notif-item--unread': !notif.read }"
              >
                <div class="notif-icon-wrap" :style="{ background: notif.iconBg }">
                  <component :is="notif.icon" :size="14" />
                </div>
                <div class="notif-content">
                  <p class="notif-text">{{ notif.title }}</p>
                  <p class="notif-meta">{{ notif.time }}</p>
                </div>
              </div>
              <p v-if="!notifications.length" class="notif-empty">No notifications</p>
            </div>
          </div>
        </Transition>

        <!-- Spacer/Divider -->
        <div class="w-[1px] h-5 mx-0.5" style="background: var(--color-surface-border);"></div>

        <!-- Dark Mode Toggle -->
        <button
          @click="toggleDarkMode"
          class="relative flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 active:scale-95"
          style="color: var(--color-nav-pill-text);"
          aria-label="Toggle Dark Mode"
        >
          <Moon 
            :size="18" 
            :color="isDarkMode ? 'var(--color-primary)' : 'var(--color-nav-pill-text)'" 
            :stroke-width="2" 
          />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell, Moon, LogOut, Calendar, Megaphone, Clock, CheckCircle } from 'lucide-vue-next'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'

const props = defineProps({
  user: {
    type: Object,
    default: null,
  },
  unreadCount: {
    type: Number,
    default: 0,
  },
})

defineEmits(['toggle-notifications'])

const isProfileExpanded = ref(false)
const showNotifications = ref(false)
const { logout } = useAuth()

const notifications = ref([
  {
    id: 1,
    title: 'Orientation 2026 starts tomorrow',
    time: '2 hours ago',
    read: false,
    icon: Calendar,
    iconBg: 'rgba(0, 87, 184, 0.15)',
  },
  {
    id: 2,
    title: 'New announcement from Student Government',
    time: '5 hours ago',
    read: false,
    icon: Megaphone,
    iconBg: 'rgba(255, 212, 0, 0.2)',
  },
  {
    id: 3,
    title: 'Attendance recorded for General Assembly',
    time: '1 day ago',
    read: true,
    icon: CheckCircle,
    iconBg: 'rgba(0, 200, 100, 0.15)',
  },
  {
    id: 4,
    title: 'Remember: General Assembly at 9 AM',
    time: '2 days ago',
    read: true,
    icon: Clock,
    iconBg: 'rgba(255, 140, 0, 0.15)',
  },
])

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
}

function markAllRead() {
  notifications.value = notifications.value.map(n => ({ ...n, read: true }))
}

function handleClickOutside(event) {
  const target = event.target
  if (!target.closest('.notifications-dropdown') && !target.closest('[aria-label="Notifications"]')) {
    showNotifications.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

async function handleLogout() {
  await logout()
}

const displayName = computed(() => {
  if (!props.user) return 'User'
  const names = [props.user.first_name, props.user.middle_name, props.user.last_name]
    .filter(Boolean)
  if (names.length) return names.join(' ')
  return props.user.email?.split('@')[0] || 'User'
})

const initials = computed(() => {
  const name = displayName.value
  const parts = name.split(' ').filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const avatarUrl = computed(() => {
  return (
    props.user?.student_profile?.photo_url ||
    props.user?.student_profile?.avatar_url ||
    props.user?.avatar_url ||
    null
  )
})
</script>

<style scoped>
.profile-pill:hover .signout-pill,
.profile-pill.is-expanded .signout-pill {
  max-width: 150px;
  opacity: 1;
  margin-left: 24px;
  margin-right: 4px;
}

/* Notifications Dropdown */
.notifications-dropdown {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 320px;
  max-height: 420px;
  border-radius: 20px;
  background: var(--aura-glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--aura-glass-border);
  box-shadow: var(--aura-shadow-premium);
  overflow: hidden;
  z-index: 100;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px 12px;
  border-bottom: 1px solid var(--color-surface-border);
}

.notif-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.notif-mark-read {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.notif-mark-read:hover {
  background: rgba(0, 87, 184, 0.08);
}

.notif-list {
  max-height: 340px;
  overflow-y: auto;
  padding: 8px;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.notif-item:hover {
  background: var(--color-field-surface);
}

.notif-item--unread {
  background: color-mix(in srgb, var(--color-primary) 6%, transparent);
}

.notif-item--unread:hover {
  background: rgba(0, 87, 184, 0.08);
}

.notif-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-text-primary);
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  margin: 0;
}

.notif-meta {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  margin: 4px 0 0;
}

.notif-empty {
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  padding: 32px 16px;
}

/* Dropdown animation */
.notif-dropdown-enter-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.notif-dropdown-leave-active {
  transition: all 0.2s ease;
}

.notif-dropdown-enter-from,
.notif-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
</style>
