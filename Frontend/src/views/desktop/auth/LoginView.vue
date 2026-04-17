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

          <label class="remember-row" for="remember-me">
            <input
              id="remember-me"
              v-model="rememberMe"
              type="checkbox"
              class="remember-row__checkbox"
              :disabled="isLoading"
            >
            <span class="remember-row__label">Remember me</span>
          </label>

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
  rememberMe,
  isMounted,
  isLoading,
  visibleMessage,
  handleLogin,
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

.remember-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 4px 0;
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 600;
}

.remember-row__checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

.remember-row__label {
  line-height: 1.2;
}
</style>
