"""
Authentication routes – register & login.
Blueprint prefix: /api/auth
"""

from flask import Blueprint, jsonify, request

from models.user import authenticate_user, create_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"ok": False, "error": "name, email and password are required"}), 400

    user = create_user(name, email, password)
    if user is None:
        return jsonify({"ok": False, "error": "Email already registered"}), 409

    return jsonify({"ok": True, "user": user}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"ok": False, "error": "email and password are required"}), 400

    user = authenticate_user(email, password)
    if user is None:
        return jsonify({"ok": False, "error": "Invalid email or password"}), 401

    return jsonify({"ok": True, "user": user}), 200
