from datetime import datetime

from sqlalchemy import UniqueConstraint

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey("emergencies.id"), nullable=True, index=True)
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, default="INFO")
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Prevent duplicate EMERGENCY_ALERT per (user, emergency).
    # Works for both SQLite (tests) and PostgreSQL (production).
    __table_args__ = (
        UniqueConstraint(
            "user_id", "emergency_id", "notification_type",
            name="uq_notification_user_emergency_type",
        ),
    )

    user = db.relationship("User", back_populates="notifications")
    emergency = db.relationship("Emergency", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "emergency_id": self.emergency_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

