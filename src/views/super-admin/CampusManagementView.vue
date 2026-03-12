<template>
  <div class="campus-management-container">
    <div class="flex flex-col gap-6 px-4 md:px-10 pb-10">
      <!-- Top Bar with Search and Action -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mt-6">
        <div>
          <h1 class="text-[32px] font-black" style="color: var(--color-text-primary);">Campus Management</h1>
          <p class="font-bold uppercase tracking-wider text-[12px] -mt-1" style="color: var(--color-text-muted);">Manage all university tenants and subscriptions</p>
        </div>
        <div class="flex items-center gap-4">
          <button 
            @click="showAddModal = true"
            class="bg-black text-[#6366F1] px-8 py-4 rounded-full font-black text-[14px] flex items-center justify-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-xl shadow-black/10"
          >
            <Plus :size="18" /> Register New Campus
          </button>
          
          <div class="flex items-center gap-2">
            <button class="w-12 h-12 rounded-full shadow-sm border flex items-center justify-center transition-colors relative" style="background: var(--color-card-bg); border-color: var(--color-border);">
              <Bell :size="20" style="color: var(--color-text-secondary);" />
              <span class="absolute top-3.5 right-3.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
            </button>
            <button 
              @click="toggleDarkMode"
              class="w-12 h-12 rounded-full shadow-sm border flex items-center justify-center transition-colors"
              style="background: var(--color-card-bg); border-color: var(--color-border);"
            >
              <Moon :size="20" :class="isDarkMode ? 'text-[#6366F1]' : ''" :style="!isDarkMode ? 'color: var(--color-text-secondary)' : ''" />
            </button>
          </div>
        </div>
      </div>

      <!-- Filters and Search -->
      <div class="flex flex-col lg:flex-row gap-4 items-center p-3 rounded-[32px] shadow-sm border" style="background: var(--color-card-bg); border-color: var(--color-border);">
        <div class="relative flex-1 w-full">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search campuses by name, code, or location..."
            class="w-full rounded-full px-6 py-3.5 text-[15px] font-bold outline-none transition-all pl-14"
            style="background: var(--color-input-bg); color: var(--color-text-always-dark);"
          />
          <Search :size="18" class="absolute left-6 top-1/2 -translate-y-1/2" style="color: var(--color-text-muted);" />
        </div>
        
        <div class="flex gap-2 w-full lg:w-auto">
          <select v-model="filterStatus" class="rounded-full px-6 py-3.5 font-bold text-[14px] outline-none border-none flex-1 lg:flex-none" style="background: var(--color-input-bg); color: var(--color-text-always-dark);">
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button class="p-3.5 rounded-full transition-colors" style="background: var(--color-input-bg);">
            <Filter :size="20" style="color: var(--color-text-secondary);" />
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="campus in filteredCampuses" :key="campus.id" 
          class="rounded-[40px] p-8 border shadow-sm hover:shadow-xl transition-all group flex flex-col gap-6"
          style="background: var(--color-card-bg); border-color: var(--color-border);"
        >
          <div class="flex justify-between items-start">
            <div class="w-16 h-16 rounded-3xl flex items-center justify-center p-3" style="background: var(--color-input-bg);">
               <img :src="campus.logo" class="w-full h-full object-contain" :alt="campus.name" />
            </div>
            <div :class="campus.status === 'Active' ? 'bg-indigo-500/10 text-[#6366F1]' : 'bg-red-500/10 text-red-500'" class="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest">
              {{ campus.status }}
            </div>
          </div>

          <div>
            <h3 class="text-xl font-black leading-tight group-hover:text-[#6366F1] transition-colors line-clamp-2" style="color: var(--color-text-primary);">
              {{ campus.name }}
            </h3>
            <p class="font-bold text-[13px] mt-1 flex items-center gap-1.5" style="color: var(--color-text-muted);">
              <MapPin :size="14" /> {{ campus.location }}
            </p>
          </div>

          <div class="grid grid-cols-2 gap-4 py-6 border-y" style="border-color: var(--color-border);">
             <div>
               <span class="text-[10px] font-bold uppercase tracking-widest block mb-1" style="color: var(--color-text-muted);">Students</span>
               <span class="text-[16px] font-black" style="color: var(--color-text-primary);">{{ campus.students.toLocaleString() }}</span>
             </div>
             <div>
               <span class="text-[10px] font-bold uppercase tracking-widest block mb-1" style="color: var(--color-text-muted);">Staff</span>
               <span class="text-[16px] font-black" style="color: var(--color-text-primary);">{{ campus.staff.toLocaleString() }}</span>
             </div>
          </div>

          <div v-if="campus.admin" class="flex flex-col gap-1">
            <span class="text-[10px] font-black uppercase tracking-widest" style="color: var(--color-text-muted);">Primary Admin</span>
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black" style="background: var(--color-input-bg); color: var(--color-text-secondary);">
                {{ campus.admin.name.charAt(0) }}
              </div>
              <div>
                <p class="text-[12px] font-black leading-none" style="color: var(--color-text-primary);">{{ campus.admin.name }}</p>
                <p class="text-[10px] font-bold" style="color: var(--color-text-muted);">{{ campus.admin.email }}</p>
              </div>
            </div>
          </div>

          <div class="flex flex-col gap-3 mt-auto">
            <div class="flex justify-between items-center px-5 py-4 rounded-3xl" style="background: var(--color-input-bg);">
               <div class="flex flex-col">
                 <span class="text-[9px] font-bold uppercase tracking-widest" style="color: var(--color-text-muted);">Subscription</span>
                 <span class="text-[13px] font-black" style="color: var(--color-text-primary);">{{ campus.plan }} Plan</span>
               </div>
               <CreditCard :size="18" style="color: var(--color-text-muted);" />
            </div>
            
            <div class="flex gap-2">
              <button 
                @click="openEditModal(campus)"
                class="flex-1 py-4 rounded-full text-[13px] font-bold hover:scale-105 transition-all flex items-center justify-center gap-2"
                style="background: var(--color-input-bg); color: var(--color-text-primary);"
              >
                <Pencil :size="14" /> Edit
              </button>
              <button 
                @click="manageDashboard(campus)"
                class="flex-1 bg-[#6366F1] text-white py-4 rounded-full text-[13px] font-black hover:scale-105 transition-all shadow-lg shadow-[#6366F1]/20 flex items-center justify-center gap-2"
                title="Inspect Campus Dashboard"
              >
                <LayoutDashboard :size="14" /> Inspect
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
        <div class="rounded-[40px] w-full max-w-4xl p-10 relative z-10 shadow-2xl transition-all duration-300 transform scale-100 border" style="background: var(--color-card-bg); border-color: var(--color-border);">
          <div class="flex justify-between items-start mb-8">
            <div>
              <h2 class="text-3xl font-black mb-2" style="color: var(--color-text-primary);">Register New Campus</h2>
              <p class="font-bold" style="color: var(--color-text-muted);">Onboard a new university to the system.</p>
            </div>
            <button @click="showAddModal = false" class="w-12 h-12 rounded-full flex items-center justify-center transition-colors" style="background: var(--color-input-bg);">
              <Plus class="rotate-45" :size="24" style="color: var(--color-text-primary);" />
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <!-- University Information -->
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-2xl bg-[#6366F1]/10 flex items-center justify-center">
                  <Building2 :size="20" style="color: var(--color-primary);" />
                </div>
                <h3 class="text-lg font-black uppercase tracking-wider" style="color: var(--color-text-primary);">University Details</h3>
              </div>

              <div class="flex flex-col gap-5">
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Full University Name</label>
                  <input v-model="newCampus.name" type="text" placeholder="e.g. Technological University" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Location</label>
                  <input v-model="newCampus.location" type="text" placeholder="City, Country" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                </div>
                <div class="flex flex-col gap-2">
                   <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Logo URL</label>
                   <div class="flex gap-3">
                     <div class="w-14 h-14 rounded-2xl flex items-center justify-center p-2 shrink-0 overflow-hidden border" style="background: var(--color-input-bg); border-color: var(--color-border);">
                       <img v-if="newCampus.logo" :src="newCampus.logo" class="w-full h-full object-contain" />
                       <Building2 v-else :size="20" style="color: var(--color-text-muted);" />
                     </div>
                     <input v-model="newCampus.logo" type="text" placeholder="https://logo.png" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                   </div>
                </div>
                <div class="flex flex-col gap-2">
                   <label class="text-[12px] font-black text-black/60 uppercase tracking-widest ml-4">Subscription Plan</label>
                   <select v-model="newCampus.plan" class="w-full bg-black/5 border-none rounded-full px-6 py-4 font-bold outline-none focus:bg-white focus:ring-4 focus:ring-black/5 transition-all">
                     <option>Standard Plan</option>
                     <option>Advanced Plan</option>
                     <option>Enterprise Elite</option>
                   </select>
                </div>
              </div>
            </div>

            <!-- Administrator Information -->
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-2xl flex items-center justify-center" style="background: var(--color-input-bg);">
                  <LayoutDashboard :size="20" style="color: var(--color-text-muted);" />
                </div>
                <h3 class="text-lg font-black uppercase tracking-wider" style="color: var(--color-text-primary);">Admin Access</h3>
              </div>

              <div class="p-8 rounded-[40px] flex flex-col gap-5 border" style="background: var(--color-input-bg); border-color: var(--color-border);">
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Full Name</label>
                  <input v-model="newCampus.adminName" type="text" placeholder="e.g. Ricardo Garcia" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all border" style="background: var(--color-card-bg); color: var(--color-text-always-dark); border-color: var(--color-border);" />
                </div>

                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Gmail</label>
                  <input v-model="newCampus.adminEmail" type="email" placeholder="admin@gmail.com" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all border" style="background: var(--color-card-bg); color: var(--color-text-always-dark); border-color: var(--color-border);" />
                </div>

                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Account Password</label>
                  <input v-model="newCampus.adminPassword" type="password" placeholder="••••••••" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all border" style="background: var(--color-card-bg); color: var(--color-text-always-dark); border-color: var(--color-border);" />
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-4 mt-12 pt-8 border-t" style="border-color: var(--color-border);">
            <button @click="showAddModal = false" class="px-10 py-4 rounded-full font-bold transition-all" style="background: var(--color-input-bg); color: var(--color-text-primary);">Cancel</button>
            <button @click="handleRegister" class="px-12 py-4 rounded-full font-black bg-[#6366F1] text-white hover:scale-105 transition-all shadow-xl shadow-[#6366F1]/20">Register Campus</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit Modal -->
    <Transition name="fade">
      <div v-if="showEditModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/85 backdrop-blur-md" @click="showEditModal = false"></div>
        <div class="rounded-[40px] w-full max-w-4xl p-10 relative z-10 shadow-2xl transition-all duration-300 transform scale-100 border" style="background: var(--color-card-bg); border-color: var(--color-border);">
          <div class="flex justify-between items-start mb-8">
            <div>
              <h2 class="text-3xl font-black mb-2" style="color: var(--color-text-primary);">Edit Campus Details</h2>
              <p class="font-bold" style="color: var(--color-text-muted);">Update the information for this university.</p>
            </div>
            <button @click="showEditModal = false" class="w-12 h-12 rounded-full flex items-center justify-center transition-colors" style="background: var(--color-input-bg);">
              <Plus class="rotate-45" :size="24" style="color: var(--color-text-primary);" />
            </button>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
            <!-- University Information -->
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-2xl bg-[#6366F1]/10 flex items-center justify-center">
                  <Building2 :size="20" style="color: var(--color-primary);" />
                </div>
                <h3 class="text-lg font-black uppercase tracking-wider" style="color: var(--color-text-primary);">University Details</h3>
              </div>

              <div class="flex flex-col gap-5">
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Full University Name</label>
                  <input v-model="editForm.name" type="text" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Location</label>
                  <input v-model="editForm.location" type="text" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Logo URL</label>
                  <div class="flex gap-3">
                    <div class="w-14 h-14 rounded-2xl flex items-center justify-center p-2 shrink-0 overflow-hidden border" style="background: var(--color-input-bg); border-color: var(--color-border);">
                      <img v-if="editForm.logo" :src="editForm.logo" class="w-full h-full object-contain" />
                      <Building2 v-else :size="20" style="color: var(--color-text-muted);" />
                    </div>
                    <input v-model="editForm.logo" type="text" placeholder="https://logo.png" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="flex flex-col gap-2">
                    <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Subscription Plan</label>
                    <select v-model="editForm.plan" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);">
                      <option>Standard</option>
                      <option>Advanced</option>
                      <option>Enterprise Elite</option>
                    </select>
                  </div>
                  <div class="flex flex-col gap-2">
                    <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Status</label>
                    <select v-model="editForm.status" class="w-full border-none rounded-full px-6 py-4 font-bold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-input-bg); color: var(--color-text-always-dark);">
                      <option>Active</option>
                      <option>Inactive</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <!-- Administrator Information -->
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-2xl flex items-center justify-center font-black" style="background: var(--color-input-bg);">
                  <LayoutDashboard :size="20" style="color: var(--color-text-muted);" />
                </div>
                <h3 class="text-lg font-black uppercase tracking-wider" style="color: var(--color-text-primary);">Admin Access</h3>
              </div>

              <div class="p-8 rounded-[40px] flex flex-col gap-5 border" style="background: var(--color-input-bg); border-color: var(--color-border);">
                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Full Name</label>
                  <input v-model="editForm.adminName" type="text" class="w-full border-none rounded-full px-6 py-4 font-extrabold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-card-bg); color: var(--color-text-always-dark);" />
                </div>

                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Email</label>
                  <input v-model="editForm.adminEmail" type="email" class="w-full border-none rounded-full px-6 py-4 font-extrabold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all" style="background: var(--color-card-bg); color: var(--color-text-always-dark);" />
                </div>

                <div class="flex flex-col gap-2">
                  <label class="text-[12px] font-black uppercase tracking-widest ml-4" style="color: var(--color-text-muted);">Admin Password</label>
                  <input v-model="editForm.adminPassword" type="password" placeholder="Change administrator password" class="w-full border-none rounded-full px-6 py-4 font-extrabold outline-none focus:ring-4 focus:ring-[#6366F1]/20 transition-all font-black" style="background: var(--color-card-bg); color: var(--color-text-always-dark);" />
                  <p class="text-[10px] font-bold ml-4 mt-1 italic" style="color: var(--color-text-muted);">Leave empty to keep current password</p>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end gap-4 mt-12 pt-8 border-t" style="border-color: var(--color-border);">
            <button @click="showEditModal = false" class="px-10 py-4 rounded-full font-bold transition-all" style="background: var(--color-input-bg); color: var(--color-text-primary);">Cancel</button>
            <button @click="handleUpdate" class="px-12 py-4 rounded-full font-black bg-[#6366F1] text-white hover:scale-105 transition-all shadow-xl shadow-[#6366F1]/20">Save General Changes</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, Filter, MoreHorizontal, MapPin, CreditCard, ChevronRight, Pencil, Building2, LayoutDashboard, Bell, Moon } from 'lucide-vue-next'
