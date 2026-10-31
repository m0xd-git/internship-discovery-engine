"""
Flask Application Factory Package
=============================================================================
Defines create_app() to instantiate and configure the Flask web application.
Supports configuration overrides for isolated testing with temporary databases.
=============================================================================
"""

from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from app.config import DB_PATH

__version__ = "0.1.0"


def create_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Creates and configures a Flask application instance.
    Uses the Application Factory pattern for modularity and testability.
    """
    base_dir = Path(__file__).resolve().parent

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )

    # Default configuration
    app.config["DB_PATH"] = DB_PATH
    app.config["JSON_SORT_KEYS"] = False

    # Apply configuration overrides (e.g. for testing)
    if config_override:
        app.config.update(config_override)

    # Register Blueprints
    from app.routes.api import api_bp
    from app.routes.views import views_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(views_bp)

    # Defensive Error Handlers (never expose internal paths or stack traces)
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "Bad request. Please check the structure and types of your input data.",
            }), 400
        return "Bad Request", 400

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "The requested API endpoint or resource was not found.",
            }), 404
        return "Page Not Found", 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "An unexpected server error occurred. Please try again later.",
            }), 500
        return "Internal Server Error", 500

    return app
