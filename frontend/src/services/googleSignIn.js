import { resolveGoogleWebClientId } from '@/config/googleAuth.js'

const GIS_SCRIPT_URL = 'https://accounts.google.com/gsi/client'
let scriptPromise = null

function loadGisScript() {
    if (typeof window === 'undefined') {
        return Promise.reject(new Error('Google Sign-In is only available in the browser.'))
    }
    if (window.google?.accounts?.id) {
        return Promise.resolve(window.google)
    }
    if (scriptPromise) return scriptPromise

    scriptPromise = new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${GIS_SCRIPT_URL}"]`)
        const handleLoad = () => {
            if (window.google?.accounts?.id) resolve(window.google)
            else reject(new Error('Google Identity Services failed to initialize.'))
        }
        if (existing) {
            existing.addEventListener('load', handleLoad)
            existing.addEventListener('error', () => reject(new Error('Failed to load Google script.')))
            return
        }
        const script = document.createElement('script')
        script.src = GIS_SCRIPT_URL
        script.async = true
        script.defer = true
        script.onload = handleLoad
        script.onerror = () => reject(new Error('Failed to load Google script.'))
        document.head.appendChild(script)
    })

    return scriptPromise
}

export async function ensureGoogleClientReady() {
    const clientId = resolveGoogleWebClientId()
    if (!clientId) throw new Error('Google login is not configured.')
    const google = await loadGisScript()
    return { google, clientId }
}

export async function renderGoogleButton(targetElement, { onCredential, theme = 'outline', size = 'large' } = {}) {
    const { google, clientId } = await ensureGoogleClientReady()
    google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
            if (response?.credential) onCredential(response.credential)
        },
        ux_mode: 'popup',
        auto_select: false,
    })
    google.accounts.id.renderButton(targetElement, {
        theme,
        size,
        type: 'standard',
        shape: 'pill',
        text: 'continue_with',
        logo_alignment: 'left',
        locale: 'en',
        width: targetElement?.clientWidth || 320,
    })
}

export async function signInWithGooglePopup() {
    const { google, clientId } = await ensureGoogleClientReady()
    return new Promise((resolve, reject) => {
        google.accounts.id.initialize({
            client_id: clientId,
            callback: (response) => {
                if (response?.credential) resolve(response.credential)
                else reject(new Error('No credential returned by Google.'))
            },
            ux_mode: 'popup',
            auto_select: false,
        })
        google.accounts.id.prompt((notification) => {
            if (notification.isNotDisplayed?.() || notification.isSkippedMoment?.()) {
                reject(new Error('Google sign-in was dismissed.'))
            }
        })
    })
}
