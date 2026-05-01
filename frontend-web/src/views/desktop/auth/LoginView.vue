<template>
  <div class="desktop-login" :class="{ 'desktop-login--mounted': isMounted }">
    <!-- Left: Dynamic Obsidian Hero -->
    <ObsidianHero class="desktop-login__hero">
      <div class="desktop-login__hero-content">
        <img :src="auraLogoWhite" alt="Aura" class="desktop-login__logo" />
        
        <div class="desktop-login__hero-text">
          <h2 class="desktop-login__hero-headline">
            The Intelligence <br />
            <span>of your Campus.</span>
          </h2>
          <p class="desktop-login__hero-tagline">
            Automate, monitor, and scale your institution with Aura AI.
          </p>
        </div>
      </div>
    </ObsidianHero>

    <!-- Right: Form sheet -->
    <div class="desktop-login__sheet">
      <div class="desktop-login__content">
        <h1 class="desktop-login__title">Log In.</h1>

        <form class="desktop-login__form" @submit.prevent="handleLogin">
          <label class="desktop-login__field">
            <span class="sr-only">Gmail</span>
            <input
              id="email"
              v-model="email"
              class="desktop-login__input"
              type="email"
              placeholder="Gmail"
              autocomplete="email"
              autocapitalize="none"
              spellcheck="false"
              :disabled="isLoading || googleLoading"
            />
          </label>

          <label class="desktop-login__field desktop-login__field--password">
            <span class="sr-only">Password</span>
            <input
              id="password"
              v-model="password"
              class="desktop-login__input"
              :type="passwordVisible ? 'text' : 'password'"
              placeholder="Password"
              autocomplete="current-password"
              :disabled="isLoading || googleLoading"
            />
            <button
              type="button"
              class="desktop-login__field-action"
              :aria-label="passwordVisible ? 'Hide password' : 'Show password'"
              :disabled="isLoading || googleLoading"
              @click="passwordVisible = !passwordVisible"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M1.5 12s3.75-6.75 10.5-6.75S22.5 12 22.5 12 18.75 18.75 12 18.75 1.5 12 1.5 12Z"
                  fill="none" stroke="currentColor" stroke-linecap="round"
                  stroke-linejoin="round" stroke-width="1.6"
                />
                <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.6" />
              </svg>
            </button>
          </label>

          <div class="desktop-login__forgot-password">
            <a href="#" class="desktop-login__forgot-link" @click.prevent="goToForgotPassword">
              Forgot password?
            </a>
          </div>

          <Transition name="login-message">
            <p v-if="visibleMessage" class="desktop-login__message">{{ visibleMessage }}</p>
          </Transition>

          <button
            type="submit"
            class="desktop-login__button desktop-login__button--primary"
            :disabled="isLoading || googleLoading"
          >
            {{ isLoading ? 'Logging In...' : 'Log In' }}
          </button>

          <div class="desktop-login__divider" aria-hidden="true">
            <span /><strong>or</strong><span />
          </div>

          <div class="desktop-login__google">
            <GoogleSignInButton @credential="handleGoogleCredential" />
          </div>
        </form>
      </div>

      <footer class="desktop-login__footer">
        <div class="desktop-login__footer-branding">
          <img src="/logos/aura_logo_black.png" alt="Aura" class="desktop-login__footer-logo" />
          <span class="desktop-login__footer-powered">Powered by Aura Ai</span>
        </div>
        <a
          href="https://aura-landing-page-iota.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          class="desktop-login__footer-link"
        >
          Learn more about Aura Project
        </a>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import ObsidianHero from '@/components/auth/ObsidianHero.vue'
import { useLoginViewModel } from '@/composables/useLoginViewModel.js'

const passwordVisible = ref(false)
const auraLogoWhite = '/logos/aura_logo_white.png'

const {
  email, password, isMounted, isLoading, googleLoading,
  visibleMessage, handleLogin, handleGoogleCredential, goToForgotPassword,
} = useLoginViewModel()
</script>

<style scoped>
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0;
  margin: -1px; overflow: hidden; clip: rect(0,0,0,0);
  white-space: nowrap; border: 0;
}

