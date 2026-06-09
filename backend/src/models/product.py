"""
Product model operations for EasyBudget.
Supports soft-delete via is_deleted / deleted_at columns.
Sprint 4: added `stock` field for inventory management.
Compatible with both PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime, timezone

from models.db import USE_POSTGRES, get_db, ph


def _row_to_dict(row):
    """Convert a DB row (dict or sqlite3.Row) to a plain dict."""
    if row is None:
        return None
    if USE_POSTGRES:
        # row is already a dict
        return {
            "id": row["id"],
            "userId": row["user_id"],
            "name": row["name"],
            "fixedCost": row["fixed_cost"],
            "variableCost": row["variable_cost"],
            "salePrice": row["sale_price"],
            "forecastUnits": row["forecast_units"],
            "stock": row.get("stock", 0) if isinstance(row, dict) else row["stock"],
            "isDeleted": bool(row["is_deleted"]),
            "createdAt": row["created_at"],
            "deletedAt": row["deleted_at"],
        }
    else:
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


def _pg_fetchone(conn, sql, params=()):
    """Execute a query and return one row as dict (PostgreSQL)."""
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    if row is None:
        return None
    cols = [desc[0] for desc in cur.description]
    return dict(zip(cols, row))


def _pg_fetchall(conn, sql, params=()):
    """Execute a query and return all rows as list of dicts (PostgreSQL)."""
    cur = conn.cursor()
    cur.execute(sql, params)
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def get_products_for_user(user_id: str, deleted: bool = False) -> list[dict]:
    """Return active (or deleted) products belonging to user_id."""
    flag = 1 if deleted else 0
    conn = get_db()
    p = ph()
    try:
        sql = f"SELECT * FROM products WHERE user_id = {p} AND is_deleted = {p} ORDER BY created_at DESC"
        if USE_POSTGRES:
            rows = _pg_fetchall(conn, sql, (user_id, flag))
        else:
            rows = conn.execute(sql, (user_id, flag)).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_product_by_id(product_id: str) -> dict | None:
    """Return a single product by its primary key."""
    conn = get_db()
    p = ph()
    try:
        sql = f"SELECT * FROM products WHERE id = {p}"
        if USE_POSTGRES:
            row = _pg_fetchone(conn, sql, (product_id,))
        else:
            row = conn.execute(sql, (product_id,)).fetchone()
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
    p = ph()
    try:
        sql = (
            f"INSERT INTO products "
            f"(id, user_id, name, fixed_cost, variable_cost, sale_price, "
            f"forecast_units, stock, is_deleted, created_at) "
            f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},0,{p})"
        )
        params = (product_id, user_id, name, fixed_cost, variable_cost,
                  sale_price, forecast_units, stock, created_at)
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
        else:
            conn.execute(sql, params)
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
    p = ph()
    try:
        sql = (
            f"UPDATE products "
            f"SET name={p}, fixed_cost={p}, variable_cost={p}, "
            f"sale_price={p}, forecast_units={p}, stock={p} "
            f"WHERE id={p}"
        )
        params = (name, fixed_cost, variable_cost, sale_price, forecast_units, stock, product_id)
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            if cur.rowcount == 0:
                return None
        else:
            cur = conn.execute(sql, params)
            conn.commit()
            if cur.rowcount == 0:
                return None
        return get_product_by_id(product_id)
    finally:
        conn.close()


def update_product_stock(product_id: str, stock: int) -> dict | None:
    """Update only the stock field of a product."""
    conn = get_db()
    p = ph()
    try:
        sql = f"UPDATE products SET stock={p} WHERE id={p} AND is_deleted=0"
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, (stock, product_id))
            conn.commit()
            if cur.rowcount == 0:
                return None
        else:
            cur = conn.execute(sql, (stock, product_id))
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
    p = ph()
    try:
        sql = f"UPDATE products SET is_deleted=1, deleted_at={p} WHERE id={p} AND is_deleted=0"
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, (deleted_at, product_id))
            conn.commit()
            return cur.rowcount > 0
        else:
            cur = conn.execute(sql, (deleted_at, product_id))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


def restore_product(product_id: str) -> bool:
    """Restore a soft-deleted product. Returns True on success."""
    conn = get_db()
    p = ph()
    try:
        sql = f"UPDATE products SET is_deleted=0, deleted_at=NULL WHERE id={p} AND is_deleted=1"
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(sql, (product_id,))
            conn.commit()
            return cur.rowcount > 0
        else:
            cur = conn.execute(sql, (product_id,))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()
