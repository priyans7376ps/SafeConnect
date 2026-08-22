import os
from datetime import timedelta

from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config.settings import get_settings
from app.extensions import cors, db, jwt, limiter, migrate, socketio
from app.middleware.error_handler import register_error_handlers


def create_app(test_config=None):
    settings = get_settings()
    app = Flask(__name__)

    database_url = settings.normalized_database_url

    engine_options = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    if "sqlite" not in database_url.lower():
        engine_options.update({
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        })

    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        JWT_SECRET_KEY=settings.jwt_secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options,
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    )

    if test_config:
        app.config.update(test_config)

    # Reverse proxy header support (HTTPS / X-Forwarded-Proto / X-Forwarded-For)
    proxy_count = int(os.getenv("PROXY_COUNT", "0"))
    if proxy_count > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxy_count,
            x_proto=proxy_count,
            x_host=proxy_count,
            x_port=proxy_count,
            x_prefix=proxy_count,
        )

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": settings.cors_origin_list}},
        supports_credentials=True,
    )
    socketio.init_app(app, cors_allowed_origins=settings.cors_origin_list)

    register_error_handlers(app)

    @app.after_request
    def set_security_headers(response):
        """Production Security Headers."""
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
        # Auto table creation for non-testing environments (Development and Production)
        if not app.config.get("TESTING"):
            db.create_all()

    from app.routes import register_routes
    from app.sockets import register_socket_events

    register_routes(app)
    register_socket_events(app)

    return app