<script setup>
import { ref, computed, onMounted } from 'vue';
import { Search, Shield, Users, Trash2, Eye, Filter, X } from 'lucide-vue-next';
// ⬇️ MOCK DATA: imported from API service
// 🔴 BACKEND: see src/services/api.js → getUsers()
import { getUsers, deleteUser } from '../../services/api.js';

const searchQuery = ref('');
const filterStatus = ref('All');
const filterRole = ref('All');
const isLoading = ref(true);
const isDeletingId = ref(null);

const viewUser = ref(null); // Holds the currently selected user for viewing

// ⬇️ MOCK DATA: loaded from API service on mount
// 🔴 BACKEND: will be populated by GET /api/users
const users = ref([]);

onMounted(async () => {
  try {
    // 🔴 BACKEND: Replace getUsers() body in services/api.js with fetch('/api/users')
    const allUsers = await getUsers();
    // Map to display format
    users.value = allUsers.map(u => ({
      id: u.studentId || u.id,
      backendId: u.backendId || u.id,
      name: u.name,
      email: u.email,
      college: u.college,
      program: u.program || '-',
      status: u.status,
      role: u.role.charAt(0).toUpperCase() + u.role.slice(1), // capitalize
      sgAssigned: getSgForCollege(u.college, allUsers),
    }));
  } catch (err) {
    console.error('Failed to load users:', err);
  } finally {
    isLoading.value = false;
  }
});

// Helper: find SG officer for a given college
function getSgForCollege(college, allUsers) {
  const sg = allUsers.find(u => u.role === 'sg' && u.college === college);
  return sg ? sg.name : '-';
}

const filteredUsers = computed(() => {
  return users.value.filter(user => {
    const matchSearch = user.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                        user.id.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchStatus = filterStatus.value === 'All' || user.status === filterStatus.value;
    const matchRole = filterRole.value === 'All' || user.role === filterRole.value;
    return matchSearch && matchStatus && matchRole;
  });
});

const getStatusBadge = (status) => {
  switch (status) {
    case 'Active': return 'badge-green';
    case 'Pending': return 'badge-amber';
    case 'Inactive': return 'badge-red';
    default: return 'badge-gray';
  }
};

const getRoleBadge = (role) => {
  switch (role) {
    case 'Admin': return 'badge-red';
    case 'Sg': return 'badge-blue';
    default: return 'badge-gray';
  }
};

