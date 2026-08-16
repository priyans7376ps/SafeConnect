from flask import Blueprint, g, request

from app.extensions import db, socketio
from app.models.emergency import Emergency
from app.routes.response_routes import _handle_create_response
from app.services.emergency_service import (
    build_public_emergency_payload,
    cancel_emergency,
    can_view_emergency,
    create_emergency,
    get_user_emergencies,
    resolve_emergency,
    update_emergency,
)
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response

emergency_bp = Blueprint("emergencies", __name__)


def _emit_emergency_ended_if_needed(emergency):
    """Helper to emit emergency_ended event if status is RESOLVED or CANCELLED."""
    if emergency and emergency.status in {"RESOLVED", "CANCELLED"}:
        payload = {
            "event": "emergency_ended",
            "emergency_id": emergency.id,
            "status": emergency.status,
        }
        socketio.emit("emergency_ended", payload, to=f"emergency:{emergency.id}")


@emergency_bp.route("", methods=["POST"])
@jwt_required_custom
def create():
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    try:
        emergency = create_emergency(user_id, data)
        return success_response("Emergency created", {"emergency": emergency.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to create emergency", 500)


@emergency_bp.route("", methods=["GET"])
@jwt_required_custom
def list_emergencies():
    user_id = int(g.current_user_id)
    emergencies = get_user_emergencies(user_id)
    return success_response("Emergencies retrieved", {"emergencies": [item.to_dict() for item in emergencies]})


@emergency_bp.route("/community/active", methods=["GET"])
@jwt_required_custom
def list_active_community_emergencies():
    emergencies = Emergency.query.filter_by(status="ACTIVE").order_by(Emergency.created_at.desc()).all()
    return success_response("Active community emergencies retrieved", {"emergencies": [build_public_emergency_payload(item) for item in emergencies]})


@emergency_bp.route("/<int:emergency_id>", methods=["GET"])
@jwt_required_custom
def get_emergency(emergency_id):
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if not can_view_emergency(user_id, emergency):
        return error_response("Not authorized to view this emergency", 403)
    return success_response("Emergency retrieved", {"emergency": emergency.to_dict()})


@emergency_bp.route("/<int:emergency_id>/respond", methods=["POST"])
@jwt_required_custom
def respond(emergency_id):
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    return _handle_create_response(emergency_id, user_id, data)


@emergency_bp.route("/<int:emergency_id>", methods=["PUT"])
@jwt_required_custom
def update(emergency_id):
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if emergency.user_id != user_id:
        return error_response("Not authorized to update this emergency", 403)
    data = request.get_json(silent=True) or {}
    try:
        emergency = update_emergency(user_id, emergency_id, data)
        _emit_emergency_ended_if_needed(emergency)
        return success_response("Emergency updated", {"emergency": emergency.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to update emergency", 500)


@emergency_bp.route("/<int:emergency_id>/resolve", methods=["POST"])
@jwt_required_custom
def resolve(emergency_id):
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if emergency.user_id != user_id:
        return error_response("Not authorized to resolve this emergency", 403)
    try:
        emergency = resolve_emergency(user_id, emergency_id)
        _emit_emergency_ended_if_needed(emergency)
        return success_response("Emergency resolved", {"emergency": emergency.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to resolve emergency", 500)


@emergency_bp.route("/<int:emergency_id>/cancel", methods=["POST"])
@jwt_required_custom
def cancel(emergency_id):
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if emergency.user_id != user_id:
        return error_response("Not authorized to cancel this emergency", 403)
    try:
        emergency = cancel_emergency(user_id, emergency_id)
        _emit_emergency_ended_if_needed(emergency)
        return success_response("Emergency cancelled", {"emergency": emergency.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to cancel emergency", 500)
