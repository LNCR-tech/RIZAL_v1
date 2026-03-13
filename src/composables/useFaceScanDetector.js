import { FaceDetector, FilesetResolver } from '@mediapipe/tasks-vision'

let detectorPromise = null
let detectorInstance = null

export async function initFaceScanDetector(options) {
    if (detectorInstance) return detectorInstance
    if (detectorPromise) return detectorPromise

    detectorPromise = (async () => {
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

        detectorInstance = detector
        return detector
    })()

    return detectorPromise
}

export function resetFaceScanDetector() {
    try {
        detectorInstance?.close?.()
    } catch {
        // ignore cleanup errors
    }
    detectorInstance = null
    detectorPromise = null
}
