export function resolveGoogleWebClientId() {
    const runtime = typeof window !== 'undefined' ? window.__AURA_RUNTIME_CONFIG__ : null
    const fromRuntime = runtime?.googleWebClientId
    if (fromRuntime && !fromRuntime.startsWith('${')) {
        return String(fromRuntime).trim()
    }
    const fromEnv = import.meta?.env?.VITE_GOOGLE_WEB_CLIENT_ID
    return String(fromEnv ?? '').trim()
}

export function isGoogleLoginAvailable() {
    return resolveGoogleWebClientId().length > 0
}
