from datetime import datetime

from app.extensions import db
from app.models.emergency import Emergency
from app.models.emergency_response import EmergencyResponse
from app.models.notification import Notification
from app.services.notification_service import broadcast_emergency_alert, broadcast_safe_arrival
from app.utils.validators import validate_emergency_status, validate_priority


def create_emergency(user_id, data):
    """Create an ACTIVE emergency and broadcast EMERGENCY_ALERT to all community members."""
    emergency_type = (data.get("emergency_type") or "").strip()
    description = (data.get("description") or "").strip()
    priority = validate_priority(data.get("priority", "MEDIUM"))

    if not emergency_type:
        raise ValueError("Emergency type is required")
    if not description:
        raise ValueError("Description is required")

    emergency = Emergency(
        user_id=user_id,
        emergency_type=emergency_type,
        description=description,
        status="ACTIVE",
        priority=priority,
    )
    db.session.add(emergency)
    db.session.flush()

    broadcast_emergency_alert(emergency)

    db.session.commit()
    return emergency


def get_user_emergencies(user_id):
    return Emergency.query.filter_by(user_id=user_id).order_by(Emergency.created_at.desc()).all()


def get_emergency_by_id(user_id, emergency_id):
    emergency = Emergency.query.filter_by(id=emergency_id).first()
    if not emergency:
        return None
    if can_view_emergency(user_id, emergency):
        return emergency
    return None


def is_emergency_owner(user_id, emergency):
    return emergency and emergency.user_id == user_id


def is_authorized_response_user(user_id, emergency):
    return bool(
        emergency
        and EmergencyResponse.query.filter_by(
            emergency_id=emergency.id, responder_id=user_id
        ).first()
    )


def is_emergency_alert_recipient(user_id, emergency):
    if not emergency:
        return False
    return bool(
        Notification.query.filter_by(
            user_id=user_id,
            emergency_id=emergency.id,
            notification_type="EMERGENCY_ALERT",
        ).first()
    )


def can_view_emergency(user_id, emergency):
    return bool(
        emergency
        and (
            is_emergency_owner(user_id, emergency)
            or is_authorized_response_user(user_id, emergency)
            or is_emergency_alert_recipient(user_id, emergency)
        )
    )


def build_public_emergency_payload(emergency):
    return {
        "id": emergency.id,
        "emergency_type": emergency.emergency_type,
        "description": emergency.description,
        "status": emergency.status,
        "priority": emergency.priority,
        "created_at": emergency.created_at.isoformat() if emergency.created_at else None,
    }


def update_emergency(user_id, emergency_id, data):
    emergency = get_emergency_by_id(user_id, emergency_id)
    if not emergency:
        raise ValueError("Emergency not found")
    if "emergency_type" in data and data["emergency_type"]:
        emergency.emergency_type = str(data["emergency_type"]).strip()
    if "description" in data and data["description"]:
        emergency.description = str(data["description"]).strip()
    if "priority" in data and data["priority"]:
        emergency.priority = validate_priority(data["priority"])
    if "status" in data and data["status"]:
        old_status = emergency.status
        new_status = validate_emergency_status(data["status"])
        emergency.status = new_status
        if new_status in {"RESOLVED", "CANCELLED"} and not emergency.resolved_at:
            emergency.resolved_at = datetime.utcnow()
        if old_status != "RESOLVED" and new_status == "RESOLVED":
            broadcast_safe_arrival(emergency)
    db.session.commit()
    return emergency


def resolve_emergency(user_id, emergency_id):
    emergency = get_emergency_by_id(user_id, emergency_id)
    if not emergency:
        raise ValueError("Emergency not found")
    if emergency.status == "RESOLVED":
        raise ValueError("Emergency is already resolved")
    emergency.status = "RESOLVED"
    emergency.resolved_at = datetime.utcnow()

    # Create EMERGENCY_SAFE in-app notifications for alert recipients and responders
    broadcast_safe_arrival(emergency)

    db.session.commit()
    return emergency


def cancel_emergency(user_id, emergency_id):
    emergency = get_emergency_by_id(user_id, emergency_id)
    if not emergency:
        raise ValueError("Emergency not found")
    if emergency.status == "CANCELLED":
        raise ValueError("Emergency is already cancelled")
    emergency.status = "CANCELLED"
    emergency.resolved_at = datetime.utcnow()
    db.session.commit()
    return emergency
