<template>
  <nav class="breadcrumbs" aria-label="Breadcrumb">
    <ol class="breadcrumbs__list">
      <li class="breadcrumbs__item">
        <router-link to="/" class="breadcrumbs__link">
          <Home :size="14" />
          <span class="breadcrumbs__text">Home</span>
        </router-link>
      </li>
      <li
        v-for="(crumb, index) in crumbs"
        :key="index"
        class="breadcrumbs__item"
      >
        <span class="breadcrumbs__separator">
          <ChevronRight :size="14" />
        </span>
        <component
          :is="crumb.to ? 'router-link' : 'span'"
          :to="crumb.to"
          class="breadcrumbs__link"
          :class="{ 'breadcrumbs__link--current': !crumb.to }"
        >
          {{ crumb.label }}
        </component>
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Home, ChevronRight } from 'lucide-vue-next'

const route = useRoute()

const routeNameLabels = {
  'Dashboard': 'Dashboard',
  'Profile': 'Profile',
  'ProfileSecurity': 'Security',
  'ProfileFaceUpdate': 'Face Verification',
  'ProfileSettings': 'Settings',
  'SchoolItHome': 'School IT',
  'SchoolItSettings': 'Settings',
  'SchoolItDepartmentPrograms': 'Departments',
  'SchoolItProgramStudents': 'Programs',
  'SchoolItUsers': 'Users',
  'SchoolItStudentCouncil': 'Student Council',
  'SchoolItAttendanceMonitor': 'Attendance',
  'SchoolItSchedule': 'Schedule',
  'SchoolItEventReports': 'Reports',
  'SchoolItImportStudents': 'Import',
  'AdminHome': 'Admin',
  'AdminSchools': 'Schools',
  'AdminAccounts': 'Accounts',
  'AdminOversight': 'Oversight',
  'AdminProfile': 'Profile',
  'PreviewAdminHome': 'Admin',
  'PreviewAdminSchools': 'Schools',
  'PreviewAdminAccounts': 'Accounts',
  'PreviewAdminOversight': 'Oversight',
  'PreviewAdminProfile': 'Profile',
  'SgDashboard': 'Student Government',
  'SgEvents': 'Events',
  'SgAttendance': 'Attendance',
  'SgMembers': 'Members',
  'SgStudents': 'Students',
  'SgAnnouncements': 'Announcements',
  'Attendance': 'Attendance',
  'Analytics': 'Analytics',
  'Schedule': 'Schedule',
  'EventDetail': 'Event Details',
}

const crumbs = computed(() => {
  const matched = route.matched || []
  const result = []
  
  for (const record of matched) {
    if (!record.name || record.name === 'root') continue
    
    const label = routeNameLabels[record.name] || record.name
    const to = record.path || '/'
    
    result.push({
      label,
      to: record.name !== route.name ? to : undefined,
    })
  }
  
  return result.slice(1)
})
</script>

<style scoped>
.breadcrumbs {
  padding: 0;
}

.breadcrumbs__list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.breadcrumbs__item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.breadcrumbs__link {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.15s ease;
}

.breadcrumbs__link:hover:not(.breadcrumbs__link--current) {
  color: var(--color-primary);
}

.breadcrumbs__link--current {
  color: var(--color-text-primary);
  font-weight: 600;
  cursor: default;
}

.breadcrumbs__separator {
  display: flex;
  align-items: center;
  color: var(--color-text-muted);
  opacity: 0.5;
}

.breadcrumbs__text {
  display: inline;
}

@media (min-width: 768px) {
  .breadcrumbs__link {
    font-size: 13px;
  }
}
</style>
