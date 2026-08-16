from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.utils.validators import validate_email, validate_password, validate_phone


def create_user(data):
    name = (data.get("name") or "").strip()
    email = validate_email(data.get("email"))
    phone = validate_phone(data.get("phone"))
    password = validate_password(data.get("password"))

    if not name:
        raise ValueError("Name is required")

    user = User(name=name, email=email, phone=phone)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("Email already registered")
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email.strip().lower()).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def update_user(user, data):
    if "name" in data and data["name"] is not None:
        user.name = data["name"].strip()
    if "phone" in data and data["phone"] is not None:
        user.phone = validate_phone(data["phone"])
    if "email" in data and data["email"] is not None:
        user.email = validate_email(data["email"])
    if "profile_image" in data and data["profile_image"] is not None:
        user.profile_image = data["profile_image"]
    db.session.commit()
    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user or not user.check_password(password):
        raise ValueError("Invalid email or password")
    return user
