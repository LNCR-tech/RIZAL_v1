<template>
  <div class="login-page min-h-dvh flex flex-col overflow-auto" style="background: var(--color-bg);">
    <div class="flex-1 flex flex-col items-center justify-center px-8 relative z-10">
      <div class="w-full max-w-[340px] flex flex-col gap-6 login-form-area">
        <h1
          class="text-[22px] font-semibold leading-[1.4] tracking-[-0.3px] transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          style="color: var(--color-text-primary);"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
        >
          Find your account
        </h1>

        <p 
          class="text-[14px] leading-[1.5] transition-all duration-700 delay-75 ease-[cubic-bezier(0.22,1,0.36,1)]"
          style="color: var(--color-text-secondary);"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
        >
          Enter your email to reset your password.
        </p>

        <form
          class="flex flex-col gap-3 transition-all duration-700 delay-100 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
          @submit.prevent="handleSubmit"
        >
          <BaseInput
            id="email"
            v-model="email"
            type="email"
            placeholder="Email"
            autocomplete="email"
            tone="neutral"
            :disabled="isLoading"
          />

          <Transition name="fade">
            <p v-if="message" :class="messageClass">
              {{ message }}
            </p>
          </Transition>

          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            class="mt-1 group"
            :loading="isLoading"
          >
            Reset Password
          </BaseButton>

          <BaseButton
            type="button"
            variant="secondary"
            size="md"
            :disabled="isLoading"
            @click="goBack"
          >
            Back to Login
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
import { useForgotPasswordViewModel } from '@/composables/useForgotPasswordViewModel.js'

const {
  email,
  isLoading,
  message,
  messageClass,
  isMounted,
  handleSubmit,
  goBack,
} = useForgotPasswordViewModel()
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
</style>
