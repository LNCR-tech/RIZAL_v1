import { computed, ref } from 'vue'

const MOBILE_FULLSCREEN_HINT_KEY = 'aura_mobile_fullscreen_hint_seen'
const mobileFullscreenEligible = ref(false)
const mobileFullscreenHintDismissed = ref(false)

function isAndroid() {
    if (typeof navigator === 'undefined') return false
    return /android/i.test(navigator.userAgent || '')
}

function isLikelyMobileViewport() {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
    return window.matchMedia('(max-width: 900px)').matches
}

function isStandaloneDisplay() {
    if (typeof window === 'undefined') return false

    return (
        window.matchMedia?.('(display-mode: standalone)').matches ||
        window.matchMedia?.('(display-mode: fullscreen)').matches ||
        window.navigator?.standalone === true
    )
}

function canRequestFullscreen() {
    if (typeof document === 'undefined') return false
    return (
        typeof document.documentElement?.requestFullscreen === 'function' &&
        document.fullscreenEnabled !== false
    )
}

function markMobileFullscreenHintDismissed() {
    mobileFullscreenHintDismissed.value = true

    if (typeof window !== 'undefined') {
        window.sessionStorage?.setItem(MOBILE_FULLSCREEN_HINT_KEY, '1')
    }
}

export const mobileFullscreenHintVisible = computed(() => {
    return mobileFullscreenEligible.value && !mobileFullscreenHintDismissed.value
})

export async function requestMobileFullscreen() {
    if (!canRequestFullscreen() || isStandaloneDisplay()) return

    try {
        await document.documentElement.requestFullscreen({ navigationUI: 'hide' })
    } catch {
        // Ignore platform-level fullscreen rejections. Android browsers may refuse
        // this outside supported contexts, but the app still benefits from PWA mode.
    }
}

export function startMobileFullscreenSync() {
    if (typeof window === 'undefined') return
    const eligible =
        isAndroid() &&
        isLikelyMobileViewport() &&
        !isStandaloneDisplay() &&
        canRequestFullscreen()

    mobileFullscreenEligible.value = eligible
    mobileFullscreenHintDismissed.value =
        window.sessionStorage?.getItem(MOBILE_FULLSCREEN_HINT_KEY) === '1'

    if (!eligible) return

    let attempted = false

    const handleFirstInteraction = () => {
        if (attempted) return
        attempted = true
        markMobileFullscreenHintDismissed()
        requestMobileFullscreen().catch(() => null)
    }

    const handleFullscreenChange = () => {
        if (document.fullscreenElement) {
            markMobileFullscreenHintDismissed()
        }
    }

    window.addEventListener('pointerup', handleFirstInteraction, {
        once: true,
        passive: true,
    })
    document.addEventListener('fullscreenchange', handleFullscreenChange, {
        passive: true,
    })
}

export function registerAuraServiceWorker() {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return
    if (!window.isSecureContext && window.location.hostname !== 'localhost') return

    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => null)
    }, { once: true })
}
