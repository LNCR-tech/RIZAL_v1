# Google OAuth Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Google Sign-In to the FastAPI backend and the Vue/Capacitor frontend so registered users can authenticate with their Google account on web and Android, while keeping email/password login intact.

**Architecture:** Backend exposes `POST /auth/google` that verifies a Google ID token via `google-auth`, validates against allowed client IDs (web + android), enforces `email_verified=true`, looks up an existing user by email (no auto-create), and reuses `validate_login_account_state` + `issue_login_token_response`. Login history records `auth_method="google"`. Frontend web uses Google Identity Services (GIS) script to render a "Continue with Google" button on the login page; Capacitor Android uses GIS in the WebView with the Android client ID. Forgot password link is repositioned right-aligned under the password field. Branch: `aura_ci_cd`.

**Tech Stack:** FastAPI 0.110 + Pydantic 2 + SQLAlchemy + `google-auth` (new dep), Vue 3 + Vite + Pinia, Capacitor 8 (Android), Google Identity Services JS (web), pytest + SQLite in-memory for backend tests.

---

## File Structure

**Backend (new):**
- `Backend/app/services/google_auth_service.py` — Verifies the Google ID token, validates client IDs / `email_verified`, returns the verified payload or raises domain-specific errors.
- `Backend/app/schemas/google_auth.py` — Request/response schemas: `GoogleLoginRequest { id_token: str }`. Response reuses `Token`.
- `Backend/tests/test_google_auth.py` — Unit + integration tests for the new endpoint.

**Backend (modify):**
- `Backend/app/core/config.py` — Add `google_web_client_id`, `google_android_client_id`, `google_login_enabled` to `Settings` and read from env.
- `Backend/app/routers/auth.py` — Add `POST /auth/google` route with rate limit, error handling, login-history recording.
- `Backend/requirements.txt` — Add `google-auth==2.35.0` (latest stable compatible with Python 3.11).
- `.env.example` — Document new envs.

**Frontend (new):**
- `Frontend/src/services/googleSignIn.js` — Loads Google Identity Services script, renders Google button, exposes `signInWithGoogle()` returning the `id_token`.
- `Frontend/src/composables/useGoogleLogin.js` — Wraps the GIS service + backend POST `/auth/google`, mirrors `useAuth` redirect logic.
- `Frontend/src/components/auth/GoogleSignInButton.vue` — Reusable button mounted under the form on `LoginView`.

**Frontend (modify):**
- `Frontend/src/services/backendApi.js` — Add `loginWithGoogle(baseUrl, idToken)`.
- `Frontend/src/views/auth/LoginView.vue` — Add Google button beneath the Log In button; move "Forgot password?" to right-aligned position under the password input.
- `Frontend/src/services/backendBaseUrl.js` (or new `Frontend/src/config/googleAuth.js`) — Expose `resolveGoogleWebClientId()` reading from `import.meta.env.VITE_GOOGLE_WEB_CLIENT_ID` and `window.__AURA_RUNTIME_CONFIG__.googleWebClientId`.
- `Frontend/.env.development.local.example` — Add `VITE_GOOGLE_WEB_CLIENT_ID`.
- `Frontend/runtime-config.js.template` — Add `googleWebClientId`.
- `Frontend/scripts/write-runtime-config.mjs` — Pass through `AURA_GOOGLE_WEB_CLIENT_ID`.
- `Frontend/index.html` — Add CSP-safe script tag for `https://accounts.google.com/gsi/client` (deferred load via service is also acceptable; preferred is the service to keep CSP simple).
- `Frontend/capacitor.config.json` — Allow `accounts.google.com` in `allowNavigation`.

**Docs (modify):**
- `README.md` (or `docs/setup/google-auth.md` if README is bloated) — Google Cloud Console setup steps for web + Android, incl. `com.aura.app` package and SHA-1.

---

## Task 1: Add `google-auth` dependency

**Files:**
- Modify: `Backend/requirements.txt`

- [ ] **Step 1: Append `google-auth` (already pulls `google-auth-httplib2` transitively via `requests`; we use the bare verifier)**

```
google-auth==2.35.0
requests==2.32.3
```

If `requests` is already present, do not duplicate. Verify via:

```bash
grep -E '^(google-auth|requests)==' Backend/requirements.txt
```

- [ ] **Step 2: Install locally**

Run:
```bash
cd Backend && python -m pip install -r requirements.txt
```
Expected: succeeds without resolver conflicts.

- [ ] **Step 3: Commit**

```bash
git add Backend/requirements.txt
git commit -m "chore(backend): add google-auth dependency for Google OAuth verification"
```

---

## Task 2: Backend config — Google client IDs & feature flag

**Files:**
- Modify: `Backend/app/core/config.py`

- [ ] **Step 1: Extend `Settings` dataclass**

In `Backend/app/core/config.py`, inside the `@dataclass(frozen=True) class Settings:` block, after `cors_allowed_origins: list[str]`, add:

```python
    google_login_enabled: bool
    google_web_client_id: str
    google_android_client_id: str
```

- [ ] **Step 2: Populate in `get_settings()`**

