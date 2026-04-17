const FONT_SIZE_STORAGE_KEY = 'aura_font_size'
const REMEMBER_ME_STORAGE_KEY = 'aura_remember_me'

export const FONT_SIZE_MIN = 80
export const FONT_SIZE_MAX = 130
export const FONT_SIZE_STEP = 5
export const DEFAULT_FONT_SIZE = 100

export function snapFontSize(value) {
  const numericValue = Number(value)
  const safeValue = Number.isFinite(numericValue) ? numericValue : DEFAULT_FONT_SIZE
  const steppedValue = Math.round(safeValue / FONT_SIZE_STEP) * FONT_SIZE_STEP
  return Math.min(FONT_SIZE_MAX, Math.max(FONT_SIZE_MIN, steppedValue))
}

export function getStoredFontSize() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return DEFAULT_FONT_SIZE
  }

  try {
    const rawValue = Number(window.localStorage.getItem(FONT_SIZE_STORAGE_KEY) ?? DEFAULT_FONT_SIZE)
    const isModernStoredValue = Number.isFinite(rawValue) && rawValue >= FONT_SIZE_MIN && rawValue <= FONT_SIZE_MAX
    const normalizedValue = isModernStoredValue ? snapFontSize(rawValue) : DEFAULT_FONT_SIZE

    if (!isModernStoredValue || rawValue !== normalizedValue) {
      window.localStorage.setItem(FONT_SIZE_STORAGE_KEY, String(normalizedValue))
    }

    return normalizedValue
  } catch {
    return DEFAULT_FONT_SIZE
  }
}

export function applyFontSizePreference(value) {
  const normalizedValue = snapFontSize(value)

  if (typeof document === 'undefined') {
    return normalizedValue
  }

  const root = document.documentElement
  const baseSize = 16 * (normalizedValue / 100)

  root.style.zoom = ''
  root.style.setProperty('--aura-font-base', `${baseSize}px`)
  root.style.setProperty('--aura-text-size-adjust', `${normalizedValue}%`)

  return normalizedValue
}

export function storeFontSizePreference(value) {
  const normalizedValue = applyFontSizePreference(value)

  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return normalizedValue
  }

  try {
    window.localStorage.setItem(FONT_SIZE_STORAGE_KEY, String(normalizedValue))
  } catch {
    // Ignore storage failures and keep the live UI usable.
  }

  return normalizedValue
}

export function initializeStoredFontSize() {
  const normalizedValue = getStoredFontSize()
  applyFontSizePreference(normalizedValue)
  return normalizedValue
}

export function getStoredRememberMePreference() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return false
  }

  try {
    return window.localStorage.getItem(REMEMBER_ME_STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

export function storeRememberMePreference(value) {
  const normalizedValue = Boolean(value)

  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return normalizedValue
  }

  try {
    window.localStorage.setItem(REMEMBER_ME_STORAGE_KEY, normalizedValue ? '1' : '0')
  } catch {
    // Ignore storage failures and keep login usable.
  }

  return normalizedValue
}
