# Observability & Monitoring

## Tech Stack
- **Logs**: Loki (structured JSON logs)
- **Metrics**: Prometheus & Node Exporter
- **Dashboards**: Grafana
- **Uptime / Alerting**: Uptime Kuma

## Logging Standards
- All backend logs must output as structured JSON.
- Include `trace_id`, `user_id`, and `role` context.
- Errors must include full stack traces and contextual state.

## Metrics Exposed
- `http_requests_total`
- `http_request_duration_seconds`
- `db_query_duration_seconds`
- `active_users`

## Alerting Rules
- **P1 (Critical)**: Error rate > 5% over 5m, Database Unreachable, API Latency > 2s.
- **P2 (High)**: High CPU/RAM > 85%, High 4xx rate.
- **P3 (Warning)**: Cert expiring in 7 days, Backup job failed.
