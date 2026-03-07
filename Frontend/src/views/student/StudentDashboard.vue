<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { Clock, Users, Calendar as CalendarIcon, Bell, ClipboardCheck, ArrowRight, UserCheck, ChevronLeft, ChevronRight, Check } from 'lucide-vue-next';
import { getProfile, getCurrentUser, getStudentEvents, getAnnouncements, getAttendanceRecords } from '../../services/api.js';

const router = useRouter();

// State
const isLoading = ref(true);
const profile = ref({ name: '', college: '', program: '', studentId: '', faceScanRegistered: false });
const recentAttendance = ref([]);
const recentAnnouncements = ref([]);
const events = ref([]);

// Calendar Setup
const today = new Date();
const currentMonthIdx = ref(today.getMonth());
const currentYear = ref(today.getFullYear());
const currentDay = today.getDate();
const isCurrentMonth = computed(() => currentMonthIdx.value === today.getMonth() && currentYear.value === today.getFullYear());

const monthName = computed(() => {
  return new Date(currentYear.value, currentMonthIdx.value).toLocaleString('default', { month: 'long' }).toUpperCase();
});

const calendarDays = computed(() => {
  const daysInMonth = new Date(currentYear.value, currentMonthIdx.value + 1, 0).getDate();
  const firstDay = new Date(currentYear.value, currentMonthIdx.value, 1).getDay();
  const days = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let i = 1; i <= daysInMonth; i++) days.push(i);
  return days;
});

const prevMonth = () => {
  if (currentMonthIdx.value === 0) {
    currentMonthIdx.value = 11;
    currentYear.value--;
  } else {
    currentMonthIdx.value--;
  }
};

const nextMonth = () => {
  if (currentMonthIdx.value === 11) {
    currentMonthIdx.value = 0;
    currentYear.value++;
  } else {
    currentMonthIdx.value++;
  }
};

// Derived Stats
const upcomingCount = computed(() => events.value.filter(e => e.status.toLowerCase() === 'upcoming').length);
const completedCount = computed(() => recentAttendance.value.length);
const totalEventsCount = computed(() => events.value.length);

