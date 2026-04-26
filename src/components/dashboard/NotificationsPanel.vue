<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] bg-black/45 backdrop-blur-[3px]"
        @click="$emit('close')"
      ></div>
    </Transition>

    <Transition name="slide-up">
      <section
        v-if="isOpen"
        class="notifications-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="notifications-panel-title"
      >
        <header class="notifications-panel__header">
          <div class="notifications-panel__copy">
            <p class="notifications-panel__eyebrow">Notification center</p>
            <h2 id="notifications-panel-title" class="notifications-panel__title">Notifications</h2>
            <p class="notifications-panel__subtitle">{{ subtitle }}</p>
          </div>

          <div class="notifications-panel__header-actions">
            <button
              type="button"
              class="notifications-panel__icon-btn"
              aria-label="Refresh notifications"
              @click="$emit('refresh')"
            >
              <RefreshCw :size="16" :stroke-width="2.15" />
            </button>
            <button
              type="button"
              class="notifications-panel__icon-btn"
              aria-label="Close notifications"
              @click="$emit('close')"
            >
              <X :size="16" :stroke-width="2.15" />
            </button>
          </div>
        </header>

        <div class="notifications-panel__toolbar">
          <div class="notifications-panel__tabs">
            <button
              type="button"
              class="notifications-panel__tab"
              :class="{ 'notifications-panel__tab--active': activeTab === 'all' }"
              @click="activeTab = 'all'"
            >
              All
            </button>
            <button
              type="button"
              class="notifications-panel__tab"
              :class="{ 'notifications-panel__tab--active': activeTab === 'unread' }"
              @click="activeTab = 'unread'"
            >
              Unread
            </button>
          </div>

          <button
            v-if="unreadCount > 0"
            type="button"
            class="notifications-panel__mark-read"
            @click="$emit('mark-all-read')"
          >
            Mark all read
          </button>
        </div>

        <div class="notifications-panel__list custom-scrollbar">
          <div
            v-if="error"
            class="notifications-panel__status notifications-panel__status--error"
            role="alert"
          >
            {{ error }}
          </div>

          <div
            v-if="loading && filteredNotifications.length === 0"
            class="notifications-panel__status"
          >
            Loading your latest announcements and notifications…
          </div>

          <div
            v-else-if="filteredNotifications.length === 0"
            class="notifications-panel__status"
          >
            {{ emptyStateMessage }}
          </div>

          <button
            v-for="item in filteredNotifications"
            :key="item.id"
            type="button"
            class="notifications-panel__item"
            :class="{ 'notifications-panel__item--unread': item.unread }"
            @click="$emit('item-click', item)"
          >
            <span
              v-if="item.unread"
              class="notifications-panel__unread-dot"
              aria-hidden="true"
            ></span>

            <span
              class="notifications-panel__icon"
              :class="item.iconBgClass || 'bg-[#F3F4F6] text-[#111827]'"
            >
              <component :is="item.icon" v-if="item.icon" :size="18" :stroke-width="2.2" />
            </span>

            <span class="notifications-panel__content">
              <span class="notifications-panel__meta-row">
                <span class="notifications-panel__chip">{{ item.kindLabel || 'Update' }}</span>
                <span v-if="item.metaLabel" class="notifications-panel__chip notifications-panel__chip--muted">{{ item.metaLabel }}</span>
                <span class="notifications-panel__time">{{ item.time }}</span>
              </span>

              <span class="notifications-panel__item-title">{{ item.title }}</span>
              <span class="notifications-panel__item-body">{{ item.bodyPreview }}</span>
            </span>
          </button>
        </div>
      </section>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import { RefreshCw, X } from 'lucide-vue-next'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  notifications: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

defineEmits(['close', 'refresh', 'mark-all-read', 'item-click'])

const activeTab = ref('all')

const unreadCount = computed(() => props.notifications.filter((item) => item.unread).length)

const subtitle = computed(() => {
  if (props.loading && props.notifications.length === 0) {
    return 'Loading the latest activity for this account.'
  }

  if (unreadCount.value > 0) {
    return `${unreadCount.value} unread update${unreadCount.value === 1 ? '' : 's'} across announcements and system activity.`
  }

  if (props.notifications.length > 0) {
    return 'You are caught up across announcements and system activity.'
  }

  return 'Announcements and account activity will appear here.'
})

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return props.notifications.filter((item) => item.unread)
  }

  return props.notifications
})

const emptyStateMessage = computed(() => (
  activeTab.value === 'unread'
    ? 'No unread items right now.'
    : 'No notifications to show yet.'
))

