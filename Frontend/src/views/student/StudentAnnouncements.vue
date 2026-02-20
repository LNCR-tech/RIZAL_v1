<script setup>
import { ref, computed, onMounted } from 'vue';
import { Megaphone, Search, Clock, Building2, AlertTriangle, BookOpen, Calendar, Tag } from 'lucide-vue-next';
import { getAnnouncements, getCurrentUser } from '../../services/api.js';

const isLoading = ref(true);
const announcements = ref([]);
const searchQuery = ref('');
const filterType = ref('All');

// Get current logged-in user's college
const currentUser = getCurrentUser();
const studentCollege = currentUser?.college || 'College of Engineering';

onMounted(async () => {
  try {
    const data = await getAnnouncements(studentCollege);
    announcements.value = data;
  } catch (err) {
    console.error('Failed to load announcements:', err);
  } finally {
    isLoading.value = false;
  }
});

const filteredAnnouncements = computed(() => {
  return announcements.value.filter(a => {
    const matchSearch = a.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                        a.content.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchType = filterType.value === 'All' || a.type === filterType.value;
    return matchSearch && matchType;
  });
});

const urgentCount = computed(() => announcements.value.filter(a => a.priority === 'urgent').length);

const getTypeBadge = (type) => {
  switch (type) {
    case 'Academic': return 'badge-blue';
    case 'Event': return 'badge-green';
    case 'General': return 'badge-gray';
    case 'Urgent': return 'badge-red';
    default: return 'badge-gray';
  }
};

const getTypeIcon = (type) => {
  switch (type) {
    case 'Academic': return BookOpen;
    case 'Event': return Calendar;
    case 'General': return Megaphone;
    default: return Megaphone;
  }
};

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const timeAgo = (dateStr) => {
  const now = new Date('2026-02-20T20:30:00+08:00');
  const date = new Date(dateStr);
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return formatDate(dateStr);
};
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Announcements</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Stay updated with campus & college news</p>
      </div>
      <!-- Urgent Badge -->
      <div v-if="urgentCount > 0" class="flex items-center gap-2 px-3 py-2 bg-red-50 dark:bg-red-500/10 rounded-xl border border-red-200 dark:border-red-500/20">
        <AlertTriangle class="w-4 h-4 text-red-500" />
        <span class="text-sm font-semibold text-red-600 dark:text-red-400">{{ urgentCount }} Urgent</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-16">
      <div class="w-8 h-8 border-4 border-brand-500/30 border-t-brand-500 rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- Search & Filter -->
      <div class="glass-card p-4 flex flex-col md:flex-row gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input v-model="searchQuery" type="text" placeholder="Search announcements..." class="form-input pl-10" />
        </div>
        <select v-model="filterType" class="form-input w-full md:w-44">
          <option value="All">All Types</option>
          <option value="Academic">Academic</option>
          <option value="Event">Event</option>
          <option value="General">General</option>
        </select>
      </div>

      <!-- Announcements List -->
      <div class="space-y-4">
        <div
          v-for="item in filteredAnnouncements"
          :key="item.id"
          :class="[
            'glass-card overflow-hidden transition-all duration-300 hover:ring-2 hover:ring-brand-500/30',
            item.priority === 'urgent' ? 'ring-1 ring-red-300 dark:ring-red-500/30' : ''
          ]"
        >
          <!-- Left accent border for urgency -->
          <div class="flex">
            <div :class="[
              'w-1 shrink-0',
              item.priority === 'urgent' ? 'bg-red-500' :
              item.priority === 'high' ? 'bg-amber-500' :
              'bg-transparent'
            ]"></div>

            <div class="flex-1 p-5">
              <div class="flex items-start gap-4">
                <!-- Type Icon -->
                <div :class="[
                  'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
                  item.priority === 'urgent'
                    ? 'bg-red-100 dark:bg-red-500/20 text-red-500 dark:text-red-400'
                    : item.type === 'Academic'
                      ? 'bg-blue-100 dark:bg-blue-500/20 text-blue-500 dark:text-blue-400'
                      : item.type === 'Event'
                        ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-500 dark:text-emerald-400'
                        : 'bg-gray-100 dark:bg-white/[0.06] text-gray-500 dark:text-gray-400'
                ]">
                  <AlertTriangle v-if="item.priority === 'urgent'" class="w-5 h-5" />
                  <component v-else :is="getTypeIcon(item.type)" class="w-5 h-5" />
                </div>

                <!-- Content -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-3 flex-wrap">
                    <h3 :class="[
                      'font-semibold text-sm',
                      item.priority === 'urgent' ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'
                    ]">
                      {{ item.title }}
                    </h3>
                    <div class="flex items-center gap-2 shrink-0">
                      <span :class="['badge', getTypeBadge(item.type)]">
                        <Tag class="w-3 h-3" /> {{ item.type }}
                      </span>
                    </div>
                  </div>

                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-2 leading-relaxed">
                    {{ item.content }}
                  </p>

                  <div class="flex items-center gap-4 mt-3 flex-wrap">
                    <div class="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
                      <Clock class="w-3.5 h-3.5" />
                      <span>{{ timeAgo(item.date) }}</span>
                    </div>
                    <div v-if="item.college" class="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
                      <Building2 class="w-3.5 h-3.5" />
                      <span>{{ item.college.replace('College of ', '') }}</span>
                    </div>
                    <div v-else class="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500">
                      <Megaphone class="w-3.5 h-3.5" />
                      <span>Campus-Wide</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredAnnouncements.length === 0" class="glass-card p-12 text-center">
        <Megaphone class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
        <p class="text-gray-500 dark:text-gray-400 font-medium">No announcements found</p>
        <p class="text-sm text-gray-400 dark:text-gray-500 mt-1">Try adjusting your search or filter</p>
      </div>
    </template>
  </div>
</template>
