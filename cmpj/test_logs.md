# TEST LOGS

| Date Tested | Path | File | API/UI Page | Response Time | Recommendations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-03-11 | /login | Backend/app/routers/auth.py | User Login (Attempt 1) | N/A | Fix bcrypt version incompatibility. |
| 2026-03-11 | /login | Backend/app/routers/auth.py | User Login (Attempt 2) | N/A | Patch email service to mock MFA codes in dev. |
| 2026-03-11 | /login | Backend/app/routers/auth.py | User Login (Attempt 3) | 2.1s | **SUCCESS**. |

<br>

# ERROR/BUGS LOGS

| Date Issued | Path | File | Issue | Patch/Diff (Line#) | Recommendations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-03-11 | /login | Backend/requirements.txt | Network error: 502 (Bad Gateway) - bcrypt/passlib incompatibility. | (L4): - `bcrypt==4.3.0` <br> + `bcrypt==4.0.1` | Use `bcrypt` 4.0.1 for `passlib` compatibility. |
| 2026-03-11 | /login | Backend/app/services/email_service.py | Network error: 502 (Bad Gateway) - Unconfigured SMTP. | (L16-34): Added console printing fallback. | Implement dev email mock to avoid crashes. |
| 2026-03-11 | /login | Frontend/src/pages/Login.jsx | Login button can be spammed during MFA trigger. | TBD | Disable button and show loading state after first click. |
