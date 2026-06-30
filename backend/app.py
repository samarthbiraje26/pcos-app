"""
Flask Application Factory
--------------------------
Run with:
    python app.py
The server starts at http://localhost:5000
"""
import os
from flask import Flask, send_from_directory, jsonify

from extensions import db, jwt, bcrypt, cors
from config import Config


def create_app(config_class=Config):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )
    app.config.from_object(config_class)

    # ── Extensions ──────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # ── JWT error handlers ───────────────────────────────────────────────
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({"error": "Authorization required", "reason": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "Invalid token", "reason": reason}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    # ── Blueprints ───────────────────────────────────────────────────────
    from auth      import auth_bp
    from predict   import predict_bp
    from history   import history_bp
    from diet      import diet_bp
    from chat      import chat_bp
    from awareness import awareness_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(diet_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(awareness_bp)

    # ── Serve frontend static files ──────────────────────────────────────
    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        # SPA fallback
        return send_from_directory(app.static_folder, "index.html")

    # ── Create database tables on startup ────────────────────────────────
    with app.app_context():
        db.create_all()
        print("[DB] ✅ Database tables ready.")

    return app


if __name__ == "__main__":
    application = create_app()
    print("\n" + "=" * 55)
    print("  PCOS Detection App  |  http://localhost:5000")
    print("=" * 55 + "\n")
    application.run(debug=True, host="0.0.0.0", port=5000)
