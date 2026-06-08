"""
EasyBudget – Flask application entry point.
Run with:  python app.py
"""

import sys
import os

# Ensure the src/ directory is on sys.path so that `models` and `routes`
# packages can be imported regardless of the working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

from models.db import init_db
from routes.auth import auth_bp
from routes.products import products_bp


def create_app() -> Flask:
    app = Flask(__name__)

    # Enable CORS for all origins
    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    # Health-check endpoint
    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    # Create tables on startup
    init_db()

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
