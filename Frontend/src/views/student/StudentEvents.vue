<script setup>
import { ref, computed, onMounted } from 'vue';
import { Calendar, MapPin, Clock, Search, Users, ChevronLeft, ChevronRight } from 'lucide-vue-next';
import { getStudentEvents, getCurrentUser } from '../../services/api.js';

const isLoading = ref(true);
const events = ref([]);
const searchQuery = ref('');
const filterStatus = ref('All');
const selectedDate = ref(null);

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
    const matchDate = !selectedDate.value || e.date === selectedDate.value;
    return matchSearch && matchStatus && matchDate;
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

// --- MINI CALENDAR LOGIC ---
const calendarDate = ref(new Date());

const currentMonthName = computed(() => {
  return calendarDate.value.toLocaleString('default', { month: 'long' });
});

const currentYear = computed(() => calendarDate.value.getFullYear());

// Helper to check if a specific date has any events
const hasEventsOnDate = (year, month, day) => {
  const formattedMonth = String(month + 1).padStart(2, '0');
  const formattedDay = String(day).padStart(2, '0');
  const dateStr = `${year}-${formattedMonth}-${formattedDay}`;
  
  // Important: Check against the master `events` list, not `filteredEvents`, 
  // so the dots don't disappear when a date is selected.
  return events.value.some(e => e.date === dateStr);
};

const calendarDays = computed(() => {
  const year = calendarDate.value.getFullYear();
  const month = calendarDate.value.getMonth();
  
  const firstDayOfMonth = new Date(year, month, 1).getDay(); // 0 is Sunday
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, month, 0).getDate();
  
  const days = [];
  
  // Previous month padding
  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    days.push({
      date: daysInPrevMonth - i,
      isCurrentMonth: false,
      isToday: false,
    });
  }
  
  // Current month days
  const today = new Date();
  for (let i = 1; i <= daysInMonth; i++) {
    const isToday = today.getDate() === i && today.getMonth() === month && today.getFullYear() === year;
    const hasEvent = hasEventsOnDate(year, month, i);
    
    const formattedMonth = String(month + 1).padStart(2, '0');
    const formattedDay = String(i).padStart(2, '0');
    const dateStr = `${year}-${formattedMonth}-${formattedDay}`;
    const isSelected = selectedDate.value === dateStr;

    days.push({
        date: i,
        isCurrentMonth: true,
        isToday: isToday,
        hasEvent: hasEvent,
        isSelected: isSelected,
        dateStr: dateStr
    });
  }
  
  // Next month padding to complete 42 cells (6 rows max to keep layout stable)
  const remainingCells = 42 - days.length;
  for (let i = 1; i <= remainingCells; i++) {
      days.push({
          date: i,
          isCurrentMonth: false,
          isToday: false,
          hasEvent: false,
          isSelected: false,
          dateStr: null
      });
  }
  
  return days;
});

const selectDate = (day) => {
  if (!day.isCurrentMonth) return;
  
  if (selectedDate.value === day.dateStr) {
    selectedDate.value = null; // Toggle off if already selected
  } else {
    selectedDate.value = day.dateStr; // Select new date
  }
};

const prevMonth = () => {
  calendarDate.value = new Date(calendarDate.value.getFullYear(), calendarDate.value.getMonth() - 1, 1);
};

