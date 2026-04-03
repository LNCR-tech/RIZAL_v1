import argparse
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

# API runner intended for testers. It simulates user actions via HTTP calls (no UI automation).

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
DEFAULT_OUT_DIR = os.getenv("TEST_OUT_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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
    "Test ID",
    "Endpoint",
    "Status",
    "Latency (ms)",
    "Remarks",
]


@dataclass
class Config:
    base_url: str
    admin_email: str
    admin_password: str
    run_id: str
    out_dir: str
    suites: set[str]
    enable_mfa_bypass: bool
    health_timeout_seconds: int


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
            if not os.path.exists(path) or os.path.getsize(path) == 0:
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


def log_core(
    logger: PsvLogger,
    test_id: str,
    iteration: int,
    endpoint: str,
    status: str,
    latency_ms: Any,
    remarks: str,
) -> None:
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


def log_security(
    logger: PsvLogger,
    actor_role: str,
    target_school: str,
    action: str,
    expected: str,
    actual: str,
    lockdown_pass: str,
) -> None:
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


def log_bulk(
    logger: PsvLogger,
    job_id: str,
    operation: str,
    rows_total: str,
    success: str,
    failure: str,
    duration: str,
    error_report: str,
) -> None:
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


def log_biometrics(
    logger: PsvLogger,
    test_id: str,
    endpoint: str,
    status: str,
    latency_ms: Any,
    remarks: str,
) -> None:
    print(f"[BIOMETRICS] {now_ts()} {test_id} {endpoint} {status} {latency_ms}ms {remarks}")
    logger.write(
        "biometrics",
        [
            now_ts(),
            test_id,
            endpoint,
            status,
            str(latency_ms),
            remarks,
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


def wait_for_health(logger: PsvLogger, client: ApiClient, timeout_seconds: int) -> bool:
    deadline = time.monotonic() + max(timeout_seconds, 1)
    while time.monotonic() < deadline:
        resp, ok = request_and_log(logger, client, "HEALTH_WAIT", 1, "GET", "/health", expected_status=200)
        if ok and resp is not None:
            return True
        time.sleep(1.0)
    return False


def login_token(
    logger: PsvLogger,
    client: ApiClient,
    email: str,
    password: str,
    test_id: str,
    enable_mfa_bypass: bool = False,
) -> Optional[str]:
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
    if data.get("mfa_required"):
        if not enable_mfa_bypass:
            log_core(logger, test_id, 1, "/token", "BLOCKED", "N/A", "MFA required but bypass disabled")
            return None
        log_core(logger, test_id, 1, "/token", "MFA_PENDING", "N/A", "MFA bypass not implemented")
        return None

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


def change_password(logger: PsvLogger, client: ApiClient, current_password: str, new_password: str, test_id: str) -> bool:
    payload = {"current_password": current_password, "new_password": new_password}
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


def create_department(logger: PsvLogger, client: ApiClient, name: str, test_id: str) -> Optional[int]:
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/api/departments/",
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
        "/api/programs/",
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
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        "/api/events/",
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
        "/api/users/",
        expected_status=200,
        json=payload,
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def create_student_profile(
    logger: PsvLogger,
    client: ApiClient,
    user_id: int,
    student_id: str,
    department_id: int,
    program_id: int,
    test_id: str,
) -> bool:
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
        "/api/users/admin/students/",
        expected_status=200,
        json=payload,
    )
    return ok and resp is not None


def reset_user_password(logger: PsvLogger, client: ApiClient, user_id: int, new_password: str, test_id: str) -> bool:
    endpoint = f"/api/users/{user_id}/reset-password"
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


def get_governance_access(logger: PsvLogger, client: ApiClient, test_id: str) -> None:
    request_and_log(logger, client, test_id, 1, "GET", "/api/governance/access/me", expected_status=200)


def get_ssg_setup(logger: PsvLogger, client: ApiClient, test_id: str) -> Optional[Dict[str, Any]]:
    resp, ok = request_and_log(logger, client, test_id, 1, "GET", "/api/governance/ssg/setup", expected_status=200)
    if not ok or resp is None:
        return None
    return resp.json()


def list_governance_units(logger: PsvLogger, client: ApiClient, test_id: str) -> None:
    request_and_log(logger, client, test_id, 1, "GET", "/api/governance/units?unit_type=SSG", expected_status=200)


def get_governance_event_defaults(logger: PsvLogger, client: ApiClient, unit_id: int, test_id: str) -> None:
    request_and_log(logger, client, test_id, 1, "GET", f"/api/governance/units/{unit_id}/event-defaults", expected_status=200)


def assign_governance_member(logger: PsvLogger, client: ApiClient, unit_id: int, user_id: int, test_id: str) -> Optional[int]:
    payload = {
        "user_id": user_id,
        "position_title": "SSG Officer",
        "permission_codes": ["manage_events", "manage_attendance", "view_students"],
    }
    resp, ok = request_and_log(
        logger,
        client,
        test_id,
        1,
        "POST",
        f"/api/governance/units/{unit_id}/members",
        expected_status=201,
        json=payload,
    )
    if not ok or resp is None:
        return None
    return resp.json().get("id")


def list_governance_students(logger: PsvLogger, client: ApiClient, test_id: str) -> None:
    request_and_log(logger, client, test_id, 1, "GET", "/api/governance/students", expected_status=200)


def event_time_status(logger: PsvLogger, client: ApiClient, event_id: int, test_id: str) -> None:
    request_and_log(logger, client, test_id, 1, "GET", f"/api/events/{event_id}/time-status", expected_status=200)


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


def face_status(logger: PsvLogger, client: ApiClient, test_id: str) -> None:
    try:
        resp, latency = client.request("GET", "/api/auth/security/face-status")
        ok = resp.status_code == 200
        status = "SUCCESS" if ok else "FAIL"
        remarks = f"status={resp.status_code}"
        if not ok:
            detail = safe_detail(resp)
            if detail:
                remarks = f"status={resp.status_code} detail={detail}"
        log_biometrics(logger, test_id, "/api/auth/security/face-status", status, latency, remarks)
    except Exception as exc:
        log_biometrics(logger, test_id, "/api/auth/security/face-status", "ERROR", "N/A", str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="VALID8 automated API test runner")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--admin-email", default=os.getenv("ADMIN_EMAIL", "admin@yourdomain.com"))
    parser.add_argument("--admin-password", default=os.getenv("ADMIN_PASSWORD", "AdminPass123!"))
    parser.add_argument("--run-id", default=os.getenv("TEST_RUN_ID", make_run_id()))
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--suites", default=os.getenv("TEST_SUITES", "health,core,governance,events,bulk,security"))
    parser.add_argument("--enable-mfa-bypass", action="store_true", help="Enable MFA bypass (dev only)")
    parser.add_argument("--health-timeout-seconds", type=int, default=int(os.getenv("TEST_HEALTH_TIMEOUT_SECONDS", "60")))
    args = parser.parse_args()

    suites = {item.strip().lower() for item in args.suites.split(",") if item.strip()}
    cfg = Config(
        base_url=args.base_url,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        run_id=args.run_id,
        out_dir=args.out_dir,
        suites=suites,
        enable_mfa_bypass=args.enable_mfa_bypass,
        health_timeout_seconds=args.health_timeout_seconds,
    )

    logger = PsvLogger(cfg.out_dir)
    admin_client = ApiClient(cfg.base_url)

    if not wait_for_health(logger, admin_client, cfg.health_timeout_seconds):
        log_core(logger, "HEALTH_WAIT", 1, "/health", "FAIL", "N/A", f"timeout after {cfg.health_timeout_seconds}s")
        return 1

    admin_token = login_token(
        logger,
        admin_client,
        cfg.admin_email,
        cfg.admin_password,
        "AUTH_TOKEN_ADMIN",
        cfg.enable_mfa_bypass,
    )
    if not admin_token:
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

    school_it_password = reset_school_it_password(logger, admin_client, int(school_it_user_id), "SCHOOL_IT_RESET_PASSWORD")
    if not school_it_password:
        return 1

    school_it_client = ApiClient(cfg.base_url)
    school_it_token = login_token(
        logger,
        school_it_client,
        str(school_it_email),
        school_it_password,
        "AUTH_TOKEN_SCHOOL_IT",
        cfg.enable_mfa_bypass,
    )
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

    event_id = None
    if "events" in cfg.suites:
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

    student_password = "StudentPass123!"
    if not reset_user_password(logger, school_it_client, student_user_id, student_password, "STUDENT_RESET_PASSWORD"):
        return 1

    ssg_setup = None
    if "governance" in cfg.suites:
        ssg_setup = get_ssg_setup(logger, school_it_client, "GOV_SSG_SETUP")
        if not ssg_setup:
            return 1
        unit_id = ssg_setup.get("unit", {}).get("id")
        if not unit_id:
            return 1
        assign_governance_member(logger, school_it_client, int(unit_id), student_user_id, "GOV_ASSIGN_SSG_MEMBER")
        list_governance_units(logger, school_it_client, "GOV_LIST_UNITS")
        get_governance_event_defaults(logger, school_it_client, int(unit_id), "GOV_EVENT_DEFAULTS")
        list_governance_students(logger, school_it_client, "GOV_STUDENTS")

    student_client = ApiClient(cfg.base_url)
    student_token = login_token(
        logger,
        student_client,
        student_email,
        student_password,
        "AUTH_TOKEN_STUDENT",
        cfg.enable_mfa_bypass,
    )
    if not student_token:
        return 1
    student_client.token = student_token

    if not change_password(logger, student_client, student_password, student_password, "STUDENT_CHANGE_PASSWORD"):
        return 1

    if "governance" in cfg.suites:
        get_governance_access(logger, student_client, "GOV_ACCESS_STUDENT")

    if "events" in cfg.suites and event_id is not None:
        event_time_status(logger, school_it_client, event_id, "EVENT_TIME_STATUS")

    if "bulk" in cfg.suites:
        bulk_preview(logger, school_it_client, os.path.join(REPO_ROOT, "Backend", "e2e_import_invalid.xlsx"))

    if "biometrics" in cfg.suites:
        face_status(logger, school_it_client, "FACE_STATUS")

    if "security" in cfg.suites:
        suffix_b = uuid.uuid4().hex[:6]
        school_payload_b = create_school_with_it(logger, admin_client, suffix_b, "SCHOOL_CREATE_WITH_IT_B")
        if not school_payload_b:
            log_security(logger, "school_it", "unknown", "cross_tenant_user_read", "403 or 404", "setup_failed", "NO")
        else:
            school_it_user_id_b = school_payload_b.get("school_it_user_id")
            school_it_email_b = school_payload_b.get("school_it_email")
            school_name_b = school_payload_b.get("school", {}).get("school_name", "Unknown")
            if not school_it_user_id_b or not school_it_email_b:
                log_security(logger, "school_it", "unknown", "cross_tenant_user_read", "403 or 404", "setup_failed", "NO")
            else:
                school_it_password_b = reset_school_it_password(logger, admin_client, int(school_it_user_id_b), "SCHOOL_IT_RESET_PASSWORD_B")
                if not school_it_password_b:
                    log_security(logger, "school_it", school_name_b, "cross_tenant_user_read", "403 or 404", "setup_failed", "NO")
                else:
                    school_it_client_b = ApiClient(cfg.base_url)
                    token_b = login_token(
                        logger,
                        school_it_client_b,
                        str(school_it_email_b),
                        school_it_password_b,
                        "AUTH_TOKEN_SCHOOL_IT_B",
                        cfg.enable_mfa_bypass,
                    )
                    if not token_b:
                        log_security(logger, "school_it", school_name_b, "cross_tenant_user_read", "403 or 404", "setup_failed", "NO")
                    else:
                        school_it_client_b.token = token_b
                        endpoint = f"/api/users/{student_user_id}"
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
                                "403 or 404",
                                f"error {exc}",
                                "NO",
                            )

    log_core(logger, "RUN_COMPLETE", 1, "-", "SUCCESS", "N/A", f"run_id={cfg.run_id} school={school_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

