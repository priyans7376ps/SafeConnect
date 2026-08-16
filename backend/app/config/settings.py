import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass
class Settings:
    flask_env: str = os.getenv("FLASK_ENV", "development")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///safeconnect.db")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    cors_origins: str = os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_URL", "http://localhost:5173"))
    vapid_public_key: str = os.getenv("VAPID_PUBLIC_KEY", "")
    vapid_private_key: str = os.getenv("VAPID_PRIVATE_KEY", "")
    vapid_claim_email: str = os.getenv("VAPID_CLAIM_EMAIL", "mailto:security@safeconnect.local")

    @property
    def normalized_database_url(self) -> str:
        url = self.database_url
        if url and url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.flask_env.lower() in ("production", "prod")

    @property
    def cors_origin_list(self):
        if not self.cors_origins or self.cors_origins.strip() == "*":
            if self.is_production:
                # In production, disallow wildcard CORS
                return [self.frontend_url] if self.frontend_url else []
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def get_settings():
    return Settings()

