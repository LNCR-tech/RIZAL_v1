"""
Loads and validates seeder/variables.py before anything else runs.
Fails fast with a human-readable message on any misconfiguration.
"""

from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SeederConfig:
    SEED_ADMIN_EMAIL: str
    SEED_ADMIN_PASSWORD: str
    SEED_DATABASE: bool
    SEED_WIPE_EXISTING: bool
    SEED_RANDOMIZER_KEY: int
    SEED_UNIQUE_PASSWORDS: bool
    SEED_USER_SUFFIX_PROBABILITY: float
    SEED_CREDENTIALS_FORMAT: str
    SEED_N_SCHOOLS: int
    SEED_MIN_STUDENTS: int
    SEED_MAX_STUDENTS: int
    SEED_MIN_EVENTS: int
    SEED_MAX_EVENTS: int
    SEED_MIN_COLLEGES: int
    SEED_MAX_COLLEGES: int
    SEED_MIN_PROGRAMS: int
    SEED_START_MMDDYY: tuple
    SEED_END_MMDDYY: tuple


def load_config() -> SeederConfig:
    variables_path = Path(__file__).resolve().parent / "variables.py"

    if not variables_path.exists():
        _abort(
            "variables.py not found.\n"
            "  Expected location: seeder/variables.py\n"
            "  This file holds all seeder configuration. Create it by copying\n"
            "  the defaults from the comments in seeder/seed.py or the repo docs."
        )

    try:
        spec = importlib.util.spec_from_file_location("variables", variables_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        _abort(f"variables.py has a syntax error and could not be loaded:\n  {e}")
    except Exception as e:
        _abort(f"variables.py could not be imported:\n  {e}")

    errors = []

    def require(name: str, expected_type: type, extra: callable = None):
        if not hasattr(mod, name):
            errors.append(f"  - {name} is missing")
            return None
        val = getattr(mod, name)
        if not isinstance(val, expected_type):
            errors.append(f"  - {name} must be {expected_type.__name__}, got {type(val).__name__} ({val!r})")
            return None
        if extra:
            msg = extra(val)
            if msg:
                errors.append(f"  - {name}: {msg}")
                return None
        return val

    def non_empty_str(val: str):
        if not val.strip():
            return "must not be empty"

    def positive_int(val: int):
        if val < 1:
            return "must be >= 1"

    def non_negative_int(val: int):
        if val < 0:
            return "must be >= 0"

    def unit_float(val: float):
        if not (0.0 <= val <= 1.0):
            return "must be between 0.0 and 1.0"

    def valid_format(val: str):
        if val not in ("csv", "tsv", "psv"):
            return f"must be one of 'csv', 'tsv', 'psv', got {val!r}"

    def valid_mmddyy(val: tuple):
        if len(val) != 3:
            return "must be a 3-tuple of (month, day, year)"
        m, d, y = val
        if not all(isinstance(x, int) for x in (m, d, y)):
            return "all elements must be integers"
        if not (1 <= m <= 12):
            return f"month {m} is out of range (1–12)"
        if not (1 <= d <= 31):
            return f"day {d} is out of range (1–31)"
        if y < 2000:
            return f"year {y} looks wrong (expected >= 2000)"

    admin_email    = require("SEED_ADMIN_EMAIL",            str,   non_empty_str)
    admin_password = require("SEED_ADMIN_PASSWORD",         str,   non_empty_str)
    seed_db        = require("SEED_DATABASE",               bool)

    # Allow the SEED_DATABASE env var to override variables.py (e.g. when running via Docker)
    if seed_db is False:
        env_override = os.environ.get("SEED_DATABASE", "").strip().lower()
        if env_override in ("true", "1", "yes"):
            seed_db = True
    wipe           = require("SEED_WIPE_EXISTING",          bool)
    rng_key        = require("SEED_RANDOMIZER_KEY",         int)
    unique_pw      = require("SEED_UNIQUE_PASSWORDS",       bool)
    suffix_prob    = require("SEED_USER_SUFFIX_PROBABILITY",float, unit_float)
    cred_fmt       = require("SEED_CREDENTIALS_FORMAT",     str,   valid_format)
    n_schools      = require("SEED_N_SCHOOLS",              int,   positive_int)
    min_students   = require("SEED_MIN_STUDENTS",           int,   non_negative_int)
    max_students   = require("SEED_MAX_STUDENTS",           int,   non_negative_int)
    min_events     = require("SEED_MIN_EVENTS",             int,   non_negative_int)
    max_events     = require("SEED_MAX_EVENTS",             int,   non_negative_int)
    min_colleges   = require("SEED_MIN_COLLEGES",           int,   positive_int)
    max_colleges   = require("SEED_MAX_COLLEGES",           int,   positive_int)
    min_programs   = require("SEED_MIN_PROGRAMS",           int,   positive_int)
    start_mmddyy   = require("SEED_START_MMDDYY",           tuple, valid_mmddyy)
    end_mmddyy     = require("SEED_END_MMDDYY",             tuple, valid_mmddyy)

    if not errors and start_mmddyy and end_mmddyy:
        sm, sd, sy = start_mmddyy
        em, ed, ey = end_mmddyy
        if (sy, sm, sd) > (ey, em, ed):
            errors.append(
                f"  - SEED_START_MMDDYY {start_mmddyy} is later than SEED_END_MMDDYY {end_mmddyy}"
            )

    if errors:
        _abort("variables.py has invalid configuration:\n" + "\n".join(errors))

    return SeederConfig(
        SEED_ADMIN_EMAIL=admin_email,
        SEED_ADMIN_PASSWORD=admin_password,
        SEED_DATABASE=seed_db,
        SEED_WIPE_EXISTING=wipe,
        SEED_RANDOMIZER_KEY=rng_key,
        SEED_UNIQUE_PASSWORDS=unique_pw,
        SEED_USER_SUFFIX_PROBABILITY=suffix_prob,
        SEED_CREDENTIALS_FORMAT=cred_fmt,
        SEED_N_SCHOOLS=n_schools,
        SEED_MIN_STUDENTS=min_students,
        SEED_MAX_STUDENTS=max_students,
        SEED_MIN_EVENTS=min_events,
        SEED_MAX_EVENTS=max_events,
        SEED_MIN_COLLEGES=min_colleges,
        SEED_MAX_COLLEGES=max_colleges,
        SEED_MIN_PROGRAMS=min_programs,
        SEED_START_MMDDYY=start_mmddyy,
        SEED_END_MMDDYY=end_mmddyy,
    )


def _abort(message: str) -> None:
    print(f"\n[Seeder] Configuration error — cannot start.\n{message}\n", file=sys.stderr)
    sys.exit(1)
