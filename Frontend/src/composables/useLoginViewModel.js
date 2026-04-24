import { computed, onBeforeMount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth.js'
import { applyTheme, loadUnbrandedTheme } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'

export function useLoginViewModel() {
  const email = ref('')
  const password = ref('')
  const isMounted = ref(false)
  const sessionNotice = ref('')
  const router = useRouter()
  const { login, isLoading, error } = useAuth()
  const visibleMessage = computed(() => error.value || sessionNotice.value)
  const previewRoles = [
    {
      id: 'student-ssg',
      label: 'Student + SSG',
      description: 'Student dashboard with SSG switch flow',
      location: { name: 'PreviewHome', query: { variant: 'ssg' } },
    },
    {
      id: 'sg',
      label: 'SG',
      description: 'College-level council workspace',
      location: { name: 'PreviewSgDashboard', query: { variant: 'sg' } },
    },
    {
      id: 'ssg',
      label: 'SSG',
      description: 'Campus-wide council workspace',
      location: { name: 'PreviewSgDashboard', query: { variant: 'ssg' } },
    },
    {
      id: 'campus-admin',
      label: 'Campus Admin',
      description: 'School IT workspace preview',
      location: { name: 'PreviewSchoolItHome' },
    },
    {
      id: 'admin',
      label: 'Admin',
      description: 'Platform admin workspace',
      location: { name: 'PreviewAdminHome' },
    },
  ]

  onBeforeMount(() => {
    applyTheme(loadUnbrandedTheme())
  })

  onMounted(() => {
    sessionNotice.value = consumeSessionExpiredNotice()

    setTimeout(() => {
      isMounted.value = true
    }, 50)
  })

  async function handleLogin() {
    await login(email.value, password.value)
  }

  function openQuickAttendance() {
    router.push({ name: 'QuickAttendance' })
  }

  function openRolePreview(location) {
    router.push(location)
  }

  return {
    email,
    password,
    isMounted,
    isLoading,
    visibleMessage,
    previewRoles,
    handleLogin,
    openQuickAttendance,
    openRolePreview,
  }
}
