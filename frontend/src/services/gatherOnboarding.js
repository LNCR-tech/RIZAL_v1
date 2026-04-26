const GATHER_ONBOARDING_SEEN_KEY = 'aura_gather_onboarding_seen_v1'

function getStorage() {
  if (typeof window === 'undefined' || typeof window.localStorage === 'undefined') {
    return null
  }

  return window.localStorage
}

export function hasSeenGatherOnboarding() {
  const storage = getStorage()
  if (!storage) return false

  try {
    return storage.getItem(GATHER_ONBOARDING_SEEN_KEY) === '1'
  } catch {
    return false
  }
}

export function markGatherOnboardingSeen() {
  const storage = getStorage()
  if (!storage) return

  try {
    storage.setItem(GATHER_ONBOARDING_SEEN_KEY, '1')
  } catch {
    // Ignore storage failures and keep Gather usable.
  }
}

export function clearGatherOnboardingSeen() {
  const storage = getStorage()
  if (!storage) return

  try {
    storage.removeItem(GATHER_ONBOARDING_SEEN_KEY)
  } catch {
    // Ignore storage failures and keep Gather usable.
  }
}
