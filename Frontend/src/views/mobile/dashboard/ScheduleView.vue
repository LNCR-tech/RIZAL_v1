<template>
  <section class="mobile-student-events">
    <header class="mobile-student-events__header">
      <div class="mobile-student-events__profile">
        <img
          v-if="avatarUrl"
          :src="avatarUrl"
          :alt="displayName"
          class="mobile-student-events__avatar"
        >
        <span v-else class="mobile-student-events__avatar mobile-student-events__avatar--fallback">
          {{ initials }}
        </span>

        <span class="mobile-student-events__profile-copy">
          <span class="mobile-student-events__eyebrow">Welcome Back</span>
          <span class="mobile-student-events__name">{{ displayName }}</span>
        </span>
      </div>

      <button type="button" class="mobile-student-events__bell" aria-label="Notifications" @click="toggleNotifications">
        <Bell :size="18" :stroke-width="2" />
        <span
          v-if="notificationBadgeCount > 0"
          class="mobile-student-events__bell-dot"
          aria-hidden="true"
        ></span>
      </button>
    </header>

    <div class="mobile-student-events__content">
      <h1 class="mobile-student-events__title">Events</h1>

      <StudentScheduleDateRail
        v-model="selectedDateKey"
        :week-pages="weekPages"
        :initial-week-index="todayWeekIndex"
      />

      <StudentScheduleFilters
        v-model="activeFilter"
        :filters="filters"
      />

      <div v-if="visibleRows.length" class="mobile-student-events__list">
        <StudentScheduleEventRow
          v-for="row in visibleRows"
          :key="row.eventId"
          :item="row"
          :expanded="expandedEventId === row.eventId"
          @open-detail="openEventDetail"
          @primary-action="openPrimaryAction"
          @toggle-expand="toggleExpanded"
        />
      </div>

      <div v-else class="mobile-student-events__empty">
        <p class="mobile-student-events__empty-title">No events for this day.</p>
        <p class="mobile-student-events__empty-copy">
          Pick another date from the week rail to see more student events.
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { Bell } from 'lucide-vue-next'
import StudentScheduleDateRail from '@/components/mobile/dashboard/StudentScheduleDateRail.vue'
import StudentScheduleEventRow from '@/components/mobile/dashboard/StudentScheduleEventRow.vue'
import StudentScheduleFilters from '@/components/mobile/dashboard/StudentScheduleFilters.vue'
import { useMobileStudentSchedule } from '@/composables/useMobileStudentSchedule.js'
import { useNotifications } from '@/composables/useNotifications.js'

const props = defineProps({
  preview: {
    type: Boolean,
    default: false,
  },
})

const {
  activeFilter,
  activeUnreadAnnouncements,
  avatarUrl,
  displayName,
  expandedEventId,
  filters,
  initials,
  openEventDetail,
  openPrimaryAction,
  selectedDateKey,
  todayWeekIndex,
  toggleExpanded,
  visibleRows,
  weekPages,
} = useMobileStudentSchedule(() => props.preview)

const { toggleNotifications, unreadNotifCount } = useNotifications()

const notificationBadgeCount = computed(() => (
  props.preview
    ? 0
    : Math.max(activeUnreadAnnouncements.value, unreadNotifCount.value)
))
</script>

<style scoped>
.mobile-student-events {
  min-height: 100vh;
  padding: 28px 20px 120px;
  background: var(--color-bg);
  font-family: 'Manrope', sans-serif;
}

.mobile-student-events__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.mobile-student-events__profile {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 58px;
  padding: 6px 18px 6px 6px;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  min-width: 0;
}

.mobile-student-events__avatar {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  object-fit: cover;
  flex: 0 0 auto;
}

.mobile-student-events__avatar--fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-nav);
  color: var(--color-nav-text);
  font-size: 14px;
  font-weight: 800;
}

.mobile-student-events__profile-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mobile-student-events__eyebrow {
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.mobile-student-events__name {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-always-dark);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-student-events__bell {
  position: relative;
  width: 58px;
  height: 58px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}

.mobile-student-events__bell-dot {
  position: absolute;
  top: 15px;
  right: 16px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-primary);
}

.mobile-student-events__content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 34px;
}

.mobile-student-events__title {
  margin: 0;
  font-size: 34px;
  line-height: 0.98;
  font-weight: 800;
  letter-spacing: -0.06em;
  color: var(--color-text-always-dark);
}

.mobile-student-events__list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 6px;
}

.mobile-student-events__empty {
  margin-top: 10px;
  padding: 28px 24px;
  border-radius: 28px;
  background: var(--color-surface);
  text-align: center;
}

.mobile-student-events__empty-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: var(--color-text-always-dark);
}

.mobile-student-events__empty-copy {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-secondary);
}
</style>
