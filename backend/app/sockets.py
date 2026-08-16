from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room

from app.extensions import db, socketio
from app.models.emergency import Emergency
from app.models.emergency_response import EmergencyResponse
from app.models.user import User


def get_token_from_socket_context(auth_data=None, data=None):
    """Extract JWT token string from connection auth dict, event data dict, or request query/header."""
    token = None
    if isinstance(auth_data, dict):
        token = auth_data.get("token") or auth_data.get("Authorization")
    if not token and isinstance(data, dict):
        token = data.get("token") or data.get("Authorization")
    if not token and request:
        token = request.args.get("token")
        if not token and request.headers.get("Authorization"):
            auth_header = request.headers.get("Authorization")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
    if token and isinstance(token, str) and token.startswith("Bearer "):
        token = token.split(" ", 1)[1]
    return token


def authenticate_socket_user(auth_data=None, data=None):
    """Decode JWT token and return authenticated user_id (int) or None if invalid/missing."""
    token = get_token_from_socket_context(auth_data, data)
    if not token:
        return None
    try:
        decoded = decode_token(token)
        user_id = decoded.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except Exception:
        return None


def register_socket_events(app):
    """Register all Flask-SocketIO event handlers."""

    @socketio.on("connect")
    def handle_connect(auth=None):
        pass

    @socketio.on("disconnect")
    def handle_disconnect():
        pass

    @socketio.on("join_emergency")
    def handle_join_emergency(data):
        """Handler for joining an authorized emergency location room."""
        if not isinstance(data, dict):
            emit("error", {"message": "Invalid payload format"})
            return

        emergency_id = data.get("emergency_id")
        if not emergency_id:
            emit("error", {"message": "Emergency ID is required"})
            return

        try:
            emergency_id = int(emergency_id)
        except (ValueError, TypeError):
            emit("error", {"message": "Invalid emergency ID"})
            return

        # Authenticate user from socket connection / event data
        user_id = authenticate_socket_user(data=data)
        if not user_id:
            emit("error", {"message": "Authentication required"})
            return

        emergency = Emergency.query.filter_by(id=emergency_id).first()
        if not emergency:
            emit("error", {"message": "Emergency not found"})
            return

        if emergency.status != "ACTIVE":
            emit("error", {"message": "Cannot join an emergency that is not active"})
            return

        # Authorization check: Emergency owner OR authorized responder
        is_owner = (emergency.user_id == user_id)
        is_responder = bool(
            EmergencyResponse.query.filter_by(
                emergency_id=emergency.id, responder_id=user_id
            ).first()
        )

        if not (is_owner or is_responder):
            emit("error", {"message": "Not authorized to join this emergency room"})
            return

        room_name = f"emergency:{emergency_id}"
        join_room(room_name)
        emit("joined_emergency", {"event": "joined_emergency", "emergency_id": emergency_id})

    @socketio.on("leave_emergency")
    def handle_leave_emergency(data):
        if isinstance(data, dict) and "emergency_id" in data:
            try:
                emergency_id = int(data["emergency_id"])
                leave_room(f"emergency:{emergency_id}")
            except Exception:
                pass
