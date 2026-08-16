from flask import Blueprint, g, request

from app.extensions import db
from app.models.emergency import Emergency
from app.models.emergency_response import EmergencyResponse
from app.models.user import User
from app.services.notification_service import notify_owner_of_response
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response

response_bp = Blueprint("responses", __name__)


def _handle_create_response(emergency_id, user_id, data):
    """Shared helper for processing an 'I CAN HELP' emergency response."""
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)
    if emergency.status != "ACTIVE":
        return error_response("Emergency is not active", 400)
    if emergency.user_id == user_id:
        return error_response("The emergency owner cannot respond to their own emergency", 403)
    if EmergencyResponse.query.filter_by(emergency_id=emergency_id, responder_id=user_id).first():
        return error_response("You have already responded to this emergency", 409)

    message = (data.get("message") or "I can help").strip()
    if not message:
        return error_response("Message is required", 400)

    responder = User.query.get(user_id)
    responder_name = responder.name if responder else "Volunteer"
    responder_type = "USER"

    response = EmergencyResponse(
        emergency_id=emergency_id,
        responder_id=user_id,
        responder_name=responder_name,
        responder_type=responder_type,
        status="ACCEPTED",
        message=message,
    )
    db.session.add(response)

    # Notify emergency owner
    notify_owner_of_response(emergency, responder)

    db.session.commit()
    return success_response("Response added", {"response": response.to_dict()}, 201)


@response_bp.route("/responses/emergency/<int:emergency_id>", methods=["GET"])
@jwt_required_custom
def get_responses(emergency_id):
    user_id = int(g.current_user_id)
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return error_response("Emergency not found", 404)

    # Owner or authorized responder can view responses
    is_owner = (emergency.user_id == user_id)
    is_responder = bool(EmergencyResponse.query.filter_by(emergency_id=emergency_id, responder_id=user_id).first())
    if not (is_owner or is_responder):
        return error_response("Not authorized to view responses for this emergency", 403)

    responses = EmergencyResponse.query.filter_by(emergency_id=emergency_id).order_by(EmergencyResponse.created_at.desc()).all()
    return success_response("Responses retrieved", {"responses": [item.to_dict() for item in responses]})


@response_bp.route("/responses/emergency/<int:emergency_id>", methods=["POST"])
@jwt_required_custom
def create_response(emergency_id):
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    return _handle_create_response(emergency_id, user_id, data)
