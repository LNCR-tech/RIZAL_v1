import { Capacitor } from '@capacitor/core'

export const DESKTOP_PLATFORM = 'desktop'
export const MOBILE_PLATFORM = 'mobile'
export const MOBILE_VIEWPORT_MAX_WIDTH = 767

const MOBILE_USER_AGENT_PATTERN = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile/i

function getGlobalWindow() {
  return typeof window !== 'undefined' ? window : null
}

function getGlobalNavigator() {
  return typeof navigator !== 'undefined' ? navigator : null
}

export function hasMobileUserAgent(userAgent = getGlobalNavigator()?.userAgent || '') {
  return MOBILE_USER_AGENT_PATTERN.test(String(userAgent || ''))
}

export function getViewportWidth() {
  const runtimeWindow = getGlobalWindow()
  return runtimeWindow?.innerWidth ?? 1280
}

export function detectRuntimePlatform(options = {}) {
  const viewportWidth = Number(options.viewportWidth ?? getViewportWidth())
  const userAgent = String(options.userAgent ?? getGlobalNavigator()?.userAgent ?? '')
  const nativePlatform = options.nativePlatform ?? Capacitor.isNativePlatform()

  if (nativePlatform) {
    return {
      platform: MOBILE_PLATFORM,
      strategy: 'native',
      viewportWidth,
      userAgent,
    }
  }

  if (hasMobileUserAgent(userAgent)) {
    return {
      platform: MOBILE_PLATFORM,
      strategy: 'user-agent',
      viewportWidth,
      userAgent,
    }
  }

  return {
    platform: viewportWidth <= MOBILE_VIEWPORT_MAX_WIDTH ? MOBILE_PLATFORM : DESKTOP_PLATFORM,
    strategy: 'viewport',
    viewportWidth,
    userAgent,
  }
}

