import { jsPDF } from 'jspdf'
import { downloadBlobFile } from '@/services/fileDownload.js'

const PDF_COLORS = {
  surface: [248, 249, 251],
  surfaceStrong: [255, 255, 255],
  surfaceMuted: [239, 243, 247],
  text: [18, 24, 38],
  muted: [94, 104, 121],
  accent: [184, 235, 88],
  accentSoft: [230, 243, 205],
  accentPale: [244, 250, 231],
  accentDark: [70, 88, 18],
  border: [229, 234, 241],
}

function sanitizeFilename(value = 'report') {
  return String(value || 'report')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'report'
}

function toCsvField(value) {
  const stringValue = String(value ?? '')
  if (!/[",\r\n]/.test(stringValue)) return stringValue
  return `"${stringValue.replace(/"/g, '""')}"`
}

function setFillColor(doc, [r, g, b]) {
  doc.setFillColor(r, g, b)
}

function setTextColor(doc, [r, g, b]) {
  doc.setTextColor(r, g, b)
}

function setDrawColor(doc, [r, g, b]) {
  doc.setDrawColor(r, g, b)
}

function ensurePageSpace(doc, y, neededHeight, margin) {
  const pageHeight = doc.internal.pageSize.getHeight()
  if (y + neededHeight <= pageHeight - margin) return y
  doc.addPage()
  return 48
}

function truncateLabel(value = '', maxLength = 26) {
  const normalized = String(value || '').trim()
  if (normalized.length <= maxLength) return normalized
  return `${normalized.slice(0, maxLength - 1)}…`
}

function getBarRatio(item = null, fallbackPeak = 1) {
  const explicitRatio = Number(item?.ratio)
  if (Number.isFinite(explicitRatio) && explicitRatio > 0) {
    return Math.max(0, Math.min(100, explicitRatio))
  }

  const value = Number(item?.value)
  if (!Number.isFinite(value) || fallbackPeak <= 0) return 0
  return Math.max(0, Math.min(100, (value / fallbackPeak) * 100))
}

function formatPercentValue(value = 0) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue) || numericValue <= 0) return '0%'
  if (numericValue >= 10) return `${Math.round(numericValue)}%`
  return `${numericValue.toFixed(1)}%`
}

function getCeiledPercentScale(value = 0) {
  const numericValue = Math.max(0, Number(value) || 0)
  if (numericValue <= 20) return 20
  if (numericValue <= 40) return Math.ceil(numericValue / 5) * 5
  return Math.ceil(numericValue / 10) * 10
}

function drawSectionCardHeader(doc, {
  x,
  y,
  width,
  title,
  subtitle,
}) {
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(15)
  setTextColor(doc, PDF_COLORS.text)
  doc.text(String(title || 'Section'), x + 16, y + 24)

  const subtitleLines = doc.splitTextToSize(String(subtitle || ''), width - 32)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  setTextColor(doc, PDF_COLORS.muted)
  doc.text(subtitleLines, x + 16, y + 42)

  return {
    subtitleLines,
    bodyStartY: y + 54 + (Math.max(0, subtitleLines.length - 1) * 12),
  }
}

function drawEmptyState(doc, {
  x,
  y,
  width,
  message,
}) {
  setFillColor(doc, PDF_COLORS.surfaceStrong)
  doc.roundedRect(x + 16, y, width - 32, 48, 14, 14, 'F')
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  setTextColor(doc, PDF_COLORS.muted)
  doc.text(String(message || 'No data available.'), x + 28, y + 28)
}

function drawHorizontalBreakdownChart(doc, {
  x,
  y,
  width,
  title,
  subtitle,
  items = [],
  empty,
}) {
  const visibleItems = Array.isArray(items) ? items.slice(0, 6) : []
  const chartHeight = visibleItems.length ? 92 + (visibleItems.length * 38) : 132

  setFillColor(doc, PDF_COLORS.surface)
  doc.roundedRect(x, y, width, chartHeight, 22, 22, 'F')

  const { bodyStartY } = drawSectionCardHeader(doc, { x, y, width, title, subtitle })
  if (!visibleItems.length) {
    drawEmptyState(doc, { x, y: bodyStartY, width, message: empty })
    return y + chartHeight + 18
  }

  const chartLeft = x + 16
  const chartRight = x + width - 16
  const barX = chartLeft
  const barWidth = chartRight - chartLeft
  const peakValue = Math.max(1, ...visibleItems.map((item) => Number(item?.value) || 0))
  const totalValue = Math.max(1, visibleItems.reduce((sum, item) => sum + (Number(item?.value) || 0), 0))

  visibleItems.forEach((item, index) => {
    const rowY = bodyStartY + (index * 38)
    const ratio = getBarRatio(item, peakValue)
    const fillWidth = Math.max(12, (barWidth * ratio) / 100)
    const share = ((Number(item?.value) || 0) / totalValue) * 100
    const statLabel = `${item?.valueLabel || item?.value || 0} · ${formatPercentValue(share)}`

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    setTextColor(doc, PDF_COLORS.text)
    doc.text(truncateLabel(item?.label, 28), barX, rowY + 10)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    setTextColor(doc, PDF_COLORS.muted)
    doc.text(statLabel, chartRight, rowY + 10, { align: 'right' })

    setFillColor(doc, PDF_COLORS.surfaceStrong)
    doc.roundedRect(barX, rowY + 16, barWidth, 8, 4, 4, 'F')

    setFillColor(doc, index === 0 ? PDF_COLORS.accent : PDF_COLORS.accentSoft)
    doc.roundedRect(barX, rowY + 16, fillWidth, 8, 4, 4, 'F')

    setFillColor(doc, index === 0 ? PDF_COLORS.accentDark : PDF_COLORS.accent)
    doc.circle(barX + fillWidth, rowY + 20, 3, 'F')
  })

  return y + chartHeight + 18
}

