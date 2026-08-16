from flask import Blueprint
from sqlalchemy import text

from app.extensions import db
from app.utils.helpers import error_response, success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Simple API health check endpoint (Part 5 / Phase 11)."""
    return success_response("Service operational", {"status": "ok", "service": "SafeConnect API", "version": "1.0.0"})


@health_bp.route("/health/db", methods=["GET"])
def health_db_check():
    """Database connectivity health check without exposing internal credentials."""
    try:
        db.session.execute(text("SELECT 1"))
        return success_response("Database connected", {"status": "ok", "database": "healthy"})
    except Exception:
        return error_response("Database connection unhealthy", 500)
