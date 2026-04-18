"""Run backend web, optional migrations/seed, and optional Celery sidecars.

This is intended for constrained platforms where multiple backend processes need
to share a single service allocation, such as a small Railway project.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_step(command: list[str], *, label: str) -> None:
    print(f"[runtime-stack] starting {label}: {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(
            f"[runtime-stack] {label} failed with exit code {completed.returncode}"
        )


def _start_process(command: list[str], *, label: str) -> subprocess.Popen[str]:
    print(f"[runtime-stack] launching {label}: {' '.join(command)}", flush=True)
    return subprocess.Popen(command, cwd=ROOT)


def main() -> int:
    import_dir = Path(os.getenv("IMPORT_STORAGE_DIR", "/tmp/valid8_imports"))
    logo_dir = Path(os.getenv("SCHOOL_LOGO_STORAGE_DIR", "/tmp/valid8_school_logos"))
    import_dir.mkdir(parents=True, exist_ok=True)
    logo_dir.mkdir(parents=True, exist_ok=True)

    if _as_bool("RUN_MIGRATIONS_ON_START"):
        _run_step(["alembic", "upgrade", "heads"], label="database migrations")

    if _as_bool("RUN_SEED_ON_START"):
        _run_step([sys.executable, "seed.py"], label="database seeding")

    processes: list[tuple[str, subprocess.Popen[str]]] = []
    celery_pool = os.getenv("CELERY_WORKER_POOL", "solo")
    celery_concurrency = os.getenv("CELERY_WORKER_CONCURRENCY", "1")

    if _as_bool("RUN_CELERY_WORKER"):
        processes.append(
            (
                "celery-worker",
                _start_process(
                    [
                        "celery",
                        "-A",
                        "app.workers.celery_app.celery_app",
                        "worker",
                        f"--loglevel={os.getenv('CELERY_LOGLEVEL', 'info')}",
                        "--pool",
                        celery_pool,
                        "--concurrency",
                        celery_concurrency,
                    ],
                    label="celery worker",
                ),
            )
        )

    if _as_bool("RUN_CELERY_BEAT"):
        processes.append(
            (
                "celery-beat",
                _start_process(
                    [
                        "celery",
                        "-A",
                        "app.workers.celery_app.celery_app",
                        "beat",
                        f"--loglevel={os.getenv('CELERY_LOGLEVEL', 'info')}",
                        "--schedule",
                        "/tmp/celerybeat-schedule",
                    ],
                    label="celery beat",
                ),
            )
        )

    processes.append(
        (
            "uvicorn",
            _start_process(
                [
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    os.getenv("PORT", "8000"),
                    "--workers",
                    os.getenv("UVICORN_WORKERS", "2"),
                    "--proxy-headers",
                ],
                label="uvicorn",
            ),
        )
    )

    shutting_down = False

    def _terminate_all() -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        print("[runtime-stack] terminating child processes", flush=True)
        for _, process in processes:
            if process.poll() is None:
                process.terminate()

        deadline = time.time() + 20
        while time.time() < deadline:
            if all(process.poll() is not None for _, process in processes):
                return
            time.sleep(0.25)

        for _, process in processes:
            if process.poll() is None:
                process.kill()

    def _handle_signal(signum: int, _frame) -> None:
        print(f"[runtime-stack] received signal {signum}", flush=True)
        _terminate_all()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        while True:
            for label, process in processes:
                returncode = process.poll()
                if returncode is None:
                    continue
                print(
                    f"[runtime-stack] process exited: {label} ({returncode})",
                    flush=True,
                )
                _terminate_all()
                return returncode
            time.sleep(1)
    finally:
        _terminate_all()


if __name__ == "__main__":
    raise SystemExit(main())
