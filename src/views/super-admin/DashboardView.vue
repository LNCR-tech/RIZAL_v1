<template>
  <div class="super-admin-dashboard-container">
    <div class="flex flex-col gap-6 px-4 md:px-10 pb-10">
      <!-- TopBar (Similar to student but with Super Admin context) -->
      <div class="flex items-center justify-between py-6">
        <!-- Hoverable Welcome Pill with Integrated Logout -->
        <div class="flex items-center gap-4 rounded-full px-5 py-2.5 shadow-sm border group cursor-pointer relative overflow-hidden transition-all duration-300 hover:pr-4" style="background: var(--color-card-bg); border-color: var(--color-border);">
          <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shrink-0" style="background: var(--color-primary);">
            SA
          </div>
          <div class="flex flex-col mr-4 group-hover:mr-10 transition-all duration-300">
            <span class="text-[11px] font-bold uppercase tracking-wider leading-none mb-1" style="color: var(--color-text-muted);">Welcome Back</span>
            <span class="text-[15px] font-extrabold leading-none whitespace-nowrap" style="color: var(--color-text-primary);">Super Admin</span>
          </div>
          
          <!-- Secret Logout Button (Reveals on Hover) -->
          <button 
            @click.stop="handleLogout"
            class="absolute right-0 top-0 bottom-0 px-5 bg-red-500 text-white translate-x-full group-hover:translate-x-0 transition-transform duration-300 flex items-center justify-center gap-2"
          >
            <LogOut :size="18" stroke-width="2.5" />
            <span class="text-[12px] font-black uppercase tracking-tighter">Exit</span>
          </button>
        </div>

        <div class="flex items-center gap-3">
          <button class="w-11 h-11 rounded-full shadow-sm border flex items-center justify-center transition-colors relative" style="background: var(--color-card-bg); border-color: var(--color-border);">
            <Bell :size="20" style="color: var(--color-text-secondary);" />
            <span class="absolute top-3 right-3 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
          </button>
          <button 
            @click="toggleDarkMode"
            class="w-11 h-11 rounded-full shadow-sm border flex items-center justify-center transition-colors"
            style="background: var(--color-card-bg); border-color: var(--color-border);"
          >
            <Moon :size="20" :class="isDarkMode ? 'text-[#6366F1]' : ''" :style="!isDarkMode ? 'color: var(--color-text-secondary)' : ''" />
          </button>
        </div>
      </div>

      <!-- Page Title -->
      <div>
        <h1 class="text-[32px] font-black tracking-tight" style="color: var(--color-text-primary);">Super Admin Dashboard</h1>
        <p class="font-medium -mt-1" style="color: var(--color-text-muted);">Manage global system operations and campus tenants.</p>
      </div>

      <!-- Search bar -->
      <div class="relative max-w-2xl">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search for campuses, admins, or settings..."
          class="w-full rounded-full px-7 py-4.5 text-[15px] font-medium pr-14 outline-none shadow-sm transition-all duration-150 focus:ring-4 focus:ring-[#6366F1]/10 border"
          style="background: var(--color-card-bg); color: var(--color-text-always-dark); border-color: var(--color-border);"
        />
        <Search
          :size="20"
          class="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none"
          style="color: var(--color-text-muted);"
        />
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div v-for="stat in stats" :key="stat.label" class="p-6 rounded-[32px] shadow-sm border flex flex-col gap-4" style="background: var(--color-card-bg); border-color: var(--color-border);">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center" :style="{ backgroundColor: stat.color + '15' }">
            <component :is="stat.icon" :size="24" :style="{ color: isDarkMode ? '#6366F1' : stat.color }" />
          </div>
          <div>
            <p class="text-[13px] font-bold uppercase tracking-widest" style="color: var(--color-text-muted);">{{ stat.label }}</p>
            <div class="flex items-end gap-2">
              <h3 class="text-3xl font-black leading-none" style="color: var(--color-text-primary);">{{ stat.value }}</h3>
              <span class="text-[12px] font-bold text-[#6366F1] mb-0.5" v-if="stat.trend">+{{ stat.trend }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Layout -->
      <div class="flex flex-col lg:flex-row gap-6">
        <!-- Campus Overview (Left) -->
        <div class="flex-1 flex flex-col gap-6">
          <div class="bg-black rounded-[40px] p-8 relative overflow-hidden group shadow-xl shadow-black/10">
            <!-- Background Pattern -->
            <div class="absolute right-0 top-0 h-full w-1/3 opacity-20 pointer-events-none group-hover:scale-110 transition-transform duration-700">
               <img src="/images/login-aura-logo.jpg" class="w-full h-full object-contain rotate-12 translate-x-1/4" alt="" />
            </div>
            
            <div class="relative z-10 flex flex-col gap-6">
               <div>
                 <span class="bg-white/10 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border border-white/20">Aura Super Admin</span>
                 <h2 class="text-4xl font-black text-white mt-4 leading-tight">Aura<br/>System</h2>
               </div>
               
               <div class="flex items-center gap-4">
                 <button @click="navigate('/super-admin/campuses')" class="bg-white text-black px-8 py-3.5 rounded-full text-[14px] font-black flex items-center gap-2 hover:bg-zinc-200 active:scale-95 transition-all">
                   System Management <ArrowRight :size="18" />
                 </button>
               </div>
            </div>
          </div>

          
        </div>

        <!-- Quick Actions & System Health (Right) -->
        <div class="w-full lg:w-[380px] flex flex-col gap-6">
          <!-- Quick Actions (Moved Up) -->
          <div class="rounded-[40px] p-8 shadow-sm border" style="background: var(--color-card-bg); border-color: var(--color-border);">
            <h3 class="text-xl font-black mb-6" style="color: var(--color-text-primary);">Quick Actions</h3>
            <div class="grid grid-cols-2 gap-4">
              <button 
                @click="showAddModal = true"
                class="flex flex-col items-center justify-center gap-3 p-6 rounded-[32px] hover:scale-105 transition-all group border border-transparent shadow-sm"
                style="background: var(--color-input-bg);"
              >
                <Plus :size="24" class="group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);" />
                <span class="text-[11px] font-black uppercase tracking-widest text-center group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);">New<br/>Campus</span>
              </button>
              <button 
                @click="navigate('/super-admin/campuses')"
                class="flex flex-col items-center justify-center gap-3 p-6 rounded-[32px] hover:scale-105 transition-all group border border-transparent shadow-sm"
                style="background: var(--color-input-bg);"
              >
                <Users :size="24" class="group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);" />
                <span class="text-[11px] font-black uppercase tracking-widest text-center group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);">Manage<br/>Admins</span>
              </button>
              <button class="flex flex-col items-center justify-center gap-3 p-6 rounded-[32px] hover:scale-105 transition-all group border border-transparent shadow-sm" style="background: var(--color-input-bg);">
                <FileText :size="24" class="group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);" />
                <span class="text-[11px] font-black uppercase tracking-widest text-center group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);">Billing<br/>History</span>
              </button>
              <button class="flex flex-col items-center justify-center gap-3 p-6 rounded-[32px] hover:scale-105 transition-all group border border-transparent shadow-sm" style="background: var(--color-input-bg);">
                <Settings :size="24" class="group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);" />
                <span class="text-[11px] font-black uppercase tracking-widest text-center group-hover:text-[#6366F1] transition-colors" style="color: var(--color-text-muted);">Global<br/>Config</span>
              </button>
            </div>
          </div>

          
        </div>
      </div>
    </div>

    <!-- Register Modal -->
    <Transition name="fade">
      <div v-if="showAddModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/85 backdrop-blur-md" @click="showAddModal = false"></div>
        <div class="rounded-[40px] w-full max-w-xl p-10 relative z-10 shadow-2xl transition-all duration-300 transform scale-100 border" style="background: var(--color-card-bg); border-color: var(--color-border);">
          <h2 class="text-2xl font-black mb-2" style="color: var(--color-text-primary);">Register New Campus</h2>
          <p class="font-bold mb-8" style="color: var(--color-text-muted);">Onboard a new university to the system.</p>
          
          <div class="flex flex-col gap-5">
            <div class="flex flex-col gap-2">
              <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Full University Name</label>
              <input v-model="newCampus.name" type="text" placeholder="e.g. Technological University" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Location</label>
              <input v-model="newCampus.location" type="text" placeholder="City, Country" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
            </div>
            <div class="flex flex-col gap-2">
               <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Subscription Plan</label>
               <select v-model="newCampus.plan" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);">
                 <option>Standard Plan</option>
                 <option>Advanced Plan</option>
                 <option>Enterprise Elite</option>
               </select>
            </div>
            
            <div class="h-px bg-black/5 my-2" style="background: var(--color-border);"></div>
            <p class="text-[11px] font-black uppercase tracking-widest" style="color: var(--color-text-muted);">Admin Credentials</p>

            <div class="flex flex-col gap-2">
              <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Name</label>
              <input v-model="newCampus.adminName" type="text" placeholder="Full Name" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Gmail</label>
              <input v-model="newCampus.adminEmail" type="email" placeholder="email@gmail.com" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Account Password</label>
              <input v-model="newCampus.adminPassword" type="password" placeholder="••••••••" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
            </div>
          </div>

          <div class="flex gap-4 mt-10">
            <button @click="showAddModal = false" class="flex-1 py-4 rounded-full font-bold transition-all" style="background: var(--color-input-bg); color: var(--color-text-primary);">Cancel</button>
            <button @click="handleRegister" class="flex-1 py-4 rounded-full font-black text-white hover:scale-105 transition-all shadow-lg shadow-[#6366F1]/20" style="background: var(--color-primary);">Register Campus</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Premium Logout Confirmation Modal -->
    <Transition name="fade">
      <div v-if="showLogoutConfirm" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Search, Bell, Moon, TrendingUp, Building2, Users, Calendar, 
  ArrowRight, ChevronRight, Activity, Globe, ShieldCheck,
  ExternalLink, Plus, FileText, Settings, LogOut, LayoutDashboard
} from 'lucide-vue-next'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { useAuth } from '@/composables/useAuth.js'
import { mockEvents } from '@/data/mockData.js'
import { useCampuses } from '@/composables/useCampuses.js'