function sampleArrivalItems(items = [], maxCount = 8) {
  const source = Array.isArray(items) ? items : []
  if (source.length <= maxCount) return source

  const peakIndex = source.reduce((bestIndex, item, index, array) => (
    Number(item?.value || 0) > Number(array[bestIndex]?.value || 0) ? index : bestIndex
  ), 0)
  const step = Math.max(1, Math.floor(source.length / maxCount))
  const pickedIndices = new Set([0, peakIndex, source.length - 1])

  for (let index = 0; index < source.length; index += step) {
    pickedIndices.add(index)
  }

  return [...pickedIndices]
    .sort((left, right) => left - right)
    .slice(0, maxCount)
    .map((index) => source[index])
}

function drawArrivalChart(doc, {
  x,
  y,
  width,
  title,
  subtitle,
  items = [],
  empty,
}) {
  const visibleItems = sampleArrivalItems(items, 8)
  const chartHeight = visibleItems.length ? 244 : 132

  setFillColor(doc, PDF_COLORS.surface)
  doc.roundedRect(x, y, width, chartHeight, 22, 22, 'F')

  const { bodyStartY } = drawSectionCardHeader(doc, { x, y, width, title, subtitle })
  if (!visibleItems.length) {
    drawEmptyState(doc, { x, y: bodyStartY, width, message: empty })
    return y + chartHeight + 18
  }

  const chartX = x + 42
  const chartY = bodyStartY + 18
  const chartWidth = width - 64
  const chartBodyHeight = 124
  const baselineY = chartY + chartBodyHeight
  const peakPercentage = Math.max(1, ...visibleItems.map((item) => Number(item?.percentage) || 0))
  const axisScale = getCeiledPercentScale(peakPercentage)
  const peakItem = visibleItems.reduce((best, item) => (
    Number(item?.value || 0) > Number(best?.value || 0) ? item : best
  ), visibleItems[0] || null)
  const pointGap = visibleItems.length > 1 ? chartWidth / (visibleItems.length - 1) : 0
  const peakIndex = visibleItems.findIndex((item) => item?.key === peakItem?.key)
  const peakX = chartX + (peakIndex * pointGap)
  const highlightWidth = Math.min(52, Math.max(36, pointGap * 0.62))
  const chartBottomPadding = 26

  setFillColor(doc, PDF_COLORS.accentPale)
  doc.roundedRect(
    peakX - (highlightWidth / 2),
    chartY + 8,
    highlightWidth,
    chartBodyHeight - 8,
    16,
    16,
    'F'
  )

  setDrawColor(doc, PDF_COLORS.border)
  doc.setLineWidth(0.8)
  ;[0, 0.25, 0.5, 0.75, 1].forEach((step) => {
    const lineY = chartY + (chartBodyHeight * step)
    doc.setLineDashPattern(step === 1 ? [] : [3, 4], 0)
    doc.line(chartX, lineY, chartX + chartWidth, lineY)

    const axisValue = axisScale - (axisScale * step)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    setTextColor(doc, PDF_COLORS.muted)
    doc.text(formatPercentValue(axisValue), chartX - 10, lineY + 3, { align: 'right' })
  })
  doc.setLineDashPattern([], 0)

  const points = visibleItems.map((item, index) => {
    const percentage = Math.max(0, Number(item?.percentage) || 0)
    const xPoint = chartX + (index * pointGap)
    const yPoint = baselineY - ((percentage / axisScale) * chartBodyHeight)
    return { item, xPoint, yPoint }
  })

  setDrawColor(doc, PDF_COLORS.accent)
  doc.setLineWidth(2)
  for (let index = 1; index < points.length; index += 1) {
    doc.line(points[index - 1].xPoint, points[index - 1].yPoint, points[index].xPoint, points[index].yPoint)
  }

  points.forEach(({ item, xPoint, yPoint }, index) => {
    const isPeak = peakItem?.key === item?.key
    setFillColor(doc, isPeak ? PDF_COLORS.accent : PDF_COLORS.surfaceStrong)
    doc.circle(xPoint, yPoint, isPeak ? 5 : 3.5, 'F')
    if (!isPeak) {
      setDrawColor(doc, PDF_COLORS.accent)
      doc.setLineWidth(1.2)
      doc.circle(xPoint, yPoint, 3.5, 'S')
    }

    const shouldLabel = visibleItems.length <= 5
      || index === 0
      || index === visibleItems.length - 1
      || index === Math.floor((visibleItems.length - 1) / 2)

    if (shouldLabel) {
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(8)
      setTextColor(doc, PDF_COLORS.muted)
      doc.text(truncateLabel(item?.label, 12), xPoint, baselineY + chartBottomPadding, { align: 'center' })
    }
  })

  if (peakItem) {
    const badgeText = `${peakItem?.valueLabel || peakItem?.value || 0} students · ${peakItem?.percentageLabel || formatPercentValue(peakItem?.percentage)}`
    const badgeWidth = Math.min(138, doc.getTextWidth(badgeText) + 20)
    const badgeX = Math.max(x + 20, Math.min(peakX - (badgeWidth / 2), x + width - badgeWidth - 20))
    const badgeY = Math.max(y + 58, chartY - 30)

    setFillColor(doc, PDF_COLORS.accent)
    doc.roundedRect(badgeX, badgeY, badgeWidth, 22, 11, 11, 'F')
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8)
    setTextColor(doc, PDF_COLORS.accentDark)
    doc.text(badgeText, badgeX + (badgeWidth / 2), badgeY + 14, { align: 'center' })
  }

  return y + chartHeight + 18
}

