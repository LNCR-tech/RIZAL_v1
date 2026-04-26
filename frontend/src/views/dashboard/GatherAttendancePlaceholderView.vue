<template>
  <div class="gather-attendance-placeholder">
    <div class="gather-attendance-placeholder__shell">
      <button class="gather-attendance-placeholder__back" type="button" @click="goBack">
        <ArrowLeft :size="18" />
        <span>Back</span>
      </button>

      <section class="gather-attendance-placeholder__card">
        <span class="gather-attendance-placeholder__tag">Gather</span>
        <h1 class="gather-attendance-placeholder__title">Gather attendance screen goes here next.</h1>
        <p class="gather-attendance-placeholder__description">
          This placeholder route is ready for the reworked attendance UI. We can replace this screen with the new Gather experience in the next pass.
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'
import {
  hasNavigableHistory,
  isGatherWelcomePath,
  isGovernanceWorkspaceContext,
  resolveGatherWelcomeLocation,
  resolveGovernanceWorkspaceLocation,
  resolveStudentHomeLocation,
} from '@/services/routeWorkspace.js'

const router = useRouter()
const route = useRoute()

function goBack() {
  if (hasNavigableHistory(route)) {
    router.back()
    return
  }

  if (route.path.includes('/gather/attendance') || isGatherWelcomePath(route)) {
    router.push(resolveGatherWelcomeLocation(route))
    return
  }

  router.push(
    isGovernanceWorkspaceContext(route)
      ? resolveGovernanceWorkspaceLocation(route)
      : resolveStudentHomeLocation(route)
  )
}
</script>

<style scoped>
.gather-attendance-placeholder {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--color-primary) 14%, white) 0%, transparent 34%),
    linear-gradient(180deg, #f8f8fb 0%, #ececf3 100%);
  padding: 18px 14px max(28px, calc(env(safe-area-inset-bottom, 0px) + 14px));
  color: #111827;
  font-family: 'Manrope', sans-serif;
}

.gather-attendance-placeholder__shell {
  width: min(100%, 420px);
  min-height: calc(100vh - 36px);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.gather-attendance-placeholder__back {
  width: fit-content;
  min-height: 42px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #121826;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  box-shadow:
    0 12px 28px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
  -webkit-backdrop-filter: blur(18px) saturate(145%);
  backdrop-filter: blur(18px) saturate(145%);
  cursor: pointer;
}

.gather-attendance-placeholder__card {
  flex: 1;
  border-radius: 38px;
  padding: 28px 24px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94) 0%, rgba(247, 248, 251, 0.86) 100%);
  border: 1px solid rgba(255, 255, 255, 0.96);
  box-shadow:
    0 28px 60px rgba(15, 23, 42, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.88);
  -webkit-backdrop-filter: blur(22px) saturate(150%);
  backdrop-filter: blur(22px) saturate(150%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
}

.gather-attendance-placeholder__tag {
  width: fit-content;
  min-height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-primary) 12%, white);
  color: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.gather-attendance-placeholder__title {
  margin: 0;
  font-size: clamp(30px, 9vw, 42px);
  line-height: 0.98;
  letter-spacing: -0.06em;
}

.gather-attendance-placeholder__description {
  margin: 0;
  max-width: 30ch;
  font-size: 15px;
  line-height: 1.72;
  color: #5e6578;
}
</style>
