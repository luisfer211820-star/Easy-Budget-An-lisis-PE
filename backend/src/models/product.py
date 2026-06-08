"""
Product model operations for EasyBudget.
Supports soft-delete via the is_deleted / deleted_at columns.
Sprint 4: added `stock` field for inventory management.
"""

import uuid
from datetime import datetime, timezone

from models.db import get_db


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "userId": row["user_id"],
        "name": row["name"],
        "fixedCost": row["fixed_cost"],
        "variableCost": row["variable_cost"],
        "salePrice": row["sale_price"],
        "forecastUnits": row["forecast_units"],
        "stock": row["stock"] if "stock" in row.keys() else 0,
        "isDeleted": bool(row["is_deleted"]),
        "createdAt": row["created_at"],
        "deletedAt": row["deleted_at"],
    }


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def get_products_for_user(user_id: str, deleted: bool = False) -> list[dict]:
    """Return active (or deleted) products belonging to *user_id*."""
    flag = 1 if deleted else 0
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE user_id = ? AND is_deleted = ? ORDER BY created_at DESC",
            (user_id, flag),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_product_by_id(product_id: str) -> dict | None:
    """Return a single product by its primary key."""
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def create_product(
    user_id: str,
    name: str,
    fixed_cost: float,
    variable_cost: float,
    sale_price: float,
    forecast_units: int = 1,
    stock: int = 0,
) -> dict:
    """Insert a new product and return it."""
    product_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO products
               (id, user_id, name, fixed_cost, variable_cost, sale_price, forecast_units, stock, is_deleted, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
            (product_id, user_id, name, fixed_cost, variable_cost, sale_price, forecast_units, stock, created_at),
        )
        conn.commit()
        return get_product_by_id(product_id)
    finally:
        conn.close()


def update_product(
    product_id: str,
    name: str,
    fixed_cost: float,
    variable_cost: float,
    sale_price: float,
    forecast_units: int,
    stock: int = 0,
) -> dict | None:
    """Update fields of an existing product and return the updated row."""
    conn = get_db()
    try:
        cur = conn.execute(
            """UPDATE products
               SET name = ?, fixed_cost = ?, variable_cost = ?, sale_price = ?, forecast_units = ?, stock = ?
               WHERE id = ?""",
            (name, fixed_cost, variable_cost, sale_price, forecast_units, stock, product_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        return get_product_by_id(product_id)
    finally:
        conn.close()


def update_product_stock(product_id: str, stock: int) -> dict | None:
    """Update only the stock field of a product."""
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE products SET stock = ? WHERE id = ? AND is_deleted = 0",
            (stock, product_id),
        )
        conn.commit()
        if cur.rowcount == 0:
            return None
        return get_product_by_id(product_id)
    finally:
        conn.close()


def soft_delete_product(product_id: str) -> bool:
    """Mark a product as deleted. Returns True on success."""
    deleted_at = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE products SET is_deleted = 1, deleted_at = ? WHERE id = ? AND is_deleted = 0",
            (deleted_at, product_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def restore_product(product_id: str) -> bool:
    """Restore a soft-deleted product. Returns True on success."""
    conn = get_db()
    try:
        cur = conn.execute(
            "UPDATE products SET is_deleted = 0, deleted_at = NULL WHERE id = ? AND is_deleted = 1",
            (product_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
