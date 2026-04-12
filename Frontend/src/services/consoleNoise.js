let installed = false

const MEDIAPIPE_NOISE_PATTERNS = [
  /gl_context\.cc:/,
  /gl_context_webgl\.cc:/,
  /Graph successfully started running\./,
  /Graph finished closing successfully\./,
  /Created TensorFlow Lite XNNPACK delegate/i,
  /inference_feedback_manager\.cc:/,
]

function isMediapipeConsoleNoise(args) {
  if (!args || args.length === 0) return false

  const first = args[0]
  if (typeof first !== 'string') return false

  return MEDIAPIPE_NOISE_PATTERNS.some((pattern) => pattern.test(first))
}

export function installConsoleNoiseFilters() {
  if (installed || typeof window === 'undefined' || typeof console === 'undefined') return
  installed = true

  if (!import.meta.env.PROD) return

  ;['log', 'info', 'warn', 'debug'].forEach((method) => {
    const original = console[method]
    if (typeof original !== 'function') return

    console[method] = (...args) => {
      if (isMediapipeConsoleNoise(args)) return
      original.apply(console, args)
    }
  })
}

