"""
Application Configuration
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env file from the backend directory
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "pcos-super-secret-key-change-in-production")

    # Database — SQLite stored inside backend/
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(BASE_DIR, 'pcos.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # CORS — allow frontend origin
    CORS_ORIGINS = ["http://localhost:5000", "http://127.0.0.1:5000"]

    # Model path (relative to project root)
    MODEL_DIR = os.path.join(BASE_DIR, "..", "model")

    # Frontend
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:5000")

    # Email
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_FROM = os.environ.get("MAIL_FROM", MAIL_USERNAME or "noreply@example.com")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "false").lower() == "true"

    # Password reset
    RESET_TOKEN_EXPIRES_MINUTES = int(os.environ.get("RESET_TOKEN_EXPIRES_MINUTES", "30"))
