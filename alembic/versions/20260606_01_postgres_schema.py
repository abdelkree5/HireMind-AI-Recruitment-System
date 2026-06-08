from __future__ import annotations

from alembic import op

from database.schema_sql import build_postgres_rollback_script, build_schema_script

# revision identifiers, used by Alembic.
revision = "20260606_01_postgres_schema"
down_revision = None
branch_labels = None
depends_on = None


def _split_statements(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False

    for char in script:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double

        if char == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def upgrade() -> None:
    for statement in _split_statements(build_schema_script("postgresql")):
        op.execute(statement)


def downgrade() -> None:
    for statement in build_postgres_rollback_script():
        op.execute(statement)