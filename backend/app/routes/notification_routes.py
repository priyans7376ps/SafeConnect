from flask import Blueprint, g, request

from app.extensions import db
from app.models.notification import Notification
from app.services.notification_service import (
    get_notifications,
    get_unread_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.services.push_service import save_push_subscription
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response

notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/notifications", methods=["GET"])
@jwt_required_custom
def list_notifications():
    user_id = int(g.current_user_id)
    notifications = get_notifications(user_id)
    return success_response("Notifications retrieved", {"notifications": [item.to_dict() for item in notifications]})


@notification_bp.route("/notifications/unread", methods=["GET"])
@jwt_required_custom
def unread_notifications():
    user_id = int(g.current_user_id)
    notifications = get_unread_notifications(user_id)
    return success_response("Unread notifications retrieved", {"notifications": [item.to_dict() for item in notifications]})


@notification_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@jwt_required_custom
def mark_read(notification_id):
    user_id = int(g.current_user_id)
    try:
        notification = mark_notification_read(notification_id, user_id)
        return success_response("Notification marked as read", {"notification": notification.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception:
        db.session.rollback()
        return error_response("Unable to update notification", 500)


@notification_bp.route("/notifications/read-all", methods=["PUT"])
@jwt_required_custom
def mark_all_read():
    user_id = int(g.current_user_id)
    try:
        notifications = mark_all_notifications_read(user_id)
        return success_response("All notifications marked as read", {"notifications": [item.to_dict() for item in notifications]})
    except Exception:
        db.session.rollback()
        return error_response("Unable to update notifications", 500)


@notification_bp.route("/notifications/push-subscription", methods=["POST"])
@jwt_required_custom
def create_push_subscription():
    user_id = int(g.current_user_id)
    data = request.get_json(silent=True) or {}
    try:
        sub = save_push_subscription(user_id, data)
        return success_response("Push subscription saved", {"subscription": sub.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to save push subscription", 500)
