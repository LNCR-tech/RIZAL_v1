const ATTENDANCE_STORAGE_KEY = 'attendance_cache'
const ATTENDANCE_EXPIRY_HOURS = 24

function getStoredAttendance() {
  try {
    const data = localStorage.getItem(ATTENDANCE_STORAGE_KEY)
    if (!data) return null

    const parsed = JSON.parse(data)
    if (!parsed.timestamp || !parsed.data) return null

    const hoursSince = (Date.now() - parsed.timestamp) / (1000 * 60 * 60)
    if (hoursSince > ATTENDANCE_EXPIRY_HOURS) {
      localStorage.removeItem(ATTENDANCE_STORAGE_KEY)
      return null
    }

    return parsed.data
  } catch {
    return null
  }
}

function setStoredAttendance(data) {
  try {
    localStorage.setItem(ATTENDANCE_STORAGE_KEY, JSON.stringify({
      timestamp: Date.now(),
      data,
    }))
  } catch (e) {
    console.warn('Failed to store attendance data:', e)
  }
}

function clearStoredAttendance() {
  try {
    localStorage.removeItem(ATTENDANCE_STORAGE_KEY)
  } catch {
    // Ignore
  }
}

function getAttendanceRecordKey(studentId, eventId) {
  return `${studentId}_${eventId}`
}

export function storeAttendanceRecord(record) {
  const existing = getStoredAttendance() || {}
  const key = getAttendanceRecordKey(record.student_id, record.event_id)
  
  existing[key] = {
    ...record,
    stored_at: new Date().toISOString(),
  }
  
  setStoredAttendance(existing)
}

export function getAttendanceRecord(studentId, eventId) {
  const existing = getStoredAttendance() || {}
  const key = getAttendanceRecordKey(studentId, eventId)
  return existing[key] || null
}

export function getAllStoredAttendance() {
  return getStoredAttendance() || {}
}

export function removeAttendanceRecord(studentId, eventId) {
  const existing = getStoredAttendance() || {}
  const key = getAttendanceRecordKey(studentId, eventId)
  
  if (existing[key]) {
    delete existing[key]
    setStoredAttendance(existing)
  }
}

export function clearAllStoredAttendance() {
  clearStoredAttendance()
}

export function getOfflineAttendanceQueue() {
  try {
    const data = localStorage.getItem('attendance_queue')
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function addToOfflineAttendanceQueue(record) {
  try {
    const queue = getOfflineAttendanceQueue()
    queue.push({
      ...record,
      queued_at: new Date().toISOString(),
    })
    localStorage.setItem('attendance_queue', JSON.stringify(queue))
  } catch (e) {
    console.warn('Failed to queue attendance:', e)
  }
}

export function removeFromOfflineAttendanceQueue(index) {
  try {
    const queue = getOfflineAttendanceQueue()
    if (index >= 0 && index < queue.length) {
      queue.splice(index, 1)
      localStorage.setItem('attendance_queue', JSON.stringify(queue))
    }
  } catch {
    // Ignore
  }
}

export function clearOfflineAttendanceQueue() {
  try {
    localStorage.removeItem('attendance_queue')
  } catch {
    // Ignore
  }
}
