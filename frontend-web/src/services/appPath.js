function normalizeBaseUrl(value = '/') {
    const normalized = String(value || '/').trim()

    if (!normalized || normalized === '/') {
        return '/'
    }

    return `/${normalized.replace(/^\/+|\/+$/g, '')}/`
}

export function readEnvFlag(value = '') {
    return ['1', 'true', 'yes', 'on'].includes(String(value || '').trim().toLowerCase())
}

export const appBaseUrl = normalizeBaseUrl(import.meta.env.BASE_URL || '/')
export const hashRouterEnabled = readEnvFlag(import.meta.env.VITE_USE_HASH_ROUTER)

export function withBase(path = '') {
    const normalized = String(path || '').trim()

    if (!normalized) {
        return appBaseUrl
    }

    if (/^(?:[a-z]+:)?\/\//i.test(normalized) || normalized.startsWith('data:')) {
        return normalized
    }

    return `${appBaseUrl}${normalized.replace(/^\/+/, '')}`
}
