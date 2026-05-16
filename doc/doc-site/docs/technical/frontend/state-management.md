---
sidebar_position: 3
title: State Management
---

# State Management

🔒 **Restricted**: Developer documentation

## Pinia Stores

Aura uses Pinia for state management.

## Core Stores

### authStore
Manages authentication state:
- Current user
- JWT token
- Login/logout actions
- Role checking

```javascript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = authStore.user
const isAdmin = authStore.hasRole('admin')
```

### eventStore
Manages event data:
- Event list
- Current event
- CRUD operations

### attendanceStore
Manages attendance records:
- User attendance history
- Check-in status
- Attendance statistics

## Store Structure

```javascript
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role,
  },
  actions: {
    async login(credentials) {
      // Login logic
    },
  },
})
```

## Persistence

Stores are persisted to localStorage using `pinia-plugin-persistedstate`.