const handleDelete = async (user) => {
  if (confirm(`Are you sure you want to delete the account for ${user.name} (${user.email})?\\nThis action cannot be undone.`)) {
    try {
      isDeletingId.value = user.id;
      await deleteUser(user.backendId || user.id);
      
      // Remove user locally instantly
      users.value = users.value.filter(u => u.id !== user.id);
      alert(`Account for ${user.name} successfully deleted.`);
    } catch (err) {
      console.error('Failed to delete account:', err);
      alert(`Wait, deletion failed:\\n${err.message}`);
    } finally {
      isDeletingId.value = null;
    }
  }
};
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Students & Accounts</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ users.length }} total accounts across all colleges</p>
      </div>
      <button class="btn-primary flex items-center gap-2">
        <Filter class="w-4 h-4" /> Export Data
      </button>
    </div>

    <!-- Filters -->
    <div class="glass-card p-4 flex flex-col md:flex-row gap-3">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <input v-model="searchQuery" type="text" placeholder="Search by name or ID..." class="form-input pl-10" />
      </div>
      <select v-model="filterRole" class="form-input w-full md:w-36">
        <option value="All">All Roles</option>
        <option value="Student">Student</option>
        <option value="Sg">SG</option>
        <option value="Admin">Admin</option>
      </select>
      <select v-model="filterStatus" class="form-input w-full md:w-36">
        <option value="All">All Status</option>
        <option value="Active">Active</option>
        <option value="Pending">Pending</option>
        <option value="Inactive">Inactive</option>
      </select>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <!-- Table -->
    <div v-else class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name / Email</th>
              <th>ID</th>
              <th>College</th>
              <th>Program</th>
              <th>Role</th>
              <th>SG Officer</th>
              <th>Status</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.id">
              <td>
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500/20 to-purple-500/20 flex items-center justify-center text-brand-600 dark:text-brand-400 font-bold text-xs shrink-0">
                    {{ user.name.charAt(0) }}
                  </div>
                  <div>
                    <div class="font-medium text-gray-900 dark:text-white text-sm">{{ user.name }}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{{ user.email }}</div>
                  </div>
                </div>
              </td>
              <td class="font-mono text-xs text-gray-600 dark:text-gray-400">{{ user.id }}</td>
              <td class="text-sm text-gray-600 dark:text-gray-400">{{ user.college }}</td>
              <td class="text-sm text-gray-600 dark:text-gray-400">{{ user.program }}</td>
              <td>
                <span :class="['badge', getRoleBadge(user.role)]">
                  <Shield v-if="user.role === 'Admin'" class="w-3 h-3" />
                  <Users v-if="user.role === 'Sg'" class="w-3 h-3" />
                  {{ user.role }}
                </span>
              </td>
              <td class="text-sm text-gray-600 dark:text-gray-400">{{ user.sgAssigned }}</td>
              <td>
                <span :class="['badge', getStatusBadge(user.status)]">{{ user.status }}</span>
              </td>
              <td class="text-right">
                <div class="flex items-center justify-end gap-1">
                  <button @click="viewUser = user" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/[0.06] text-gray-500 transition" title="View Details"><Eye class="w-4 h-4" /></button>
                  <button 
                    @click="handleDelete(user)"
                    :disabled="isDeletingId === user.id"
                    class="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 text-gray-500 hover:text-red-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete Account"
                  >
                    <div v-if="isDeletingId === user.id" class="w-4 h-4 border-2 border-red-500/30 border-t-red-500 rounded-full animate-spin"></div>
                    <Trash2 v-else class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="filteredUsers.length === 0">
              <td colspan="8" class="text-center py-8 text-gray-400">No users found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- View User Modal Overlay -->
    <Transition name="fade">
      <div v-if="viewUser" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/50 backdrop-blur-sm">
        <div class="glass-card w-full max-w-md overflow-hidden relative" @click.stop>
          
          <!-- Header -->
          <div class="p-6 pb-0 flex items-start justify-between">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Account Details</h2>
            <button @click="viewUser = null" class="p-2 -mr-2 text-gray-400 hover:text-gray-600 dark:hover:text-white transition rounded-full hover:bg-gray-100 dark:hover:bg-white/10">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-6 space-y-5">
            <div class="flex items-center gap-4">
              <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-500/20 to-purple-500/20 flex items-center justify-center text-brand-600 dark:text-brand-400 font-bold text-2xl shrink-0">
                {{ viewUser.name.charAt(0) }}
              </div>
              <div>
                <h3 class="text-lg font-bold text-gray-900 dark:text-white">{{ viewUser.name }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ viewUser.email }}</p>
                <div class="mt-2 flex gap-2">
                  <span :class="['badge', getRoleBadge(viewUser.role)]">
                    <Shield v-if="viewUser.role === 'Admin'" class="w-3 h-3" />
                    <Users v-if="viewUser.role === 'Sg'" class="w-3 h-3" />
                    {{ viewUser.role }}
                  </span>
                  <span :class="['badge', getStatusBadge(viewUser.status)]">{{ viewUser.status }}</span>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100 dark:border-white/5">
              <div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">ID Number</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ viewUser.id }}</p>
              </div>
              <div v-if="viewUser.backendId">
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Database Key</p>
                <p class="font-medium font-mono text-gray-600 dark:text-gray-300 text-xs">{{ viewUser.backendId }}</p>
              </div>
              <div class="col-span-2" v-if="viewUser.college">
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">College / Department</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ viewUser.college }}</p>
              </div>
              <div class="col-span-2" v-if="viewUser.program && viewUser.program !== '-'">
                <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Program</p>
                <p class="font-medium text-gray-900 dark:text-white">{{ viewUser.program }}</p>
              </div>
            </div>
          </div>
          
          <!-- Footer -->
          <div class="p-6 pt-4 bg-gray-50/50 dark:bg-black/20 flex justify-end">
             <button @click="viewUser = null" class="btn-primary py-2 px-6">Close</button>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
