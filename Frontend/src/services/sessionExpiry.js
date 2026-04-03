export const SESSION_EXPIRED_EVENT = 'aura-session-expired'
const SESSION_EXPIRED_NOTICE_KEY = 'aura_session_expired_notice'
const DEFAULT_SESSION_EXPIRED_MESSAGE = 'Session expired. Please log in again.'

export function markSessionExpiredNotice(message = DEFAULT_SESSION_EXPIRED_MESSAGE) {
    if (typeof window === 'undefined') return

    window.sessionStorage.setItem(
        SESSION_EXPIRED_NOTICE_KEY,
        String(message || DEFAULT_SESSION_EXPIRED_MESSAGE)
    )
}

export function consumeSessionExpiredNotice() {
    if (typeof window === 'undefined') return ''

    const message = window.sessionStorage.getItem(SESSION_EXPIRED_NOTICE_KEY) || ''
    if (message) {
        window.sessionStorage.removeItem(SESSION_EXPIRED_NOTICE_KEY)
    }

    return message
}

export function clearSessionExpiredNotice() {
    if (typeof window === 'undefined') return
    window.sessionStorage.removeItem(SESSION_EXPIRED_NOTICE_KEY)
}

export function notifySessionExpired(message = DEFAULT_SESSION_EXPIRED_MESSAGE) {
    if (typeof window === 'undefined') return

    const normalizedMessage = String(message || DEFAULT_SESSION_EXPIRED_MESSAGE)
    markSessionExpiredNotice(normalizedMessage)
    window.dispatchEvent(
        new CustomEvent(SESSION_EXPIRED_EVENT, {
            detail: {
                message: normalizedMessage,
            },
        })
    )
}
