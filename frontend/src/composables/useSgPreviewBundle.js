import { computed, unref } from 'vue'
import { useRoute } from 'vue-router'
import { getSgPreviewBundle, resolveSgPreviewVariant } from '@/data/sgPreviewData.js'

export function useSgPreviewBundle(previewSource = false) {
  const route = useRoute()
  const previewEnabled = computed(() => (
    typeof previewSource === 'function'
      ? Boolean(previewSource())
      : Boolean(unref(previewSource))
  ))
  const previewVariant = computed(() => resolveSgPreviewVariant(route.query?.variant))
  const previewBundle = computed(() => (
    previewEnabled.value ? getSgPreviewBundle(previewVariant.value) : null
  ))

  return {
    previewVariant,
    previewBundle,
  }
}
