import { ref } from 'vue'

/**
 * Global Dark Mode State
 */
export const isDarkMode = ref(false)
export const activeAuraLogo = ref('/logos/aura_logo_black.png')
let currentActiveTheme = null

/**
 * School Theme Configuration
 * School IT can customize: primary accent color, logo, and school name.
 * These would be loaded from /school-settings/me endpoint in production.
 */
export const defaultTheme = {
    // Customizable by School IT
    primaryColor: '#6366F1',       // Indigo - more professional for Super Admin
    primaryDark: '#4F46E5',        // Darker indigo for hover states
    primaryText: '#0A0A0A',        // Text on primary colored backgrounds
    schoolName: 'University Name',
    schoolSlogan: 'Slogan Goes Here',
    schoolLogo: '/logos/university_logo.svg', // Replace with actual school PNG

    // Fixed Aura system colors
    background: '#EBEBEB',
    surfaceColor: '#FFFFFF',
    navColor: '#0A0A0A',
    navActiveColor: '#6366F1',
    textPrimary: '#0A0A0A',
    textSecondary: '#555555',
    textMuted: '#999999',
}

/**
 * Load theme - in production, fetches from API and merges school settings.
 */
export function loadTheme(schoolSettings = null) {
    // If we're impersonating a school (Super Admin feature)
    const impersonateId = localStorage.getItem('aura_impersonate_school_id')
    const impersonateName = localStorage.getItem('aura_impersonate_school_name')
    const impersonateLogo = localStorage.getItem('aura_impersonate_school_logo')

    if (impersonateId) {
        // In a real app, we'd fetch the specific theme colors for this school_id.
        // For now, we'll use a dynamic primary color if it's JRMSU (id 2) to show it working.
        const isJrmsu = parseInt(impersonateId) === 2
        return {
            ...defaultTheme,
            primaryColor: isJrmsu ? '#00205B' : defaultTheme.primaryColor,
            primaryDark: isJrmsu ? '#00153D' : defaultTheme.primaryDark,
            schoolName: impersonateName || defaultTheme.schoolName,
            schoolLogo: impersonateLogo || defaultTheme.schoolLogo,
        }
    }

    if (!schoolSettings) return defaultTheme

    return {
        ...defaultTheme,
        primaryColor: schoolSettings.primary_color ?? defaultTheme.primaryColor,
        primaryDark: schoolSettings.primary_color_dark ?? darkenHex(schoolSettings.primary_color || defaultTheme.primaryColor, 15),
        schoolName: schoolSettings.school_name ?? defaultTheme.schoolName,
        schoolSlogan: schoolSettings.slogan ?? defaultTheme.schoolSlogan,
        schoolLogo: schoolSettings.logo_url ?? defaultTheme.schoolLogo,
    }
}

/**
 * Darken a hex color by a given percentage
 */
function darkenHex(hex, percent) {
    hex = hex.replace('#', '')
    if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
    if (hex.length === 8) hex = hex.substring(0, 6) // ignore alpha channel

    let r = parseInt(hex.substring(0, 2), 16)
    let g = parseInt(hex.substring(2, 4), 16)
    let b = parseInt(hex.substring(4, 6), 16)

    const multiplier = 1 - (percent / 100)

    r = Math.max(0, Math.min(255, Math.floor(r * multiplier)))
    g = Math.max(0, Math.min(255, Math.floor(g * multiplier)))
    b = Math.max(0, Math.min(255, Math.floor(b * multiplier)))

    const toHex = (n) => {
        const h = n.toString(16)
        return h.length === 1 ? '0' + h : h
    }

    return '#' + toHex(r) + toHex(g) + toHex(b)
}

/**
 * Calculate the best text color (black or white) for a given hex background
 * using the YIQ luminance formula.
 */
function getContrastYIQ(hexcolor) {
    hexcolor = hexcolor.replace('#', '')
    if (hexcolor.length === 3) {
        hexcolor = hexcolor[0] + hexcolor[0] + hexcolor[1] + hexcolor[1] + hexcolor[2] + hexcolor[2]
    }
    const r = parseInt(hexcolor.substr(0, 2), 16)
    const g = parseInt(hexcolor.substr(2, 2), 16)
    const b = parseInt(hexcolor.substr(4, 2), 16)
    // YIQ formula
    const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000
    // If luminance is > 128, background is light, use dark text. Otherwise use white text.
    return (yiq >= 128) ? '#0A0A0A' : '#FFFFFF'
}

export function toggleDarkMode() {
    isDarkMode.value = !isDarkMode.value
    if (currentActiveTheme) {
        applyTheme(currentActiveTheme)
    }
}

/**
 * Apply theme CSS variables to the document root.
 */
export function applyTheme(theme) {
    currentActiveTheme = theme
    const root = document.documentElement

    // Dynamic colors based on dark mode state
    let bgColor = theme.background
    let surfaceColor = theme.surfaceColor
    let textPrimary = theme.textPrimary
    let textSecondary = theme.textSecondary
    let navPillBg = '#FFFFFF'
    let profileBg = '#FFFFFF'
    let cardBg = '#FFFFFF'
    let borderColor = 'rgba(0,0,0,0.05)'
    let inputBg = 'rgba(0,0,0,0.05)'

    if (isDarkMode.value) {
        // Sophisticated Dark Mode (Deep Slate/Indigo)
        bgColor = '#0A0A0B'
        cardBg = '#141416'
        surfaceColor = '#141416'
        textPrimary = '#FFFFFF'
        textSecondary = '#A1A1AA'
        navPillBg = '#1E1E21'
        profileBg = '#1E1E21'
        borderColor = 'rgba(255,255,255,0.08)'
        inputBg = '#1E1E21'
    }

    root.style.setProperty('--color-primary', theme.primaryColor)
    root.style.setProperty('--color-primary-dark', theme.primaryDark)
    root.style.setProperty('--color-primary-text', theme.primaryText)
    root.style.setProperty('--color-bg', bgColor)
    root.style.setProperty('--color-surface', surfaceColor)
    root.style.setProperty('--color-card-bg', cardBg)
    root.style.setProperty('--color-profile-bg', profileBg)
    root.style.setProperty('--color-nav-pill-bg', navPillBg)
    root.style.setProperty('--color-nav', isDarkMode.value ? '#FFFFFF' : theme.navColor)
    root.style.setProperty('--color-nav-active', theme.navActiveColor)
    root.style.setProperty('--color-text-primary', textPrimary)
    root.style.setProperty('--color-text-secondary', textSecondary)
    root.style.setProperty('--color-text-muted', isDarkMode.value ? '#71717A' : theme.textMuted)
    root.style.setProperty('--color-border', borderColor)
    root.style.setProperty('--color-input-bg', inputBg)

    // Create a special variable for text that must ALWAYS be dark (only when light mode)
    root.style.setProperty('--color-text-always-dark', isDarkMode.value ? '#FFFFFF' : '#0A0A0A')

    // Smart contrast text for the dark/light University Banner
    const bannerTextColor = getContrastYIQ(theme.primaryColor)
    root.style.setProperty('--color-banner-text', bannerTextColor)

    // Automatically serve the correct Aura logo color
    activeAuraLogo.value = bannerTextColor === '#FFFFFF' || isDarkMode.value
        ? '/logos/aura_logo_white.png'
        : '/logos/aura_logo_black.png'
}
