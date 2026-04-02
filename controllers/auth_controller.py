from flask import jsonify, request, session

from models.user_model import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_for_login,
    update_last_login,
    update_password,
)
from utils.security import hash_password, verify_password
from utils.validators import normalize_login_identifier, validate_signup_payload


def signup():
    payload = request.get_json(silent=True) or {}
    errors = validate_signup_payload(payload)
    if errors:
        return jsonify({"error": errors[0]}), 400

    name = payload["name"].strip()
    email = payload["email"].strip().lower()
    username = normalize_login_identifier(payload.get("username") or email)
    password = payload["password"]

    if get_user_by_username(username):
        return jsonify({"error": "Username already taken"}), 409

    if get_user_by_email(email):
        return jsonify({"error": "An account already exists for this email."}), 409

    create_user(
        name=name,
        email=email,
        username=username,
        password_hash=hash_password(password),
    )

    session.clear()
    session.permanent = True
    session["user_email"] = email
    return jsonify({"message": "Account created successfully.", "redirect": "/"})


def login():
    payload = request.get_json(silent=True) or {}
    password = payload.get("password") or ""
    identifier = normalize_login_identifier(
        payload.get("username") or payload.get("email") or ""
    )

    if not identifier or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = get_user_for_login(identifier)
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401

    password_is_valid, should_upgrade = verify_password(
        plain_password=password,
        stored_password=user["password"],
        password_algorithm=user.get("password_algorithm") or "bcrypt",
    )
    if not password_is_valid:
        return jsonify({"error": "Invalid email or password."}), 401

    if should_upgrade:
        update_password(user["email"], hash_password(password))

    update_last_login(user["email"])

    session.clear()
    session.permanent = True
    session["user_email"] = user["email"]
    return jsonify({"message": "Signed in successfully.", "redirect": "/"})
