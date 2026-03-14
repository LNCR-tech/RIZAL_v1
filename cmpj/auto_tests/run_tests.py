import argparse
import json
import os
import time
import uuid
import sqlite3
import psycopg2
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

# --- Settings ---
BASE_URL = "http://localhost:8000"
DEFAULT_OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Database connection settings (Update as needed)
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rizal_v1")

# --- PSV Headers ---
CORE_HEADER = [
    "Timestamp",
    "Test ID",
    "Iteration",
    "Endpoint",
    "Status",
    "Latency (ms)",
    "Remarks",
]

SECURITY_HEADER = [
    "Timestamp",
    "Actor Role",
    "Target School",
    "Action Attempted",
    "Expected",
    "Actual",
    "Lockdown Pass",
]

BULK_HEADER = [
    "Timestamp",
    "Job ID",
    "Operation Type",
    "Rows Total",
    "Success",
    "Failure",
    "Duration",
    "Error Report",
]

BIOMETRICS_HEADER = [
    "Timestamp",
    "Test Image ID",
    "Match ID",
    "Confidence",
    "Encoding Delta",
    "Expected",
    "Result",
]


@dataclass
class Config:
    base_url: str
    admin_email: str
    admin_password: str
    run_id: str
    out_dir: str
    suites: set
    db_url: str
    enable_mfa_bypass: bool


class PsvLogger:
    def __init__(self, base_dir: str) -> None:
        resolved_base = os.path.abspath(base_dir)
        os.makedirs(resolved_base, exist_ok=True)
        self.paths = {
            "core": os.path.join(resolved_base, "logs_core_api.psv"),
            "security": os.path.join(resolved_base, "logs_security.psv"),
            "bulk": os.path.join(resolved_base, "logs_bulk_ops.psv"),
            "biometrics": os.path.join(resolved_base, "logs_biometrics.psv"),
        }
        self.headers = {
            "core": CORE_HEADER,
            "security": SECURITY_HEADER,
            "bulk": BULK_HEADER,
            "biometrics": BIOMETRICS_HEADER,
        }
        self._ensure_headers()

    def _ensure_headers(self) -> None:
        for key, path in self.paths.items():
            header_line = "|".join(self.headers[key])
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(header_line + "\n")
                continue

            if os.path.getsize(path) == 0:
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(header_line + "\n")
                continue

            with open(path, "r", encoding="utf-8") as handle:
                first_line = (handle.readline() or "").strip()

            if first_line != header_line:
                with open(path, "r", encoding="utf-8") as handle:
                    existing = handle.read()
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(header_line + "\n")
                    if existing:
                        handle.write(existing.lstrip("\n"))

    def write(self, key: str, row: list[str]) -> None:
        path = self.paths[key]
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("|".join(row) + "\n")


class ApiClient:
    def __init__(self, base_url: str, token: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def request(self, method: str, endpoint: str, **kwargs: Any) -> Tuple[httpx.Response, int]:
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        start = time.monotonic()
        response = self.client.request(method, endpoint, headers=headers, **kwargs)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return response, elapsed_ms


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def make_run_id() -> str:
    return "RUN_" + datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")


def safe_detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict) and "detail" in data:
            return str(data["detail"])
        return json.dumps(data)[:200]
    except Exception:
        return (resp.text or "").strip()[:200]


def log_core(logger: PsvLogger, test_id: str, iteration: int, endpoint: str, status: str, latency_ms: Any, remarks: str) -> None:
    print(f"[CORE] {now_ts()} {test_id} {endpoint} {status} {latency_ms}ms {remarks}")
    logger.write(
        "core",
        [
            now_ts(),
            test_id,
            str(iteration),
            endpoint,
            status,
            str(latency_ms),
            remarks,
        ],
    )


def log_security(logger: PsvLogger, actor_role: str, target_school: str, action: str, expected: str, actual: str, lockdown_pass: str) -> None:
    print(f"[SECURITY] {now_ts()} {actor_role} {action} expected={expected} actual={actual} pass={lockdown_pass}")
    logger.write(
        "security",
        [
            now_ts(),
            actor_role,
            target_school,
            action,
            expected,
            actual,
            lockdown_pass,
        ],
    )


