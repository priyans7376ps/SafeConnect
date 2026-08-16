from datetime import datetime

from app.extensions import db


class Emergency(db.Model):
    __tablename__ = "emergencies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    emergency_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ACTIVE", index=True)
    priority = db.Column(db.String(20), nullable=False, default="MEDIUM")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="emergencies")
    locations = db.relationship("Location", back_populates="emergency", cascade="all, delete-orphan")
    responses = db.relationship("EmergencyResponse", back_populates="emergency", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="emergency", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "emergency_type": self.emergency_type,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
