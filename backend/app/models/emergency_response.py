from datetime import datetime

from app.extensions import db


class EmergencyResponse(db.Model):
    __tablename__ = "emergency_responses"
    __table_args__ = (
        db.UniqueConstraint("emergency_id", "responder_id", name="uq_emergency_response_responder"),
    )

    id = db.Column(db.Integer, primary_key=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey("emergencies.id"), nullable=False, index=True)
    responder_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    responder_name = db.Column(db.String(120), nullable=False)
    responder_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    responded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    emergency = db.relationship("Emergency", back_populates="responses")
    responder = db.relationship("User", back_populates="emergency_responses", foreign_keys=[responder_id])

    def to_dict(self):
        created = self.created_at or self.responded_at
        updated = self.updated_at or self.responded_at
        return {
            "id": self.id,
            "emergency_id": self.emergency_id,
            "responder_id": self.responder_id,
            "responder_name": self.responder_name,
            "responder_type": self.responder_type,
            "status": self.status,
            "message": self.message,
            "created_at": created.isoformat() if created else None,
            "updated_at": updated.isoformat() if updated else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }
