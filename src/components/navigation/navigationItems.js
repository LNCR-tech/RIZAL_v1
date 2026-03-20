import {
    CalendarDays,
    House,
    PieChart,
    Settings,
    UserRound,
    UsersRound,
} from 'lucide-vue-next'

export const dashboardNavigationItems = [
    { name: 'Home', route: '/dashboard', icon: House },
    { name: 'Schedule', route: '/dashboard/schedule', icon: CalendarDays },
    { name: 'Analytics', route: '/dashboard/analytics', icon: PieChart },
    { name: 'Profile', route: '/dashboard/profile', icon: UserRound },
]

export const schoolItNavigationItems = [
    { name: 'Home', route: '/workspace', icon: House },
    { name: 'Users', route: '/workspace/users', icon: UsersRound, matchPrefixes: ['/workspace/student-council'] },
    { name: 'Schedule', route: '/workspace/schedule', icon: CalendarDays },
    { name: 'Settings', route: '/workspace/settings', icon: Settings },
    { name: 'Profile', route: '/workspace/profile', icon: UserRound },
]

export const exposedSchoolItNavigationItems = [
    { name: 'Home', route: '/exposed/workspace', icon: House },
    { name: 'Users', route: '/exposed/workspace/users', icon: UsersRound, matchPrefixes: ['/exposed/workspace/student-council'] },
    { name: 'Schedule', route: '/exposed/workspace/schedule', icon: CalendarDays },
    { name: 'Settings', route: '/exposed/workspace/settings', icon: Settings },
    { name: 'Profile', route: '/exposed/workspace/profile', icon: UserRound },
]

export const exposedDashboardNavigationItems = [
    { name: 'Home', route: '/exposed/dashboard', icon: House },
    { name: 'Schedule', route: '/exposed/dashboard/schedule', icon: CalendarDays },
    { name: 'Analytics', route: '/exposed/dashboard/analytics', icon: PieChart },
    { name: 'Profile', route: '/exposed/dashboard/profile', icon: UserRound },
]

export function getNavigationItemsForPath(path = '') {
    const normalizedPath = String(path || '')
    if (normalizedPath.startsWith('/exposed/dashboard')) {
        return exposedDashboardNavigationItems
    }
    if (normalizedPath.startsWith('/exposed/workspace')) {
        return exposedSchoolItNavigationItems
    }
    if (normalizedPath.startsWith('/workspace')) {
        return schoolItNavigationItems
    }
    return dashboardNavigationItems
}
