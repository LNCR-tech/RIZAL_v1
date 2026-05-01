# Database Migration and Safety

## Core Principles
Database changes are high-risk operations. The following practices ensure data integrity and system stability during deployments.

## Migration Workflow
1. **Local Development**:
   - Developers create migrations using `alembic revision --autogenerate`.
   - Migrations are tested locally with `alembic upgrade head` and `alembic downgrade -1`.

2. **Pre-Deployment (Staging & Production)**:
   - A full automated backup of the target database is taken before any migration scripts run.
   - The backup script includes a health check to verify the backup file's integrity.

3. **Deployment**:
   - Migrations are applied automatically during the CD pipeline (`alembic upgrade head`).
   - A **migration lock** mechanism is enforced to prevent concurrent migrations if multiple nodes try to run them simultaneously.

4. **Rollback**:
   - If migrations fail, the deployment halts.
   - The automated rollback process restores the pre-deployment database backup.
   - Runbook documents manual restore procedures for catastrophic failures.

## Performance Tuning & Logging
- **Slow Query Logging**: Enabled in production to identify and optimize inefficient queries.
- **Connection Pooling**: Implemented via PgBouncer or SQLAlchemy's built-in pool to manage database connections efficiently under load.
- **Retention Policy**: Automated scripts periodically clean up old backups based on a defined retention schedule (e.g., daily backups kept for 30 days, weekly backups kept for 1 year).
