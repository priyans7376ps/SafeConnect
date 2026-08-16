from flask import Blueprint, g, request

from app.extensions import db, socketio
from app.models.emergency import Emergency
from app.models.emergency_response import EmergencyResponse
from app.services.location_service import (
    get_emergency_locations,
    get_latest_emergency_location,
    get_latest_location,
    get_user_locations,
    save_location,
)
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response

location_bp = Blueprint("locations", __name__)


def _is_owner_or_responder(user_id, emergency):
    """Return True if user is the emergency owner or an authorized responder."""
    if not emergency:
        return False
    if emergency.user_id == user_id:
        return True
    return bool(
        EmergencyResponse.query.filter_by(
            emergency_id=emergency.id, responder_id=user_id
        ).first()
    )


# ---------------------------------------------------------------------------
# General location endpoints (not emergency-scoped)
# ---------------------------------------------------------------------------

@location_bp.route("/locations", methods=["POST"])
@jwt_required_custom
def create_location():
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    try:
        location = save_location(user_id, data)
        return success_response("Location saved", {"location": location.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to save location", 500)


@location_bp.route("/locations", methods=["GET"])
@jwt_required_custom
def get_locations():
    user_id = int(g.current_user_id)
    locations = get_user_locations(user_id)
    return success_response("Locations retrieved", {"locations": [item.to_dict() for item in locations]})


@location_bp.route("/locations/latest", methods=["GET"])
@jwt_required_custom
def get_latest():
    user_id = int(g.current_user_id)
    location = get_latest_location(user_id)
    if not location:
        return error_response("No location found", 404)
    return success_response("Latest location retrieved", {"location": location.to_dict()})


# ---------------------------------------------------------------------------
# Emergency-scoped location endpoints
# ---------------------------------------------------------------------------

@location_bp.route("/locations/emergency/<int:emergency_id>", methods=["POST"])
@jwt_required_custom
def create_emergency_location(emergency_id):
    """Submit a live location update for an active emergency.

    Authorization rules (Milestone 1 IDOR fix preserved):
      - Must be authenticated.
      - Emergency must exist.
      - Emergency must be ACTIVE (rejects RESOLVED / CANCELLED).
      - Only the emergency owner may write location updates.
    """
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if emergency.status != "ACTIVE":
        return error_response("Location updates are only allowed while the emergency is active", 400)
    if emergency.user_id != user_id:
        return error_response("Only the emergency owner may create emergency location updates", 403)

    data = request.get_json(silent=True) or {}
    try:
        location = save_location(user_id, data, emergency_id=emergency_id)
        payload = {
            "emergency_id": emergency_id,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "timestamp": location.created_at.isoformat() if location.created_at else None,
        }
        socketio.emit("location_update", payload, to=f"emergency:{emergency_id}")
        return success_response("Emergency location saved", {"location": location.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to save emergency location", 500)


@location_bp.route("/locations/emergency/<int:emergency_id>", methods=["GET"])
@jwt_required_custom
def get_emergency_locations_route(emergency_id):
    """Return all location history for an emergency.

    Authorization: owner or authorized responder only.
    Random users who received an EMERGENCY_ALERT may NOT read private locations.
    """
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if not _is_owner_or_responder(user_id, emergency):
        return error_response("Not authorized to view this emergency location", 403)

    locations = get_emergency_locations(user_id, emergency_id)
    return success_response(
        "Emergency locations retrieved",
        {"locations": [item.to_dict() for item in locations]},
    )


@location_bp.route("/locations/emergency/<int:emergency_id>/latest", methods=["GET"])
@jwt_required_custom
def get_latest_emergency_location_route(emergency_id):
    """Return the most recent location for an emergency.

    Authorization: owner or authorized responder only.
    Response omits user_id and address to avoid exposing unnecessary personal data.
    """
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if not _is_owner_or_responder(user_id, emergency):
        return error_response("Not authorized to view this emergency location", 403)

    location = get_latest_emergency_location(emergency_id)
    if not location:
        return error_response("No location data found for this emergency", 404)

    return success_response(
        "Latest emergency location retrieved",
        {
            "location": {
                "emergency_id": location.emergency_id,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "accuracy": location.accuracy,
                "timestamp": location.created_at.isoformat() if location.created_at else None,
            }
        },
    )
