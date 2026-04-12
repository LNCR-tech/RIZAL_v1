import { jsPDF } from 'jspdf'

function sanitizeFilename(value = 'report') {
  return String(value || 'report')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'report'
}

function triggerFileDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}

function toCsvField(value) {
  const stringValue = String(value ?? '')
  if (!/[",\r\n]/.test(stringValue)) return stringValue
  return `"${stringValue.replace(/"/g, '""')}"`
}

export function downloadGovernanceMasterlistCsv({ event = null, report = null, rows = [] } = {}) {
  const csvLines = [
    ['Event', report?.event_name || event?.name || 'Governance Event'],
    ['Date', report?.event_date || event?.start_datetime || 'N/A'],
    ['Location', report?.event_location || event?.location || 'N/A'],
    [],
    ['Student ID', 'Student Name', 'Department', 'Program', 'Year', 'Status', 'Time In', 'Time Out', 'Duration', 'Method'],
    ...(Array.isArray(rows) ? rows : []).map((row) => ([
      row.studentId,
      row.studentName,
      row.departmentName,
      row.programName,
      row.yearLabel,
      row.statusLabel,
      row.timeInLabel,
      row.timeOutLabel,
      row.durationLabel,
      row.methodLabel,
    ])),
  ]

  const csvContent = `\uFEFF${csvLines.map((line) => line.map(toCsvField).join(',')).join('\r\n')}`
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  triggerFileDownload(blob, `${sanitizeFilename(event?.name || report?.event_name || 'governance_masterlist')}.csv`)
}

export function downloadGovernanceParPdf({
  event = null,
  report = null,
  eventHealth = null,
  demographicBreakdown = null,
  arrivalInsights = null,
} = {}) {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'a4',
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const margin = 40
  const contentWidth = pageWidth - (margin * 2)
  let y = 48

  const title = report?.event_name || event?.name || 'Post-Activity Report'
  const dateLine = report?.event_date || event?.start_datetime || 'Date unavailable'
  const locationLine = report?.event_location || event?.location || 'Location unavailable'

  doc.setFillColor(248, 249, 251)
  doc.roundedRect(margin, y, contentWidth, 112, 20, 20, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(18, 24, 38)
  doc.setFontSize(22)
  doc.text(title, margin + 18, y + 30)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(11)
  doc.setTextColor(94, 104, 121)
  doc.text(`Generated PAR`, margin + 18, y + 50)
  doc.text(String(dateLine), margin + 18, y + 68)
  doc.text(String(locationLine), margin + 18, y + 84)

  const attendanceRate = String(eventHealth?.valueLabel || `${Math.round(Number(report?.attendance_rate || 0))}%`)
  const totalParticipants = String(eventHealth?.totalLabel || report?.total_participants || 0)
  const attendees = String(eventHealth?.attendedLabel || report?.attendees || 0)

  doc.setFillColor(255, 255, 255)
  doc.roundedRect(margin + contentWidth - 154, y + 18, 136, 76, 18, 18, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(18, 24, 38)
  doc.setFontSize(26)
  doc.text(attendanceRate, margin + contentWidth - 136, y + 52)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(94, 104, 121)
  doc.text(`Attendance Rate`, margin + contentWidth - 136, y + 70)

  y += 136

  const statCards = [
    ['Total Participants', totalParticipants],
    ['Attended', attendees],
    ['Late', String(report?.late_attendees ?? eventHealth?.lateLabel ?? 0)],
    ['Absent', String(report?.absentees ?? eventHealth?.absentLabel ?? 0)],
  ]

  const statCardWidth = (contentWidth - 18) / 2
  statCards.forEach(([label, value], index) => {
    const row = Math.floor(index / 2)
    const column = index % 2
    const x = margin + ((statCardWidth + 18) * column)
    const yOffset = y + (row * 86)
    doc.setFillColor(248, 249, 251)
    doc.roundedRect(x, yOffset, statCardWidth, 70, 18, 18, 'F')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(94, 104, 121)
    doc.text(label, x + 16, yOffset + 24)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(22)
    doc.setTextColor(18, 24, 38)
    doc.text(String(value), x + 16, yOffset + 50)
  })

  y += 188

  const sections = [
    {
      title: demographicBreakdown?.title || 'Demographic Breakdown',
      subtitle: demographicBreakdown?.summary || 'Attendance reach by the strongest visible segment.',
      rows: Array.isArray(demographicBreakdown?.items) ? demographicBreakdown.items.slice(0, 5).map((item) => ({
        label: item.label,
        value: item.valueLabel,
      })) : [],
      empty: 'Segment data is not available from the current attendance bundle.',
    },
    {
      title: 'Peak Arrival Times',
      subtitle: arrivalInsights?.summary || 'Most students arrived during the strongest check-in window.',
      rows: Array.isArray(arrivalInsights?.items) ? arrivalInsights.items
        .filter((item) => Number(item.value) > 0)
        .sort((left, right) => Number(right.value) - Number(left.value))
        .slice(0, 5)
        .map((item) => ({
          label: item.label,
          value: item.valueLabel,
        })) : [],
      empty: 'No sign-in timestamps are available for this event range yet.',
    },
  ]

  sections.forEach((section) => {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(15)
    doc.setTextColor(18, 24, 38)
    doc.text(section.title, margin, y)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(94, 104, 121)
    doc.text(doc.splitTextToSize(section.subtitle, contentWidth), margin, y + 16)

    y += 40

    if (!section.rows.length) {
      doc.setFillColor(248, 249, 251)
      doc.roundedRect(margin, y, contentWidth, 52, 16, 16, 'F')
      doc.text(section.empty, margin + 14, y + 30)
      y += 72
      return
    }

    section.rows.forEach((row) => {
      doc.setFillColor(248, 249, 251)
      doc.roundedRect(margin, y, contentWidth, 36, 14, 14, 'F')
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(18, 24, 38)
      doc.text(String(row.label), margin + 14, y + 23)
      doc.setFont('helvetica', 'bold')
      doc.text(String(row.value), margin + contentWidth - 14, y + 23, { align: 'right' })
      y += 44
    })

    y += 14
  })

  doc.save(`${sanitizeFilename(event?.name || report?.event_name || 'post_activity_report')}_par.pdf`)
}
