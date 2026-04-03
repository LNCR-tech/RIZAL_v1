import { watch } from 'vue'
import { resolveLoadableMediaUrl } from '@/services/backendMedia.js'
import { AUTH_META_CHANGED_EVENT, getStoredAuthMeta } from '@/services/localAuth.js'
import { useDashboardSession } from '@/composables/useDashboardSession.js'
import { schoolItPreviewData } from '@/data/schoolItPreview.js'

const DEFAULT_TITLE = 'Aura'
const DEFAULT_ICON_PATH = '/logos/aura.png'
const DEFAULT_ICON_URL = DEFAULT_ICON_PATH
let brandingRequestId = 0

function upsertLink(rel, href) {
    if (typeof document === 'undefined') return

    let link = document.querySelector(`link[rel="${rel}"]`)
    if (!link) {
        link = document.createElement('link')
        link.setAttribute('rel', rel)
        document.head.appendChild(link)
    }

    link.setAttribute('href', href)
    if (!link.getAttribute('type')) {
        link.setAttribute('type', 'image/png')
    }
}

function withCacheKey(href, key) {
    const normalizedHref = String(href || '').trim()
    if (!normalizedHref) return normalizedHref

    const separator = normalizedHref.includes('?') ? '&' : '?'
    return `${normalizedHref}${separator}v=${encodeURIComponent(key)}`
}

function updateMobileTitle(title) {
    if (typeof document === 'undefined') return
    const meta = document.querySelector('meta[name="apple-mobile-web-app-title"]')
    if (meta) {
        meta.setAttribute('content', title)
    }
}

function abbreviateSchoolName(name) {
    const text = String(name || '').trim()
    if (!text) return DEFAULT_TITLE

    const letters = [...text.matchAll(/\b[\p{L}\p{N}]/gu)]
        .map((match) => match[0]?.toUpperCase?.() || '')
        .filter(Boolean)

    if (!letters.length) return DEFAULT_TITLE
    return `${letters.join('.')}.`
}

function isPreviewSchoolItRoute(routeName) {
    return typeof routeName === 'string' && routeName.startsWith('PreviewSchoolIt')
}

function resolveBranding(routeName, user, schoolSettings) {
    if (routeName === 'Login') {
        return {
            title: DEFAULT_TITLE,
            schoolLogo: null,
        }
    }

    const previewUser = isPreviewSchoolItRoute(routeName) ? schoolItPreviewData.user : null
    const previewSchoolSettings = isPreviewSchoolItRoute(routeName) ? schoolItPreviewData.schoolSettings : null
    const authMeta = getStoredAuthMeta()
    const schoolName = schoolSettings?.school_name
        || user?.school_name
        || previewSchoolSettings?.school_name
        || previewUser?.school_name
        || authMeta?.schoolName
        || ''

    const schoolLogo = schoolSettings?.logo_url
        || previewSchoolSettings?.logo_url
        || authMeta?.logoUrl
        || null

    const title = abbreviateSchoolName(schoolName)
    return {
        title,
        schoolLogo,
    }
}

export async function applyDocumentBranding({ routeName, user, schoolSettings, apiBaseUrl = '' }) {
    if (typeof document === 'undefined') return

    const requestId = ++brandingRequestId
    const branding = resolveBranding(routeName, user, schoolSettings)
    document.title = branding.title
    updateMobileTitle(branding.title)

    const fallbackIconUrl = withCacheKey(DEFAULT_ICON_URL, `${branding.title}:${DEFAULT_ICON_URL}`)
    upsertLink('icon', fallbackIconUrl)
    upsertLink('shortcut icon', fallbackIconUrl)
    upsertLink('apple-touch-icon', fallbackIconUrl)

    if (!branding.schoolLogo) {
        return
    }

    const resolvedIconUrl = await resolveLoadableMediaUrl(branding.schoolLogo, apiBaseUrl)
    if (requestId !== brandingRequestId || typeof document === 'undefined') {
        return
    }

    const finalIconUrl = withCacheKey(
        resolvedIconUrl || DEFAULT_ICON_URL,
        `${branding.title}:${resolvedIconUrl || DEFAULT_ICON_URL}`
    )
    upsertLink('icon', finalIconUrl)
    upsertLink('shortcut icon', finalIconUrl)
    upsertLink('apple-touch-icon', finalIconUrl)
}

export function startDocumentBrandingSync(router) {
    const { currentUser, schoolSettings, apiBaseUrl } = useDashboardSession()
    const applyCurrentBranding = () => {
        void applyDocumentBranding({
            routeName: router.currentRoute.value.name,
            user: currentUser.value,
            schoolSettings: schoolSettings.value,
            apiBaseUrl: apiBaseUrl.value,
        })
    }

    watch(
        [
            () => router.currentRoute.value.name,
            currentUser,
            schoolSettings,
            apiBaseUrl,
        ],
        applyCurrentBranding,
        {
            immediate: true,
            deep: true,
        }
    )

    if (typeof window !== 'undefined') {
        window.addEventListener(AUTH_META_CHANGED_EVENT, applyCurrentBranding)
        window.addEventListener('storage', (event) => {
            if (event.key === 'aura_auth_meta') {
                applyCurrentBranding()
            }
        })
    }
}
