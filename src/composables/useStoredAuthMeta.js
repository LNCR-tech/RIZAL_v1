import { onBeforeUnmount, onMounted, ref } from 'vue'
import { AUTH_META_CHANGED_EVENT, getStoredAuthMeta } from '@/services/localAuth.js'

export function useStoredAuthMeta() {
    const authMeta = ref(getStoredAuthMeta())

    const syncAuthMeta = () => {
        authMeta.value = getStoredAuthMeta()
    }

    const handleStorage = (event) => {
        if (!event || event.key === 'aura_auth_meta') {
            syncAuthMeta()
        }
    }

    onMounted(() => {
        syncAuthMeta()

        if (typeof window === 'undefined') return
        window.addEventListener(AUTH_META_CHANGED_EVENT, syncAuthMeta)
        window.addEventListener('storage', handleStorage)
        window.addEventListener('focus', syncAuthMeta)
    })

    onBeforeUnmount(() => {
        if (typeof window === 'undefined') return
        window.removeEventListener(AUTH_META_CHANGED_EVENT, syncAuthMeta)
        window.removeEventListener('storage', handleStorage)
        window.removeEventListener('focus', syncAuthMeta)
    })

    return authMeta
}