.desktop-login {
  display: flex;
  min-height: 100dvh;
  font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

/* Hero — left half */
.desktop-login__hero {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 52px 40px;
  opacity: 0;
  transform: translateX(-24px);
  transition: opacity 0.72s ease, transform 0.72s cubic-bezier(0.22, 1, 0.36, 1);
}

.desktop-login--mounted .desktop-login__hero {
  opacity: 1;
  transform: translateX(0);
}

.desktop-login__hero-content {
  position: relative;
  z-index: 10;
  width: 100%;
  height: 100%;
  padding: 60px 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none; /* Let clicks pass through to the mesh */
}

.desktop-login__logo {
  width: 48px;
  height: auto;
  opacity: 0;
  transform: translateY(-20px);
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.desktop-login--mounted .desktop-login__logo {
  opacity: 1;
  transform: translateY(0);
}

.desktop-login__hero-text {
  margin-top: auto;
  margin-bottom: 40px;
}

.desktop-login__hero-headline {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.1;
  color: #ffffff;
  letter-spacing: -0.04em;
  margin-bottom: 24px;
  opacity: 0;
  transform: translateY(30px);
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s;
}

.desktop-login__hero-headline span {
  color: rgba(255, 255, 255, 0.4);
}

.desktop-login--mounted .desktop-login__hero-headline {
  opacity: 1;
  transform: translateY(0);
}

.desktop-login__hero-tagline {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.5);
  max-width: 400px;
  line-height: 1.6;
  opacity: 0;
  transform: translateY(20px);
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1) 0.4s;
}

.desktop-login--mounted .desktop-login__hero-tagline {
  opacity: 1;
  transform: translateY(0);
}

.desktop-login--mounted .desktop-login__hero-tagline {
  opacity: 1;
  transform: translateY(0);
}

/* Sheet — right half */
.desktop-login__sheet {
  width: min(480px, 45vw);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #f7f7f4;
  padding: 52px 52px calc(env(safe-area-inset-bottom, 0px) + 32px);
  opacity: 0;
  transform: translateX(24px);
  transition: opacity 0.8s ease, transform 0.8s cubic-bezier(0.22, 1, 0.36, 1);
  overflow-y: auto;
}

.desktop-login--mounted .desktop-login__sheet {
  opacity: 1;
  transform: translateX(0);
}

.desktop-login__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 360px;
  width: 100%;
  margin: 0 auto;
}

.desktop-login__title {
  margin: 0 0 48px;
  font-size: 2.4rem;
  font-weight: 600;
  letter-spacing: -0.04em;
  line-height: 1.02;
  color: #111111;
}

.desktop-login__form {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.desktop-login__field {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 0 4px 10px;
  border-bottom: 1.4px solid rgba(15,15,15,0.34);
}

.desktop-login__field--password { padding-right: 40px; }

.desktop-login__input {
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

.desktop-login__input::placeholder { color: rgba(17,17,17,0.28); }
.desktop-login__input:disabled { cursor: not-allowed; opacity: 0.56; }

.desktop-login__field-action {
  position: absolute;
  right: 0; top: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px; height: 30px;
  margin-top: -16px;
  border: 0; border-radius: 999px;
  background: transparent;
  color: rgba(17,17,17,0.84);
  padding: 0; cursor: pointer;
}

.desktop-login__field-action:disabled { opacity: 0.48; }
.desktop-login__field-action svg { width: 21px; height: 21px; }

.desktop-login__message {
  margin: -6px 0 0;
  font-size: 0.78rem;
  line-height: 1.45;
  color: #c33232;
}

.desktop-login__button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 58px;
  border-radius: 999px;
  padding: 0 24px;
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: -0.02em;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.desktop-login__button:disabled { cursor: not-allowed; opacity: 0.6; }
.desktop-login__button:active:not(:disabled) { transform: scale(0.985); }

.desktop-login__button--primary {
  margin-top: 10px;
  border: 0;
  background: #050505;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(0,0,0,0.14);
}

.desktop-login__forgot-password {
  display: flex;
  justify-content: flex-end;
  margin-top: -10px;
}

.desktop-login__forgot-link {
  font-size: 0.88rem;
  font-weight: 500;
  letter-spacing: -0.015em;
  color: rgba(16,16,16,0.72);
  text-decoration: none;
  transition: color 0.18s ease;
}

.desktop-login__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: -4px 0;
  color: rgba(16,16,16,0.54);
}

.desktop-login__divider span {
  flex: 1; height: 1px;
  background: rgba(16,16,16,0.18);
}

.desktop-login__divider strong {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.desktop-login__google { min-height: 44px; }

.desktop-login__footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-top: 40px;
  max-width: 360px;
  width: 100%;
  margin: 0 auto;
}

.desktop-login__footer-branding {
  display: flex;
  align-items: center;
  gap: 10px;
}

.desktop-login__footer-logo { width: 28px; height: 28px; object-fit: contain; }

.desktop-login__footer-powered {
  font-size: 0.82rem;
  font-weight: 500;
  letter-spacing: -0.015em;
  color: rgba(16,16,16,0.82);
}

.desktop-login__footer-link {
  font-size: 0.78rem;
  font-weight: 500;
  color: rgba(16,16,16,0.72);
  text-decoration: none;
  transition: color 0.18s ease;
}

.login-message-enter-active, .login-message-leave-active {
  transition: opacity 0.24s ease, transform 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}
.login-message-enter-from, .login-message-leave-to { opacity: 0; }
</style>
