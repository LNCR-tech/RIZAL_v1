# Bulk Import Fix for APK

## Problem
The bulk student import feature was working correctly on localhost (web) but failing in the Android APK build.

## Root Cause
The issue was caused by **CapacitorHttp plugin being enabled** in `capacitor.config.json`. When CapacitorHttp is enabled, Capacitor intercepts all HTTP requests, including `fetch()` calls. However, CapacitorHttp has poor support for `multipart/form-data` file uploads using `FormData`, which is exactly what the bulk import feature uses to upload Excel/CSV files.

## Solution
Disabled CapacitorHttp plugin and added cleartext support to allow the standard browser `fetch()` API to handle file uploads properly.

### Changes Made

#### 1. `capacitor.config.json`
- Changed `CapacitorHttp.enabled` from `true` to `false`
- Added `"cleartext": true` to the server configuration to allow HTTP connections (needed for the backend API at `http://18.142.190.113:8001/`)

```json
{
  "server": {
    "androidScheme": "https",
    "cleartext": true,  // Added this
    ...
  },
  "plugins": {
    "CapacitorHttp": {
      "enabled": false  // Changed from true to false
    },
    ...
  }
}
```

## Why This Works

1. **Standard Fetch API**: The browser's native `fetch()` API has full support for `FormData` and multipart file uploads
2. **Cleartext Support**: Since the backend uses HTTP (not HTTPS), we need to explicitly allow cleartext traffic on Android
3. **No Interception**: With CapacitorHttp disabled, requests go directly through the WebView's native networking stack

## Testing
After rebuilding the APK with these changes:
1. The bulk import preview should work correctly
2. File uploads should complete successfully
3. Import jobs should be queued and processed properly

## Rebuild Instructions
```bash
cd "d:\Aura - Frontend\aura-frontend\frontend"
npm run build
npx cap sync android
npx cap open android
# Build APK from Android Studio
```

## Alternative Solutions (Not Implemented)
If you need CapacitorHttp for other features, you could:
1. Use Capacitor's Filesystem plugin to read files and send as base64
2. Implement a custom native plugin for file uploads
3. Use a different HTTP client library that works with CapacitorHttp

However, disabling CapacitorHttp is the simplest and most reliable solution for this use case.
