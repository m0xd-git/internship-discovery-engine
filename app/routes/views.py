"""
Web Views Blueprint
=============================================================================
Serves the student-facing HTML interface:
- Discovery Dashboard (/)
- Profile Editor (/profile)
- Health Check (/health)
=============================================================================
"""

from flask import Blueprint, render_template, jsonify

views_bp = Blueprint("views", __name__)


@views_bp.route("/", methods=["GET"])
def dashboard():
    """Renders the main student discovery and recommendation dashboard."""
    return render_template("dashboard.html")


@views_bp.route("/profile", methods=["GET"])
def profile():
    """Renders the student profile editor."""
    return render_template("profile.html")


@views_bp.route("/health", methods=["GET"])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Internship Discovery & Skill-Gap Recommendation Engine",
        "version": "0.1.0",
    }), 200
