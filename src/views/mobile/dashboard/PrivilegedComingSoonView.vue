<template>
  <div class="min-h-screen px-6 py-8 md:px-10 md:py-10" style="background: var(--color-bg);">
    <div class="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl items-center justify-center">
      <section
        class="dashboard-enter dashboard-enter--1 w-full overflow-hidden rounded-[36px] border border-black/5 bg-white shadow-[0_30px_80px_rgba(10,10,10,0.08)]"
      >
        <div
          class="relative px-7 py-8 md:px-10 md:py-10"
          style="background: linear-gradient(135deg, var(--color-primary) 0%, color-mix(in srgb, var(--color-primary) 72%, #ffffff 28%) 100%);"
        >
          <div class="absolute inset-0 opacity-20" style="background: radial-gradient(circle at top right, #ffffff 0%, transparent 40%);" />
          <div class="relative flex flex-col gap-4">
            <p class="text-[12px] font-extrabold uppercase tracking-[0.24em]" style="color: var(--color-banner-text);">
              Privileged Portal
            </p>
            <div class="max-w-2xl">
              <h1 class="text-[34px] font-extrabold leading-tight md:text-[42px]" style="color: var(--color-banner-text);">
                {{ headingText }}
              </h1>
              <p class="mt-3 max-w-xl text-[14px] leading-6 md:text-[15px]" style="color: color-mix(in srgb, var(--color-banner-text) 84%, transparent);">
                {{ bodyText }}
              </p>
            </div>
          </div>
        </div>

        <div class="grid gap-5 px-7 py-7 md:grid-cols-[1.3fr_0.9fr] md:px-10 md:py-9">
          <div class="rounded-[28px] bg-[#F6F6F1] p-6">
            <p class="text-[12px] font-extrabold uppercase tracking-[0.22em] text-[#687019]">Current Session</p>
            <h2 class="mt-3 text-[26px] font-extrabold text-[#0A0A0A]">{{ displayName }}</h2>
            <p class="mt-1 text-[14px] text-[#4F4F4A]">{{ currentUser?.email || 'No email available' }}</p>

            <div class="mt-5 grid gap-3 md:grid-cols-2">
              <div class="rounded-[22px] bg-white px-4 py-4">
                <p class="text-[11px] font-extrabold uppercase tracking-[0.18em] text-[#7B8441]">Role</p>
                <p class="mt-2 text-[18px] font-bold text-[#0A0A0A]">{{ roleLabel }}</p>
              </div>
              <div class="rounded-[22px] bg-white px-4 py-4">
                <p class="text-[11px] font-extrabold uppercase tracking-[0.18em] text-[#7B8441]">School</p>
                <p class="mt-2 text-[18px] font-bold text-[#0A0A0A]">{{ schoolLabel }}</p>
              </div>
            </div>

            <p class="mt-5 text-[14px] leading-6 text-[#4F4F4A]">
              Student screens are live now. This privileged dashboard is intentionally parked here until you build the
              full admin and School IT experience.
            </p>
          </div>

          <div class="rounded-[28px] bg-[#0A0A0A] p-6 text-white">
            <p class="text-[12px] font-extrabold uppercase tracking-[0.22em] text-[#D0D88C]">Next Step</p>
            <h2 class="mt-3 text-[24px] font-extrabold">Coming soon</h2>
            <p class="mt-3 text-[14px] leading-6 text-white/74">
              Privileged workspace pages are still being built. You can sign out and continue testing the student flow for now.
            </p>

            <div class="mt-6 flex flex-col gap-3">
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-full border border-white/15 px-5 py-3 text-[14px] font-extrabold text-white transition-colors hover:bg-white/8"
                @click="handleSignOut"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'

const { logout } = useAuth()
const { currentUser, schoolSettings, getSessionRoleNames } = useDashboardSession()

const roleNames = computed(() => getSessionRoleNames(currentUser.value))

const displayName = computed(() => {
  const first = currentUser.value?.first_name || ''
  const middle = currentUser.value?.middle_name || ''
  const last = currentUser.value?.last_name || ''
  return [first, middle, last].filter(Boolean).join(' ') || 'Privileged User'
})

const roleLabel = computed(() => {
  const primaryRole = roleNames.value[0] || 'privileged'
  return primaryRole === 'school_IT'
    ? 'School IT'
    : primaryRole.charAt(0).toUpperCase() + primaryRole.slice(1)
})

const schoolLabel = computed(() => schoolSettings.value?.school_name || 'Platform-wide access')

const headingText = computed(() =>
  roleNames.value.includes('school_IT')
    ? 'School IT dashboard is coming soon.'
    : 'Admin dashboard is coming soon.'
)

const bodyText = computed(() =>
  roleNames.value.includes('school_IT')
    ? 'Your School IT account is working, but the dedicated School IT workspace is still being built.'
    : 'Your admin session is working, but the dedicated admin workspace is still being built.'
)

function handleSignOut() {
  logout()
}
</script>
