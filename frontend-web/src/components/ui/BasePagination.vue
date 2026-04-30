<template>
  <nav v-if="totalPages > 1" class="base-pagination" aria-label="Pagination">
    <button
      class="base-pagination__btn base-pagination__btn--prev"
      :disabled="currentPage <= 1 || loading"
      type="button"
      aria-label="Previous page"
      @click="$emit('page-change', currentPage - 1)"
    >
      <ChevronLeft :size="18" :stroke-width="2.2" />
      <span class="base-pagination__label">Previous</span>
    </button>

    <div class="base-pagination__info">
      <span class="base-pagination__text">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <span v-if="total > 0" class="base-pagination__meta">
        {{ total }} total {{ total === 1 ? 'item' : 'items' }}
      </span>
    </div>

    <button
      class="base-pagination__btn base-pagination__btn--next"
      :disabled="currentPage >= totalPages || loading"
      type="button"
      aria-label="Next page"
      @click="$emit('page-change', currentPage + 1)"
    >
      <span class="base-pagination__label">Next</span>
      <ChevronRight :size="18" :stroke-width="2.2" />
    </button>
  </nav>
</template>

<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

defineProps({
  currentPage: {
    type: Number,
    required: true,
    default: 1,
  },
  totalPages: {
    type: Number,
    required: true,
    default: 1,
  },
  total: {
    type: Number,
    default: 0,
  },
  limit: {
    type: Number,
    default: 20,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['page-change'])
</script>

<style scoped>
.base-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 24px;
  background: var(--color-surface);
  box-shadow: 0 8px 20px color-mix(in srgb, var(--color-nav) 6%, transparent);
  margin-top: 20px;
}

.base-pagination__btn {
  min-height: 48px;
  padding: 0 18px;
  border: none;
  border-radius: 16px;
  background: var(--color-primary);
  color: var(--color-banner-text);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease, filter 0.18s ease;
  font-family: 'Manrope', sans-serif;
}

.base-pagination__btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.base-pagination__btn:not(:disabled):hover {
  transform: translateY(-1px);
  filter: brightness(1.08);
}

.base-pagination__btn:not(:disabled):active {
  transform: scale(0.96);
}

.base-pagination__info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.base-pagination__text {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
}

.base-pagination__meta {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
}

@media (max-width: 767px) {
  .base-pagination {
    padding: 14px 16px;
    gap: 12px;
  }

  .base-pagination__label {
    display: none;
  }

  .base-pagination__btn {
    min-width: 48px;
    padding: 0 12px;
    justify-content: center;
  }

  .base-pagination__text {
    font-size: 13px;
  }

  .base-pagination__meta {
    font-size: 10px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .base-pagination__btn {
    transition: none;
  }
}
</style>