const { campuses } = useCampuses()
const { logout } = useAuth()
const router = useRouter()

const searchQuery = ref('')
const showAddModal = ref(false)
const showLogoutConfirm = ref(false)

const newCampus = ref({
  name: '',
  location: '',
  plan: 'Standard Plan',
  adminName: '',
  adminEmail: '',
  adminPassword: ''
})

const services = [
  { name: 'API Server', status: 'Operational', uptime: 99.9 },
  { name: 'Database', status: 'Operational', uptime: 100 },
  { name: 'Auth Service', status: 'Operational', uptime: 99.8 },
  { name: 'Asset Delivery', status: 'Slow', uptime: 96.5 }
]

const stats = computed(() => {
  const currentCampuses = (campuses.value || [])
  const totalStudents = currentCampuses.reduce((sum, c) => sum + (c.students || 0), 0)
  const formattedStudents = totalStudents.toLocaleString()
  const avgUptime = (services.reduce((sum, s) => sum + s.uptime, 0) / services.length).toFixed(1)

  return [
    { label: 'Total Campuses', value: currentCampuses.length.toString(), icon: Building2, color: '#000000', trend: 8 },
    { label: 'Active Students', value: formattedStudents, icon: Users, color: '#000000', trend: 12 },
    { label: 'Global Events', value: (mockEvents || []).length.toString(), icon: Calendar, color: '#000000', trend: 5 },
    { label: 'System Health', value: avgUptime + '%', icon: Activity, color: '#000000' }
  ]
})

