#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any


@dataclass
class TransactionResult:
    success: bool
    duration_ms: float
    steps: int
    statuses: list[int]
    error: str | None = None


def build_url(base_url: str, path: str) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{normalized_base}{normalized_path}"


def request_json(
    *,
    method: str,
    url: str,
    timeout: float,
    insecure: bool,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        data=payload,
        headers=request_headers,
        method=method.upper(),
    )
    ssl_context = ssl._create_unverified_context() if insecure else None

    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.getcode(), json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        parsed = raw
        if raw.strip():
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw
        raise RuntimeError(f"HTTP {error.code}: {parsed}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Network error: {error.reason}") from error


def authenticate(base_url: str, api_prefix: str, email: str, password: str, timeout: float, insecure: bool) -> str:
    status, body = request_json(
        method="POST",
        url=build_url(base_url, f"{api_prefix}/login"),
        timeout=timeout,
        insecure=insecure,
        body={"email": email, "password": password},
    )
    token = body.get("access_token") if isinstance(body, dict) else None
    if status != 200 or not isinstance(token, str) or not token:
        raise RuntimeError("Login succeeded without an access_token response.")
    return token


def run_health(base_url: str, timeout: float, insecure: bool) -> TransactionResult:
    started_at = time.perf_counter()
    try:
        status, _ = request_json(
            method="GET",
            url=build_url(base_url, "/"),
            timeout=timeout,
            insecure=insecure,
        )
        return TransactionResult(
            success=status == 200,
            duration_ms=(time.perf_counter() - started_at) * 1000,
            steps=1,
            statuses=[status],
            error=None if status == 200 else f"Unexpected status {status}",
        )
    except Exception as error:  # noqa: BLE001
        return TransactionResult(
            success=False,
            duration_ms=(time.perf_counter() - started_at) * 1000,
            steps=1,
            statuses=[],
            error=str(error),
        )


def run_authenticated_transaction(
    *,
    base_url: str,
    api_prefix: str,
    timeout: float,
    insecure: bool,
    email: str,
    password: str,
    scenario: str,
    include_governance: bool,
) -> TransactionResult:
    started_at = time.perf_counter()
    statuses: list[int] = []

    try:
        token = authenticate(base_url, api_prefix, email, password, timeout, insecure)
        statuses.append(200)
        headers = {"Authorization": f"Bearer {token}"}

        request_plan: list[tuple[str, str]] = []
        if scenario in {"events", "mixed"}:
            request_plan.append(("GET", f"{api_prefix}/events/"))
        if scenario == "mixed":
            request_plan.append(("GET", f"{api_prefix}/users/me/"))
            request_plan.append(("GET", f"{api_prefix}/school-settings/me"))
            if include_governance:
                request_plan.append(("GET", f"{api_prefix}/api/governance/units/my-access"))

        for method, path in request_plan:
            status, _ = request_json(
                method=method,
                url=build_url(base_url, path),
                timeout=timeout,
                insecure=insecure,
                headers=headers,
            )
            statuses.append(status)

        return TransactionResult(
            success=True,
            duration_ms=(time.perf_counter() - started_at) * 1000,
            steps=len(statuses),
            statuses=statuses,
        )
    except Exception as error:  # noqa: BLE001
        return TransactionResult(
            success=False,
            duration_ms=(time.perf_counter() - started_at) * 1000,
            steps=len(statuses),
            statuses=statuses,
            error=str(error),
        )


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]

    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile_value
    low_index = int(rank)
    high_index = min(low_index + 1, len(ordered) - 1)
    fraction = rank - low_index
    return ordered[low_index] + (ordered[high_index] - ordered[low_index]) * fraction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simple concurrent load test for the RIZAL app and API."
    )
    parser.add_argument("--base-url", required=True, help="Base URL to test, e.g. http://127.0.0.1:8000 or https://your-app.example")
    parser.add_argument(
        "--api-prefix",
        default="",
        help="API prefix when testing through the frontend proxy, e.g. /api. Leave empty for direct backend access.",
    )
    parser.add_argument(
        "--scenario",
        default="health",
        choices=["health", "login", "events", "mixed"],
        help="health hits only /. login authenticates. events authenticates then loads events. mixed authenticates then loads several main pages' APIs.",
    )
    parser.add_argument("--email", help="Login email required for login, events, and mixed scenarios.")
    parser.add_argument("--password", help="Login password required for login, events, and mixed scenarios.")
    parser.add_argument("--requests", type=int, default=50, help="Total transactions to execute.")
    parser.add_argument("--concurrency", type=int, default=10, help="Maximum concurrent transactions.")
    parser.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout in seconds.")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification for self-signed HTTPS endpoints.")
    parser.add_argument(
        "--include-governance",
        action="store_true",
        help="In mixed mode, also call the governance access endpoint.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.requests < 1 or args.concurrency < 1:
        print("requests and concurrency must both be at least 1", file=sys.stderr)
        return 2

    if args.scenario != "health" and (not args.email or not args.password):
        print("email and password are required for login, events, and mixed scenarios", file=sys.stderr)
        return 2

    started_at = time.perf_counter()
    results: list[TransactionResult] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = []
        for _ in range(args.requests):
            if args.scenario == "health":
                futures.append(executor.submit(run_health, args.base_url, args.timeout, args.insecure))
            else:
                futures.append(
                    executor.submit(
                        run_authenticated_transaction,
                        base_url=args.base_url,
                        api_prefix=args.api_prefix,
                        timeout=args.timeout,
                        insecure=args.insecure,
                        email=args.email,
                        password=args.password,
                        scenario=args.scenario,
                        include_governance=args.include_governance,
                    )
                )

        for future in as_completed(futures):
            results.append(future.result())

    elapsed_seconds = time.perf_counter() - started_at
    durations = [result.duration_ms for result in results]
    successes = [result for result in results if result.success]
    failures = [result for result in results if not result.success]
    status_counts = Counter(status for result in results for status in result.statuses)
    error_counts = Counter(result.error for result in failures if result.error)

    print(f"Scenario: {args.scenario}")
    print(f"Base URL: {args.base_url}")
    print(f"API Prefix: {args.api_prefix or '(direct backend)'}")
    print(f"Transactions: {len(results)}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Elapsed Seconds: {elapsed_seconds:.2f}")
    print(f"Throughput (txn/s): {len(results) / elapsed_seconds:.2f}" if elapsed_seconds > 0 else "Throughput (txn/s): inf")
    print(f"Successful Transactions: {len(successes)}")
    print(f"Failed Transactions: {len(failures)}")
    print(f"Latency Min/Avg/P50/P95/P99/Max (ms): {min(durations):.2f} / {statistics.fmean(durations):.2f} / {percentile(durations, 0.50):.2f} / {percentile(durations, 0.95):.2f} / {percentile(durations, 0.99):.2f} / {max(durations):.2f}")

    if status_counts:
        print("HTTP Status Counts:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

    if error_counts:
        print("Top Errors:")
        for error, count in error_counts.most_common(5):
            print(f"  {count}x {error}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
