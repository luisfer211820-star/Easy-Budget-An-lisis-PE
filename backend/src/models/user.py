"""
User model operations for EasyBudget.
Compatible with both PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from models.db import USE_POSTGRES, get_db, ph


def _row_to_dict(row):
    """Convert a DB row to a plain dict (only safe fields)."""
    if row is None:
        return None
    if USE_POSTGRES:
        return {"id": row["id"], "name": row["name"], "email": row["email"]}
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def create_user(name: str, email: str, password: str) -> dict | None:
    """
    Register a new user.
    Returns the public user dict on success, or None if the email already exists.
    """
    user_id = str(uuid.uuid4())
    hashed = generate_password_hash(password)
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        p = ph()
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(
                f"INSERT INTO users (id, name, email, password, created_at) VALUES ({p},{p},{p},{p},{p})",
                (user_id, name, email, hashed, created_at),
            )
            conn.commit()
        else:
            conn.execute(
                f"INSERT INTO users (id, name, email, password, created_at) VALUES ({p},{p},{p},{p},{p})",
                (user_id, name, email, hashed, created_at),
            )
            conn.commit()
        return {"id": user_id, "name": name, "email": email}
    except Exception:
        # Most likely a UNIQUE constraint on email
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    """
    Validate credentials.
    Returns the public user dict if email + password match, else None.
    """
    conn = get_db()
    try:
        p = ph()
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM users WHERE email = {p}", (email,))
            row = cur.fetchone()
            if row is None:
                return None
            cols = [desc[0] for desc in cur.description]
            row_dict = dict(zip(cols, row))
            if not check_password_hash(row_dict["password"], password):
                return None
            return {"id": row_dict["id"], "name": row_dict["name"], "email": row_dict["email"]}
        else:
            row = conn.execute(f"SELECT * FROM users WHERE email = {p}", (email,)).fetchone()
            if row is None:
                return None
            if not check_password_hash(row["password"], password):
                return None
            return _row_to_dict(row)
    finally:
        conn.close()