In the same file, inside the `return Settings(...)` call, after the `cors_allowed_origins=...` line, add:

```python
        google_login_enabled=_as_bool(os.getenv("GOOGLE_LOGIN_ENABLED"), True),
        google_web_client_id=os.getenv("GOOGLE_WEB_CLIENT_ID", "").strip(),
        google_android_client_id=os.getenv("GOOGLE_ANDROID_CLIENT_ID", "").strip(),
```

- [ ] **Step 3: Run a smoke import**

```bash
cd Backend && python -c "from app.core.config import get_settings; s = get_settings(); print(s.google_login_enabled, bool(s.google_web_client_id))"
```
Expected: prints `True False` (no env values set yet).

- [ ] **Step 4: Commit**

```bash
git add Backend/app/core/config.py
git commit -m "feat(backend): add google_login_enabled and Google client ID settings"
```

---

## Task 3: Backend Google auth service (TDD)

**Files:**
- Create: `Backend/app/services/google_auth_service.py`
- Create: `Backend/tests/test_google_auth_service.py`

- [ ] **Step 1: Write failing test for happy path**

Create `Backend/tests/test_google_auth_service.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.google_auth_service import (
    GoogleAuthDisabledError,
    GoogleAuthInvalidTokenError,
    GoogleEmailNotVerifiedError,
    verify_google_id_token,
)


def _settings(*, enabled=True, web="web-id", android="android-id"):
    return SimpleNamespace(
        google_login_enabled=enabled,
        google_web_client_id=web,
        google_android_client_id=android,
    )


def test_returns_payload_for_web_audience():
    payload = {
        "aud": "web-id",
        "iss": "accounts.google.com",
        "email": "USER@Example.com",
        "email_verified": True,
        "sub": "1234",
    }
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        result = verify_google_id_token("token", settings=_settings())
    assert result["email"] == "user@example.com"
    assert result["sub"] == "1234"


def test_returns_payload_for_android_audience():
    payload = {
        "aud": "android-id",
        "iss": "https://accounts.google.com",
        "email": "user@example.com",
        "email_verified": True,
        "sub": "9",
    }
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        result = verify_google_id_token("token", settings=_settings())
    assert result["email"] == "user@example.com"


def test_raises_when_disabled():
    with pytest.raises(GoogleAuthDisabledError):
        verify_google_id_token("token", settings=_settings(enabled=False))


def test_raises_when_no_client_ids_configured():
    with pytest.raises(GoogleAuthDisabledError):
        verify_google_id_token("token", settings=_settings(web="", android=""))


def test_raises_invalid_token_when_audience_mismatches():
    payload = {"aud": "other", "iss": "accounts.google.com", "email": "u@x", "email_verified": True}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())


def test_raises_invalid_token_when_issuer_mismatches():
    payload = {"aud": "web-id", "iss": "evil.example", "email": "u@x", "email_verified": True}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())


def test_raises_email_not_verified():
    payload = {"aud": "web-id", "iss": "accounts.google.com", "email": "u@x", "email_verified": False}
    with patch("app.services.google_auth_service.id_token.verify_oauth2_token", return_value=payload):
        with pytest.raises(GoogleEmailNotVerifiedError):
            verify_google_id_token("token", settings=_settings())


def test_raises_invalid_token_when_google_lib_raises():
    with patch(
        "app.services.google_auth_service.id_token.verify_oauth2_token",
        side_effect=ValueError("bad token"),
    ):
        with pytest.raises(GoogleAuthInvalidTokenError):
            verify_google_id_token("token", settings=_settings())
```

- [ ] **Step 2: Run the test — confirm it fails (module missing)**

Run: `cd Backend && pytest tests/test_google_auth_service.py -v`
Expected: ImportError on `app.services.google_auth_service`.

- [ ] **Step 3: Implement the service**

Create `Backend/app/services/google_auth_service.py`:

```python
"""Use: Verifies Google ID tokens for the /auth/google endpoint.
Where to use: Called by the auth router when a frontend sends a Google id_token.
Role: Service layer. Encapsulates google-auth verification and policy checks.
"""

from __future__ import annotations

from typing import Any

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import Settings, get_settings


_ALLOWED_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class GoogleAuthError(Exception):
    """Base class for Google auth domain errors."""


class GoogleAuthDisabledError(GoogleAuthError):
    """Raised when Google login is disabled or unconfigured."""


class GoogleAuthInvalidTokenError(GoogleAuthError):
    """Raised when the ID token cannot be validated."""


class GoogleEmailNotVerifiedError(GoogleAuthError):
    """Raised when the Google account email is not verified."""


def _allowed_audiences(settings: Settings) -> list[str]:
    return [c for c in (settings.google_web_client_id, settings.google_android_client_id) if c]


def verify_google_id_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    if not settings.google_login_enabled:
        raise GoogleAuthDisabledError("Google login is disabled.")

    audiences = _allowed_audiences(settings)
    if not audiences:
        raise GoogleAuthDisabledError("Google login is disabled.")

    try:
        payload = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=audiences,
        )
    except ValueError as exc:
        raise GoogleAuthInvalidTokenError(str(exc)) from exc

    if payload.get("aud") not in audiences:
        raise GoogleAuthInvalidTokenError("Token audience is not allowed.")

    if payload.get("iss") not in _ALLOWED_ISSUERS:
        raise GoogleAuthInvalidTokenError("Token issuer is not allowed.")

    if not payload.get("email_verified"):
        raise GoogleEmailNotVerifiedError("Google email is not verified.")

    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise GoogleAuthInvalidTokenError("Token has no email claim.")
    payload["email"] = email
    return payload
```

