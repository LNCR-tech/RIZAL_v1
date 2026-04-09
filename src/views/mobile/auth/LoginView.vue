<template>
  <section class="mobile-login">
  <!-- TEMPORARY MOBILE VIEW BANNER -->
  <div style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#f59e0b;color:#1c1917;text-align:center;font-size:11px;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;padding:4px 8px;pointer-events:none;">
    ⚠ Temporary Mobile View
  </div>
    <div class="mobile-login__halo mobile-login__halo--top" aria-hidden="true"></div>
    <div class="mobile-login__halo mobile-login__halo--bottom" aria-hidden="true"></div>

    <header class="mobile-login__brand" :class="isMounted ? 'mobile-login__brand--ready' : ''">
      <img :src="surfaceAuraLogo" alt="Aura" class="mobile-login__brand-logo">
      <span class="mobile-login__brand-copy">Aura mobile portal</span>
    </header>

    <div class="mobile-login__card" :class="isMounted ? 'mobile-login__card--ready' : ''">
      <p class="mobile-login__eyebrow">Mobile View</p>
      <h1 class="mobile-login__title">Sign in from your phone.</h1>
      <p class="mobile-login__copy">Same session and API layer, but a dedicated mobile screen file for your second developer.</p>

      <form class="mobile-login__form" @submit.prevent="handleLogin">
        <BaseInput
          id="email"
          v-model="email"
          type="email"
          placeholder="School email"
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

        <Transition name="mobile-login__message">
          <p v-if="visibleMessage" class="mobile-login__message">
            {{ visibleMessage }}
          </p>
        </Transition>

        <BaseButton
          type="submit"
          variant="primary"
          size="md"
          :loading="isLoading"
        >
          Log In
        </BaseButton>

        <BaseButton
          type="button"
          variant="secondary"
          size="md"
          :disabled="isLoading"
          @click="openQuickAttendance"
        >
          Quick Attendance
        </BaseButton>
      </form>
    </div>

    <footer class="mobile-login__footer" :class="isMounted ? 'mobile-login__footer--ready' : ''">
      <span class="mobile-login__footer-pill">src/views/mobile/ owns this experience</span>
    </footer>
  </section>
</template>

<script setup>
import BaseButton from '@/components/desktop/ui/BaseButton.vue'
import BaseInput from '@/components/desktop/ui/BaseInput.vue'
import { surfaceAuraLogo } from '@/config/theme.js'
import { useLoginViewModel } from '@/composables/useLoginViewModel.js'

const {
  email,
  password,
  isMounted,
  isLoading,
  visibleMessage,
  handleLogin,
  openQuickAttendance,
} = useLoginViewModel()
</script>

<style scoped>
.mobile-login {
  position: relative;
  min-height: 100dvh;
  overflow: hidden;
  padding: max(24px, env(safe-area-inset-top, 24px)) 20px max(28px, env(safe-area-inset-bottom, 28px));
  background: linear-gradient(180deg, #10281f 0%, #14392b 32%, #edf0e4 32%, #edf0e4 100%);
  font-family: 'Manrope', sans-serif;
}

.mobile-login__halo {
  position: absolute;
  border-radius: 999px;
  filter: blur(14px);
  opacity: 0.5;
}

.mobile-login__halo--top {
  top: 18px;
  right: -28px;
  width: 140px;
  height: 140px;
  background: rgba(220, 255, 148, 0.4);
}

.mobile-login__halo--bottom {
  left: -36px;
  bottom: 110px;
  width: 170px;
  height: 170px;
  background: rgba(16, 40, 31, 0.16);
}

.mobile-login__brand,
.mobile-login__card,
.mobile-login__footer {
  position: relative;
  z-index: 1;
  opacity: 0;
  transform: translateY(14px);
  transition: opacity 0.45s ease, transform 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}

.mobile-login__brand--ready,
.mobile-login__card--ready,
.mobile-login__footer--ready {
  opacity: 1;
  transform: translateY(0);
}

.mobile-login__brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.mobile-login__brand-logo {
  height: 28px;
  width: auto;
}

.mobile-login__brand-copy {
  color: #f3f7ef;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mobile-login__card {
  margin-top: 82px;
  border-radius: 30px;
  padding: 28px 22px 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(16, 40, 31, 0.08);
  box-shadow: 0 22px 40px rgba(16, 40, 31, 0.12);
}

.mobile-login__eyebrow {
  margin: 0;
  color: #48614c;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.mobile-login__title {
  margin: 14px 0 0;
  font-size: 32px;
  line-height: 0.97;
  letter-spacing: -0.06em;
  color: #0f1c13;
}

.mobile-login__copy {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: #55675a;
}

.mobile-login__form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 22px;
}

.mobile-login__message {
  margin: 0;
  color: #b42318;
  font-size: 12px;
  text-align: center;
}

.mobile-login__message-enter-active,
.mobile-login__message-leave-active {
  transition: opacity 0.2s ease;
}

.mobile-login__message-enter-from,
.mobile-login__message-leave-to {
  opacity: 0;
}

.mobile-login__footer {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}

.mobile-login__footer-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(16, 40, 31, 0.08);
  color: #2f4636;
  font-size: 11px;
  font-weight: 700;
}
</style>
