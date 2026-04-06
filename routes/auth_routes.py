from flask import jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from services.user_store import create_user_record, load_users, save_users


def register_auth_routes(app):
    @app.route("/api/auth/signup", methods=["POST"])
    def signup():
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""

        if not name or not email or not password:
            return jsonify({"error": "Name, email, and password are required."}), 400

        users = load_users()
        if email in users:
            return jsonify({"error": "An account already exists for this email."}), 409

        users[email] = create_user_record(name, email, generate_password_hash(password))
        save_users(users)

        session.clear()
        session.permanent = True
        session["user_email"] = email
        return jsonify({"message": "Account created successfully.", "redirect": "/"})

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""

        if not email or not password:
            return jsonify({"error": "Email and password are required."}), 400

        users = load_users()
        user = users.get(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password."}), 401

        from datetime import datetime, timezone

        user["last_login_at"] = datetime.now(timezone.utc).isoformat()
        users[email] = user
        save_users(users)

        session.clear()
        session.permanent = True
        session["user_email"] = email
        return jsonify({"message": "Signed in successfully.", "redirect": "/"})

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        session.pop("user_email", None)
        return jsonify({"message": "Signed out successfully.", "redirect": "/"})
