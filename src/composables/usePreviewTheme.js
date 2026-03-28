import { watch, unref } from 'vue'
import { applyTheme, loadTheme } from '@/config/theme.js'

export function usePreviewTheme(previewSource, schoolSettingsSource) {
  watch(
    [() => unref(previewSource), () => unref(schoolSettingsSource)],
    ([preview, schoolSettings]) => {
      if (!preview || !schoolSettings) return
      applyTheme(loadTheme(schoolSettings))
    },
    { immediate: true, deep: true }
  )
}