- [ ] **Step 4: Run the test — confirm it passes**

Run: `cd Backend && pytest tests/test_google_auth_service.py -v`
Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add Backend/app/services/google_auth_service.py Backend/tests/test_google_auth_service.py
git commit -m "feat(backend): add Google ID token verification service"
```

---

## Task 4: Backend `POST /auth/google` route (TDD)

**Files:**
- Create: `Backend/app/schemas/google_auth.py`
- Modify: `Backend/app/routers/auth.py`
- Create: `Backend/tests/test_google_auth.py`

- [ ] **Step 1: Write the failing integration test**

Create `Backend/tests/test_google_auth.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.dependencies import get_db
from app.core.rate_limit import reset_rate_limit_state
from app.models import Base
from app.models.role import Role
from app.models.school import School
from app.models.user import User, UserRole
from app.routers import auth as auth_router
from app.services import google_auth_service


@pytest.fixture()
def app_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router.router)
    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limit_state()

    db = TestingSessionLocal()
    school = School(name="Test", school_name="Test", school_code="TST")
    db.add(school)
    db.flush()
    role = Role(name="student")
    db.add(role)
    db.flush()
    user = User(
        email="user@example.com",
        first_name="U",
        last_name="L",
        is_active=True,
        school_id=school.id,
    )
    user.set_password("StrongP@ssword1!")
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.close()

    with TestClient(app) as client:
        yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _patch_verify(payload):
    return patch.object(google_auth_service, "verify_google_id_token", return_value=payload)


def test_google_login_succeeds_for_existing_user(app_client):
    client, _ = app_client
    payload = {"email": "user@example.com", "email_verified": True, "sub": "1"}
    with _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["email"] == "user@example.com"


def test_google_login_rejects_unregistered_email(app_client):
    client, _ = app_client
    payload = {"email": "stranger@example.com", "email_verified": True, "sub": "2"}
    with _patch_verify(payload):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Google account is not registered."


