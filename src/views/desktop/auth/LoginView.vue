<template>
  <section class="desktop-login">
    <div class="desktop-login__backdrop" aria-hidden="true"></div>

    <div class="desktop-login__shell">
      <aside class="desktop-login__hero" :class="isMounted ? 'desktop-login__hero--ready' : ''">
        <div class="desktop-login__brand">
          <img :src="surfaceAuraLogo" alt="Aura" class="desktop-login__brand-logo">
          <span class="desktop-login__brand-copy">Powered by Aura Ai</span>
        </div>

        <p class="desktop-login__eyebrow">Desktop Workspace</p>
        <h1 class="desktop-login__title">Operate the full campus portal from one focused control room.</h1>
        <p class="desktop-login__copy">
          Desktop and mobile now live in separate folders, while auth, stores, and API services stay shared underneath.
        </p>

        <div class="desktop-login__chips">
          <span class="desktop-login__chip">Shared Pinia stores</span>
          <span class="desktop-login__chip">Shared API services</span>
          <span class="desktop-login__chip">Desktop-only UI files</span>
        </div>
      </aside>

      <div class="desktop-login__card" :class="isMounted ? 'desktop-login__card--ready' : ''">
        <div class="desktop-login__card-head">
          <p class="desktop-login__card-kicker">Sign in</p>
          <h2 class="desktop-login__card-title">Welcome back</h2>
          <p class="desktop-login__card-copy">Use your school account to open the web workspace.</p>
        </div>

        <form class="desktop-login__form" @submit.prevent="handleLogin">
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

          <Transition name="desktop-login__message">
            <p v-if="visibleMessage" class="desktop-login__message">
              {{ visibleMessage }}
            </p>
          </Transition>

          <div class="desktop-login__actions">
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
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import BaseButton from '@/components/desktop/ui/BaseButton.vue'
import BaseInput from '@/components/desktop/ui/BaseInput.vue'
import { applyLightOverride, removeLightOverride, surfaceAuraLogo } from '@/config/theme.js'
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

onMounted(() => {
  applyLightOverride()
})

onUnmounted(() => {
  removeLightOverride()
})
</script>

<style scoped>
.desktop-login {
  position: relative;
  min-height: 100dvh;
  overflow: hidden;
  padding: 40px;
  background:
    radial-gradient(circle at top left, rgba(206, 255, 132, 0.34), transparent 36%),
    radial-gradient(circle at bottom right, rgba(18, 28, 35, 0.16), transparent 34%),
    linear-gradient(135deg, #eef2e5 0%, #dce4d5 46%, #f7f8f3 100%);
  font-family: 'Manrope', sans-serif;
}

.desktop-login__backdrop {
  position: absolute;
  inset: 24px;
  border-radius: 36px;
  border: 1px solid rgba(10, 10, 10, 0.06);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0.16));
  backdrop-filter: blur(8px);
}

.desktop-login__shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(320px, 1.15fr) minmax(360px, 480px);
  align-items: center;
  gap: 36px;
  min-height: calc(100dvh - 80px);
  max-width: 1180px;
  margin: 0 auto;
}

.desktop-login__hero,
.desktop-login__card {
  opacity: 0;
  transform: translateY(18px);
  transition: opacity 0.55s ease, transform 0.55s cubic-bezier(0.22, 1, 0.36, 1);
}

.desktop-login__hero--ready,
.desktop-login__card--ready {
  opacity: 1;
  transform: translateY(0);
}

.desktop-login__brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 34px;
}

.desktop-login__brand-logo {
  height: 36px;
  width: auto;
  object-fit: contain;
}

.desktop-login__brand-copy {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: #203025;
}

.desktop-login__eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #425740;
}

.desktop-login__title {
  max-width: 11ch;
  margin: 16px 0 0;
  font-size: clamp(38px, 4.4vw, 62px);
  line-height: 0.94;
  letter-spacing: -0.06em;
  color: #111a12;
}

.desktop-login__copy {
  max-width: 48ch;
  margin: 18px 0 0;
  font-size: 15px;
  line-height: 1.7;
  color: #405046;
}

.desktop-login__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.desktop-login__chip {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(17, 26, 18, 0.08);
  color: #203025;
  font-size: 12px;
  font-weight: 700;
}

.desktop-login__card {
  border-radius: 32px;
  padding: 34px 30px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(17, 26, 18, 0.08);
  box-shadow: 0 30px 60px rgba(17, 26, 18, 0.12);
}

.desktop-login__card-head {
  margin-bottom: 24px;
}

.desktop-login__card-kicker {
  margin: 0;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #56714f;
}

.desktop-login__card-title {
  margin: 12px 0 0;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: #111a12;
}

.desktop-login__card-copy {
  margin: 10px 0 0;
  font-size: 14px;
  line-height: 1.6;
  color: #536355;
}

.desktop-login__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.desktop-login__message {
  margin: 0;
  color: #b42318;
  font-size: 12px;
  text-align: center;
}

.desktop-login__actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.desktop-login__message-enter-active,
.desktop-login__message-leave-active {
  transition: opacity 0.2s ease;
}

.desktop-login__message-enter-from,
.desktop-login__message-leave-to {
  opacity: 0;
}

@media (max-width: 960px) {
  .desktop-login {
    padding: 22px;
  }

  .desktop-login__shell {
    grid-template-columns: 1fr;
    gap: 22px;
    min-height: calc(100dvh - 44px);
  }

  .desktop-login__backdrop {
    inset: 12px;
  }

  .desktop-login__title {
    max-width: 14ch;
  }
}
</style>

