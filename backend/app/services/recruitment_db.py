from __future__ import annotations

from database.connection import get_connection, DB_PATH
from database.init_db import init_recruitment_db, utc_now_iso

# This file now acts as a bridge for the new database package
# to maintain backward compatibility with existing services.