def test_google_login_rejects_unverified_email(app_client):
    client, _ = app_client
    with patch.object(
        google_auth_service,
        "verify_google_id_token",
        side_effect=google_auth_service.GoogleEmailNotVerifiedError("nope"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Google email is not verified."


def test_google_login_returns_403_when_disabled(app_client):
    client, _ = app_client
    with patch.object(
        google_auth_service,
        "verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthDisabledError("off"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Google login is disabled."


def test_google_login_returns_401_for_invalid_token(app_client):
    client, _ = app_client
    with patch.object(
        google_auth_service,
        "verify_google_id_token",
        side_effect=google_auth_service.GoogleAuthInvalidTokenError("bad"),
    ):
        response = client.post("/auth/google", json={"id_token": "fake"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google token."
```

- [ ] **Step 2: Run the test — confirm it fails**

Run: `cd Backend && pytest tests/test_google_auth.py -v`
Expected: 404 from FastAPI on `/auth/google` (route not yet defined).

- [ ] **Step 3: Create the request schema**

Create `Backend/app/schemas/google_auth.py`:

```python
"""Use: Request schemas for Google OAuth login.
Where to use: The /auth/google endpoint.
Role: Schema layer.
"""

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., min_length=10, description="Google ID token from the client.")
```

- [ ] **Step 4: Add the route to `Backend/app/routers/auth.py`**

At the top of the file, extend imports:

```python
from app.schemas.google_auth import GoogleLoginRequest
from app.services.google_auth_service import (
    GoogleAuthDisabledError,
    GoogleAuthInvalidTokenError,
    GoogleEmailNotVerifiedError,
    verify_google_id_token,
)
```

After the `login_with_email` endpoint and before `change_password`, add:

```python
@router.post("/auth/google", response_model=Token)
def login_with_google(
    request: Request,
    payload: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    """Verify a Google ID token and issue an access token for a registered user."""
    enforce_rate_limit(
        build_login_rule(),
        f"{client_ip_identity(request)}:google",
        request=request,
    )

    try:
        google_payload = verify_google_id_token(payload.id_token)
    except GoogleAuthDisabledError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="google_login_disabled",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google login is disabled.")
    except GoogleEmailNotVerifiedError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="email_not_verified",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email is not verified.")
    except GoogleAuthInvalidTokenError:
        record_login_history(
            db,
            email_attempted="",
            user=None,
            success=False,
            auth_method="google",
            failure_reason="invalid_token",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token.")

    email = google_payload["email"]

    user = (
        db.query(User)
        .options(joinedload(User.roles).joinedload(UserRole.role))
        .filter(User.email == email)
        .first()
    )
    if user is None:
        record_login_history(
            db,
            email_attempted=email,
            user=None,
            success=False,
            auth_method="google",
            failure_reason="not_registered",
            request=request,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google account is not registered.")

    validate_login_account_state(db, user)

    response_payload = issue_login_token_response(
        db=db,
        user=user,
        request=request,
        remember_me=False,
    )
    record_login_history(
        db,
        email_attempted=user.email,
        user=user,
        success=True,
        auth_method="google",
        request=request,
    )
    db.commit()
    return response_payload
```

- [ ] **Step 5: Run the tests — confirm they pass**

Run: `cd Backend && pytest tests/test_google_auth.py -v`
Expected: all 5 tests pass.

- [ ] **Step 6: Run the full backend suite to ensure no regressions**

Run: `cd Backend && pytest -q`
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add Backend/app/schemas/google_auth.py Backend/app/routers/auth.py Backend/tests/test_google_auth.py
git commit -m "feat(backend): add POST /auth/google endpoint with rate limit and login history"
```

---

## Task 5: Backend env example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Append Google OAuth section**

After the `# Optional` block beginning at line ~22 (`PRIVILEGED_FACE_VERIFICATION_ENABLED=true`), add:

```
# Google OAuth (optional). When unset, /auth/google returns 403.
GOOGLE_LOGIN_ENABLED=true
GOOGLE_WEB_CLIENT_ID=529915700328-odjfatcruou55sv6ddolf3h9kbjc0p2u.apps.googleusercontent.com
GOOGLE_ANDROID_CLIENT_ID=
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "docs: document Google OAuth env vars in .env.example"
```

---

## Task 6: Frontend env + runtime config plumbing

**Files:**
- Modify: `Frontend/.env.development.local.example`
- Modify: `Frontend/runtime-config.js.template`
- Modify: `Frontend/scripts/write-runtime-config.mjs`
- Create: `Frontend/src/config/googleAuth.js`

- [ ] **Step 1: Add `VITE_GOOGLE_WEB_CLIENT_ID` to dev example**

Append to `Frontend/.env.development.local.example`:

```
# Google OAuth (web). Use the Web client ID from Google Cloud Console.
VITE_GOOGLE_WEB_CLIENT_ID=529915700328-odjfatcruou55sv6ddolf3h9kbjc0p2u.apps.googleusercontent.com
```

- [ ] **Step 2: Update runtime-config template**

Replace `Frontend/runtime-config.js.template` with:

```javascript
window.__AURA_RUNTIME_CONFIG__ = {
  apiBaseUrl: "${AURA_API_BASE_URL}",
  apiTimeoutMs: "${AURA_API_TIMEOUT_MS}",
  googleWebClientId: "${AURA_GOOGLE_WEB_CLIENT_ID}"
}
```

- [ ] **Step 3: Update the runtime-config writer script**

Open `Frontend/scripts/write-runtime-config.mjs`. Find where `AURA_API_BASE_URL` and `AURA_API_TIMEOUT_MS` are read from `process.env` and substituted into the template. Add the same substitution for `AURA_GOOGLE_WEB_CLIENT_ID`, defaulting to an empty string when unset.

If the script reads pairs like:

```js
const replacements = {
  AURA_API_BASE_URL: process.env.AURA_API_BASE_URL ?? '',
  AURA_API_TIMEOUT_MS: process.env.AURA_API_TIMEOUT_MS ?? '',
}
```

Add:

```js
  AURA_GOOGLE_WEB_CLIENT_ID: process.env.AURA_GOOGLE_WEB_CLIENT_ID ?? '',
```

(If the file uses a different shape, mirror it verbatim. Read it first, then edit.)

- [ ] **Step 4: Create resolver helper**

Create `Frontend/src/config/googleAuth.js`:

```javascript
export function resolveGoogleWebClientId() {
    const runtime = typeof window !== 'undefined' ? window.__AURA_RUNTIME_CONFIG__ : null
    const fromRuntime = runtime?.googleWebClientId
    if (fromRuntime && !fromRuntime.startsWith('${')) {
        return String(fromRuntime).trim()
    }
    const fromEnv = import.meta?.env?.VITE_GOOGLE_WEB_CLIENT_ID
    return String(fromEnv ?? '').trim()
}

export function isGoogleLoginAvailable() {
    return resolveGoogleWebClientId().length > 0
}
```

- [ ] **Step 5: Commit**

```bash
git add Frontend/.env.development.local.example Frontend/runtime-config.js.template Frontend/scripts/write-runtime-config.mjs Frontend/src/config/googleAuth.js
git commit -m "feat(frontend): plumb Google web client ID through env and runtime config"
```

---

## Task 7: Frontend Google Sign-In service

**Files:**
- Create: `Frontend/src/services/googleSignIn.js`

- [ ] **Step 1: Implement the GIS loader**

Create `Frontend/src/services/googleSignIn.js`:

```javascript
import { resolveGoogleWebClientId } from '@/config/googleAuth.js'

const GIS_SCRIPT_URL = 'https://accounts.google.com/gsi/client'
let scriptPromise = null

function loadGisScript() {
    if (typeof window === 'undefined') {
        return Promise.reject(new Error('Google Sign-In is only available in the browser.'))
    }
    if (window.google?.accounts?.id) {
        return Promise.resolve(window.google)
    }
    if (scriptPromise) return scriptPromise

    scriptPromise = new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${GIS_SCRIPT_URL}"]`)
        const handleLoad = () => {
            if (window.google?.accounts?.id) resolve(window.google)
            else reject(new Error('Google Identity Services failed to initialize.'))
        }
        if (existing) {
            existing.addEventListener('load', handleLoad)
            existing.addEventListener('error', () => reject(new Error('Failed to load Google script.')))
            return
        }
        const script = document.createElement('script')
        script.src = GIS_SCRIPT_URL
        script.async = true
        script.defer = true
        script.onload = handleLoad
        script.onerror = () => reject(new Error('Failed to load Google script.'))
        document.head.appendChild(script)
    })

    return scriptPromise
}

export async function ensureGoogleClientReady() {
    const clientId = resolveGoogleWebClientId()
    if (!clientId) throw new Error('Google login is not configured.')
    const google = await loadGisScript()
    return { google, clientId }
}

export async function renderGoogleButton(targetElement, { onCredential, theme = 'outline', size = 'large' } = {}) {
    const { google, clientId } = await ensureGoogleClientReady()
    google.accounts.id.initialize({
        client_id: clientId,
        callback: (response) => {
            if (response?.credential) onCredential(response.credential)
        },
        ux_mode: 'popup',
        auto_select: false,
    })
    google.accounts.id.renderButton(targetElement, {
        theme,
        size,
        type: 'standard',
        shape: 'pill',
        text: 'continue_with',
        logo_alignment: 'left',
        width: targetElement?.clientWidth || 320,
    })
}

export async function signInWithGooglePopup() {
    const { google, clientId } = await ensureGoogleClientReady()
    return new Promise((resolve, reject) => {
        google.accounts.id.initialize({
            client_id: clientId,
            callback: (response) => {
                if (response?.credential) resolve(response.credential)
                else reject(new Error('No credential returned by Google.'))
            },
            ux_mode: 'popup',
            auto_select: false,
        })
        google.accounts.id.prompt((notification) => {
            if (notification.isNotDisplayed?.() || notification.isSkippedMoment?.()) {
                reject(new Error('Google sign-in was dismissed.'))
            }
        })
    })
}
```

- [ ] **Step 2: Commit**

```bash
git add Frontend/src/services/googleSignIn.js
git commit -m "feat(frontend): add Google Identity Services loader and button renderer"
```

---

## Task 8: Frontend backend API client

**Files:**
- Modify: `Frontend/src/services/backendApi.js`

- [ ] **Step 1: Add `loginWithGoogle` next to `loginForAccessToken`**

After the `loginForAccessToken` function (around line 380), add:

```javascript
export async function loginWithGoogle(baseUrl, idToken) {
    return normalizeTokenPayload(await requestWithFallback(baseUrl, ['/api/auth/google', '/auth/google'], {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token: String(idToken ?? '') }),
    }, [404, 405]))
}
```

- [ ] **Step 2: Commit**

```bash
git add Frontend/src/services/backendApi.js
git commit -m "feat(frontend): add loginWithGoogle API client"
```

---

## Task 9: Frontend `useGoogleLogin` composable

**Files:**
- Create: `Frontend/src/composables/useGoogleLogin.js`

- [ ] **Step 1: Implement the composable mirroring `useAuth.login`**

Create `Frontend/src/composables/useGoogleLogin.js`:

```javascript
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginWithGoogle, resolveApiBaseUrl } from '@/services/backendApi.js'
import { BackendApiError } from '@/services/backendApi.js'
import {
    clearDashboardSession,
    getDefaultAuthenticatedRoute,
    initializeDashboardSession,
    sessionUsesLimitedMode,
    sessionNeedsFaceRegistration,
} from '@/composables/useDashboardSession.js'
import { hasPrivilegedPendingFace, storeAuthMeta } from '@/services/localAuth.js'
import { markCurrentRuntimeSession } from '@/services/sessionPersistence.js'
import { clearSessionExpiredNotice } from '@/services/sessionExpiry.js'

