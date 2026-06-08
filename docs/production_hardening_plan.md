# Production Hardening Plan

## Scope

This plan covers the remaining infrastructure work required to move HireMind from a secure demo platform to an enterprise deployment target.

## Database Migration

- Replace SQLite with PostgreSQL in production.
- Add Alembic migrations for all schemas currently created in `database/init_db.py`.
- Use a connection pool with per-request transaction boundaries.
- Add read/write timeout handling and retry policy for transient database errors.
- Add scheduled backups, restore drills, and point-in-time recovery procedures.

## Message Bus Migration

- Replace the in-process agent queue with RabbitMQ as the production event bus.
- Build a topic exchange topology with durable agent queues, retry queues, and DLQs.
- Use routing keys such as `agent.supervisor`, `agent.cv_analysis`, and `event.candidate.matched`.
- Persist domain events in `domain_events` for audit, replay, and workflow recovery.
- Add queue depth, retry counts, DLQ counts, and consumer lag alerting.
- Ensure all messages are acknowledged only after successful processing.
- Implement exponential backoff and poison message handling by moving failures to DLQ.
- Maintain recovery playbooks for: agent crash, RabbitMQ restart, and consumer restart.

## Observability

- Emit OpenTelemetry traces for API requests, agent runs, queue operations, and database calls.
- Add structured JSON logging with correlation IDs.
- Export latency, error rate, queue depth, and resource utilization metrics.
- Build dashboards for auth failures, agent failures, queue lag, and slow database queries.

## Load Testing

- Add a load test harness for 100, 500, 1000, and 5000 concurrent users.
- Measure p50, p95, p99 latency, throughput, failure rate, CPU, memory, and queue wait time.
- Include long-running soak tests to detect memory leaks and backlog growth.

## Failure Testing

- Simulate database outage, queue outage, agent crash, model unavailability, and network latency spikes.
- Verify retries, circuit-breaking, fallback behavior, and graceful degradation.
- Record recovery time objectives and recovery point objectives.

## Security Operations

- Rotate JWT secrets and database credentials through environment-managed secret storage.
- Enforce least-privilege service accounts for database and queue access.
- Review access logs for unauthorized route access and tool execution attempts.
- Run recurring prompt-injection and privilege-escalation audits against agent-facing endpoints.

## Deployment Baseline

- Run backend behind a reverse proxy with HTTPS only.
- Use container health checks and rolling deployments.
- Separate public API, internal worker, queue, and database tiers.
- Maintain backup, restore, and incident response runbooks.
