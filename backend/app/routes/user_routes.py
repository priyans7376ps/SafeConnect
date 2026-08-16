from flask import Blueprint, g, request

from app.extensions import db
from app.models.user import User
from app.services.user_service import get_user_by_id, update_user
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response
from app.utils.validators import validate_email, validate_phone

user_bp = Blueprint("users", __name__)


@user_bp.route("/profile", methods=["GET"])
@jwt_required_custom
def get_profile():
    user = get_user_by_id(int(g.current_user_id))
    if not user:
        return error_response("User not found", 404)
    return success_response("Profile retrieved", {"user": user.to_dict()})


@user_bp.route("/profile", methods=["PUT"])
@jwt_required_custom
def update_profile():
    user = get_user_by_id(int(g.current_user_id))
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    try:
        if "email" in data and data["email"] is not None:
            data["email"] = validate_email(data["email"])
        if "phone" in data and data["phone"] is not None:
            data["phone"] = validate_phone(data["phone"])
        updated = update_user(user, data)
        return success_response("Profile updated", {"user": updated.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to update profile", 500)
