import { FaceDetector, FilesetResolver } from '@mediapipe/tasks-vision'

let detectorPromise = null
let detectorInstance = null
let detectorLoadVersion = 0

function withTimeout(promise, timeoutMs, message) {
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) return promise

    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            reject(new Error(message))
        }, timeoutMs)

        promise.then(
            (value) => {
                clearTimeout(timer)
                resolve(value)
            },
            (error) => {
                clearTimeout(timer)
                reject(error)
            }
        )
    })
}

export async function initFaceScanDetector(options) {
    if (detectorInstance) return detectorInstance
    if (detectorPromise) return detectorPromise

    const loadVersion = ++detectorLoadVersion
    const timeoutMs = Number(options?.timeoutMs ?? 8000)

    const createPromise = (async () => {
        const wasmBaseUrl = options?.wasmBaseUrl
        const modelAssetPath = options?.modelAssetPath

        if (!wasmBaseUrl || !modelAssetPath) {
            throw new Error('Face detector config missing.')
        }

        const vision = await FilesetResolver.forVisionTasks(wasmBaseUrl)
        const detector = await FaceDetector.createFromOptions(vision, {
            baseOptions: { modelAssetPath },
            runningMode: options?.runningMode || 'VIDEO',
            minDetectionConfidence: options?.minDetectionConfidence,
            minSuppressionThreshold: options?.minSuppressionThreshold,
        })

        return detector
    })()

    createPromise.then((detector) => {
        if (loadVersion !== detectorLoadVersion || detectorPromise == null) {
            try {
                detector?.close?.()
            } catch {
                // ignore cleanup errors for abandoned detector loads
            }
        }
    }).catch(() => {
        // ignore deferred create errors; the active caller handles them below
    })

    detectorPromise = withTimeout(
        createPromise,
        timeoutMs,
        'Face detector initialization timed out.'
    ).then((detector) => {
        if (loadVersion !== detectorLoadVersion) {
            try {
                detector?.close?.()
            } catch {
                // ignore cleanup errors for superseded detector loads
            }
            throw new Error('Face detector initialization was superseded.')
        }

        detectorInstance = detector
        return detector
    }).catch((error) => {
        if (loadVersion === detectorLoadVersion) {
            detectorPromise = null
            detectorInstance = null
        }
        throw error
    })

    return detectorPromise
}

export function resetFaceScanDetector() {
    detectorLoadVersion += 1
    try {
        detectorInstance?.close?.()
    } catch {
        // ignore cleanup errors
    }
    detectorInstance = null
    detectorPromise = null
}