def log_bulk(logger: PsvLogger, job_id: str, operation: str, rows_total: str, success: str, failure: str, duration: str, error_report: str) -> None:
    print(f"[BULK] {now_ts()} {operation} job={job_id} rows={rows_total} ok={success} fail={failure} duration={duration} note={error_report}")
    logger.write(
        "bulk",
        [
            now_ts(),
            job_id,
            operation,
            rows_total,
            success,
            failure,
            duration,
            error_report,
        ],
    )


def log_biometrics(logger: PsvLogger, test_image_id: str, match_id: str, confidence: str, encoding_delta: str, expected: str, result: str) -> None:
    print(f"[BIOMETRICS] {now_ts()} {test_image_id} match={match_id} expected={expected} result={result}")
    logger.write(
        "biometrics",
        [
            now_ts(),
            test_image_id,
            match_id,
            confidence,
            encoding_delta,
            expected,
            result,
        ],
    )


def request_and_log(
    logger: PsvLogger,
    client: ApiClient,
    test_id: str,
    iteration: int,
    method: str,
    endpoint: str,
    expected_status: int = 200,
    **kwargs: Any,
) -> Tuple[Optional[httpx.Response], bool]:
    try:
        resp, latency = client.request(method, endpoint, **kwargs)
        ok = resp.status_code == expected_status
        status = "SUCCESS" if ok else "FAIL"
        remarks = f"status={resp.status_code}"
        if not ok:
            detail = safe_detail(resp)
            if detail:
                remarks = f"status={resp.status_code} detail={detail}"
        log_core(logger, test_id, iteration, endpoint, status, latency, remarks)
        return resp, ok
    except Exception as exc:
        log_core(logger, test_id, iteration, endpoint, "ERROR", "N/A", str(exc))
        return None, False


def get_latest_mfa_code(db_url: str, user_id: int) -> Optional[str]:
    """Retrieve the latest MFA code from the database for bypass."""
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(
            "SELECT code_hash FROM mfa_challenges WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            # Note: The code_hash is hashed. In our fallback mock, we are printing the RAW code to the console.
            # If we want the runner to "grab" it from the DB, we need to know how the mock stores it.
            # IN SOME SYSTEMS, WE MIGHT STORE THE RAW CODE IN A LOG TABLE OR JUST USE THE PRINTED LOG.
            # FOR NOW, LET'S ASSUME THE RUNNER CAN GRAB THE RAW CODE IF WE MODIFIED THE MOCK TO STORE IT SOMETHING SPECIAL.
            # Alternatively, if we can't get the RAW code from the DB (because it's hashed), we might need to rely on the console mock log.
            return row[0] # This is likely hashed!
        return None
    except Exception as e:
        print(f"[DB_ERROR] Failed to fetch MFA code: {e}")
        return None


def login_token(logger: PsvLogger, client: ApiClient, email: str, password: str, test_id: str, enable_mfa_bypass: bool = False, db_url: str = "") -> Optional[str]:
    # 1. Primary Login
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/token",
        expected_status=200,
        data={"username": email, "password": password},
    )
    if not ok or resp is None:
        return None
    
    data = resp.json()
    
    # 2. Check for MFA requirement
    if data.get("mfa_required"):
        if not enable_mfa_bypass:
            log_core(logger, test_id, 1, "/token", "BLOCKED", "N/A", "MFA required but bypass disabled")
            return None
        
        challenge_id = data.get("mfa_challenge_id")
        user_id = data.get("user_id")
        
        # IN REALITY: We'd need to scrape the log or have a custom "dev" endpoint to get the code.
        # FOR NOW: Let's log that we hit an MFA roadblock.
        log_core(logger, test_id, 1, "/token", "MFA_PENDING", "N/A", f"Challenge ID: {challenge_id}")
        
        # Placeholder for where we'd "grab" the code if we had a dedicated dev access
        # Since we're in AGENT/TESTER mode, we'll implement the logic to get the code.
        return None # Implementation pending real-time log access or DB raw storage
        
    return data.get("access_token")


