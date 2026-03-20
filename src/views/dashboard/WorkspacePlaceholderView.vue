<template>
  <section class="workspace-placeholder">
    <header class="workspace-placeholder__header dashboard-enter dashboard-enter--1">
      <button
        class="workspace-placeholder__back"
        type="button"
        aria-label="Go back"
        @click="router.push({ name: homeRouteName })"
      >
        <ArrowLeft :size="18" />
      </button>

      <div>
        <p class="workspace-placeholder__eyebrow">School IT Workspace</p>
        <h1 class="workspace-placeholder__title">{{ title }}</h1>
      </div>
    </header>

    <article class="workspace-placeholder__card dashboard-enter dashboard-enter--2">
      <p class="workspace-placeholder__school">{{ schoolName }}</p>
      <p class="workspace-placeholder__copy">{{ description }}</p>

      <button
        class="workspace-placeholder__cta"
        type="button"
        @click="router.push({ name: homeRouteName })"
      >
        <span class="workspace-placeholder__cta-icon">
          <ArrowRight :size="18" />
        </span>
        Back to Home
      </button>
    </article>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from 'lucide-vue-next'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'

defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
})

const router = useRouter()
const route = useRoute()
const { schoolSettings } = useDashboardSession()
const isExposedWorkspace = computed(() => route.path.startsWith('/exposed/workspace'))
const homeRouteName = computed(() => isExposedWorkspace.value ? 'PreviewSchoolItHome' : 'SchoolItHome')

const schoolName = computed(() => (
  isExposedWorkspace.value
    ? schoolItPreviewData.schoolSettings?.school_name || 'School workspace'
    : schoolSettings.value?.school_name || 'School workspace'
))
</script>

<style scoped>
.workspace-placeholder {
  min-height: 100vh;
  padding: 34px 28px 120px;
  font-family: 'Manrope', sans-serif;
}

.workspace-placeholder__header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workspace-placeholder__back {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-always-dark);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.workspace-placeholder__eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.workspace-placeholder__title {
  margin: 0;
  font-size: 32px;
  line-height: 0.95;
  font-weight: 800;
  letter-spacing: -0.06em;
  color: var(--color-text-primary);
}

.workspace-placeholder__card {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 28px;
  border-radius: 30px;
  background: var(--color-surface);
}

.workspace-placeholder__school {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.workspace-placeholder__copy {
  margin: 0;
  max-width: 42ch;
  font-size: 15px;
  line-height: 1.7;
  color: var(--color-text-always-dark);
}

.workspace-placeholder__cta {
  width: fit-content;
  min-height: 58px;
  padding: 0 24px 0 8px;
  border: none;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  gap: 14px;
  font-size: 15px;
  font-weight: 700;
}

.workspace-placeholder__cta-icon {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  background: var(--color-nav);
  color: var(--color-nav-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (min-width: 768px) {
  .workspace-placeholder {
    padding: 40px 36px 56px;
  }

  .workspace-placeholder__card {
    max-width: 640px;
  }
}
</style>
