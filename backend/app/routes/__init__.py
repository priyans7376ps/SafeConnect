from app.routes.auth_routes import auth_bp
from app.routes.contact_routes import contact_bp
from app.routes.emergency_routes import emergency_bp
from app.routes.health_routes import health_bp
from app.routes.location_routes import location_bp
from app.routes.notification_routes import notification_bp
from app.routes.response_routes import response_bp
from app.routes.user_routes import user_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(emergency_bp, url_prefix="/api/emergencies")
    app.register_blueprint(location_bp, url_prefix="/api")
    app.register_blueprint(contact_bp, url_prefix="/api")
    app.register_blueprint(response_bp, url_prefix="/api")
    app.register_blueprint(notification_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
