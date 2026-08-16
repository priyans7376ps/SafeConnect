from datetime import datetime

from sqlalchemy import Index

from app.extensions import db


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey("emergencies.id"), nullable=True, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Composite index: speeds up "latest location for this emergency" queries.
    # ORDER BY created_at DESC with emergency_id filter uses this index directly.
    __table_args__ = (
        Index("ix_location_emergency_created", "emergency_id", "created_at"),
    )

    user = db.relationship("User", back_populates="locations")
    emergency = db.relationship("Emergency", back_populates="locations")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "emergency_id": self.emergency_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy": self.accuracy,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
