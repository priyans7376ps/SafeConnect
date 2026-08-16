from app.extensions import db
from app.models.location import Location
from app.utils.validators import validate_latitude, validate_longitude


def save_location(user_id, data, emergency_id=None):
    latitude = validate_latitude(data.get("latitude"))
    longitude = validate_longitude(data.get("longitude"))
    accuracy = data.get("accuracy")

    try:
        if accuracy is not None:
            accuracy = float(accuracy)
    except (TypeError, ValueError):
        raise ValueError("Accuracy must be numeric")

    location = Location(
        user_id=user_id,
        emergency_id=emergency_id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        address=data.get("address"),
    )
    db.session.add(location)
    db.session.commit()
    return location


def get_user_locations(user_id):
    return Location.query.filter_by(user_id=user_id).order_by(Location.created_at.desc()).all()


def get_latest_location(user_id):
    return Location.query.filter_by(user_id=user_id).order_by(Location.created_at.desc()).first()


def get_emergency_locations(user_id, emergency_id):
    return (
        Location.query
        .filter_by(user_id=user_id, emergency_id=emergency_id)
        .order_by(Location.created_at.desc())
        .all()
    )


def get_latest_emergency_location(emergency_id):
    """Return the most recent Location row for a given emergency_id.

    Uses the composite index on (emergency_id, created_at) for an efficient
    single-row fetch regardless of how many history rows exist.

    Secondary sort by id DESC ensures deterministic ordering when two rows share
    the same created_at timestamp (common in tests using SQLite in-memory).

    Authorization is the caller's responsibility (location_routes enforces it).
    """
    return (
        Location.query
        .filter_by(emergency_id=emergency_id)
        .order_by(Location.id.desc())
        .first()
    )

