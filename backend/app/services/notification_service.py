from app.extensions import db
from app.models.emergency_response import EmergencyResponse
from app.models.notification import Notification
from app.models.user import User
from app.services.push_service import send_push_to_users

EMERGENCY_ALERT_TYPE = "EMERGENCY_ALERT"
EMERGENCY_RESPONSE_TYPE = "EMERGENCY_RESPONSE"
EMERGENCY_SAFE_TYPE = "EMERGENCY_SAFE"


def create_notification(user_id, title, message, notification_type="INFO", emergency_id=None):
    notification = Notification(
        user_id=user_id,
        emergency_id=emergency_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )
    db.session.add(notification)
    db.session.commit()

    send_push_to_users([user_id], {
        "title": title,
        "body": message,
        "emergency_id": emergency_id,
        "url": f"/emergency/{emergency_id}" if emergency_id else "/notifications",
        "notification_type": notification_type,
    })

    return notification


def broadcast_emergency_alert(emergency):
    """Broadcast an EMERGENCY_ALERT notification to all active users except the owner."""
    if emergency.status != "ACTIVE":
        return {"recipients_notified": 0, "duplicates_skipped": 0}

    owner_id = emergency.user_id

    recipients = User.query.filter(
        User.is_active == True,  # noqa: E712
        User.id != owner_id,
    ).all()

    already_notified_ids = set(
        row.user_id
        for row in Notification.query.filter_by(
            emergency_id=emergency.id,
            notification_type=EMERGENCY_ALERT_TYPE,
        ).with_entities(Notification.user_id).all()
    )

    notified = 0
    skipped = 0
    notified_user_ids = []

    for recipient in recipients:
        if recipient.id in already_notified_ids:
            skipped += 1
            continue

        notification = Notification(
            user_id=recipient.id,
            emergency_id=emergency.id,
            title="Emergency Alert",
            message="A community member has requested emergency assistance.",
            notification_type=EMERGENCY_ALERT_TYPE,
            is_read=False,
        )
        db.session.add(notification)
        notified += 1
        notified_user_ids.append(recipient.id)

    # Web push delivery to newly notified users (omits sensitive coordinates & JWT)
    if notified_user_ids:
        send_push_to_users(notified_user_ids, {
            "title": "SafeConnect Emergency Alert",
            "body": "A community member has requested emergency assistance.",
            "emergency_id": emergency.id,
            "url": f"/emergency/{emergency.id}",
            "notification_type": EMERGENCY_ALERT_TYPE,
        })

    return {"recipients_notified": notified, "duplicates_skipped": skipped}


def notify_owner_of_response(emergency, responder):
    """Notify the emergency owner when a community member clicks I CAN HELP."""
    if not emergency or not responder:
        return None

    owner_id = emergency.user_id
    if owner_id == responder.id:
        return None

    existing = Notification.query.filter_by(
        user_id=owner_id,
        emergency_id=emergency.id,
        notification_type=EMERGENCY_RESPONSE_TYPE,
    ).first()

    message_text = f"{responder.name} has responded to your emergency."

    if existing:
        existing.message = f"Community members (including {responder.name}) have responded to your emergency."
        notification = existing
    else:
        notification = Notification(
            user_id=owner_id,
            emergency_id=emergency.id,
            title="Help is on the way",
            message=message_text,
            notification_type=EMERGENCY_RESPONSE_TYPE,
            is_read=False,
        )
        db.session.add(notification)

    # Web push delivery to emergency owner
    send_push_to_users([owner_id], {
        "title": "Help is on the way",
        "body": message_text,
        "emergency_id": emergency.id,
        "url": f"/emergency/{emergency.id}",
        "notification_type": EMERGENCY_RESPONSE_TYPE,
    })

    return notification


def broadcast_safe_arrival(emergency):
    """Notify alert recipients and responders that the user has reached destination safely."""
    if not emergency or emergency.status != "RESOLVED":
        return {"recipients_notified": 0}

    owner_id = emergency.user_id

    # 1. Alert recipients
    alert_recipients = set(
        row.user_id
        for row in Notification.query.filter_by(
            emergency_id=emergency.id,
            notification_type=EMERGENCY_ALERT_TYPE,
        ).with_entities(Notification.user_id).all()
    )

    # 2. Responders
    responders = set(
        row.responder_id
        for row in EmergencyResponse.query.filter_by(
            emergency_id=emergency.id
        ).with_entities(EmergencyResponse.responder_id).all()
        if row.responder_id is not None
    )

    eligible_user_ids = (alert_recipients | responders) - {owner_id}

    already_notified_ids = set(
        row.user_id
        for row in Notification.query.filter_by(
            emergency_id=emergency.id,
            notification_type=EMERGENCY_SAFE_TYPE,
        ).with_entities(Notification.user_id).all()
    )

    notified = 0
    to_push_ids = []

    for uid in eligible_user_ids:
        if uid in already_notified_ids:
            continue

        notification = Notification(
            user_id=uid,
            emergency_id=emergency.id,
            title="Emergency Resolved",
            message="The user has reached their destination safely.",
            notification_type=EMERGENCY_SAFE_TYPE,
            is_read=False,
        )
        db.session.add(notification)
        notified += 1
        to_push_ids.append(uid)

    if to_push_ids:
        send_push_to_users(to_push_ids, {
            "title": "Emergency Resolved",
            "body": "The user has reached their destination safely.",
            "emergency_id": emergency.id,
            "url": f"/emergency/{emergency.id}",
            "notification_type": EMERGENCY_SAFE_TYPE,
        })

    return {"recipients_notified": notified}


def get_notifications(user_id):
    return Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()


def get_unread_notifications(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).order_by(Notification.created_at.desc()).all()


def mark_notification_read(notification_id, user_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        raise ValueError("Notification not found")
    notification.is_read = True
    db.session.commit()
    return notification


def mark_all_notifications_read(user_id):
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return notifications
