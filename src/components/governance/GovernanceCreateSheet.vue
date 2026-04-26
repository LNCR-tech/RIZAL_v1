<template>
  <Transition name="governance-create-sheet">
    <div
      v-if="open"
      class="governance-create-sheet__backdrop"
      @click.self="$emit('close')"
    >
      <section
        class="governance-create-sheet__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="governance-create-sheet-title"
      >
        <span class="governance-create-sheet__handle" aria-hidden="true" />

        <header class="governance-create-sheet__header">
          <div class="governance-create-sheet__copy">
            <p class="governance-create-sheet__eyebrow">Quick Create</p>
            <h2 id="governance-create-sheet-title" class="governance-create-sheet__title">
              What do you want to create?
            </h2>
            <p class="governance-create-sheet__description">
              Start the next governance task without losing your current context.
            </p>
          </div>

          <button
            type="button"
            class="governance-create-sheet__close"
            aria-label="Close create options"
            @click="$emit('close')"
          >
            <X :size="18" :stroke-width="2.1" />
          </button>
        </header>

        <div class="governance-create-sheet__actions">
          <button
            v-for="action in actions"
            :key="action.key"
            type="button"
            class="governance-create-sheet__action"
            :class="{ 'governance-create-sheet__action--disabled': action.disabled }"
            :disabled="action.disabled"
            @click="$emit('select', action)"
          >
            <div class="governance-create-sheet__action-icon">
              <component :is="action.icon" :size="18" :stroke-width="2" />
            </div>

            <div class="governance-create-sheet__action-copy">
              <strong>{{ action.label }}</strong>
              <span>{{ action.description }}</span>
            </div>

            <small
              v-if="action.disabled"
              class="governance-create-sheet__action-meta"
            >
              {{ action.disabledReason || 'Permission required' }}
            </small>
            <ArrowRight
              v-else
              :size="16"
              :stroke-width="2"
              class="governance-create-sheet__action-arrow"
            />
          </button>
        </div>
      </section>
    </div>
  </Transition>
</template>

<script setup>
import { ArrowRight, X } from 'lucide-vue-next'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  actions: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['close', 'select'])
</script>

<style scoped>
.governance-create-sheet__backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 24px;
  background: color-mix(in srgb, var(--color-nav) 32%, transparent);
  backdrop-filter: blur(12px);
}

.governance-create-sheet__panel {
  width: min(100%, 560px);
  border-radius: 34px;
  padding: 18px 18px 20px;
  background: var(--color-surface);
  box-shadow: 0 28px 72px color-mix(in srgb, var(--color-nav) 18%, transparent);
}

.governance-create-sheet__handle {
  width: 54px;
  height: 5px;
  display: block;
  margin: 0 auto 18px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-text-muted) 22%, transparent);
}

.governance-create-sheet__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.governance-create-sheet__copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.governance-create-sheet__eyebrow {
  margin: 0;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary);
}

.governance-create-sheet__title {
  margin: 0;
  font-size: 24px;
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
}

.governance-create-sheet__description {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.governance-create-sheet__close {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-bg) 50%, var(--color-surface));
  color: var(--color-text-primary);
}

.governance-create-sheet__actions {
  display: grid;
  gap: 12px;
}

.governance-create-sheet__action {
  width: 100%;
  border: none;
  padding: 16px;
  border-radius: 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
  background: color-mix(in srgb, var(--color-bg) 54%, var(--color-surface));
  color: inherit;
}

.governance-create-sheet__action--disabled {
  opacity: 0.56;
}

.governance-create-sheet__action-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--color-primary) 14%, transparent);
  color: var(--color-primary);
}

.governance-create-sheet__action-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.governance-create-sheet__action-copy strong {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.governance-create-sheet__action-copy span,
.governance-create-sheet__action-meta {
  font-size: 13px;
  line-height: 1.55;
  color: var(--color-text-muted);
}

.governance-create-sheet__action-meta {
  max-width: 120px;
  text-align: right;
}

.governance-create-sheet__action-arrow {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.governance-create-sheet-enter-active,
.governance-create-sheet-leave-active {
  transition: opacity 0.26s ease;
}

.governance-create-sheet-enter-active .governance-create-sheet__panel,
.governance-create-sheet-leave-active .governance-create-sheet__panel {
  transition: transform 0.36s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.24s ease;
}

.governance-create-sheet-enter-from,
.governance-create-sheet-leave-to {
  opacity: 0;
}

.governance-create-sheet-enter-from .governance-create-sheet__panel,
.governance-create-sheet-leave-to .governance-create-sheet__panel {
  transform: translateY(24px);
  opacity: 0;
}

@media (max-width: 767px) {
  .governance-create-sheet__backdrop {
    padding: 12px 12px calc(12px + env(safe-area-inset-bottom, 0px));
  }

  .governance-create-sheet__panel {
    width: 100%;
    border-radius: 30px;
  }
}
</style>
