"""
Product CRUD routes with soft-delete, restore, and stock management.
Blueprint prefix: /api/products
Sprint 4: added PATCH /<id>/stock endpoint.
"""

from flask import Blueprint, jsonify, request

from models.product import (
    create_product,
    get_product_by_id,
    get_products_for_user,
    restore_product,
    soft_delete_product,
    update_product,
    update_product_stock,
)

products_bp = Blueprint("products", __name__, url_prefix="/api/products")


# ---- List active products --------------------------------------------------
@products_bp.route("", methods=["GET"])
def list_products():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "user_id query parameter is required"}), 400

    products = get_products_for_user(user_id, deleted=False)
    return jsonify({"ok": True, "products": products}), 200


# ---- List deleted (soft-deleted) products -----------------------------------
@products_bp.route("/deleted", methods=["GET"])
def list_deleted_products():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "user_id query parameter is required"}), 400

    products = get_products_for_user(user_id, deleted=True)
    return jsonify({"ok": True, "products": products}), 200


# ---- Get single product -----------------------------------------------------
@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    product = get_product_by_id(product_id)
    if product is None:
        return jsonify({"ok": False, "error": "Product not found"}), 404
    return jsonify({"ok": True, "product": product}), 200


# ---- Create product ---------------------------------------------------------
@products_bp.route("", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    name = data.get("name", "").strip()
    fixed_cost = data.get("fixedCost")
    variable_cost = data.get("variableCost")
    sale_price = data.get("salePrice")
    forecast_units = data.get("forecastUnits", 1)
    stock = data.get("stock", 0)

    if not user_id or not name or fixed_cost is None or variable_cost is None or sale_price is None:
        return jsonify({"ok": False, "error": "user_id, name, fixedCost, variableCost and salePrice are required"}), 400

    product = create_product(
        user_id=user_id,
        name=name,
        fixed_cost=float(fixed_cost),
        variable_cost=float(variable_cost),
        sale_price=float(sale_price),
        forecast_units=int(forecast_units),
        stock=int(stock),
    )
    return jsonify({"ok": True, "product": product}), 201


# ---- Update product ---------------------------------------------------------
@products_bp.route("/<product_id>", methods=["PUT"])
def update(product_id):
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    fixed_cost = data.get("fixedCost")
    variable_cost = data.get("variableCost")
    sale_price = data.get("salePrice")
    forecast_units = data.get("forecastUnits")
    stock = data.get("stock", 0)

    if not name or fixed_cost is None or variable_cost is None or sale_price is None or forecast_units is None:
        return jsonify({"ok": False, "error": "name, fixedCost, variableCost, salePrice and forecastUnits are required"}), 400

    product = update_product(
        product_id=product_id,
        name=name,
        fixed_cost=float(fixed_cost),
        variable_cost=float(variable_cost),
        sale_price=float(sale_price),
        forecast_units=int(forecast_units),
        stock=int(stock),
    )
    if product is None:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    return jsonify({"ok": True, "product": product}), 200


# ---- Update stock only (Sprint 4 — HU013) -----------------------------------
@products_bp.route("/<product_id>/stock", methods=["PATCH"])
def patch_stock(product_id):
    data = request.get_json(silent=True) or {}
    stock = data.get("stock")

    if stock is None or int(stock) < 0:
        return jsonify({"ok": False, "error": "stock must be a non-negative integer"}), 400

    product = update_product_stock(product_id, int(stock))
    if product is None:
        return jsonify({"ok": False, "error": "Product not found or deleted"}), 404

    return jsonify({"ok": True, "product": product}), 200


# ---- Soft-delete product ----------------------------------------------------
@products_bp.route("/<product_id>", methods=["DELETE"])
def delete(product_id):
    success = soft_delete_product(product_id)
    if not success:
        return jsonify({"ok": False, "error": "Product not found or already deleted"}), 404
    return jsonify({"ok": True}), 200


# ---- Restore product --------------------------------------------------------
@products_bp.route("/<product_id>/restore", methods=["POST"])
def restore(product_id):
    success = restore_product(product_id)
    if not success:
        return jsonify({"ok": False, "error": "Product not found or not deleted"}), 404
    return jsonify({"ok": True}), 200
