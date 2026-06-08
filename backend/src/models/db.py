"""
SQLite database initialization for EasyBudget.
Database file is stored at backend/src/easybudget.db.
"""

import os
import sqlite3

# Resolve the database path: use /tmp on Render (ephemeral but writable),
# otherwise store next to this file locally.
_src_dir = os.path.dirname(os.path.abspath(__file__))
if os.environ.get("RENDER"):
    DB_PATH = "/tmp/easybudget.db"
else:
    DB_PATH = os.path.join(os.path.dirname(_src_dir), "easybudget.db")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    fixed_cost REAL NOT NULL,
    variable_cost REAL NOT NULL,
    sale_price REAL NOT NULL,
    forecast_units INTEGER NOT NULL DEFAULT 1,
    stock INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    deleted_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def get_db() -> sqlite3.Connection:
    """Return a new database connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Apply incremental migrations for existing databases."""
    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()
    }
    if "stock" not in existing_cols:
        conn.execute("ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0")
        conn.commit()


def init_db() -> None:
    """Create tables if they do not exist yet, then run migrations."""
    conn = get_db()
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
        _migrate(conn)
    finally:
        conn.close()
