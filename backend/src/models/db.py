"""
Database initialization for EasyBudget.

Uses PostgreSQL (via psycopg2) when the DATABASE_URL environment variable is
set (production / Render), and falls back to SQLite for local development.
"""

import os
import sqlite3

# ── Detect which engine to use ───────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Supabase/Render sometimes gives "postgres://" which psycopg2 needs as
# "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

# SQLite fallback path (local only)
_src_dir = os.path.dirname(os.path.abspath(__file__))
_SQLITE_PATH = os.path.join(os.path.dirname(_src_dir), "easybudget.db")

# ── Schema (PostgreSQL syntax, uses %s placeholders) ─────────────────────────
_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL REFERENCES users(id),
    name           TEXT NOT NULL,
    fixed_cost     REAL NOT NULL,
    variable_cost  REAL NOT NULL,
    sale_price     REAL NOT NULL,
    forecast_units INTEGER NOT NULL DEFAULT 1,
    stock          INTEGER NOT NULL DEFAULT 0,
    is_deleted     INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL,
    deleted_at     TEXT
);
"""

# SQLite schema (uses ? placeholders)
_SQLITE_SCHEMA = _PG_SCHEMA  # same DDL works for both

# ── Connection helpers ────────────────────────────────────────────────────────

def get_db():
    """Return a ready-to-use connection (PostgreSQL or SQLite)."""
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(_SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _placeholder(n: int = 1) -> str:
    """Return the right parameter placeholder for the active engine."""
    return "%s" if USE_POSTGRES else "?"


def ph() -> str:
    """Single placeholder string for the active engine."""
    return "%s" if USE_POSTGRES else "?"


# ── Init / migrate ────────────────────────────────────────────────────────────

def _fetchall_as_dicts(cursor):
    """Convert cursor results to list of dicts (works for both engines)."""
    if USE_POSTGRES:
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    else:
        return cursor.fetchall()


def _fetchone_as_dict(cursor):
    """Convert single cursor result to dict (works for both engines)."""
    if USE_POSTGRES:
        if cursor.description is None:
            return None
        cols = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(cols, row)) if row else None
    else:
        return cursor.fetchone()


def init_db() -> None:
    """Create tables if they do not exist yet."""
    conn = get_db()
    try:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(_PG_SCHEMA)
            # Add stock column if missing (migration)
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='products' AND column_name='stock'
                    ) THEN
                        ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0;
                    END IF;
                END
                $$;
            """)
            conn.commit()
        else:
            conn.executescript(_SQLITE_SCHEMA)
            conn.commit()
            # SQLite migration: add stock column if missing
            existing = {
                row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()
            }
            if "stock" not in existing:
                conn.execute("ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0")
                conn.commit()
    finally:
        conn.close()
