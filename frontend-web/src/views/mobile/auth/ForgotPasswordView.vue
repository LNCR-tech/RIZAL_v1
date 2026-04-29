<template>
  <div class="mobile-login" :class="{ 'mobile-login--mounted': isMounted }">
    <div class="mobile-login__frame">
      <header class="mobile-login__hero" :style="heroBackgroundStyle">
        <div class="mobile-login__hero-overlay" />

        <img
          :src="auraLogoWhite"
          alt="Aura"
          class="mobile-login__logo"
        >
      </header>

      <main class="mobile-login__sheet">
        <div class="mobile-login__content">
          <h1 class="mobile-login__title">
            Find your account
          </h1>

          <p class="mobile-login__subtitle">
            Enter your email to reset your password.
          </p>

          <form class="mobile-login__form" @submit.prevent="handleSubmit">
            <label class="mobile-login__field">
              <span class="sr-only">Email</span>
              <input
                id="email"
                v-model="email"
                class="mobile-login__input"
                type="email"
                placeholder="Email"
                autocomplete="email"
                autocapitalize="none"
                spellcheck="false"
                :disabled="isLoading"
              >
            </label>

            <Transition name="login-message">
              <p v-if="message" :class="messageClass">
                {{ message }}
              </p>
            </Transition>

            <button
              type="submit"
              class="mobile-login__button mobile-login__button--primary"
              :disabled="isLoading"
            >
              {{ isLoading ? 'Processing...' : 'Reset Password' }}
            </button>

            <button
              type="button"
              class="mobile-login__button mobile-login__button--secondary"
              :disabled="isLoading"
              @click="goBack"
            >
              Back to Login
            </button>
          </form>
        </div>

        <footer class="mobile-login__footer">
          <a
            href="#"
            class="mobile-login__footer-link"
            @click.prevent
          >
            Learn more about Aura Project
          </a>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup>
import logBackground from '@/assets/images/login_bg.jpg'
import { useForgotPasswordViewModel } from '@/composables/useForgotPasswordViewModel.js'

const auraLogoWhite = '/logos/aura_logo_white.png'
const heroBackgroundStyle = {
  backgroundImage: `linear-gradient(180deg, rgba(0, 0, 0, 0.08) 0%, rgba(0, 0, 0, 0.32) 100%), url(${logBackground})`,
}

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
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.mobile-login {
  min-height: 100dvh;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.12), transparent 32%),
    #060606;
  color: #121212;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'SF Pro Display',
    'Segoe UI',
    sans-serif;
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-font-smoothing: antialiased;
}

.mobile-login__frame {
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  max-width: 480px;
  margin: 0 auto;
}

.mobile-login__hero {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: clamp(240px, 38vh, 340px);
  padding:
    calc(env(safe-area-inset-top, 0px) + 44px)
    28px
    72px;
  background-color: #050505;
  background-position: center;
  background-repeat: no-repeat;
  background-size: cover;
  overflow: hidden;
  transform: translateY(20px);
  opacity: 0;
  transition:
    transform 0.72s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.72s ease;
}

.mobile-login--mounted .mobile-login__hero {
  transform: translateY(0);
  opacity: 1;
}

.mobile-login__hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 28%, rgba(255, 255, 255, 0.16), transparent 28%),
    linear-gradient(180deg, rgba(0, 0, 0, 0.08) 0%, rgba(0, 0, 0, 0.3) 100%);
  mix-blend-mode: screen;
  pointer-events: none;
}

.mobile-login__hero-overlay {
  position: absolute;
  inset: auto 0 0;
  height: 130px;
  background: linear-gradient(180deg, transparent 0%, rgba(0, 0, 0, 0.3) 100%);
  pointer-events: none;
}

.mobile-login__logo {
  position: relative;
  z-index: 1;
  width: min(92px, 24vw);
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 10px 30px rgba(255, 255, 255, 0.08));
}

.mobile-login__sheet {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  margin-top: -44px;
  padding:
    clamp(38px, 8vw, 52px)
    clamp(28px, 8vw, 38px)
    calc(env(safe-area-inset-bottom, 0px) + 26px);
  background: #f7f7f4;
  border-top-left-radius: 52px;
  border-top-right-radius: 0;
  box-shadow: 0 -14px 42px rgba(0, 0, 0, 0.18);
  transform: translateY(34px);
  opacity: 0;
  transition:
    transform 0.8s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.8s ease;
}

.mobile-login--mounted .mobile-login__sheet {
  transform: translateY(0);
  opacity: 1;
}

.mobile-login__content {
  width: 100%;
  max-width: 336px;
  margin: 0 auto;
}

.mobile-login__title {
  margin: 0 0 16px;
  font-size: clamp(2rem, 6.4vw, 2.3rem);
  font-weight: 600;
  letter-spacing: -0.04em;
  line-height: 1.02;
  color: #111111;
}

.mobile-login__subtitle {
  margin: 0 0 32px;
  font-size: 0.95rem;
  line-height: 1.5;
  color: rgba(17, 17, 17, 0.68);
}

.mobile-login__form {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.mobile-login__field {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 0 4px 10px;
  border-bottom: 1.4px solid rgba(15, 15, 15, 0.34);
}

.mobile-login__input {
  width: 100%;
  border: 0;
  padding: 0;
  background: transparent;
  color: #131313;
  font-size: 1.05rem;
  font-weight: 400;
  line-height: 1.4;
  outline: none;
  appearance: none;
}

.mobile-login__input::placeholder {
  color: rgba(17, 17, 17, 0.28);
}

.mobile-login__input:disabled {
  cursor: not-allowed;
  opacity: 0.56;
}

.mobile-login__message {
  margin: -6px 0 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: #c33232;
}

.mobile-login__message--success {
  color: #2d7a3e;
}

.mobile-login__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 58px;
  border-radius: 999px;
  padding: 0 24px;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    opacity 0.18s ease,
    background-color 0.18s ease,
    color 0.18s ease,
    border-color 0.18s ease;
}

.mobile-login__button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.mobile-login__button:active:not(:disabled) {
  transform: scale(0.985);
}

.mobile-login__button--primary {
  margin-top: 10px;
  border: 0;
  background: #050505;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
}

.mobile-login__button--secondary {
  border: 1.35px solid rgba(10, 10, 10, 0.72);
  background: transparent;
  color: #161616;
}

.mobile-login__footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
  margin-top: auto;
  padding-top: 52px;
  flex-wrap: wrap;
}

.mobile-login__footer-link {
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: -0.015em;
  color: rgba(16, 16, 16, 0.72);
  text-decoration: none;
  transition: color 0.18s ease;
}

.mobile-login__footer-link:active {
  color: #0c0c0c;
}

.login-message-enter-active,
.login-message-leave-active {
  transition:
    opacity 0.24s ease,
    transform 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}

.login-message-enter-from,
.login-message-leave-to {
  opacity: 0;
}

@media (max-height: 720px) {
  .mobile-login__sheet {
    padding-top: 34px;
  }

  .mobile-login__title {
    margin-bottom: 12px;
  }

  .mobile-login__subtitle {
    margin-bottom: 28px;
  }

  .mobile-login__footer {
    padding-top: 40px;
  }
}
</style>
