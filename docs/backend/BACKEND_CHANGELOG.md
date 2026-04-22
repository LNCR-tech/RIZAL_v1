# Backend Changelog

## [2026-04-22] Seeder Evolution (v2.1)

### Fixed
- **Seeder Performance**: Optimized the `wipe_records` function using high-performance PostgreSQL `TRUNCATE CASCADE`. This reduces cleanup time for large datasets (100k+ rows) from minutes to under 5 seconds.
- **Data Fidelity**: Implemented stochastic social and historical data injection (Announcements, Student Notes, Compliance Audit Trails).

### Changed
- **Architecture**: Refactored the core seeder from the Backend module to the root `/seeder` directory for better environment isolation.
- **Configuration**: Deprecated legacy absolute record target variables (`SEED_MIN_RECORDS`, `SEED_MAX_RECORDS`) in favor of entity-based stochastic density.
- **Centralization**: All sample datasets are now strictly managed within `seeder/modules/config.py`.

## [2026-04-21] Stochastic Sanction Engine Support

### Added
- Integrated sanctions universe into the massive data seeding flow.
- Added support for `SanctionRecord` and `SanctionItem` generation for absent students.
- Implemented `SEED_START_MMDDYY` and `SEED_END_MMDDYY` for temporal windowing.
