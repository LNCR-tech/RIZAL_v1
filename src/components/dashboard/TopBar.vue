<template>
  <header class="flex items-center justify-between px-0 pt-5 pb-2 md:px-0 md:pt-6">
    <!-- Profile Card (Expands on Hover or Tap) -->
    <button 
      @click="isProfileExpanded = !isProfileExpanded"
      class="group flex items-center rounded-full pl-3 pr-4 py-2 shadow-sm transition-all duration-300 hover:shadow-md cursor-pointer"
      :class="{ 'is-expanded': isProfileExpanded }"
      style="background: var(--color-profile-bg);"
    >
      <div class="flex items-center gap-3">
        <!-- Avatar -->
        <div class="relative flex-shrink-0">
          <img
            v-if="user?.student_profile?.avatar_url"
            :src="user.student_profile.avatar_url"
            :alt="displayName"
            class="w-10 h-10 rounded-full object-cover"
          />
          <div
            v-else
            class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white transition-colors duration-300"
            style="background: linear-gradient(135deg, #0A0A0A 0%, #333 100%);"
          >
            {{ initials }}
          </div>
          <!-- Online dot -->
          <span
            class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white transition-colors duration-300"
            style="background: var(--color-primary);"
          />
        </div>

        <!-- Name & greeting -->
        <div class="leading-none text-left">
          <p class="text-[10px] font-medium transition-colors duration-300" style="color: var(--color-text-muted);">Welcome Back</p>
          <p class="text-[13px] font-bold transition-colors duration-300" style="color: var(--color-text-always-dark);">{{ displayName }}</p>
        </div>
      </div>
      
      <!-- Hidden Sign Out section (Reveals on Hover or active state) -->
      <div 
        @click.stop="handleLogout"
        class="flex items-center overflow-hidden max-w-0 opacity-0 transition-all duration-300 ease-in-out whitespace-nowrap group-hover:max-w-[150px] group-hover:opacity-100 group-hover:ml-6 group-hover:mr-1 group-[.is-expanded]:max-w-[150px] group-[.is-expanded]:opacity-100 group-[.is-expanded]:ml-6 group-[.is-expanded]:mr-1 hover:opacity-75 cursor-pointer"
      >
        <LogOut :size="18" color="#FF0B0B" :stroke-width="2.5" class="mr-2" />
        <span class="text-[14px] font-medium" style="color: #FF0B0B; letter-spacing: -0.02em;">Sign Out</span>
      </div>
    </button>

    <!-- Right side actions -->
    <div class="flex items-center gap-2">
      <!-- Notifications & Theme Toggle Pill -->
      <div 
        class="flex items-center gap-1 shadow-sm transition-colors duration-300"
        style="border-radius: 28px; padding: 6px 10px; background: var(--color-nav-pill-bg);"
      >
        <!-- Bell notification -->
        <button
          @click="$emit('toggle-notifications')"
          class="relative flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 hover:bg-black/5 active:scale-95"
          aria-label="Notifications"
        >
          <Bell :size="18" color="var(--color-text-always-dark)" :stroke-width="2" />
          <!-- unread badge -->
          <span
            v-if="unreadCount > 0"
            class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full"
            style="background: var(--color-primary);"
          />
        </button>

        <!-- Spacer/Divider -->
        <div class="w-[1px] h-5 bg-gray-200 mx-0.5"></div>

        <!-- Dark Mode Toggle -->
        <button
          @click="toggleDarkMode"
          class="relative flex items-center justify-center w-9 h-9 rounded-full transition-all duration-150 hover:bg-gray-100 active:scale-95"
          aria-label="Toggle Dark Mode"
        >
          <Moon 
            :size="18" 
            :color="isDarkMode ? 'var(--color-primary)' : 'var(--color-text-primary)'" 
            :stroke-width="2" 
          />
        </button>
      </div>
    </div>

    <!-- Premium Logout Confirmation Modal -->
    <Transition name="fade">
      <div v-show="showLogoutConfirm" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/85 backdrop-blur-md" @click="showLogoutConfirm = false"></div>
        <div 
          class="w-full max-w-md p-8 rounded-[40px] relative z-10 shadow-2xl border transition-all duration-300 transform scale-100"
          style="background: var(--color-card-bg); border-color: var(--color-border);"
        >
          <div class="flex flex-col items-center text-center gap-8">
            <div class="w-24 h-24 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
              <LogOut :size="48" stroke-width="2.5" />
            </div>
            
            <div>
              <h3 class="text-3xl font-black mb-3" style="color: var(--color-text-primary);">Sign Out</h3>
              <p class="font-bold leading-relaxed text-[15px]" style="color: var(--color-text-muted);">Are you sure you want to end your session? You'll need to sign in again to access the Aura dashboard.</p>
            </div>
            
            <div class="flex w-full gap-4">
              <button 
                @click="showLogoutConfirm = false"
                class="flex-1 py-4.5 rounded-full font-bold transition-all hover:scale-105 active:scale-95"
                style="background: var(--color-input-bg); color: var(--color-text-primary);"
              >
                Go Back
              </button>
              <button 
                @click="confirmLogout"
                class="flex-1 py-4.5 rounded-full font-black bg-red-500 text-white hover:scale-105 active:scale-95 transition-all shadow-xl shadow-red-500/20"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, Moon, LogOut } from 'lucide-vue-next'
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
const showLogoutConfirm = ref(false)
const { logout } = useAuth()

function handleLogout() {
  showLogoutConfirm.value = true
}

function confirmLogout() {
  logout()
}

const displayName = computed(() => {
  if (!props.user) return 'User'
  // API shape: first_name & last_name are at the user root level
  if (props.user.first_name && props.user.last_name) {
    return `${props.user.first_name} ${props.user.last_name}`
  }
  return props.user.email?.split('@')[0] || 'User'
})

const initials = computed(() => {
  const name = displayName.value
  const parts = name.split(' ')
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.slice(0, 2).toUpperCase()
})
</script>