// Fetch Data
onMounted(async () => {
  try {
    const currentUser = getCurrentUser();
    const userId = currentUser?.id || '24-A-00123';
    
    const [profileData, eventsData, announcementsData, attendanceData] = await Promise.all([
      getProfile(userId).catch(() => ({})),
      getStudentEvents(currentUser?.college).catch(() => []),
      getAnnouncements(currentUser?.college).catch(() => []),
      getAttendanceRecords().catch(() => [])
    ]);

    profile.value = {
      name: profileData.name || currentUser?.name || 'Student',
      college: profileData.college || currentUser?.college || 'Unknown College',
      program: profileData.program || '',
      studentId: profileData.studentId || profileData.id || '',
    };

    events.value = eventsData;
    recentAttendance.value = attendanceData.slice(0, 5); // Use for completed count & list
    recentAnnouncements.value = announcementsData.slice(0, 3);

  } catch (error) {
    console.error("Dashboard failed to load data:", error);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6 animate-fadeIn pb-10">
    
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">Overview</h1>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mt-1">Hello {{ profile.name.split(' ')[0] }}, here's your campus summary.</p>
      </div>
    </div>

    <div v-if="isLoading" class="flex justify-center py-20">
      <div class="w-10 h-10 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <div v-else class="flex flex-col gap-5 lg:gap-6">
      
      <!-- ===== TOP ROW: 2 Squares (Announcements, Attendance) ===== -->
      <div class="grid grid-cols-2 gap-4 sm:gap-5 lg:gap-6">
        
        <!-- Top Left: Announcements -->
        <div class="ios-widget aspect-square flex flex-col p-4 sm:p-6 overflow-hidden group hover:shadow-[#6C5CE7]/20 transition-all duration-300 border-none relative z-10" style="background-color: #1e243b;">
          <!-- Custom Glow Behind Widget -->
          <div class="absolute -bottom-10 -z-10 left-0 right-0 h-3/4 bg-[#6C5CE7]/10 blur-3xl pointer-events-none rounded-full"></div>

          <!-- Header (Stat Card Style) -->
          <div class="mb-2 sm:mb-4 flex flex-col items-start shrink-0">
            <div class="w-10 h-10 sm:w-14 sm:h-14 rounded-full bg-gradient-to-tr from-indigo-500 to-[#6C5CE7] flex items-center justify-center mb-2 sm:mb-3 shadow-lg shadow-[#6C5CE7]/30">
              <Bell class="w-5 h-5 sm:w-7 sm:h-7 text-white" />
            </div>
            <h3 class="text-[0.6rem] sm:text-[0.7rem] font-bold text-white/70 uppercase tracking-[0.15em] leading-none">Announcements</h3>
          </div>
          
          <!-- Widget Content Area -->
          <div class="flex-1 flex flex-col mt-1 relative min-h-0">
            <!-- Empty State -->
            <div v-if="recentAnnouncements.length === 0" class="flex flex-col items-center justify-center h-full text-center opacity-60">
                <Bell class="w-6 h-6 sm:w-8 sm:h-8 text-white/30 mb-1.5 sm:mb-2" />
                <span class="text-[0.55rem] sm:text-[0.65rem] font-medium text-white/50">No new announcements</span>
            </div>
            <!-- Data State -->
            <div v-else class="absolute inset-0 overflow-y-auto custom-scrollbar space-y-2 pr-1">
              <div v-for="ann in recentAnnouncements" :key="ann.id" class="p-2 sm:p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-[#6C5CE7]/50 transition-colors cursor-pointer group/item">
                <h4 class="font-bold text-white text-[0.65rem] sm:text-xs leading-tight mb-1 line-clamp-2 group-hover/item:text-[#6C5CE7] transition-colors">{{ ann.title }}</h4>
                <p class="text-[0.55rem] sm:text-[0.65rem] font-bold text-[#6C5CE7]">{{ ann.date }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Right: Attendance Marked -->
        <div class="ios-widget aspect-square flex flex-col p-4 sm:p-6 overflow-hidden group hover:shadow-[#10B981]/20 transition-all duration-300 border-none relative z-10" style="background-color: #1e243b;">
          <!-- Custom Glow Behind Widget -->
          <div class="absolute -bottom-10 -z-10 left-0 right-0 h-3/4 bg-[#10B981]/10 blur-3xl pointer-events-none rounded-full"></div>

          <!-- Header (Stat Card Style) -->
          <div class="mb-2 sm:mb-4 flex flex-col items-start shrink-0">
            <div class="w-10 h-10 sm:w-14 sm:h-14 rounded-full bg-gradient-to-tr from-emerald-400 to-[#10B981] flex items-center justify-center mb-2 sm:mb-3 shadow-lg shadow-[#10B981]/30">
               <ClipboardCheck class="w-5 h-5 sm:w-7 sm:h-7 text-white" />
            </div>
            <h3 class="text-[0.6rem] sm:text-[0.7rem] font-bold text-white/70 uppercase tracking-[0.15em] leading-none">Attendance Marked</h3>
          </div>
          
          <!-- Widget Content Area -->
          <div class="flex-1 flex flex-col mt-1 relative min-h-0">
            <!-- Empty State -->
            <div v-if="recentAttendance.length === 0" class="flex flex-col items-center justify-center h-full text-center opacity-60">
                <ClipboardCheck class="w-6 h-6 sm:w-8 sm:h-8 text-white/30 mb-1.5 sm:mb-2" />
                <span class="text-[0.55rem] sm:text-[0.65rem] font-medium text-white/50">No recorded attendance yet</span>
            </div>
            <!-- Data State (With Checkmarks) -->
            <div v-else class="absolute inset-0 overflow-y-auto custom-scrollbar space-y-2 pr-1">
              <div v-for="att in recentAttendance" :key="att.id" class="p-2 sm:p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-[#10B981]/50 transition-colors flex items-center justify-between gap-2 group/item cursor-default">
                <div class="min-w-0 pr-1 flex-1">
                  <p class="font-bold text-[0.65rem] sm:text-xs text-white truncate mb-0.5 group-hover/item:text-[#10B981] transition-colors">{{ att.event }}</p>
                  <p class="text-[0.55rem] sm:text-[0.65rem] font-medium text-white/50 truncate">{{ att.date }} • {{ att.checkIn }}</p>
                </div>
                <!-- Check Icon if Status is Present / attended -->
                <div class="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-[#10B981]/20 flex items-center justify-center shrink-0 border border-[#10B981]/30">
                   <Check class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-[#10B981]" />
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
      <!-- ===== End Top Row ===== -->

      <!-- ===== BOTTOM ROW: Exact UI Match (Short Dark Rectangle) ===== -->
      <div class="ios-widget p-3 sm:p-5 flex flex-row gap-4 sm:gap-6 w-full h-[160px] sm:h-[200px] overflow-hidden relative border-none" style="background-color: #1e243b; box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);">
        
        <!-- Left Inner Card (Date + Glow) -->
        <div class="h-full w-[45%] sm:w-1/3 rounded-[16px] sm:rounded-[20px] bg-[#090b14] relative overflow-hidden flex flex-col justify-between p-3 sm:p-5 border border-white/5">
          <!-- Top Date -->
          <div class="relative z-10">
            <h2 class="text-white font-bold text-lg sm:text-2xl lg:text-3xl leading-none tracking-tight">
                {{ new Date().toLocaleString('default', { month: 'short' }) }} {{ new Date().getDate() }}
            </h2>
          </div>
          
          <!-- Bottom Info -->
          <div class="relative z-10">
            <p class="text-white text-[0.65rem] sm:text-sm font-semibold tracking-wide mb-0.5 sm:mb-1">
                {{ new Date().toLocaleString('default', { weekday: 'long' }) }}
            </p>
            <p class="text-white/80 text-[0.55rem] sm:text-[0.65rem] font-medium">
                {{ events.length }} events
            </p>
          </div>

          <!-- Bright Blue Glow at Bottom -->
          <div class="absolute bottom-0 left-0 right-0 h-[60%] bg-gradient-to-t from-[#2b6eff] to-transparent opacity-90 z-0"></div>
        </div>

        <!-- Right Side (Upcoming Events) -->
        <div class="flex-1 flex flex-col relative py-1 sm:py-2 min-w-0 pr-8 sm:pr-12">
          <!-- Header -->
          <h3 class="text-[0.55rem] sm:text-xs text-white/70 font-medium uppercase tracking-[0.15em] mb-2 sm:mb-4">Upcoming</h3>
          
          <!-- Event List (Max 3 to fit strict height) -->
          <div class="flex flex-col gap-2.5 sm:gap-3 flex-1 justify-center">
            <div v-if="!events || events.length === 0" class="flex items-center gap-2 justify-center opacity-60">
                <CalendarIcon class="w-3 h-3 sm:w-4 sm:h-4 text-white/50" />
                <span class="text-white/50 text-[0.55rem] sm:text-xs">No upcoming events</span>
            </div>
            <div v-else v-for="(event, index) in events.slice(0, 3)" :key="event.id" class="flex gap-2.5 sm:gap-3 items-center group cursor-pointer">
              <!-- Colored Vertical Line -->
              <div class="w-[3px] rounded-full h-full min-h-[1.5rem] sm:min-h-[2.25rem]" :class="[
                index % 3 === 0 ? 'bg-[#3b82f6]' : index % 3 === 1 ? 'bg-[#a855f7]' : 'bg-[#14b8a6]'
              ]"></div>
              
              <!-- Text -->
              <div class="flex-1 min-w-0 flex flex-col justify-center">
                <p class="text-white text-[0.65rem] sm:text-[0.85rem] font-medium truncate leading-tight mb-0.5 sm:mb-1">{{ event.title || event.name }}</p>
                <p class="text-[#8492a6] text-[0.55rem] sm:text-[0.7rem] font-medium truncate leading-none">{{ event.time }}</p>
              </div>
            </div>
          </div>

          <!-- Arrow Button Overlay (Bottom Right) -->
          <button @click="router.push('/student/events')" class="absolute bottom-0 right-0 w-7 h-7 sm:w-10 sm:h-10 rounded-full bg-[#1e243b] md:hover:bg-[#2a3454] transition-colors flex items-center justify-center flex-shrink-0 group z-20">
            <!-- Multihued inner glow ring from reference -->
            <div class="absolute inset-0 rounded-full border border-white/10 overflow-hidden">
                <div class="absolute inset-[-50%] bg-[conic-gradient(from_0deg,transparent_0_340deg,rgba(255,255,255,0.3)_360deg)] opacity-0 group-hover:opacity-100 group-hover:animate-spin transition-opacity"></div>
            </div>
            <!-- Glow ring background match -->
            <div class="absolute inset-[-1.5px] rounded-full bg-gradient-to-br from-[#14b8a6] via-[#3b82f6] to-[#a855f7] opacity-60 pointer-events-none z-0"></div>
            <div class="absolute inset-[1px] rounded-full bg-[#1e243b] pointer-events-none z-10"></div>
            
            <ArrowRight class="w-3 h-3 sm:w-4 sm:h-4 text-white relative z-20" />
          </button>
        </div>

      </div>
      <!-- ===== End Bottom Row ===== -->

    </div>
  </div>
</template>

<style scoped>
/* iOS Widget Core Styling */
.ios-widget {
  @apply bg-white/90 dark:bg-[#1A1C23]/80 backdrop-blur-2xl rounded-[32px] p-6 shadow-sm border border-white/50 dark:border-white/5 transition-all;
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.05);
}
.dark .ios-widget {
  box-shadow: 0 10px 40px -10px rgba(0,0,0,0.3);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 20px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>