function describeError(err) {
    const detail = err?.payload?.detail
    if (typeof detail === 'string' && detail.trim()) return detail
    if (err?.status === 404) return 'Google account is not registered.'
    if (err?.status === 403) return 'Google login is disabled.'
    if (err?.status === 401) return 'Invalid Google token.'
    return err?.message || 'Google login failed. Please try again.'
}

export function useGoogleLogin() {
    const router = useRouter()
    const isLoading = ref(false)
    const error = ref(null)

    async function loginWithGoogleCredential(idToken, options = {}) {
        isLoading.value = true
        error.value = null
        try {
            if (!idToken) throw new Error('Missing Google credential.')
            clearSessionExpiredNotice()

            const apiBaseUrl = resolveApiBaseUrl()
            const tokenPayload = await loginWithGoogle(apiBaseUrl, idToken)
            const accessToken = tokenPayload?.access_token
            if (!accessToken) throw new Error('The API did not return an access token.')

            localStorage.setItem('aura_token', accessToken)
            localStorage.setItem('aura_user_roles', JSON.stringify(tokenPayload?.roles ?? []))
            const authMeta = storeAuthMeta(tokenPayload)
            markCurrentRuntimeSession()

            if (hasPrivilegedPendingFace(authMeta)) {
                const nextRoute = { name: 'PrivilegedFaceVerification' }
                if (options.preventRedirect) return nextRoute
                router.push(nextRoute)
                return
            }
            if (authMeta.mustChangePassword) {
                const nextRoute = { name: 'ChangePassword' }
                if (options.preventRedirect) return nextRoute
                router.push(nextRoute)
                return
            }

            const initializedSession = await initializeDashboardSession(true)
            if (!initializedSession?.user || sessionUsesLimitedMode()) {
                throw new Error('The backend did not return a complete user session.')
            }
            const nextRoute = sessionNeedsFaceRegistration()
                ? { name: 'FaceRegistration' }
                : getDefaultAuthenticatedRoute()
            if (options.preventRedirect) return nextRoute
            router.push(nextRoute)
        } catch (err) {
            clearDashboardSession()
            error.value = describeError(err)
            if (options.preventRedirect) return null
        } finally {
            isLoading.value = false
        }
    }

    return { loginWithGoogleCredential, isLoading, error }
}
```

- [ ] **Step 2: Verify `BackendApiError` is exported from `backendApi.js`**

Run:
```bash
grep -n "export.*BackendApiError" Frontend/src/services/backendApi.js
```
If not exported, add `export` to its declaration. (Read first; only edit if needed.)

- [ ] **Step 3: Commit**

```bash
git add Frontend/src/composables/useGoogleLogin.js Frontend/src/services/backendApi.js
git commit -m "feat(frontend): add useGoogleLogin composable mirroring email login flow"
```

---

## Task 10: Frontend `GoogleSignInButton` component

**Files:**
- Create: `Frontend/src/components/auth/GoogleSignInButton.vue`

- [ ] **Step 1: Implement the button**

Create `Frontend/src/components/auth/GoogleSignInButton.vue`:

```vue
<template>
  <div class="w-full flex flex-col items-center gap-2">
    <div ref="buttonHost" class="w-full flex justify-center min-h-[44px]"></div>
    <p v-if="errorMessage" class="text-red-500 text-xs text-center">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { renderGoogleButton } from '@/services/googleSignIn.js'
