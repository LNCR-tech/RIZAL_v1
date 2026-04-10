export function optimizeImageForUpload(imageDataUrl, maxDimension = 720, quality = 0.85) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      let width = img.width
      let height = img.height

      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = Math.round((height * maxDimension) / width)
          width = maxDimension
        } else {
          width = Math.round((width * maxDimension) / height)
          height = maxDimension
        }
      }

      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')

      if (!ctx) {
        reject(new Error('Unable to prepare the image.'))
        return
      }

      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      ctx.drawImage(img, 0, 0, width, height)

      resolve(canvas.toDataURL('image/jpeg', quality))
    }
    img.onerror = () => reject(new Error('Failed to load image.'))
    img.src = imageDataUrl
  })
}

export function captureVideoFrame(videoEl, options = {}) {
  const {
    maxDimension = 720,
    quality = 0.85,
    square = true,
  } = options

  if (!videoEl || videoEl.videoWidth <= 0 || videoEl.videoHeight <= 0) {
    throw new Error('Unable to capture video frame.')
  }

  let sx = 0, sy = 0, sw = videoEl.videoWidth, sh = videoEl.videoHeight

  if (square) {
    const size = Math.min(sw, sh)
    sx = Math.max(0, (sw - size) / 2)
    sy = Math.max(0, (sh - size) / 2)
    sw = size
    sh = size
  }

  const canvas = document.createElement('canvas')
  canvas.width = maxDimension
  canvas.height = maxDimension

  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('Unable to prepare canvas context.')
  }

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(videoEl, sx, sy, sw, sh, 0, 0, maxDimension, maxDimension)

  return canvas.toDataURL('image/jpeg', quality)
}

export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('Failed to read blob.'))
    reader.readAsDataURL(blob)
  })
}

export function base64ToBlob(base64, mimeType = 'image/jpeg') {
  const parts = base64.split(',')
  if (parts.length < 2) {
    throw new Error('Invalid base64 string.')
  }

  const byteString = atob(parts[1])
  const ab = new ArrayBuffer(byteString.length)
  const ia = new Uint8Array(ab)

  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i)
  }

  return new Blob([ab], { type: mimeType })
}
