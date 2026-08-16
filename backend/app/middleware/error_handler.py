from flask import Flask

from app.utils.helpers import error_response


def register_error_handlers(app: Flask):
    @app.errorhandler(400)
    def bad_request(error):
        return error_response("Bad request", 400)

    @app.errorhandler(401)
    def unauthorized(error):
        return error_response("Authentication required", 401)

    @app.errorhandler(403)
    def forbidden(error):
        return error_response("Forbidden", 403)

    @app.errorhandler(404)
    def not_found(error):
        return error_response("Resource not found", 404)

    @app.errorhandler(409)
    def conflict(error):
        return error_response("Conflict", 409)

    @app.errorhandler(422)
    def unprocessable(error):
        return error_response("Unprocessable entity", 422)

    @app.errorhandler(500)
    def server_error(error):
        return error_response("Internal server error", 500)