const activities = ref([
  { id: 1, text: 'New campus registered: Bulacan State University', time: '2 hours ago', color: '#000000' },
  { id: 2, text: 'Subscription updated for JRMSU', time: '5 hours ago', color: '#000000' },
  { id: 3, text: 'System backup completed successfully', time: '12 hours ago', color: '#000000' },
  { id: 4, text: 'Slow response time detected in API node 2', time: '1 day ago', color: '#000000' }
])

function navigate(path) {
  router.push(path)
}

function handleLogout() {
  showLogoutConfirm.value = true
}

function confirmLogout() {
  logout()
}

function manageDashboard(campus) {
  localStorage.setItem('aura_impersonate_school_id', campus.id)
  localStorage.setItem('aura_impersonate_school_name', campus.name)
  localStorage.setItem('aura_impersonate_school_logo', campus.logo)
  window.location.href = '/dashboard'
}


function handleRegister() {
  if (!newCampus.value.name || !newCampus.value.location) {
    alert('Please fill in all fields')
    return
  }
  
  const { addCampus } = useCampuses()
  addCampus({
    name: newCampus.value.name,
    location: newCampus.value.location,
    logo: '/src/data/jrmsu_icon.png',
    plan: newCampus.value.plan.replace(' Plan', ''),
    admin: {
      name: newCampus.value.adminName || 'Pending',
      email: newCampus.value.adminEmail || 'TBD',
      password: newCampus.value.adminPassword || 'admin123'
    }
  })

  activities.value.unshift({
    id: Date.now(),
    text: `New campus registered: ${newCampus.value.name}`,
    time: 'Just now',
    color: '#000000'
  })
  
  // Reset and close
  newCampus.value = { name: '', location: '', plan: 'Standard Plan', adminName: '', adminEmail: '', adminPassword: '' }
  showAddModal.value = false
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
