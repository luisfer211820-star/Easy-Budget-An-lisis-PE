"""
User model operations for EasyBudget.
"""

import uuid
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from models.db import get_db


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict (only safe fields)."""
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def create_user(name: str, email: str, password: str) -> dict | None:
    """
    Register a new user.

    Returns the public user dict on success, or None if the email
    already exists.
    """
    user_id = str(uuid.uuid4())
    hashed = generate_password_hash(password)
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (id, name, email, password, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, hashed, created_at),
        )
        conn.commit()
        return {"id": user_id, "name": name, "email": email}
    except Exception:
        # Most likely a UNIQUE constraint on email
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
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None:
            return None
        if not check_password_hash(row["password"], password):
            return None
        return _row_to_dict(row)
    finally:
        conn.close()
