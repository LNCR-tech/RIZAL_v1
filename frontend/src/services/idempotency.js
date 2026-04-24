export function createIdempotencyKey(prefix = 'request') {
    const safePrefix = String(prefix || 'request').trim() || 'request'
    const randomUuid = globalThis.crypto?.randomUUID?.()

    if (randomUuid) {
        return `${safePrefix}:${randomUuid}`
    }

    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).slice(2, 12)
    return `${safePrefix}:${timestamp}:${random}`
}
