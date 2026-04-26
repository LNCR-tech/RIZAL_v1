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
            class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white transition-colors duration-300"
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
        class="signout-pill overflow-hidden transition-all duration-300 ease-in-out cursor-pointer hover:opacity-75"
      >
        <div class="flex items-center w-max pl-4 ml-3 border-l" style="border-left-color: var(--color-surface-border); height: 32px;">
          <LogOut :size="16" color="#D92D20" :stroke-width="2.5" class="mr-2 shrink-0" />
          <span class="text-[13px] font-bold shrink-0" style="color: #D92D20; letter-spacing: -0.01em;">Sign Out</span>
        </div>
      </div>
    </button>

    <!-- Right side actions -->
    <div class="flex items-center gap-2">
      <!-- Notifications & Theme Toggle Pill -->
      <div 
        class="flex items-center gap-1 transition-colors duration-300"
        style="border-radius: 28px; padding: 6px 10px; background: var(--color-nav-pill-bg);"
      >
        <!-- Bell notification -->
        <button
          @click="toggleNotifications"
          class="relative flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 active:scale-95"
          style="color: var(--color-nav-pill-text);"
          aria-label="Notifications"
        >
          <Bell :size="18" color="var(--color-nav-pill-text)" :stroke-width="2" />
          <!-- unread badge -->
          <span
            v-if="localUnreadCount > 0"
            class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
            style="background: #FF5A36;"
          />
        </button>

        <!-- Mobile Governance CTA -->
        <button
          v-if="hasGovernanceAccess && governanceAcronym"
          type="button"
          class="topbar-governance-btn"
          :class="{
            'topbar-governance-btn--active': isGovernanceWorkspaceActive,
            'topbar-governance-btn--desktop': true,
          }"
          :aria-label="governanceAriaLabel"
          :title="governanceAriaLabel"
          @click="openGovernanceWorkspace"
        >
          <ArrowLeft
            v-if="isGovernanceWorkspaceActive"
            :size="14"
            :stroke-width="2.25"
            class="topbar-governance-btn__icon"
          />
          <span class="topbar-governance-btn__text">{{ governanceButtonLabel }}</span>
        </button>

        <!-- Spacer/Divider -->
        <div class="hidden md:block w-[1px] h-5 mx-0.5" style="background: var(--color-surface-border);"></div>

        <!-- Dark Mode Toggle -->
        <button
          @click="toggleDarkMode"
          class="relative hidden md:flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 active:scale-95"
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
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Bell, Moon, LogOut } from 'lucide-vue-next'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'
import { useGovernanceAccess } from '@/composables/useGovernanceAccess.js'
import { useNotifications } from '@/composables/useNotifications.js'
import {
  resolveStudentHomeLocation,
  withPreservedGovernancePreviewQuery,
} from '@/services/routeWorkspace.js'

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
const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const {
  hasGovernanceAccess,
  governanceAcronym,
  governanceUnitName,
  governanceWorkspaceLocation,
  isGovernanceWorkspaceActive,
} = useGovernanceAccess()

const { toggleNotifications, unreadNotifCount } = useNotifications()

const localUnreadCount = computed(() => {
  return Math.max(props.unreadCount || 0, unreadNotifCount.value)
})

async function handleLogout() {
  await logout()
}

function openGovernanceWorkspace() {
  const target = isGovernanceWorkspaceActive.value
    ? withPreservedGovernancePreviewQuery(route, resolveStudentHomeLocation(route))
    : governanceWorkspaceLocation.value
  const resolvedTarget = router.resolve(target)
  if (route.fullPath === resolvedTarget.fullPath) return
  router.push(target)
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

const governanceAriaLabel = computed(() => {
  const label = governanceUnitName.value || governanceAcronym.value || 'Governance'
  return isGovernanceWorkspaceActive.value
    ? 'Back to student dashboard'
    : `Open ${label} dashboard`
})

const governanceButtonLabel = computed(() => {
  const acronym = String(governanceAcronym.value || 'Governance').trim()
  return isGovernanceWorkspaceActive.value ? 'Back' : `Open ${acronym}`
})
</script>

<style scoped>
.signout-pill {
  max-width: 0;
  opacity: 0;
}

.profile-pill:hover .signout-pill,
.profile-pill.is-expanded .signout-pill {
  max-width: 140px;
  opacity: 1;
}

.topbar-governance-btn {
  min-width: 0;
  max-width: 112px;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: transform 0.15s ease, background 0.18s ease, color 0.18s ease, opacity 0.18s ease;
}

.topbar-governance-btn--desktop {
  display: inline-flex;
}

.topbar-governance-btn:active {
  transform: scale(0.97);
}

.topbar-governance-btn--active {
  background: var(--color-primary);
  color: var(--color-banner-text);
}

.topbar-governance-btn__text {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.topbar-governance-btn__icon {
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .topbar-governance-btn {
    max-width: 148px;
    height: 36px;
    padding: 0 12px;
    background: color-mix(in srgb, var(--color-primary) 16%, transparent);
    color: var(--color-primary);
  }

  .topbar-governance-btn:not(.topbar-governance-btn--active) {
    opacity: 1;
  }

  .topbar-governance-btn__text {
    font-size: 12px;
    letter-spacing: 0.06em;
  }
}

@media (max-width: 767px) {
  .topbar-governance-btn--desktop {
    display: inline-flex;
  }
}
</style>
