<script setup>
import { ref, computed, onMounted } from 'vue';
import { Calendar, MapPin, Clock, Search, Users, Filter } from 'lucide-vue-next';
import { getStudentEvents, getCurrentUser } from '../../services/api.js';

const isLoading = ref(true);
const events = ref([]);
const searchQuery = ref('');
const filterStatus = ref('All');

// Get current logged-in user's college
const currentUser = getCurrentUser();
const studentCollege = currentUser?.college || 'College of Engineering';

onMounted(async () => {
  try {
    const data = await getStudentEvents(studentCollege);
    events.value = data;
  } catch (err) {
    console.error('Failed to load events:', err);
  } finally {
    isLoading.value = false;
  }
});

const filteredEvents = computed(() => {
  return events.value.filter(e => {
    const matchSearch = e.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                        e.location.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchStatus = filterStatus.value === 'All' || e.status === filterStatus.value;
    return matchSearch && matchStatus;
  });
});

const upcomingEvents = computed(() => events.value.filter(e => e.status === 'Upcoming'));
const completedEvents = computed(() => events.value.filter(e => e.status === 'Completed'));

const getStatusBadge = (status) => {
  switch (status) {
    case 'Upcoming': return 'badge-blue';
    case 'Completed': return 'badge-green';
    case 'Planning': return 'badge-amber';
    case 'Cancelled': return 'badge-red';
    default: return 'badge-gray';
  }
};

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
};

const getEventTypeLabel = (event) => {
  return event.college ? event.college.replace('College of ', '') : 'Campus-Wide';
};
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Events</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">Your college events & campus-wide activities</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- Stat Summary -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="stat-card">
          <div class="stat-icon bg-gradient-to-br from-blue-500 to-cyan-400">
            <Calendar class="w-5 h-5 text-white" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ events.length }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Total Events</p>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-gradient-to-br from-emerald-500 to-teal-400">
            <Clock class="w-5 h-5 text-white" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ upcomingEvents.length }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Upcoming</p>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon bg-gradient-to-br from-purple-500 to-violet-400">
            <Users class="w-5 h-5 text-white" />
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ completedEvents.length }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Completed</p>
          </div>
        </div>
      </div>

      <!-- Search & Filter -->
      <div class="glass-card p-4 flex flex-col md:flex-row gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" type="text" placeholder="Search events..." class="form-input pl-10" />
        </div>
        <select v-model="filterStatus" class="form-input w-full md:w-44">
          <option value="All">All Status</option>
          <option value="Upcoming">Upcoming</option>
          <option value="Planning">Planning</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </div>

      <!-- Events Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="event in filteredEvents"
          :key="event.id"
          class="glass-card overflow-hidden hover:ring-2 hover:ring-brand-500/30 transition-all duration-300 group"
        >
          <!-- Colored top accent -->
          <div :class="[
            'h-1',
            event.status === 'Upcoming' ? 'bg-gradient-to-r from-blue-500 to-cyan-400' :
            event.status === 'Completed' ? 'bg-gradient-to-r from-emerald-500 to-teal-400' :
            event.status === 'Planning' ? 'bg-gradient-to-r from-amber-500 to-orange-400' :
            'bg-gradient-to-r from-red-500 to-pink-400'
          ]"></div>

          <div class="p-5">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-900 dark:text-white text-sm group-hover:text-brand-500 dark:group-hover:text-brand-400 transition-colors">
                  {{ event.name }}
                </h3>
                <p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{{ getEventTypeLabel(event) }}</p>
              </div>
              <span :class="['badge shrink-0', getStatusBadge(event.status)]">{{ event.status }}</span>
            </div>

            <div class="mt-4 space-y-2">
              <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Calendar class="w-4 h-4 text-gray-400 shrink-0" />
                <span>{{ formatDate(event.date) }}</span>
              </div>
              <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <Clock class="w-4 h-4 text-gray-400 shrink-0" />
                <span>{{ event.time }}</span>
              </div>
              <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <MapPin class="w-4 h-4 text-gray-400 shrink-0" />
                <span>{{ event.location }}</span>
              </div>
            </div>

            <div v-if="event.attendees > 0" class="mt-4 pt-3 border-t border-gray-100 dark:border-white/[0.06]">
              <div class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                <Users class="w-3.5 h-3.5" />
                <span><span class="font-semibold text-gray-700 dark:text-gray-300">{{ event.attendees.toLocaleString() }}</span> attendees</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredEvents.length === 0" class="glass-card p-12 text-center">
        <Calendar class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
        <p class="text-gray-500 dark:text-gray-400 font-medium">No events found</p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Try adjusting your search or filter</p>
      </div>
    </template>
  </div>
</template>
