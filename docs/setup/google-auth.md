# Google OAuth Setup

This guide explains how to configure Google Sign-In for the Aura web app and the Capacitor Android app.

## Google Cloud Console

1. Open `https://console.cloud.google.com/` and select or create a project.
2. Go to `APIs & Services` > `OAuth consent screen`.
3. Configure the consent screen for the expected user type.
4. Add the standard scopes: `openid`, `email`, and `profile`.
5. Add support and developer contact emails.
6. Add test users while the app is in testing mode.

## Web Client ID

Create a web OAuth client:

1. Go to `APIs & Services` > `Credentials`.
2. Select `Create Credentials` > `OAuth client ID`.
3. Choose `Web application`.
4. Add authorized JavaScript origins:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
   - The production frontend origin.
5. Add authorized redirect URIs only if a server-side OAuth redirect flow is added later. The current Google Identity Services button uses the popup flow from the allowed origin.

Save the web client ID in:

```env
GOOGLE_WEB_CLIENT_ID=<web client id>
VITE_GOOGLE_WEB_CLIENT_ID=<web client id>
AURA_GOOGLE_WEB_CLIENT_ID=<web client id>
```

`GOOGLE_WEB_CLIENT_ID` is read by the backend. `VITE_GOOGLE_WEB_CLIENT_ID` is used by local Vite development. `AURA_GOOGLE_WEB_CLIENT_ID` is written into the runtime config for built frontend and Capacitor deployments.

## Android Client ID

Create an Android OAuth client:

1. Go to `APIs & Services` > `Credentials`.
2. Select `Create Credentials` > `OAuth client ID`.
3. Choose `Android`.
4. Set package name to `com.aura.app`.
5. Add the SHA-1 certificate fingerprint for each signing key.

For the debug keystore, run:

```powershell
keytool -list -v -alias androiddebugkey -keystore "$env:USERPROFILE\.android\debug.keystore" -storepass android -keypass android
```

For release builds, run the same command with the release keystore path and alias.

Save the Android client ID in the backend environment:

```env
GOOGLE_ANDROID_CLIENT_ID=<android client id>
```

The Capacitor WebView flow still renders the Google Identity Services button with the web client ID. The backend accepts both the web and Android audiences so deployed clients can be validated safely.

## Backend Environment

```env
GOOGLE_LOGIN_ENABLED=true
GOOGLE_WEB_CLIENT_ID=<web client id>
GOOGLE_ANDROID_CLIENT_ID=<android client id>
```

Set `GOOGLE_LOGIN_ENABLED=false` to disable Google login without removing the route.

## Frontend Environment

For local Vite development, set:

```env
VITE_GOOGLE_WEB_CLIENT_ID=<web client id>
```

For runtime config and Capacitor builds, set:

```env
AURA_GOOGLE_WEB_CLIENT_ID=<web client id>
```

Capacitor navigation must allow:

```text
accounts.google.com
*.googleusercontent.com
```

These domains are included in `frontend/capacitor.config.json` and in `frontend/scripts/write-capacitor-config.mjs`.

## Runtime Behavior

- `POST /auth/google` accepts a Google ID token and issues the normal Aura access token.
- Only existing registered Aura users can sign in. The backend does not auto-create users from Google accounts.
- Google email addresses must be verified.
- Disabled Google login returns `Google login is disabled.`
- An unregistered Google account returns `Google account is not registered.`
- An invalid Google token returns `Invalid Google token.`
- Login history records Google sign-ins with `auth_method="google"`.
- The standard login rate limit also applies to Google login.

## Verification

1. Start the backend with the Google environment variables configured.
2. Start the frontend with `VITE_GOOGLE_WEB_CLIENT_ID` configured.
3. Open the login page and confirm `Continue with Google` renders below `Log In`.
4. Confirm `Forgot password?` appears right-aligned under the password field.
5. Sign in with a registered Google account and verify the normal role-based dashboard redirect.
6. Sign in with an unregistered Google account and confirm the login page shows `Google account is not registered.`
7. Set `GOOGLE_LOGIN_ENABLED=false`, restart the backend, and confirm Google sign-in shows `Google login is disabled.`
8. For Android, build and install a debug APK, then verify the same Google login flow inside the Capacitor app.
