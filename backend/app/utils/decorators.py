from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.utils.helpers import error_response


def jwt_required_custom(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_identity = get_jwt_identity()
            g.current_user_id = current_identity
            return fn(*args, **kwargs)
        except Exception:
            return error_response("Authentication required", 401)

    return wrapper
