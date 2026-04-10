<template>
  <div class="login-page min-h-dvh flex flex-col overflow-auto" style="background: var(--color-bg);">
    <div class="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
      <div class="w-full max-w-[340px] flex flex-col gap-6 login-form-area">
        <h1
          class="text-[22px] font-semibold leading-[1.4] tracking-[-0.3px] transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          style="color: var(--color-text-primary);"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
        >
          Welcome to the portal. Log in to access your dashboard.
        </h1>

        <form
          class="flex flex-col gap-3 transition-all duration-700 delay-100 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
          @submit.prevent="handleLogin"
        >
          <BaseInput
            id="email"
            v-model="email"
            type="email"
            placeholder="Gmail"
            autocomplete="email"
            tone="neutral"
            :disabled="isLoading"
          />

          <BaseInput
            id="password"
            v-model="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            tone="neutral"
            :disabled="isLoading"
            @enter="handleLogin"
          />

          <Transition name="fade">
            <p v-if="visibleMessage" class="text-red-500 text-xs text-center mt-1">
              {{ visibleMessage }}
            </p>
          </Transition>

          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            class="mt-1 group"
            :loading="isLoading"
          >
            Log In
          </BaseButton>

          <BaseButton
            type="button"
            variant="secondary"
            size="md"
            class="group"
            :disabled="isLoading"
            @click="openQuickAttendance"
          >
            Quick Attendance
          </BaseButton>
        </form>

        <section
          class="preview-panel transition-all duration-700 delay-150 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
        >
          <div class="preview-panel__copy">
            <p class="preview-panel__eyebrow">Mock Views</p>
            <p class="preview-panel__title">Open role previews without backend auth.</p>
          </div>

          <div class="preview-panel__grid">
            <button
              v-for="role in previewRoles"
              :key="role.id"
              type="button"
              class="preview-panel__card"
              @click="openRolePreview(role.location)"
            >
              <span class="preview-panel__label">{{ role.label }}</span>
              <span class="preview-panel__description">{{ role.description }}</span>
            </button>
          </div>
        </section>

        <div
          class="flex flex-col items-center justify-center gap-2 mt-1 transition-all duration-700 delay-200 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
        >
          <div class="flex items-center justify-center gap-2">
            <img
              :src="surfaceAuraLogo"
              alt="Aura"
              class="h-8 w-auto object-contain"
            >
            <span class="text-[13px] font-medium tracking-tight" style="color: var(--color-text-primary);">
              Powered by Aura Ai
            </span>
          </div>
        </div>
      </div>
    </div>

    <footer
      class="pb-8 flex justify-center transition-all duration-1000 delay-300 ease-out relative z-10"
      :class="isMounted ? 'opacity-100' : 'opacity-0'"
    >
      <a
        href="#"
        class="text-[12px] font-medium transition-colors"
        style="color: var(--color-text-secondary);"
      >
        Learn more about Aura Project
      </a>
    </footer>
  </div>
</template>

<script setup>
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { surfaceAuraLogo } from '@/config/theme.js'
import { useLoginViewModel } from '@/composables/useLoginViewModel.js'

const {
  email,
  password,
  isMounted,
  isLoading,
  visibleMessage,
  previewRoles,
  handleLogin,
  openRolePreview,
  openQuickAttendance,
} = useLoginViewModel()
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.login-page {
  font-family: 'Manrope', sans-serif;
  -webkit-overflow-scrolling: touch;
}

.login-form-area {
  padding-bottom: env(safe-area-inset-bottom, 16px);
}

.preview-panel {
  padding: 16px;
  border-radius: 24px;
  background: var(--color-surface);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.preview-panel__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}

.preview-panel__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.preview-panel__title {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-primary);
}

.preview-panel__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.preview-panel__card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  min-height: 84px;
  padding: 14px;
  border: 1px solid var(--color-surface-border);
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-surface) 88%, var(--color-bg));
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.preview-panel__card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--color-primary) 32%, var(--color-surface-border));
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
}

.preview-panel__label {
  font-size: 13px;
  font-weight: 800;
  color: var(--color-text-primary);
}

.preview-panel__description {
  font-size: 11px;
  line-height: 1.45;
  color: var(--color-text-secondary);
}
</style>
