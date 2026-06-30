"""
Authentication Routes
---------------------
POST /api/auth/register  — Create new account
POST /api/auth/login     — Login, receive JWT tokens
POST /api/auth/forgot-password — Email password reset link
POST /api/auth/reset-password  — Reset password using one-time token
GET  /api/auth/me        — Get current user profile
POST /api/auth/refresh   — Refresh access token
"""
from datetime import datetime, timedelta
import secrets

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from extensions import db, bcrypt
from mailer import send_password_reset_email, send_welcome_email
from models import User, PasswordResetToken

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    for field in ["name", "email", "password"]:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    email = data["email"].strip().lower()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    user = User(
        name=data["name"].strip(),
        email=email,
        password_hash=password_hash,
        age=data.get("age"),
    )
    db.session.add(user)
    db.session.commit()

    send_welcome_email(user)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Account created successfully",
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Login successful",
        "user":          user.to_dict(),
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "'email' is required"}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).update(
            {"used_at": datetime.utcnow()}
        )

        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=PasswordResetToken.hash_token(raw_token),
            expires_at=datetime.utcnow() + timedelta(
                minutes=current_app.config["RESET_TOKEN_EXPIRES_MINUTES"]
            ),
        )
        db.session.add(reset_token)
        db.session.commit()

        frontend_base = current_app.config["FRONTEND_BASE_URL"].rstrip("/")
        reset_url = f"{frontend_base}/reset-password.html?token={raw_token}"
        send_password_reset_email(user, reset_url)

    return jsonify({
        "message": "If an account with that email exists, a password reset link has been sent."
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    password = data.get("password", "")

    if not token or not password:
        return jsonify({"error": "'token' and 'password' are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    token_hash = PasswordResetToken.hash_token(token)
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    if not reset_token or not reset_token.is_usable():
        return jsonify({"error": "This password reset link is invalid or has expired"}), 400

    user = User.query.get(reset_token.user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    reset_token.used_at = datetime.utcnow()
    PasswordResetToken.query.filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.id != reset_token.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": datetime.utcnow()}, synchronize_session=False)
    db.session.commit()

    return jsonify({"message": "Password reset successful. Please sign in."}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity     = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token}), 200
