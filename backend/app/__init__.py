from datetime import timedelta

from flask import Flask, request

from app.config.settings import get_settings
from app.extensions import cors, db, jwt, socketio
from app.middleware.error_handler import register_error_handlers


def create_app(test_config=None):
    settings = get_settings()
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        JWT_SECRET_KEY=settings.jwt_secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.cors_origin_list}},
        supports_credentials=True,
    )
    socketio.init_app(app, cors_allowed_origins=settings.cors_origin_list)

    register_error_handlers(app)

    @app.after_request
    def set_security_headers(response):
        """Part H — Production Security Headers."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    with app.app_context():
        from app.models import (  # noqa: F401
            Emergency,
            EmergencyResponse,
            Location,
            Notification,
            PushSubscription,
            TrustedContact,
            User,
        )
        db.create_all()

    from app.routes import register_routes
    from app.sockets import register_socket_events

    register_routes(app)
    register_socket_events(app)

    return app