import { isGoogleLoginAvailable } from '@/config/googleAuth.js'

const emit = defineEmits(['credential', 'unavailable'])
const buttonHost = ref(null)
const errorMessage = ref('')

async function mountButton() {
    if (!buttonHost.value) return
    if (!isGoogleLoginAvailable()) {
        errorMessage.value = 'Google login is not configured.'
        emit('unavailable')
        return
    }
    try {
        await renderGoogleButton(buttonHost.value, {
            onCredential: (credential) => emit('credential', credential),
        })
    } catch (err) {
        errorMessage.value = err?.message || 'Failed to load Google Sign-In.'
        emit('unavailable')
    }
}

onMounted(mountButton)
watch(buttonHost, (el) => { if (el) mountButton() })
</script>
```

- [ ] **Step 2: Commit**

```bash
git add Frontend/src/components/auth/GoogleSignInButton.vue
git commit -m "feat(frontend): add reusable GoogleSignInButton component"
```

---

## Task 11: Wire Google button into `LoginView` + reposition Forgot Password

**Files:**
- Modify: `Frontend/src/views/auth/LoginView.vue`

- [ ] **Step 1: Replace the form section**

Replace the existing `<form>` block (lines 17–75) with:

```vue
        <form
          class="flex flex-col gap-3 transition-all duration-700 delay-100 ease-[cubic-bezier(0.22,1,0.36,1)] relative"
          :class="isMounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'"
          @submit.prevent="handleLogin"
        >
          <BaseInput
            id="email"
            v-model="email"
            type="email"
            placeholder="Gmail"
            autocomplete="email"
            tone="neutral"
            :disabled="isLoading || googleLoading"
          />

          <BaseInput
            id="password"
            v-model="password"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            tone="neutral"
            :disabled="isLoading || googleLoading"
            @enter="handleLogin"
          />

          <!-- Forgot Password Link (right-aligned, under password) -->
          <div class="flex justify-end -mt-1">
            <a
              href="#"
              class="text-[12px] font-medium transition-colors"
              style="color: var(--color-text-secondary);"
              @click.prevent="goToForgotPassword"
            >
              Forgot password?
            </a>
          </div>

          <Transition name="fade">
            <p v-if="visibleMessage" class="text-red-500 text-xs text-center mt-1">
              {{ visibleMessage }}
            </p>
          </Transition>

          <BaseButton
            type="submit"
            variant="primary"
            size="md"
            class="mt-1 group"
            :loading="isLoading"
            :disabled="googleLoading"
          >
            Log In
          </BaseButton>

          <!-- Google Sign-In below Log In -->
          <div class="flex items-center gap-3 my-1" aria-hidden="true">
            <div class="flex-1 h-px" style="background: var(--color-border, #2a2a2a);"></div>
            <span class="text-[11px] uppercase tracking-wide" style="color: var(--color-text-secondary);">or</span>
            <div class="flex-1 h-px" style="background: var(--color-border, #2a2a2a);"></div>
          </div>

          <GoogleSignInButton
            @credential="handleGoogleCredential"
            @unavailable="googleUnavailable = true"
          />
        </form>
