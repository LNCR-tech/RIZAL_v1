# Deployment Strategies

## Production (Blue-Green)
The production deployment strategy utilizes a Blue-Green approach to ensure zero downtime and safe rollbacks.

1. **Pre-deploy**: A full database backup is taken.
2. **Deploy to Green**: The new version is deployed to the inactive environment (Green).
3. **Health Check**: The Green environment is tested for health and basic functionality.
4. **Traffic Switch**: The load balancer/ingress is updated to route traffic from Blue to Green.
5. **Post-deploy**: Smoke tests are run against the live Production environment.
6. **Rollback**: If any step fails, traffic is immediately routed back to Blue.

The current VPS deployment implementation is documented in
[Production Continuous Deployment](./PRODUCTION_CD.md). It uses GitHub Actions,
SSH, Docker Compose, health checks, pre-deploy database backups, and automatic
rollback. Because the current backend is published directly on host port 8001,
it minimizes downtime with Compose-managed restarts; full blue-green traffic
switching requires adding a reverse proxy or load balancer target switch.

## Staging
Staging deployments happen automatically on pushes to the `develop` branch. This environment mirrors production as closely as possible and is used for final integration testing before release.

## Hotfixes
Pushes to branches matching `hotfix/*` trigger the Hotfix CD workflow. This creates an ephemeral environment for rapid testing and validation of urgent fixes before they are merged to `main` and deployed to production.
