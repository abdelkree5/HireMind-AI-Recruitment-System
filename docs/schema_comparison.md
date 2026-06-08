# Schema Comparison

## Logical Equivalence

The PostgreSQL and SQLite schemas are intentionally aligned so application code does not need to change its data model when the backend changes.

| Entity                | SQLite                | PostgreSQL            | Notes                 |
| --------------------- | --------------------- | --------------------- | --------------------- |
| users                 | TEXT primary key      | TEXT primary key      | Preserved             |
| auth_sessions         | TEXT primary key      | TEXT primary key      | Preserved             |
| posted_jobs           | TEXT primary key      | TEXT primary key      | Preserved             |
| job_applications      | TEXT primary key      | TEXT primary key      | Preserved             |
| interview_sessions    | TEXT primary key      | TEXT primary key      | Preserved             |
| interview_turns       | INTEGER AUTOINCREMENT | BIGSERIAL             | Backend-specific only |
| recruiter_feedback    | TEXT primary key      | TEXT primary key      | Preserved             |
| dynamic_skill_weights | composite primary key | composite primary key | Preserved             |
| agent_memory_stm      | composite primary key | composite primary key | Preserved             |
| agent_memory_ltm      | composite primary key | composite primary key | Preserved             |
| agent_episodes        | TEXT primary key      | TEXT primary key      | Preserved             |
| agent_traces          | TEXT primary key      | TEXT primary key      | Preserved             |
| agent_messages        | TEXT primary key      | TEXT primary key      | Preserved             |

## Migration Notes

- Existing JSON-in-TEXT storage remains intact for backward compatibility.
- All foreign keys and indexes are preserved in the new schema definition.
- Data migration preserves row contents and primary keys.

## Operational Notes

- PostgreSQL pools and timeouts are configured in [database/connection.py](../database/connection.py).
- Alembic revision history starts at [alembic/versions/20260606_01_postgres_schema.py](../alembic/versions/20260606_01_postgres_schema.py).
