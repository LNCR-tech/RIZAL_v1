const DEFAULT_PIE_COLORS = [
    'rgba(0,87,184,0.88)',
    'rgba(245,158,11,0.88)',
    'rgba(239,68,68,0.88)',
    'rgba(16,185,129,0.88)',
    'rgba(99,102,241,0.88)',
    'rgba(71,85,105,0.88)',
]

export function toCount(value) {
    const normalized = Number(value)
    return Number.isFinite(normalized) ? Math.max(0, Math.round(normalized)) : 0
}

export function toPercent(value, digits = 0) {
    const normalized = Number(value)
    if (!Number.isFinite(normalized)) {
        return digits > 0 ? `0.${'0'.repeat(digits)}` : '0'
    }
    return normalized.toFixed(digits).replace(/\.0+$/, '').replace(/(\.\d*[1-9])0+$/, '$1')
}

export function buildPieChartData(items = [], colors = DEFAULT_PIE_COLORS) {
    const normalizedItems = (Array.isArray(items) ? items : [])
        .map((item) => ({
            label: String(item?.label || '').trim(),
            value: toCount(item?.value),
        }))
        .filter((item) => item.label && item.value > 0)

    return {
        labels: normalizedItems.map((item) => item.label),
        datasets: [{
            data: normalizedItems.map((item) => item.value),
            backgroundColor: normalizedItems.map((_, index) => colors[index % colors.length]),
            borderWidth: 0,
        }],
    }
}

export function buildBarChartData(items = [], {
    label = 'Value',
    backgroundColor = 'rgba(0,87,184,0.82)',
    borderColor = backgroundColor,
    borderWidth = 0,
} = {}) {
    const normalizedItems = (Array.isArray(items) ? items : [])
        .map((item) => ({
            label: String(item?.label || '').trim(),
            value: Number(item?.value || 0),
        }))
        .filter((item) => item.label)

    return {
        labels: normalizedItems.map((item) => item.label),
        datasets: [{
            label,
            data: normalizedItems.map((item) => item.value),
            backgroundColor,
            borderColor,
            borderWidth,
            borderRadius: 10,
            maxBarThickness: 42,
        }],
    }
}

export function buildLineChartData(labels = [], series = []) {
    const normalizedLabels = Array.isArray(labels) ? labels.map((label) => String(label || '')) : []
    const normalizedSeries = (Array.isArray(series) ? series : [])
        .map((entry) => ({
            label: String(entry?.label || '').trim(),
            data: Array.isArray(entry?.data) ? entry.data.map((value) => Number(value || 0)) : [],
            borderColor: entry?.borderColor || 'rgba(0,87,184,0.88)',
            backgroundColor: entry?.backgroundColor || entry?.borderColor || 'rgba(0,87,184,0.88)',
            tension: typeof entry?.tension === 'number' ? entry.tension : 0.28,
            fill: Boolean(entry?.fill),
        }))
        .filter((entry) => entry.label)

    return {
        labels: normalizedLabels,
        datasets: normalizedSeries,
    }
}

export function buildTrailingDayLabels(days = 7, locale = 'en-US') {
    const totalDays = Math.max(1, Number(days) || 7)
    const formatter = new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric' })

    return Array.from({ length: totalDays }, (_, index) => {
        const date = new Date()
        date.setHours(0, 0, 0, 0)
        date.setDate(date.getDate() - (totalDays - index - 1))
        return {
            key: date.toISOString().slice(0, 10),
            label: formatter.format(date),
        }
    })
}
