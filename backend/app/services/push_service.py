import json
import logging
import os
from pywebpush import WebPushException, webpush

from app.extensions import db
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


def get_vapid_config():
    """Retrieve VAPID keys and claims email from environment variables."""
    return {
        "private_key": os.getenv("VAPID_PRIVATE_KEY", ""),
        "public_key": os.getenv("VAPID_PUBLIC_KEY", ""),
        "claim_email": os.getenv("VAPID_CLAIM_EMAIL", "mailto:security@safeconnect.local"),
    }


def save_push_subscription(user_id, data):
    """Save or update a Web Push subscription for an authenticated user.

    Idempotent: Duplicate subscriptions for the same endpoint do not create
    duplicate records.
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid subscription payload")

    endpoint = data.get("endpoint")
    keys = data.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        raise ValueError("Subscription must contain endpoint, keys.p256dh, and keys.auth")

    user_agent = data.get("user_agent") or ""

    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.user_id = user_id
        existing.p256dh = p256dh
        existing.auth = auth
        existing.user_agent = user_agent
        db.session.commit()
        return existing

    sub = PushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        user_agent=user_agent,
    )
    db.session.add(sub)
    db.session.commit()
    return sub


def send_web_push_notification(subscription, payload):
    """Send a Web Push notification to a single PushSubscription record.

    Automatically removes stale/invalid subscriptions (HTTP 404/410) from DB.
    """
    vapid_cfg = get_vapid_config()
    private_key = vapid_cfg["private_key"]
    claim_email = vapid_cfg["claim_email"]

    # Security check: Ensure coordinates, passwords, and JWTs are omitted from push payloads
    clean_payload = {
        "title": payload.get("title", "SafeConnect Alert"),
        "body": payload.get("body", "Important update from SafeConnect"),
        "icon": payload.get("icon", "/shield-icon.png"),
        "data": {
            "emergency_id": payload.get("emergency_id"),
            "url": payload.get("url", "/notifications"),
            "notification_type": payload.get("notification_type", "INFO"),
        },
    }

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth,
        },
    }

    if not private_key:
        logger.info("VAPID_PRIVATE_KEY not set; skipping actual Web Push delivery.")
        return True

    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(clean_payload),
            vapid_private_key=private_key,
            vapid_claims={"sub": claim_email},
        )
        return True
    except WebPushException as exc:
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code in (404, 410):
            # Subscription expired or invalid — remove stale record
            logger.warning("Push subscription expired (%s), removing from database.", status_code)
            db.session.delete(subscription)
            db.session.commit()
        else:
            logger.error("Web Push delivery failed: %s", exc)
        return False
    except Exception as exc:
        logger.error("Unexpected Web Push error: %s", exc)
        return False


def send_push_to_users(user_ids, payload):
    """Broadcast Web Push notification to all active push subscriptions for a list of user IDs."""
    if not user_ids:
        return 0

    user_ids = list(set(user_ids))
    subscriptions = PushSubscription.query.filter(PushSubscription.user_id.in_(user_ids)).all()

    success_count = 0
    for sub in subscriptions:
        if send_web_push_notification(sub, payload):
            success_count += 1

    return success_count
