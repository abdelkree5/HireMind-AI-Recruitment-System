# Performance Comparison

## Current Baseline

The platform currently runs on SQLite in local development, which is simple but not appropriate for multi-worker production concurrency.

## Target State

PostgreSQL 16+ with SQLAlchemy pooling, `pool_pre_ping`, connection recycling, and transaction-scoped access.

## Comparison Status

| Metric                 | SQLite Baseline | PostgreSQL Target | Status              |
| ---------------------- | --------------- | ----------------- | ------------------- |
| Connection Concurrency | Limited         | Pooled            | Implemented in code |
| Transaction Isolation  | Basic           | Production-grade  | Implemented in code |
| Readiness Probe        | Manual          | Automated         | Implemented in code |
| Pool Monitoring        | N/A             | Available         | Implemented in code |
| Latency Benchmarks     | Not yet rerun   | Pending real test | Needs execution     |
| Throughput Benchmarks  | Not yet rerun   | Pending real test | Needs execution     |

## Next Validation Step

Run the load-testing suite against the PostgreSQL-backed deployment after database provisioning and data migration are complete.
