import { Capacitor } from '@capacitor/core'
import { Directory, Filesystem } from '@capacitor/filesystem'
import { Share } from '@capacitor/share'

const CACHE_DOWNLOAD_DIR = 'aura-downloads'

function sanitizeDownloadFilename(filename = 'download') {
  return String(filename || 'download')
    .trim()
    .replace(/[\\/:*?"<>|]+/g, '-')
    .replace(/\s+/g, ' ')
    .replace(/^\.+|\.+$/g, '')
    || 'download'
}

function isNativePlatform() {
  try {
    return Capacitor.isNativePlatform()
  } catch {
    return false
  }
}

function isShareCancel(error) {
  const message = String(error?.message || error || '').toLowerCase()
  return message.includes('cancel')
}

function browserDownloadBlob(blob, filename) {
  if (typeof document === 'undefined' || typeof URL === 'undefined') {
    throw new Error('File downloads are not available in this environment.')
  }

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(reader.error || new Error('Unable to prepare file for download.'))
    reader.onload = () => {
      const result = String(reader.result || '')
      const commaIndex = result.indexOf(',')
      resolve(commaIndex >= 0 ? result.slice(commaIndex + 1) : result)
    }
    reader.readAsDataURL(blob)
  })
}

export async function downloadBlobFile(blob, filename, options = {}) {
  if (!(blob instanceof Blob)) {
    throw new Error('No file content was provided for download.')
  }

  const safeFilename = sanitizeDownloadFilename(filename)

  if (!isNativePlatform()) {
    browserDownloadBlob(blob, safeFilename)
    return { native: false, filename: safeFilename }
  }

  const data = await blobToBase64(blob)
  const path = `${CACHE_DOWNLOAD_DIR}/${safeFilename}`
  const writeResult = await Filesystem.writeFile({
    path,
    data,
    directory: Directory.Cache,
    recursive: true,
  })

  const uri = writeResult?.uri
  if (!uri) {
    throw new Error('The file was created, but Android did not return a shareable URI.')
  }

  try {
    await Share.share({
      title: options.title || safeFilename,
      text: options.text || 'Save or share this file.',
      url: uri,
      dialogTitle: options.dialogTitle || 'Save file',
    })
  } catch (error) {
    if (!isShareCancel(error)) throw error
  }

  return {
    native: true,
    filename: safeFilename,
    uri,
    path,
  }
}