watch(() => props.isOpen, (isOpen) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = isOpen ? 'hidden' : ''
})

onUnmounted(() => {
  if (typeof document !== 'undefined') {
    document.body.style.overflow = ''
  }
})
</script>

<style scoped>
.notifications-panel {
  position: fixed;
  z-index: 101;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  max-height: 86vh;
  flex-direction: column;
  overflow: hidden;
  border-radius: 30px 30px 0 0;
  background:
    radial-gradient(circle at top right, rgba(255, 243, 232, 0.9), transparent 30%),
    linear-gradient(180deg, #ffffff 0%, #fcfcfc 100%);
  box-shadow: 0 24px 72px rgba(15, 23, 42, 0.22);
  font-family: 'Manrope', sans-serif;
}

@media (min-width: 768px) {
  .notifications-panel {
    top: 24px;
    right: 32px;
    bottom: auto;
    left: auto;
    width: min(440px, calc(100vw - 32px));
    max-height: min(80vh, 760px);
    border-radius: 30px;
  }
}

.notifications-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 24px 16px;
}

.notifications-panel__copy {
  min-width: 0;
}

.notifications-panel__eyebrow {
  margin: 0;
  color: #C2410C;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.notifications-panel__title {
  margin: 8px 0 0;
  color: #0F172A;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.notifications-panel__subtitle {
  margin: 8px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.5;
}

.notifications-panel__header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.notifications-panel__icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #0F172A;
  cursor: pointer;
  transition: transform 0.16s ease, background 0.18s ease, border-color 0.18s ease;
}

.notifications-panel__icon-btn:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}

.notifications-panel__icon-btn:active {
  transform: scale(0.97);
}

.notifications-panel__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 24px 16px;
}

.notifications-panel__tabs {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 999px;
  background: rgba(248, 250, 252, 0.95);
}

.notifications-panel__tab {
  border: none;
  border-radius: 999px;
  padding: 9px 14px;
  background: transparent;
  color: #64748B;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.notifications-panel__tab--active {
  background: #FFFFFF;
  color: #0F172A;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

.notifications-panel__mark-read {
  border: none;
  border-radius: 999px;
  padding: 10px 14px;
  background: rgba(15, 23, 42, 0.06);
  color: #0F172A;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.16s ease;
}

.notifications-panel__mark-read:hover {
  background: rgba(15, 23, 42, 0.1);
}

.notifications-panel__mark-read:active {
  transform: scale(0.98);
}

.notifications-panel__list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  padding: 0 24px 24px;
}

.notifications-panel__status {
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 22px;
  padding: 18px 16px;
  background: rgba(255, 255, 255, 0.82);
  color: #64748B;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  text-align: center;
}

.notifications-panel__status--error {
  border-color: rgba(248, 113, 113, 0.32);
  background: #FEF2F2;
  color: #B91C1C;
}

.notifications-panel__item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
  border: 1px solid rgba(226, 232, 240, 0.88);
  border-radius: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.94);
  text-align: left;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.notifications-panel__item:hover {
  border-color: rgba(251, 146, 60, 0.28);
  background: #FFFFFF;
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
}

.notifications-panel__item:active {
  transform: scale(0.992);
}

.notifications-panel__item--unread {
  border-color: rgba(251, 146, 60, 0.36);
  box-shadow: 0 12px 28px rgba(251, 146, 60, 0.08);
}

.notifications-panel__unread-dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #FF5A36;
}

.notifications-panel__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
}

.notifications-panel__content {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.notifications-panel__meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.notifications-panel__chip {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  border-radius: 999px;
  padding: 0 10px;
  background: rgba(255, 243, 232, 0.92);
  color: #C2410C;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.notifications-panel__chip--muted {
  background: rgba(241, 245, 249, 0.95);
  color: #475569;
}

.notifications-panel__time {
  margin-left: auto;
  color: #94A3B8;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.notifications-panel__item-title {
  margin-top: 10px;
  color: #0F172A;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.35;
}

.notifications-panel__item-body {
  margin-top: 6px;
  color: #475569;
  font-size: 13px;
  line-height: 1.55;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.26s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.32s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.24s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(24px);
  opacity: 0;
}

@media (max-width: 767px) {
  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: translateY(100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active,
  .slide-up-enter-active,
  .slide-up-leave-active,
  .notifications-panel__item,
  .notifications-panel__icon-btn,
  .notifications-panel__mark-read,
  .notifications-panel__tab {
    transition: none;
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 999px;
}
</style>
