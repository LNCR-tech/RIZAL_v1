<template>
  <div class="px-6 py-10 max-w-4xl mx-auto">
    <div v-if="isLoading" class="flex justify-center items-center min-h-[40vh]">
       <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>
    
    <div v-else-if="user" class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <!-- Header Section -->
      <div class="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100 flex flex-col md:flex-row items-center gap-8">
        <div class="relative">
          <img 
            v-if="user.student_profile?.avatar_url"
            :src="user.student_profile.avatar_url" 
            class="w-32 h-32 rounded-full object-cover border-4 border-[var(--color-primary)]"
            alt="Avatar"
          />
          <div v-else class="w-32 h-32 rounded-full bg-black flex items-center justify-center text-4xl font-bold text-white border-4 border-[var(--color-primary)]">
            {{ initials }}
          </div>
        </div>
        
        <div class="text-center md:text-left space-y-2">
          <h1 class="text-3xl font-extrabold text-gray-900">{{ fullName }}</h1>
          <p class="text-gray-500 font-medium">{{ user.email }}</p>
          <div class="flex flex-wrap justify-center md:justify-start gap-2 mt-4">
            <span v-for="role in user.roles" :key="role.role.name" class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-bold uppercase tracking-wider">
              {{ role.role.name }}
            </span>
          </div>
        </div>
        
        <div class="md:ml-auto">
          <button @click="handleLogout" class="px-6 py-2.5 bg-red-50 text-red-600 rounded-full text-sm font-bold hover:bg-red-100 transition-colors">
            Sign Out
          </button>
        </div>
      </div>

      <!-- Details Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Academic Info -->
        <div class="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100 space-y-6">
          <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            <GraduationCap :size="24" class="text-[var(--color-primary)]" />
            Academic Information
          </h2>
          
          <div class="space-y-4">
            <div class="flex justify-between border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Student ID</span>
              <span class="text-gray-900 font-bold">{{ user.student_profile?.student_id || 'N/A' }}</span>
            </div>
            <div class="flex justify-between border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Year Level</span>
              <span class="text-gray-900 font-bold">{{ user.student_profile?.year_level || 'N/A' }}</span>
            </div>
            <div class="flex flex-col gap-1 border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Department</span>
              <span class="text-gray-900 font-bold">{{ user.student_profile?.department?.name || 'N/A' }}</span>
            </div>
            <div class="flex flex-col gap-1 border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Program</span>
              <span class="text-gray-900 font-bold">{{ user.student_profile?.program?.name || 'N/A' }}</span>
            </div>
          </div>
        </div>

        <!-- Account Info -->
        <div class="bg-white rounded-[32px] p-8 shadow-sm border border-gray-100 space-y-6">
          <h2 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            <UserIcon :size="24" class="text-[var(--color-primary)]" />
            Account Details
          </h2>
          
          <div class="space-y-4">
            <div class="flex justify-between border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Account Status</span>
              <span class="px-2 py-0.5 rounded text-xs font-bold truncate" :class="user.is_active ? 'bg-indigo-50 text-indigo-600' : 'bg-red-50 text-red-600'">
                {{ user.is_active ? 'ACTIVE' : 'INACTIVE' }}
              </span>
            </div>
            <div class="flex justify-between border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Joined Date</span>
              <span class="text-gray-900 font-bold">{{ formatDate(user.created_at) }}</span>
            </div>
            <div class="flex justify-between border-b border-gray-50 pb-3">
              <span class="text-gray-500 font-medium">Last Login</span>
              <span class="text-gray-900 font-bold">Today</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="text-center py-20 text-gray-500 font-medium">
      Failed to load profile data.
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { GraduationCap, User as UserIcon, LogOut } from 'lucide-vue-next'
import { userService } from '@/services/userService.js'
import { useAuth } from '@/composables/useAuth.js'

const showLogoutConfirm = ref(false)

const user = ref(null)
const isLoading = ref(true)
const { logout } = useAuth()

onMounted(async () => {
  try {
    isLoading.value = true
    const data = await userService.getMe()
    user.value = data
  } catch (error) {
    console.error('Error fetching profile:', error)
  } finally {
    isLoading.value = false
  }
})

const fullName = computed(() => {
  if (!user.value) return ''
  return `${user.value.first_name} ${user.value.last_name}`
})

const initials = computed(() => {
  if (!user.value) return ''
  return `${user.value.first_name[0]}${user.value.last_name[0]}`.toUpperCase()
})

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric'
  })
}

function handleLogout() {
  showLogoutConfirm.value = true
}

function confirmLogout() {
  logout()
}
</script>
