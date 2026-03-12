<template>
  <!-- Desktop Left Sidebar -->
  <aside
    class="hidden md:flex fixed left-4 top-1/2 -translate-y-1/2 z-50 flex-col items-center bg-[#0A0A0A] shadow-2xl"
    style="width: 52px; border-radius: 32px; min-height: 380px;"
    aria-label="Desktop navigation"
  >
    <!-- Nav icons (top section) -->
    <div class="flex flex-col items-center gap-0 pt-5 pb-3 flex-1 w-full">
      <button
        v-for="item in navItems"
        :key="item.name"
        @click="navigate(item.route)"
        :aria-label="item.name"
        class="relative flex flex-col items-center justify-center w-full py-3.5 gap-1 transition-all duration-200"
        :class="isActive(item.route) ? '' : 'opacity-35 hover:opacity-65'"
      >
        <!-- Active glowing background -->
        <span
          v-if="isActive(item.route)"
          class="absolute w-12 h-12 rounded-full pointer-events-none"
          style="background: radial-gradient(circle, var(--color-primary) 0%, transparent 65%); opacity: 0.15; top: 50%; transform: translateY(-50%);"
        />

        <!-- Icon -->
        <component
          :is="item.icon"
          :size="19"
          :stroke-width="isActive(item.route) ? 2.2 : 1.6"
          :color="isActive(item.route) ? 'var(--color-primary)' : '#FFFFFF'"
          class="relative z-10 transition-all duration-200"
        />
        <!-- Active dot below icon -->
        <span
          class="w-1 h-1 rounded-full transition-all duration-200"
          :style="isActive(item.route)
            ? 'background: var(--color-primary); opacity: 1;'
            : 'background: transparent; opacity: 0;'"
        />
      </button>
    </div>

    <!-- Talk to Aura AI — standalone lime pill with its own border-radius, expands on click -->
    <div class="relative w-[40px] h-[74px] mx-2 mb-1.5 z-50">
      <div
        class="absolute top-0 left-0 flex flex-col overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] shadow-lg origin-left"
        :class="isChatExpanded ? 'w-[320px] h-[200px] rounded-[32px] cursor-default' : 'w-[40px] h-[74px] rounded-[26px] cursor-pointer hover:brightness-110 hover:scale-105 active:scale-95'"
        style="background: var(--color-primary);"
        @click="!isChatExpanded ? (isChatExpanded = true) : null"
      >
        <!-- COLLAPSED STATE (Icon + Text) -->
        <div 
          class="absolute inset-0 flex flex-col items-center justify-center gap-1 transition-opacity duration-300"
          :class="isChatExpanded ? 'opacity-0 pointer-events-none' : 'opacity-100'"
        >
          <img
            :src="activeAuraLogo"
            alt="Aura"
            class="w-6 h-6 object-contain opacity-90"
          />
          <span
            class="text-[8px] font-extrabold text-center leading-snug transition-colors duration-200"
            style="color: var(--color-banner-text);"
          >
            Talk to<br>Aura Ai
          </span>
        </div>

        <!-- EXPANDED STATE (Chat UI) -->
        <div 
          class="absolute inset-0 flex flex-col p-4 transition-opacity duration-300 delay-100"
          :class="isChatExpanded ? 'opacity-100' : 'opacity-0 pointer-events-none'"
          v-show="isChatExpanded"
        >
          <!-- Top row: Icon and Maximize -->
          <div class="flex items-start justify-between">
            <img
              :src="activeAuraLogo"
              alt="Aura"
              class="w-8 h-8 object-contain opacity-90 cursor-pointer transition-transform hover:scale-110"
              @click.stop="isChatExpanded = false"
            />
            <button class="p-1 hover:bg-black/10 rounded-full transition-colors">
              <Maximize2 :size="16" :color="'var(--color-banner-text)'" />
            </button>
          </div>

          <!-- Scrollable Chat bubbles -->
          <div class="flex-1 flex flex-col gap-3 overflow-y-auto pl-2 pr-2 pt-10 pb-2 scrollbar-hide">
            <template v-for="msg in chatMessages" :key="msg.id">
              <!-- AI Message -->
              <div 
                v-if="msg.sender === 'ai'" 
                class="bg-white rounded-full px-5 py-2.5 self-start shadow-sm border border-black/5 max-w-[85%]"
              >
                <span class="text-[13px] font-medium text-[var(--color-text-always-dark)] leading-snug">{{ msg.text }}</span>
              </div>
              
              <!-- User Message -->
              <div 
                v-else 
                class="bg-black/10 rounded-full px-5 py-2.5 self-end shadow-sm border border-white/10 max-w-[85%]"
              >
                <span class="text-[13px] font-medium leading-snug" style="color: var(--color-banner-text);">{{ msg.text }}</span>
              </div>
            </template>

            <!-- Loading indicator for AI -->
            <div v-if="isAiTyping" class="bg-white rounded-full px-5 py-3 self-start shadow-sm border border-black/5 max-w-[85%] flex gap-1 items-center h-[38px]">
              <div class="w-1.5 h-1.5 rounded-full bg-black/40 animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-1.5 h-1.5 rounded-full bg-black/40 animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-1.5 h-1.5 rounded-full bg-black/40 animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>

          <!-- Input field area -->
          <div class="mt-auto px-4 pb-2 w-[320px] max-w-full">
            <div 
              class="h-[42px] rounded-full border border-black/20 flex items-center px-4 justify-between bg-black/5"
              :style="{ borderColor: 'var(--color-banner-text)' }"
            >
              <input 
                type="text" 
                v-model="chatInput"
                class="bg-transparent outline-none text-[13px] w-full mr-2 placeholder-black/40 font-medium" 
                :style="{ color: 'var(--color-banner-text)' }"
                placeholder="Ask Aura anything..."
                @keyup.enter="handleSendMessage"
                :disabled="isAiTyping"
              />
              <button @click="handleSendMessage" :disabled="!chatInput.trim() || isAiTyping" class="cursor-pointer transition-opacity hover:opacity-100 disabled:opacity-50" :class="chatInput.trim() ? 'opacity-100' : 'opacity-60'">
                <Send :size="16" :color="'var(--color-banner-text)'" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

  </aside>

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
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Home, User, Calendar, BarChart2, Maximize2, Send, Building2, LayoutDashboard, LogOut, Users } from 'lucide-vue-next'
import { activeAuraLogo } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'

const isChatExpanded = ref(false)
const chatInput = ref('')
const isAiTyping = ref(false)
const showLogoutConfirm = ref(false)
const chatMessages = ref([
  { id: 1, sender: 'ai', text: 'Hi! I am Aura AI. How can I help you today?' }
])

const handleSendMessage = () => {
  if (!chatInput.value.trim() || isAiTyping.value) return
  
  // Add User message
  chatMessages.value.push({
    id: Date.now(),
    sender: 'user',
    text: chatInput.value.trim()
  })
  
  chatInput.value = ''
  isAiTyping.value = true
  
  // Simulate backend response delay
  setTimeout(() => {
    chatMessages.value.push({
      id: Date.now(),
      sender: 'ai',
      text: "I am ready and waiting for my backend brain! Once we connect the API, I'll help you with your university requests."
    })
    isAiTyping.value = false
  }, 1500)
}

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
const route  = useRoute()

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

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>
