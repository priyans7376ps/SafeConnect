import re


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[+]?\d[\d\s\-()]{7,}$")


def validate_required(value, field_name):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} is required")
    return value


def validate_email(email):
    email = validate_required(email, "Email")
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email.strip()):
        raise ValueError("Invalid email address")
    return email.strip().lower()


def validate_phone(phone):
    phone = validate_required(phone, "Phone")
    if not isinstance(phone, str) or not PHONE_PATTERN.match(phone.strip()):
        raise ValueError("Invalid phone number")
    return phone.strip()


def validate_password(password):
    password = validate_required(password, "Password")
    if not isinstance(password, str) or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long")
    return password


def validate_latitude(latitude):
    try:
        latitude = float(latitude)
    except (TypeError, ValueError):
        raise ValueError("Latitude must be a numeric value")
    if latitude < -90 or latitude > 90:
        raise ValueError("Latitude must be between -90 and 90")
    return latitude


def validate_longitude(longitude):
    try:
        longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("Longitude must be a numeric value")
    if longitude < -180 or longitude > 180:
        raise ValueError("Longitude must be between -180 and 180")
    return longitude


def validate_emergency_status(status):
    allowed = {"ACTIVE", "RESOLVED", "CANCELLED"}
    status_value = validate_required(status, "Status")
    normalized = str(status_value).upper()
    if normalized not in allowed:
        raise ValueError("Invalid emergency status")
    return normalized


def validate_priority(priority):
    allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    priority_value = validate_required(priority, "Priority")
    normalized = str(priority_value).upper()
    if normalized not in allowed:
        raise ValueError("Invalid emergency priority")
    return normalized
