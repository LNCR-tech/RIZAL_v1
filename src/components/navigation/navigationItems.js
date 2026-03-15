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

export function getNavigationItemsForPath(path = '') {
    return String(path || '').startsWith('/workspace')
        ? schoolItNavigationItems
        : dashboardNavigationItems
}
