<template>
  <!-- Trap focus; no click-outside dismiss; no ESC close -->
  <div
    class="perm-gate"
    role="dialog"
    aria-modal="true"
    aria-labelledby="perm-gate-title"
    aria-describedby="perm-gate-desc"
    @keydown.esc.prevent
  >
    <div class="perm-gate__card">
      <!-- Icon -->
      <div class="perm-gate__icon-row" aria-hidden="true">
        <span class="perm-gate__icon-bubble perm-gate__icon-bubble--camera">
          <Camera :size="22" :stroke-width="2.1" />
        </span>
        <template v-if="!cameraOnly">
          <span class="perm-gate__icon-plus">+</span>
          <span class="perm-gate__icon-bubble perm-gate__icon-bubble--location">
            <MapPin :size="22" :stroke-width="2.1" />
          </span>
        </template>
      </div>

      <!-- Checking state -->
      <template v-if="permissionState === 'checking_permissions'">
        <h2 id="perm-gate-title" class="perm-gate__title">Checking permissions…</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">Please wait.</p>
        <div class="perm-gate__spinner-row" aria-hidden="true">
          <LoaderCircle :size="24" :stroke-width="2.1" class="perm-gate__spinner" />
        </div>
      </template>

      <!-- Insecure context -->
      <template v-else-if="permissionState === 'insecure_context'">
        <h2 id="perm-gate-title" class="perm-gate__title">Secure connection required</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">{{ errorMessage }}</p>
      </template>

      <!-- Not yet requested -->
      <template v-else-if="permissionState === 'permissions_not_requested'">
        <h2 id="perm-gate-title" class="perm-gate__title">Permissions required</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">
          <template v-if="cameraOnly">
            Camera access is required to use face recognition. Please allow camera access to continue.
          </template>
          <template v-else>
            Camera and location access are required to use attendance sign-in. Please allow both permissions to continue.
          </template>
        </p>
        <button
          type="button"
          class="perm-gate__btn perm-gate__btn--primary"
          :disabled="isRequesting"
          @click="$emit('request')"
        >
          <LoaderCircle v-if="isRequesting" :size="16" :stroke-width="2.1" class="perm-gate__spinner" />
          {{ enableButtonLabel }}
        </button>
      </template>

      <!-- Prompt blocked -->
      <template v-else-if="permissionState === 'permission_prompt_blocked'">
        <h2 id="perm-gate-title" class="perm-gate__title">Permissions blocked</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">{{ errorMessage }}</p>
        <p class="perm-gate__hint">
          If the permission popup does not appear, click the lock icon beside the website URL,
          allow {{ cameraOnly ? 'Camera' : 'Camera and Location' }}, then refresh the page.
        </p>
        <button
          type="button"
          class="perm-gate__btn perm-gate__btn--secondary"
          :disabled="isRequesting"
          @click="$emit('retry')"
        >
          Try Again
        </button>
      </template>

      <!-- Denied states -->
      <template v-else-if="isDeniedState">
        <h2 id="perm-gate-title" class="perm-gate__title">Permission denied</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">{{ errorMessage }}</p>
        <p class="perm-gate__hint">
          If the permission popup does not appear, click the lock icon beside the website URL,
          allow {{ cameraOnly ? 'Camera' : 'Camera and Location' }}, then refresh the page.
        </p>
        <button
          type="button"
          class="perm-gate__btn perm-gate__btn--secondary"
          :disabled="isRequesting"
          @click="$emit('retry')"
        >
          <LoaderCircle v-if="isRequesting" :size="16" :stroke-width="2.1" class="perm-gate__spinner" />
          Try Again
        </button>
      </template>

      <!-- Unexpected error -->
      <template v-else-if="permissionState === 'permission_error'">
        <h2 id="perm-gate-title" class="perm-gate__title">Something went wrong</h2>
        <p id="perm-gate-desc" class="perm-gate__desc">{{ errorMessage }}</p>
        <button
          type="button"
          class="perm-gate__btn perm-gate__btn--secondary"
          :disabled="isRequesting"
          @click="$emit('retry')"
        >
          Try Again
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Camera, LoaderCircle, MapPin } from 'lucide-vue-next'

const props = defineProps({
  permissionState: {
    type: String,
    required: true,
  },
  errorMessage: {
    type: String,
    default: '',
  },
  isRequesting: {
    type: Boolean,
    default: false,
  },
  cameraOnly: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['request', 'retry'])

const DENIED_STATES = new Set(['camera_denied', 'location_denied', 'both_denied'])
const isDeniedState = computed(() => DENIED_STATES.has(props.permissionState))

const enableButtonLabel = computed(() =>
  props.cameraOnly ? 'Enable Camera' : 'Enable Camera and Location'
)
</script>

<style scoped>
.perm-gate {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0 16px max(24px, env(safe-area-inset-bottom, 24px));
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.perm-gate__card {
  width: min(100%, 400px);
  padding: 28px 24px 24px;
  border-radius: 28px;
  background: #ffffff;
  box-shadow: 0 24px 56px rgba(7, 14, 23, 0.28);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  text-align: center;
}

.perm-gate__icon-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.perm-gate__icon-bubble {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.perm-gate__icon-bubble--camera {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
}

.perm-gate__icon-bubble--location {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.perm-gate__icon-plus {
  font-size: 20px;
  font-weight: 700;
  color: #94a3b8;
  line-height: 1;
}

.perm-gate__title {
  margin: 0;
  font-size: 20px;
  line-height: 1.1;
  font-weight: 700;
  color: #111827;
  letter-spacing: -0.02em;
}

.perm-gate__desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #475569;
}

.perm-gate__hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.55;
  color: #64748b;
  padding: 10px 14px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid rgba(15, 23, 42, 0.07);
  text-align: left;
}

.perm-gate__spinner-row {
  display: flex;
  justify-content: center;
}

.perm-gate__btn {
  width: 100%;
  min-height: 52px;
  border: none;
  border-radius: 999px;
  font-family: 'Manrope', sans-serif;
  font-size: 16px;
  line-height: 1;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: opacity 160ms ease, transform 160ms ease;
}

.perm-gate__btn:disabled {
  opacity: 0.65;
}

.perm-gate__btn:active:not(:disabled) {
  transform: scale(0.98);
}

.perm-gate__btn--primary {
  background: #111827;
  color: #ffffff;
}

.perm-gate__btn--secondary {
  background: #f1f5f9;
  color: #1e293b;
}

.perm-gate__spinner {
  animation: perm-gate-spin 0.9s linear infinite;
  flex-shrink: 0;
}

@keyframes perm-gate-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .perm-gate__spinner,
  .perm-gate__btn {
    animation: none;
    transition: none;
  }
}
</style>