const nextMonth = () => {
  calendarDate.value = new Date(calendarDate.value.getFullYear(), calendarDate.value.getMonth() + 1, 1);
};
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="mb-2">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Events</h1>
      <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mt-1">Your college events & campus-wide activities</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- Stat Summary Widget Layout -->
      <div class="flex flex-col md:flex-row gap-4 mb-2">
        <!-- Left Side: Squares (Upcoming & Completed) -->
        <div class="grid grid-cols-2 gap-4 w-full md:w-1/2">
          <!-- Upcoming Widget -->
          <div class="glass-card flex flex-col justify-between p-5 aspect-square relative overflow-hidden group">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Clock class="w-5 h-5 text-white" />
            </div>
            <div class="mt-auto">
              <p class="text-[0.65rem] md:text-xs uppercase tracking-widest font-bold text-gray-500 dark:text-gray-400 mb-1">Upcoming</p>
              <p class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white leading-none">{{ upcomingEvents.length }}</p>
            </div>
            <!-- Decorative glow -->
            <div class="absolute -bottom-10 -right-10 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl group-hover:bg-blue-500/20 transition-all duration-500"></div>
          </div>
          
          <!-- Completed Widget -->
          <div class="glass-card flex flex-col justify-between p-5 aspect-square relative overflow-hidden group">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Users class="w-5 h-5 text-white" />
            </div>
            <div class="mt-auto">
               <p class="text-[0.65rem] md:text-xs uppercase tracking-widest font-bold text-gray-500 dark:text-gray-400 mb-1">Completed</p>
               <p class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white leading-none">{{ completedEvents.length }}</p>
            </div>
            <div class="absolute -bottom-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all duration-500"></div>
          </div>
        </div>

        <!-- Right Side: Total Events & Mini Calendar -->
        <div class="glass-card w-full md:w-1/2 p-5 relative overflow-hidden group flex flex-row items-center justify-between min-h-[140px]">
          <div class="flex flex-col h-full justify-between z-10 w-[45%]">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center mb-2 shadow-lg shadow-brand-500/20">
              <Calendar class="w-5 h-5 text-white" />
            </div>
            <div class="mt-auto pt-2">
              <p class="text-[0.65rem] md:text-xs uppercase tracking-widest font-bold text-gray-500 dark:text-gray-400 mb-1">Total Event</p>
              <p class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white leading-none">{{ events.length }}</p>
            </div>
          </div>
          
          <!-- Mini Calendar -->
          <div class="w-[55%] pl-4 border-l border-gray-200/50 dark:border-white/10 z-10 flex flex-col h-full">
             <div class="flex items-center justify-between mb-2 shrink-0">
               <button @click="prevMonth" class="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                 <ChevronLeft class="w-3.5 h-3.5" />
               </button>
               <p class="text-[0.55rem] uppercase tracking-widest font-bold text-gray-500 dark:text-gray-400 text-center flex-1">
                 {{ currentMonthName }} <span class="hidden sm:inline">{{ currentYear }}</span>
               </p>
               <button @click="nextMonth" class="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                 <ChevronRight class="w-3.5 h-3.5" />
               </button>
             </div>
             
             <div class="grid grid-cols-7 gap-y-1 gap-x-1 text-[0.6rem] sm:text-[0.65rem] font-medium text-center text-gray-700 dark:text-gray-300">
               <!-- Day Headers -->
               <span class="text-gray-400 dark:text-gray-600 mb-1">S</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">M</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">T</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">W</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">T</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">F</span>
               <span class="text-gray-400 dark:text-gray-600 mb-1">S</span>
               
               <!-- Dynamic Dates -->
               <span 
                 v-for="(day, index) in calendarDays" 
                 :key="index"
                 @click="selectDate(day)"
                 class="relative flex items-center justify-center w-5 h-5 mx-auto rounded-full transition-all"
                 :class="[
                   !day.isCurrentMonth ? 'opacity-30 cursor-default' : 'cursor-pointer',
                   day.isSelected ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/40 font-bold ring-2 ring-indigo-400 ring-offset-1 dark:ring-offset-[#1a2342]' : 
                   day.isToday ? 'bg-brand-500 text-white shadow-md shadow-brand-500/30 font-bold' : 
                   day.isCurrentMonth ? 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-700 dark:text-gray-300 hover:ring-2 hover:ring-brand-500/30' : ''
                 ]"
               >
                 {{ day.date }}
                 <!-- Event Dot Indicator -->
                 <span v-if="day.hasEvent" 
                       :class="[
                         'absolute -bottom-1 w-1 h-1 rounded-full',
                         (day.isToday || day.isSelected) ? 'bg-white' : 'bg-emerald-500'
                       ]">
                 </span>
               </span>
             </div>
          </div>
          
          <!-- Background Glow -->
          <div class="absolute -top-10 -right-10 w-40 h-40 bg-brand-500/10 rounded-full blur-3xl group-hover:bg-brand-500/20 transition-all duration-500 pointer-events-none"></div>
        </div>
      </div>

      <!-- Search & Filter -->
      <div class="glass-pill px-5 py-3 flex flex-col md:flex-row gap-4 w-full max-w-2xl mb-2 mt-4 shadow-sm border border-gray-100 dark:border-white/[0.05]">
        <div class="relative flex-1">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" type="text" placeholder="Search events..." class="w-full bg-transparent border-none outline-none pl-11 pr-4 py-2 text-sm text-gray-800 dark:text-gray-200 placeholder-gray-500 font-medium" />
        </div>
        <div class="w-px h-6 bg-gray-200 dark:bg-white/10 hidden md:block self-center"></div>
        <select v-model="filterStatus" class="bg-transparent border-none outline-none text-sm font-medium text-gray-700 dark:text-gray-300 w-full md:w-44 py-2 cursor-pointer appearance-none">
          <option value="All">All Status</option>
          <option value="Upcoming">Upcoming</option>
          <option value="Planning">Planning</option>
          <option value="Completed">Completed</option>
          <option value="Cancelled">Cancelled</option>
        </select>
      </div>

      <!-- Events Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="event in filteredEvents"
          :key="event.id"
          class="glass-card overflow-hidden hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)] hover:dark:shadow-black/40 transition-all duration-300 group hover:-translate-y-1"
        >
          <!-- Colored top accent -->
          <div :class="[
            'h-1.5',
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