def create_school_with_it(logger: PsvLogger, client: ApiClient, suffix: str, test_id: str) -> Optional[Dict[str, Any]]:
    school_name = f"Auto Test School {suffix}"
    school_code = f"AUTO{suffix}"
    school_it_email = f"schoolit_{suffix}@example.edu"
    payload = {
        "school_name": school_name,
        "primary_color": "#162F65",
        "secondary_color": "#2C5F9E",
        "school_code": school_code,
        "school_it_email": school_it_email,
        "school_it_first_name": "Auto",
        "school_it_middle_name": "",
        "school_it_last_name": "Tester",
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/api/school/admin/create-school-it",
        expected_status=200,
        data=payload,
    )
    if not ok or resp is None:
        return None
    return resp.json()


def reset_school_it_password(logger: PsvLogger, client: ApiClient, user_id: int, test_id: str) -> Optional[str]:
    endpoint = f"/api/school/admin/school-it-accounts/{user_id}/reset-password"
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        endpoint,
        expected_status=200,
    )
    if not ok or resp is None:
        return None
    return resp.json().get("temporary_password")


def create_department(logger: PsvLogger, client: ApiClient, name: str, test_id: str) -> Optional[int]:
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/departments/",
        expected_status=201,
        json={"name": name},
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def create_program(logger: PsvLogger, client: ApiClient, name: str, department_ids: list[int], test_id: str) -> Optional[int]:
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/programs/",
        expected_status=201,
        json={"name": name, "department_ids": department_ids},
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def create_event(logger: PsvLogger, client: ApiClient, name: str, department_ids: list[int], program_ids: list[int], test_id: str) -> Optional[int]:
    start_dt = datetime.now(timezone.utc) + timedelta(hours=1)
    end_dt = start_dt + timedelta(hours=2)
    payload = {
        "name": name,
        "location": "Auto Test Hall",
        "start_datetime": start_dt.isoformat(),
        "end_datetime": end_dt.isoformat(),
        "status": "upcoming",
        "department_ids": department_ids,
        "program_ids": program_ids,
        "ssg_member_ids": [],
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/events/",
        expected_status=201,
        json=payload,
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def create_user(logger: PsvLogger, client: ApiClient, email: str, first_name: str, last_name: str, roles: list[str], test_id: str) -> Optional[int]:
    payload = {
        "email": email,
        "first_name": first_name,
        "middle_name": "",
        "last_name": last_name,
        "roles": roles,
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/users/",
        expected_status=200,
        json=payload,
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def create_student_profile(logger: PsvLogger, client: ApiClient, user_id: int, student_id: str, department_id: int, program_id: int, test_id: str) -> bool:
    payload = {
        "user_id": user_id,
        "student_id": student_id,
        "department_id": department_id,
        "program_id": program_id,
        "year_level": 1,
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/users/admin/students/",
        expected_status=200,
        json=payload,
    )
    return ok and resp is not None


def reset_user_password(logger: PsvLogger, client: ApiClient, user_id: int, new_password: str, test_id: str) -> bool:
    endpoint = f"/users/{user_id}/reset-password"
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        endpoint,
        expected_status=204,
        json={"password": new_password},
    )
    return ok and resp is not None


def change_password(logger: PsvLogger, client: ApiClient, current_password: str, new_password: str, test_id: str) -> bool:
    payload = {
        "current_password": current_password,
        "new_password": new_password,
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/auth/change-password",
        expected_status=200,
        json=payload,
    )
    return ok and resp is not None


def record_face_scan(logger: PsvLogger, client: ApiClient, event_id: int, student_id: str) -> None:
    try:
        resp, latency = client.request(
            "POST",
            "/attendance/face-scan",
            params={"event_id": event_id, "student_id": student_id},
        )
        ok = resp.status_code == 200
        result = "PASS" if ok else "FAIL"
        if not ok:
            detail = safe_detail(resp)
            result = f"FAIL ({resp.status_code}) {detail}"
        log_biometrics(
            logger,
            "face_scan_api",
            student_id,
            "N/A",
            "N/A",
            "attendance_recorded",
            result,
        )
    except Exception as exc:
        log_biometrics(
            logger,
            "face_scan_api",
            student_id,
            "N/A",
            "N/A",
            "attendance_recorded",
            f"ERROR {exc}",
        )


def bulk_preview(logger: PsvLogger, client: ApiClient, file_path: str) -> None:
    if not os.path.exists(file_path):
        log_bulk(logger, "N/A", "Import_Preview", "0", "0", "0", "N/A", f"missing file: {file_path}")
        return

    try:
        with open(file_path, "rb") as handle:
            files = {
                "file": (
                    os.path.basename(file_path),
                    handle,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            start = time.monotonic()
            resp = client.client.post(
                client.base_url + "/api/admin/import-students/preview",
                headers={"Authorization": f"Bearer {client.token}"} if client.token else {},
                files=files,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            log_bulk(
                logger,
                "PREVIEW",
                "Import_Preview",
                "0",
                "0",
                "0",
                f"{elapsed_ms}ms",
                f"status={resp.status_code} {safe_detail(resp)}",
            )
            return

        data = resp.json()
        total_rows = str(data.get("total_rows", 0))
        success = str(data.get("valid_rows", 0))
        failure = str(data.get("invalid_rows", 0))
        log_bulk(
            logger,
            "PREVIEW",
            "Import_Preview",
            total_rows,
            success,
            failure,
            f"{elapsed_ms}ms",
            "preview",
        )
    except Exception as exc:
        log_bulk(logger, "PREVIEW", "Import_Preview", "0", "0", "0", "N/A", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="VALID8 automated API test runner")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--admin-email", default=os.getenv("ADMIN_EMAIL", "admin@university.edu"))
    parser.add_argument("--admin-password", default=os.getenv("ADMIN_PASSWORD", "AdminPass123!"))
    parser.add_argument("--run-id", default=os.getenv("TEST_RUN_ID", make_run_id()))
    parser.add_argument("--out-dir", default=os.getenv("TEST_OUT_DIR", DEFAULT_OUT_DIR))
    parser.add_argument("--suites", default=os.getenv("TEST_SUITES", "core,security,bulk,biometrics"))
    parser.add_argument("--db-url", default=DB_URL)
    parser.add_argument("--enable-mfa-bypass", action="store_true", help="Enable MFA code retrieval from DB (requires DB access)")
    args = parser.parse_args()

    suites = {item.strip().lower() for item in args.suites.split(",") if item.strip()}
    cfg = Config(
        base_url=args.base_url,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        run_id=args.run_id,
        out_dir=args.out_dir,
        suites=suites,
        db_url=args.db_url,
        enable_mfa_bypass=args.enable_mfa_bypass
    )

    logger = PsvLogger(cfg.out_dir)

    admin_client = ApiClient(cfg.base_url)
    admin_token = login_token(logger, admin_client, cfg.admin_email, cfg.admin_password, "AUTH_TOKEN_ADMIN", cfg.enable_mfa_bypass, cfg.db_url)
    if not admin_token:
        # If bypass implements, it would return a token. For now, we block on MFA if it triggers.
        return 1

    admin_client.token = admin_token

    suffix = uuid.uuid4().hex[:6]

    school_payload = create_school_with_it(logger, admin_client, suffix, "SCHOOL_CREATE_WITH_IT")
    if not school_payload:
        return 1

    school_it_user_id = school_payload.get("school_it_user_id")
    school_it_email = school_payload.get("school_it_email")
    school_name = school_payload.get("school", {}).get("school_name", "Unknown")

    if not school_it_user_id or not school_it_email:
        log_core(logger, "SCHOOL_IT_CONTEXT", 1, "/api/school/admin/create-school-it", "FAIL", "N/A", "missing school IT details")
        return 1

    school_it_password = reset_school_it_password(logger, admin_client, school_it_user_id, "SCHOOL_IT_RESET_PASSWORD")
    if not school_it_password:
        return 1

    school_it_client = ApiClient(cfg.base_url)
    school_it_token = login_token(logger, school_it_client, school_it_email, school_it_password, "AUTH_TOKEN_SCHOOL_IT")
    if not school_it_token:
        return 1
    school_it_client.token = school_it_token
    if not change_password(logger, school_it_client, school_it_password, school_it_password, "SCHOOL_IT_CHANGE_PASSWORD"):
        return 1

    department_name = f"Dept {suffix}"
    department_id = create_department(logger, school_it_client, department_name, "DEPARTMENT_CREATE")
    if not department_id:
        return 1

    program_name = f"Program {suffix}"
    program_id = create_program(logger, school_it_client, program_name, [department_id], "PROGRAM_CREATE")
    if not program_id:
        return 1

    event_id = create_event(logger, school_it_client, f"Event {suffix}", [department_id], [program_id], "EVENT_CREATE")
    if not event_id:
        return 1

    student_email = f"student_{suffix}@example.edu"
    student_user_id = create_user(logger, school_it_client, student_email, "Auto", "Student", ["student"], "USER_CREATE_STUDENT")
    if not student_user_id:
        return 1

    student_id = f"CS-2026-{suffix.upper()}"
    if not create_student_profile(logger, school_it_client, student_user_id, student_id, department_id, program_id, "STUDENT_PROFILE_CREATE"):
        return 1

    ssg_email = f"ssg_{suffix}@example.edu"
    ssg_user_id = create_user(logger, school_it_client, ssg_email, "Auto", "SSG", ["ssg"], "USER_CREATE_SSG")
    if not ssg_user_id:
        return 1

    ssg_password = "SsgPass123!"
    if not reset_user_password(logger, school_it_client, ssg_user_id, ssg_password, "SSG_RESET_PASSWORD"):
        return 1

    ssg_client = ApiClient(cfg.base_url)
    ssg_token = login_token(logger, ssg_client, ssg_email, ssg_password, "AUTH_TOKEN_SSG")
    if not ssg_token:
        return 1
    ssg_client.token = ssg_token
    if not change_password(logger, ssg_client, ssg_password, ssg_password, "SSG_CHANGE_PASSWORD"):
        return 1

    if "biometrics" in cfg.suites:
        record_face_scan(logger, ssg_client, event_id, student_id)

    if "bulk" in cfg.suites:
        bulk_preview(logger, school_it_client, os.path.join(REPO_ROOT, "Backend", "e2e_import_invalid.xlsx"))

    if "security" in cfg.suites:
        suffix_b = uuid.uuid4().hex[:6]
        school_payload_b = create_school_with_it(logger, admin_client, suffix_b, "SCHOOL_CREATE_WITH_IT_B")
        if not school_payload_b:
            log_security(logger, "school_it", "unknown", "cross_tenant_user_read", "404", "setup_failed", "NO")
        else:
            school_it_user_id_b = school_payload_b.get("school_it_user_id")
            school_it_email_b = school_payload_b.get("school_it_email")
            school_name_b = school_payload_b.get("school", {}).get("school_name", "Unknown")
            if not school_it_user_id_b or not school_it_email_b:
                log_security(logger, "school_it", "unknown", "cross_tenant_user_read", "404", "setup_failed", "NO")
            else:
                school_it_password_b = reset_school_it_password(logger, admin_client, school_it_user_id_b, "SCHOOL_IT_RESET_PASSWORD_B")
                if not school_it_password_b:
                    log_security(logger, "school_it", school_name_b, "cross_tenant_user_read", "404", "setup_failed", "NO")
                else:
                    school_it_client_b = ApiClient(cfg.base_url)
                    token_b = login_token(logger, school_it_client_b, school_it_email_b, school_it_password_b, "AUTH_TOKEN_SCHOOL_IT_B")
                    if not token_b:
                        log_security(logger, "school_it", school_name_b, "cross_tenant_user_read", "404", "setup_failed", "NO")
                    else:
                        school_it_client_b.token = token_b
                        endpoint = f"/users/{student_user_id}"
                        try:
                            resp, _ = school_it_client_b.request("GET", endpoint)
                            expected = "403 or 404"
                            actual = str(resp.status_code)
                            lockdown_pass = "YES" if resp.status_code in (403, 404) else "NO"
                            log_security(
                                logger,
                                "school_it",
                                school_name_b,
                                "cross_tenant_user_read",
                                expected,
                                actual,
                                lockdown_pass,
                            )
                        except Exception as exc:
                            log_security(
                                logger,
                                "school_it",
                                school_name_b,
                                "cross_tenant_user_read",
                                "404",
                                f"error {exc}",
                                "NO",
                            )

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
