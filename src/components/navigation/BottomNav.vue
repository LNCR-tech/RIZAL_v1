<template>
  <!-- Mobile Bottom Navigation -->
  <nav
    class="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 md:hidden"
    aria-label="Mobile navigation"
  >
    <div class="flex items-center gap-1 bg-[#0A0A0A] rounded-full px-4 py-3 shadow-2xl">
      <button
        v-for="item in navItems"
        :key="item.name"
        @click="navigate(item.route)"
        :aria-label="item.name"
        class="relative flex flex-col items-center justify-center w-[52px] h-12 rounded-full transition-all duration-200"
        :class="isActive(item.route) ? '' : 'opacity-40 hover:opacity-60'"
      >
        <!-- Active glowing background -->
        <span
          v-if="isActive(item.route)"
          class="absolute inset-0 rounded-full"
          style="background: radial-gradient(circle, var(--color-primary) 0%, transparent 60%); opacity: 0.15;"
        />
        
        <component
          :is="item.icon"
          :size="20"
          :stroke-width="isActive(item.route) ? 2.5 : 2"
          :color="isActive(item.route) ? 'var(--color-primary)' : '#FFFFFF'"
          class="relative z-10 transition-all duration-200"
          :class="{ 'mb-2': isActive(item.route) }"
        />

        <!-- Active Dot Indicator -->
        <span
          v-if="isActive(item.route)"
          class="absolute bottom-2 w-1.5 h-1.5 rounded-full shadow-sm"
          style="background: var(--color-primary);"
        />
      </button>
      <!-- Logout (Mobile) -->
      <button
        @click="handleLogout"
        aria-label="Logout"
        class="flex flex-col items-center justify-center w-[52px] h-12 rounded-full transition-all duration-200 opacity-40 hover:opacity-100 hover:text-red-500"
      >
        <LogOut :size="20" stroke-width="2" />
      </button>
    </div>

    <!-- Premium Logout Confirmation Modal -->
    <Transition name="fade">
      <div v-show="showLogoutConfirm" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/85 backdrop-blur-md" @click="showLogoutConfirm = false"></div>
        <div 
          class="w-full max-w-[calc(100vw-32px)] p-8 rounded-[40px] relative z-10 shadow-2xl border transition-all duration-300 transform scale-100"
          style="background: var(--color-card-bg); border-color: var(--color-border);"
        >
          <div class="flex flex-col items-center text-center gap-6">
            <div class="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
              <LogOut :size="38" stroke-width="2.5" />
            </div>
            
            <div>
              <h3 class="text-2xl font-black mb-2" style="color: var(--color-text-primary);">Sign Out</h3>
              <p class="font-bold leading-relaxed text-[14px]" style="color: var(--color-text-muted);">Are you sure you want to end your session? You'll need to sign in again to access your dashboard.</p>
            </div>
            
            <div class="flex w-full flex-col gap-3 mt-2">
              <button 
                @click="confirmLogout"
                class="w-full py-4 rounded-full font-black bg-red-500 text-white active:scale-95 transition-all shadow-xl shadow-red-500/20"
              >
                Sign Out
              </button>
              <button 
                @click="showLogoutConfirm = false"
                class="w-full py-4 rounded-full font-bold transition-all active:scale-95 border"
                style="background: transparent; border-color: var(--color-border); color: var(--color-text-primary);"
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Home, User, Calendar, BarChart2, LayoutDashboard, Building2, LogOut, Users } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth.js'

const showLogoutConfirm = ref(false)

const rolesJSON = localStorage.getItem('aura_user_roles')
let roles = []
try {
  roles = rolesJSON ? JSON.parse(rolesJSON) : []
} catch (e) {
  roles = []
}
const isSuperAdmin = (roles || []).some(r => r?.role?.name === 'super_admin' || r?.role?.name === 'superadmin')

const navItems = isSuperAdmin ? [
  { name: 'Dashboard',   route: '/super-admin',          icon: LayoutDashboard },
  { name: 'Campuses',    route: '/super-admin/campuses', icon: Building2 },
  { name: 'Profile',     route: '/dashboard/profile',    icon: User },
] : [
  { name: 'Home',      route: '/dashboard',            icon: Home },
  { name: 'Profile',   route: '/dashboard/profile',    icon: User },
  { name: 'Schedule',  route: '/dashboard/schedule',   icon: Calendar },
  { name: 'Analytics', route: '/dashboard/analytics',  icon: BarChart2 },
]

const router = useRouter()
const route = useRoute()

function isActive(path) {
  if (path === '/dashboard' || path === '/super-admin') {
    return route.path === path || route.path === path + '/'
  }
  return route.path.startsWith(path)
}

function navigate(path) {
  router.push(path)
}

const { logout } = useAuth()
function handleLogout() {
  showLogoutConfirm.value = true
}

function confirmLogout() {
  logout()
}
</script>
