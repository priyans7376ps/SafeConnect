from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.services.user_service import authenticate_user, create_user, get_user_by_id
from app.utils.decorators import jwt_required_custom
from app.utils.helpers import error_response, success_response
from app.utils.validators import validate_email, validate_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    try:
        user = create_user(data)
        access_token = create_access_token(identity=str(user.id))
        return success_response("User registered successfully", {"token": access_token, "user": user.to_dict()}, 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        db.session.rollback()
        return error_response("Unable to register user", 500)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    try:
        email = validate_email(data.get("email"))
        password = validate_password(data.get("password"))
        user = authenticate_user(email, password)
        access_token = create_access_token(identity=str(user.id))
        return success_response("Login successful", {"token": access_token, "user": user.to_dict()})
    except ValueError as exc:
        return error_response(str(exc), 401)


@auth_bp.route("/logout", methods=["POST"])
@jwt_required_custom
def logout():
    return success_response("Logged out successfully")


@auth_bp.route("/me", methods=["GET"])
@jwt_required_custom
def me():
    user = get_user_by_id(int(__import__('flask').g.current_user_id))
    if not user:
        return error_response("User not found", 404)
    return success_response("User profile loaded", {"user": user.to_dict()})
