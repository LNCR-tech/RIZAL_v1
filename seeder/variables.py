# =============================================================================
# Seeder configuration — edit these directly before running.
# No secrets here. DATABASE_URL is read by the backend's app.core.database
# from the root .env as usual.
# =============================================================================

# Platform admin account to create/preserve
SEED_ADMIN_EMAIL: str = "admin@aura.com"
SEED_ADMIN_PASSWORD: str = "AdminPass123!"

# Set to True to actually run the seeder (safety gate)
# SEED_DATABASE: bool = False  <- moved to .env

# Wipe all existing seeded data before inserting
# SEED_WIPE_EXISTING: bool = True  <- moved to .env

# Deterministic RNG key — change to generate a different universe
SEED_RANDOMIZER_KEY: int = 42

# True = unique bcrypt hash per student, False = uniform "Student123!"
SEED_UNIQUE_PASSWORDS: bool = False

# Probability (0.0–1.0) that a generated name gets a suffix (Jr., Sr., etc.)
SEED_USER_SUFFIX_PROBABILITY: float = 0.2

# Output format for credential files
SEED_CREDENTIALS_FORMAT: str = "csv"  # "csv" | "tsv" | "psv"

# Number of schools to generate
SEED_N_SCHOOLS: int = 5

# Student count range per school
SEED_MIN_STUDENTS: int = 100
SEED_MAX_STUDENTS: int = 200

# Event count range per school
SEED_MIN_EVENTS: int = 30
SEED_MAX_EVENTS: int = 100

# College (department) count range per school
SEED_MIN_COLLEGES: int = 3
SEED_MAX_COLLEGES: int = 8

# Minimum programs per college
SEED_MIN_PROGRAMS: int = 1

# Temporal range for generated event dates — (month, day, year)
SEED_START_MMDDYY: tuple = (1, 1, 2024)
SEED_END_MMDDYY: tuple = (12, 31, 2026)