export async function downloadGovernanceMasterlistCsv({ event = null, report = null, rows = [] } = {}) {
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
  return downloadBlobFile(blob, `${sanitizeFilename(event?.name || report?.event_name || 'governance_masterlist')}.csv`, {
    title: 'Governance masterlist',
  })
}

export async function downloadGovernanceParPdf({
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

  setFillColor(doc, PDF_COLORS.surface)
  doc.roundedRect(margin, y, contentWidth, 112, 20, 20, 'F')
  doc.setFont('helvetica', 'bold')
  setTextColor(doc, PDF_COLORS.text)
  doc.setFontSize(22)
  doc.text(title, margin + 18, y + 30)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(11)
  setTextColor(doc, PDF_COLORS.muted)
  doc.text(`Generated PAR`, margin + 18, y + 50)
  doc.text(String(dateLine), margin + 18, y + 68)
  doc.text(String(locationLine), margin + 18, y + 84)

  const attendanceRate = String(eventHealth?.valueLabel || `${Math.round(Number(report?.attendance_rate || 0))}%`)
  const totalParticipants = String(eventHealth?.totalLabel || report?.total_participants || 0)
  const attendees = String(eventHealth?.attendedLabel || report?.attendees || 0)

  setFillColor(doc, PDF_COLORS.surfaceStrong)
  doc.roundedRect(margin + contentWidth - 154, y + 18, 136, 76, 18, 18, 'F')
  doc.setFont('helvetica', 'bold')
  setTextColor(doc, PDF_COLORS.text)
  doc.setFontSize(26)
  doc.text(attendanceRate, margin + contentWidth - 136, y + 52)
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  setTextColor(doc, PDF_COLORS.muted)
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
    setFillColor(doc, PDF_COLORS.surface)
    doc.roundedRect(x, yOffset, statCardWidth, 70, 18, 18, 'F')
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    setTextColor(doc, PDF_COLORS.muted)
    doc.text(label, x + 16, yOffset + 24)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(22)
    setTextColor(doc, PDF_COLORS.text)
    doc.text(String(value), x + 16, yOffset + 50)
  })

  y += 188

  y = ensurePageSpace(doc, y, 210, margin)
  y = drawHorizontalBreakdownChart(doc, {
    x: margin,
    y,
    width: contentWidth,
    title: demographicBreakdown?.title || 'College Reach',
    subtitle: demographicBreakdown?.summary || 'Attendance spread across colleges for the selected event.',
    items: Array.isArray(demographicBreakdown?.items) ? demographicBreakdown.items : [],
    empty: 'College breakdown data is not available from the current attendance bundle.',
  })

  y = ensurePageSpace(doc, y, 250, margin)
  drawArrivalChart(doc, {
    x: margin,
    y,
    width: contentWidth,
    title: 'Peak Arrival Times',
    subtitle: arrivalInsights?.summary || 'Most students arrived during the strongest check-in window.',
    items: Array.isArray(arrivalInsights?.items) ? arrivalInsights.items : [],
    empty: 'No sign-in timestamps are available for this event range yet.',
  })

  const filename = `${sanitizeFilename(event?.name || report?.event_name || 'post_activity_report')}_par.pdf`
  return downloadBlobFile(doc.output('blob'), filename, {
    title: 'Post-Activity Report',
  })
}