import { isDarkMode, toggleDarkMode } from '@/config/theme.js'
import { useCampuses } from '@/composables/useCampuses.js'

const { campuses, addCampus, updateCampus } = useCampuses()
const router = useRouter()

const searchQuery = ref('')
const filterStatus = ref('all')
const showAddModal = ref(false)
const showEditModal = ref(false)
const newCampus = ref({
    name: '',
    location: '',
    logo: '',
    plan: 'Standard Plan',
    adminName: '',
    adminEmail: '',
    adminPassword: ''
})

const editForm = ref({
    name: '',
    location: '',
    logo: '',
    plan: '',
    status: '',
    adminName: '',
    adminEmail: '',
    adminPassword: ''
})

const editingCampusId = ref(null)

// Managed by useCampuses composable


const filteredCampuses = computed(() => {
    return campuses.value.filter(c => {
        const matchesSearch = (c.name?.toLowerCase() || '').includes(searchQuery.value.toLowerCase()) || 
                             (c.location?.toLowerCase() || '').includes(searchQuery.value.toLowerCase())
        const matchesFilter = filterStatus.value === 'all' || c.status?.toLowerCase() === filterStatus.value
        return matchesSearch && matchesFilter
    })
})

function handleRegister() {
    if (!newCampus.value.name || !newCampus.value.location) {
        alert('Please fill in all fields')
        return
    }

    addCampus({
        name: newCampus.value.name,
        location: newCampus.value.location,
        logo: newCampus.value.logo || '/src/data/jrmsu_icon.png',
        plan: newCampus.value.plan.replace(' Plan', ''),
        admin: {
            name: newCampus.value.adminName || 'Pending Admin',
            email: newCampus.value.adminEmail || 'TBD',
            password: newCampus.value.adminPassword || 'admin123'
        }
    })

    // Reset and close
    newCampus.value = { name: '', location: '', logo: '', plan: 'Standard Plan', adminName: '', adminEmail: '', adminPassword: '' }
    showAddModal.value = false
}

function openEditModal(campus) {
    editingCampusId.value = campus.id
    editForm.value = {
        name: campus.name,
        location: campus.location,
        logo: campus.logo,
        plan: campus.plan,
        status: campus.status,
        adminName: campus.admin?.name || '',
        adminEmail: campus.admin?.email || '',
        adminPassword: campus.admin?.password || 'admin123'
    }
    showEditModal.value = true
}

function handleUpdate() {
    updateCampus(editingCampusId.value, {
        name: editForm.value.name,
        location: editForm.value.location,
        logo: editForm.value.logo,
        plan: editForm.value.plan,
        status: editForm.value.status,
        admin: {
            name: editForm.value.adminName,
            email: editForm.value.adminEmail,
            password: editForm.value.adminPassword
        }
    })
    showEditModal.value = false
}

function manageDashboard(campus) {
    localStorage.setItem('aura_impersonate_school_id', campus.id)
    localStorage.setItem('aura_impersonate_school_name', campus.name)
    localStorage.setItem('aura_impersonate_school_logo', campus.logo)
    router.push('/dashboard')
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