```

- [ ] **Step 2: Update the `<script setup>` block**

Replace the script block (lines 116–185) with:

```vue
<script setup>
import { computed, ref, onBeforeMount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import TermsModal from '@/components/auth/TermsModal.vue'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import { useAuth } from '@/composables/useAuth.js'
import { useGoogleLogin } from '@/composables/useGoogleLogin.js'
import { applyTheme, loadUnbrandedTheme, surfaceAuraLogo } from '@/config/theme.js'
import { consumeSessionExpiredNotice } from '@/services/sessionExpiry.js'

const email = ref('')
const password = ref('')
const showTermsModal = ref(false)
const isMounted = ref(false)
const sessionNotice = ref('')
const googleUnavailable = ref(false)
const router = useRouter()

const { login, logout, isLoading, error } = useAuth()
const {
  loginWithGoogleCredential,
  isLoading: googleLoading,
  error: googleError,
} = useGoogleLogin()

const visibleMessage = computed(() => error.value || googleError.value || sessionNotice.value)
const nextRoute = ref(null)

onBeforeMount(() => {
  applyTheme(loadUnbrandedTheme())
})

onMounted(() => {
  sessionNotice.value = consumeSessionExpiredNotice()
  setTimeout(() => { isMounted.value = true }, 50)
})

async function handleLogin() {
  if (email.value === 'test' && password.value === 'test') {
    nextRoute.value = { name: 'PreviewHome' }
    showTermsModal.value = true
    return
  }
  const route = await login(email.value, password.value, { preventRedirect: true })
  if (route) {
    nextRoute.value = route
    showTermsModal.value = true
  }
}

async function handleGoogleCredential(credential) {
  const route = await loginWithGoogleCredential(credential, { preventRedirect: true })
  if (route) {
    nextRoute.value = route
    showTermsModal.value = true
  }
}

function handleAgree() {
  showTermsModal.value = false
  localStorage.setItem('aura_terms_agreed', 'true')
  if (nextRoute.value) router.push(nextRoute.value)
}

function handleDecline() {
  showTermsModal.value = false
  logout()
}

function goToForgotPassword() {
  router.push({ name: 'ForgotPassword' })
}
</script>
```

- [ ] **Step 3: Run dev server and visually verify**

```bash
cd Frontend && npm run dev
```
In a browser:
- Confirm "Continue with Google" button renders below Log In.
- Confirm "Forgot password?" appears right-aligned under the password field.
- Confirm email/password login still works.
- Confirm clicking Google button opens the popup; cancelling shows no error.
- Sign in with a registered Google account → lands on dashboard.
- Sign in with an unregistered Google account → "Google account is not registered." appears.

- [ ] **Step 4: Commit**

```bash
git add Frontend/src/views/auth/LoginView.vue
git commit -m "feat(frontend): add Google Sign-In to login page and right-align Forgot password"
```

---

## Task 12: Capacitor — allow Google domain + verify Android flow

**Files:**
- Modify: `Frontend/capacitor.config.json`
- Create: `docs/setup/google-auth.md` (or section in `README.md`)

- [ ] **Step 1: Allow Google account domain in Capacitor navigation**

In `Frontend/capacitor.config.json`, extend `server.allowNavigation`:

```json
"allowNavigation": [
  "ragweed-exemplary-sultry.ngrok-free.dev",
  "*.railway.app",
  "*.ngrok-free.dev",
  "*.ngrok.dev",
  "*.ngrok-free.app",
  "*.ngrok.app",
  "accounts.google.com",
  "*.googleusercontent.com"
]
```

- [ ] **Step 2: Build the Android APK for verification**

```bash
cd Frontend && npm run android:build:debug
```
Expected: APK builds. (CI may skip if Android SDK is unavailable — note in PR.)

- [ ] **Step 3: Install on a device/emulator and verify**

- Install the debug APK.
- Launch app → land on login.
- Tap "Continue with Google" → in-WebView Google popup loads.
- Sign in with a registered account → lands on dashboard.
- The Android client ID must be configured server-side for the audience check to pass; document the client ID requirement.

If GIS popup is blocked inside the WebView, the documented fallback is: tap-and-hold the button to open the Google sign-in URL in the system browser (the GIS library handles fallback automatically by surfacing `prompt` notifications). Capture any failure mode to the docs.

- [ ] **Step 4: Commit**

```bash
git add Frontend/capacitor.config.json
git commit -m "feat(android): allow Google account domains in Capacitor navigation"
```

---

## Task 13: Documentation — Google Console setup

**Files:**
- Create: `docs/setup/google-auth.md`
- Modify: `README.md` (add a one-line link)

- [ ] **Step 1: Write the setup guide**

Create `docs/setup/google-auth.md`:

```markdown
# Google OAuth Setup

This document explains how to wire Google Sign-In for the Aura web app and the Capacitor Android app (`com.aura.app`).

## 1. Google Cloud Console

1. Open https://console.cloud.google.com/ → select or create a project.
2. **APIs & Services → OAuth consent screen** → configure (External, internal testers, support email, scopes: `email`, `profile`, `openid`).

## 2. Web Client ID

**Credentials → Create Credentials → OAuth client ID → Web application.**

- Authorized JavaScript origins:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - Production origin (e.g., `https://app.aura.example`)
- Authorized redirect URIs (used only if you add server-side flow later; for GIS button alone, popup origin suffices):
  - `http://localhost:5173`
  - Production origin

Save the **Web client ID** (current value: `529915700328-odjfatcruou55sv6ddolf3h9kbjc0p2u.apps.googleusercontent.com`) into:
- Backend env: `GOOGLE_WEB_CLIENT_ID`
- Frontend env: `VITE_GOOGLE_WEB_CLIENT_ID` (and `AURA_GOOGLE_WEB_CLIENT_ID` for runtime config in Capacitor builds)

## 3. Android Client ID

**Credentials → Create Credentials → OAuth client ID → Android.**

- Package name: `com.aura.app`
- SHA-1 certificate fingerprint:
  - Debug: from `~/.android/debug.keystore` —
    ```
    keytool -list -v -alias androiddebugkey -keystore ~/.android/debug.keystore -storepass android -keypass android
    ```
  - Release: from your release keystore (same command with the release alias/keystore).

Save the **Android client ID** into the backend env: `GOOGLE_ANDROID_CLIENT_ID`. The Android app does NOT need it client-side because the GIS WebView flow uses the Web client ID for the popup; the backend accepts both audiences.

## 4. Backend env

```
GOOGLE_LOGIN_ENABLED=true
GOOGLE_WEB_CLIENT_ID=529915700328-...apps.googleusercontent.com
GOOGLE_ANDROID_CLIENT_ID=<android client id>
```

## 5. Frontend env

Local dev (`Frontend/.env.development.local`):
```
VITE_GOOGLE_WEB_CLIENT_ID=529915700328-...apps.googleusercontent.com
```

Capacitor build (set before `npm run android:build:debug` / `:release`):
```
AURA_GOOGLE_WEB_CLIENT_ID=529915700328-...apps.googleusercontent.com
```

## 6. Behaviour

- The endpoint `POST /auth/google` accepts only registered users — there is no auto-create. Provision the user via the existing student/admin import path before they can sign in with Google.
- Email must be `email_verified: true`. Unverified Google emails are rejected.
- Login history is recorded with `auth_method="google"`.
- Rate limit reuses the standard login bucket.
```

- [ ] **Step 2: Reference the doc from README**

Add to `README.md` under any "Setup" section (or near the top of the auth-related docs):

```markdown
- Google Sign-In: see [docs/setup/google-auth.md](docs/setup/google-auth.md).
```

- [ ] **Step 3: Commit**

```bash
git add docs/setup/google-auth.md README.md
git commit -m "docs: add Google OAuth setup guide for web and Android"
```

---

## Task 14: Final verification

- [ ] **Step 1: Backend full test suite**

```bash
cd Backend && pytest -q
```
Expected: all tests pass.

- [ ] **Step 2: Frontend dev smoke**

```bash
cd Frontend && npm run dev
```
Manually:
- Email/password login still works (regression check).
- Forgot password link is right-aligned and routes to the existing forgot-password view.
- Google button renders. Successful Google sign-in for registered email lands on dashboard with the same role-based redirect as email login.
- Unregistered Google email surfaces "Google account is not registered."
- Disabling backend env (set `GOOGLE_LOGIN_ENABLED=false` and restart) → Google sign-in returns "Google login is disabled."

- [ ] **Step 3: Capacitor Android sanity (if SDK available)**

```bash
cd Frontend && npm run android:build:debug
```
Install and verify the Google flow on device. Document any deviation in `docs/setup/google-auth.md`.

- [ ] **Step 4: Push branch**

Confirm branch is `aura_ci_cd`:
```bash
git status && git log --oneline -n 12
```

Push when the user authorizes:
```bash
git push -u origin aura_ci_cd
```

---

## Self-Review Checklist (already applied)

- Spec coverage: backend endpoint ✓, env vars ✓, google-auth verification ✓, email_verified gate ✓, no auto-create ✓, reuses `validate_login_account_state` + `issue_login_token_response` ✓, login history `auth_method="google"` ✓, rate limit ✓, env examples ✓, web button ✓, Capacitor allowance ✓, error messages exactly as specified ✓, backend tests ✓, README/docs with origins/redirect/package/SHA-1 ✓, role redirect unchanged (uses same `getDefaultAuthenticatedRoute`) ✓, email/password preserved (no changes to existing endpoints) ✓.
- Forgot password right-aligned under password input ✓.
- Type/name consistency: `verify_google_id_token`, `GoogleAuthDisabledError`, `GoogleEmailNotVerifiedError`, `GoogleAuthInvalidTokenError`, `GoogleLoginRequest` are used identically across service, router, and tests.
