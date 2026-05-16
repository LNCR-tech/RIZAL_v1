---
sidebar_position: 1
title: Architecture
---

# Frontend Architecture

🔒 **Restricted**: Developer documentation

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **State Management**: Pinia
- **Router**: Vue Router
- **UI Library**: Custom components
- **Mobile**: Capacitor (Android)

## Project Structure

```
frontend-web/
├── src/
│   ├── components/       # Reusable components
│   ├── views/            # Page components
│   ├── stores/           # Pinia stores
│   ├── router/           # Route definitions
│   ├── services/         # API services
│   ├── composables/      # Composition functions
│   └── assets/           # Static assets
├── public/               # Public files
└── capacitor.config.ts   # Mobile config
```

## Key Features

### State Management
Using Pinia for centralized state:
- `authStore` - Authentication state
- `eventStore` - Event data
- `attendanceStore` - Attendance records

### API Integration
Axios-based API client with interceptors for:
- Token injection
- Error handling
- Request/response transformation

### Mobile Support
Capacitor plugins for:
- Camera access
- Geolocation
- Push notifications
- Biometric authentication

## Development

```bash
npm run dev
```

## Build

```bash
npm run build
```
